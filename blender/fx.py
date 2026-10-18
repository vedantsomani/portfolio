"""Physical motion for the film's final renders, shared by arrival.py and lab.py.

Two kinds:
  - Computed every frame from the scene clock (geometry nodes): the wind in the plants and the
    engines' downwash flattening them, dust kicked up at each footstep, dust motes drifting in the
    light. The motion is solved in closed form (ballistic paths with air drag, gusts as moving
    noise), so any frame can be rendered on its own, in any order, on any GPU.
  - Simulated (Mantaflow): the dust cloud the lander's engines raise as it lands. It is baked once
    to disk before rendering and read back by every render process.
Everything here only builds data; the shots decide where it goes.
"""

import math
import random

import bpy
from mathutils import Vector

G_DUST = 0.06  # m/s: how fast fine dust settles out of the air


# ---------------------------------------------------------------------------------------------
# A small builder for geometry-node trees: sockets or plain numbers in, sockets out.

class Nodes:
    def __init__(self, ng):
        self.ng = ng
        self.n = ng.nodes
        self.L = ng.links

    def new(self, kind, **props):
        nd = self.n.new(kind)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def put(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.L.new(val, sock)
        else:
            sock.default_value = val

    def math(self, op, a, b=None, c=None):
        nd = self.new('ShaderNodeMath', operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def add(self, a, b):
        return self.math('ADD', a, b)

    def sub(self, a, b):
        return self.math('SUBTRACT', a, b)

    def mul(self, a, b):
        return self.math('MULTIPLY', a, b)

    def div(self, a, b):
        return self.math('DIVIDE', a, b)

    def vmath(self, op, a, b=None, scale=None):
        nd = self.new('ShaderNodeVectorMath', operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if scale is not None:
            self.put(nd.inputs['Scale'], scale)
        return nd.outputs['Vector'] if op != 'LENGTH' else nd.outputs['Value']

    def vscale(self, v, s):
        return self.vmath('SCALE', v, scale=s)

    def xyz(self, x, y, z):
        nd = self.new('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.put(nd.inputs[i], v)
        return nd.outputs[0]

    def sep(self, v):
        nd = self.new('ShaderNodeSeparateXYZ')
        self.put(nd.inputs[0], v)
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def noise(self, vec, w, scale=1.0, detail=2.0):
        """4D noise, 0..1: vec is where, w is when."""
        nd = self.new('ShaderNodeTexNoise', noise_dimensions='4D')
        self.put(nd.inputs['Vector'], vec)
        self.put(nd.inputs['W'], w)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        return nd.outputs[0]

    def noise3(self, vec, w, scale=1.0, detail=2.0):
        """A 4D noise vector, each component -0.5..0.5."""
        nd = self.new('ShaderNodeTexNoise', noise_dimensions='4D')
        self.put(nd.inputs['Vector'], vec)
        self.put(nd.inputs['W'], w)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        return self.vmath('SUBTRACT', nd.outputs['Color'], (0.5, 0.5, 0.5))

    def attr(self, name, kind='FLOAT'):
        nd = self.new('GeometryNodeInputNamedAttribute', data_type=kind)
        nd.inputs['Name'].default_value = name
        return nd.outputs['Attribute']

    def time(self):
        return self.new('GeometryNodeInputSceneTime').outputs['Seconds']

    def position(self):
        return self.new('GeometryNodeInputPosition').outputs['Position']


def tree(name):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = Nodes(ng)
    return ng, g, g.new('NodeGroupInput').outputs[0], g.new('NodeGroupOutput').inputs[0]


def points_object(name, pts, attrs):
    """A mesh of loose vertices with per-point attributes: attrs = {name: (kind, values)}."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    for key, (kind, values) in attrs.items():
        a = me.attributes.new(key, kind, 'POINT')
        if kind == 'FLOAT_VECTOR':
            a.data.foreach_set('vector', [c for v in values for c in v])
        else:
            a.data.foreach_set('value', list(values))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------------------------------------
# Walking routes: polylines on the ground, their corners rounded so a walker turns over a couple
# of metres, as people do, instead of snapping round in a frame.

def heading(v):
    """Heading (radians, 0 = +Y) of a direction in the ground plane."""
    return math.atan2(-v.x, v.y)


def route(points, dist, turn=1.2):
    """Position and heading at a distance along a route; past the end, they stop at its end."""
    pts = [Vector((p[0], p[1], 0.0)) for p in points]

    def along(x):
        if x <= 0:
            return pts[0] + (pts[1] - pts[0]).normalized() * x
        for a, b in zip(pts, pts[1:]):
            seg = (b - a).length
            if x <= seg:
                return a.lerp(b, x / seg) if seg else a.copy()
            x -= seg
        return pts[-1] + (pts[-1] - pts[-2]).normalized() * x

    d = min(dist, sum((b - a).length for a, b in zip(pts, pts[1:])))
    k = 8
    pos = sum((along(d + turn * (2 * i / k - 1)) for i in range(k + 1)), Vector()) / (k + 1)
    return pos, heading(along(d + turn) - along(d - turn))


# ---------------------------------------------------------------------------------------------
# Wind. Plants are instanced on points (arrival.scatter_col); wind tilts each instance about its
# base. Slow gusts roll across the street along WIND_DIR, each plant flutters on its own, and the
# lander's downwash pushes everything away from the 'downwash' empty, as hard as its scale.x
# (radians of lean at the centre, falling off over ~9 m).

WIND_DIR = (0.8, 0.6)


def downwash():
    ob = bpy.data.objects.get('downwash')
    if ob is None:
        ob = bpy.data.objects.new('downwash', None)
        bpy.context.scene.collection.objects.link(ob)
        ob.scale = (0.0, 0.0, 0.0)
    return ob


def wind_euler(g, euler, amp, flutter, seed=0.0):
    """The instance rotation (an Euler socket, its z the plant's own spin) with the wind's lean
    added. amp: lean in a gust, flutter: each plant's own quick sway (radians)."""
    pos = g.position()
    t = g.time()
    gust = g.noise(g.vscale(pos, 0.05), g.mul(t, 0.22), detail=2.0)
    gust = g.math('MULTIPLY_ADD', g.math('SUBTRACT', gust, 0.3), 2.5, 0.3)  # ~0.3..1.3
    gust = g.math('MAXIMUM', gust, 0.0)
    fl = g.noise3(g.vscale(pos, 1.3), g.add(g.mul(t, 1.6), seed), detail=1.0)
    fx, fy, _ = g.sep(fl)
    lean = g.mul(gust, amp)
    wx = g.add(g.mul(lean, WIND_DIR[0]), g.mul(fx, flutter * 2))
    wy = g.add(g.mul(lean, WIND_DIR[1]), g.mul(fy, flutter * 2))
    info = g.new('GeometryNodeObjectInfo', transform_space='ORIGINAL')
    info.inputs['Object'].default_value = downwash()
    dx, dy, _ = g.sep(g.vmath('SUBTRACT', pos, info.outputs['Location']))
    dist = g.math('MAXIMUM', g.math('SQRT', g.add(g.mul(dx, dx), g.mul(dy, dy))), 0.3)
    sx, _, _ = g.sep(info.outputs['Scale'])
    push = g.mul(sx, g.math('EXPONENT', g.div(dist, -9.0)))
    turb = g.math('MULTIPLY_ADD', g.noise(g.vscale(pos, 0.8), g.mul(t, 7.0), detail=2.0), 0.9, 0.55)
    push = g.mul(push, turb)
    wx = g.add(wx, g.mul(push, g.div(dx, dist)))
    wy = g.add(wy, g.mul(push, g.div(dy, dist)))
    # Into the plant's own frame (it is spun about z), then a lean about its local x and y.
    ex, ey, ez = g.sep(euler)
    c, s = g.math('COSINE', ez), g.math('SINE', ez)
    lx = g.add(g.mul(wx, c), g.mul(wy, s))
    ly = g.sub(g.mul(wy, c), g.mul(wx, s))
    return g.xyz(g.sub(ex, ly), g.add(ey, lx), ez)


# ---------------------------------------------------------------------------------------------
# Dust in the air, as real volumes (points grown into a density grid each frame).

def dust_mat(name, color=(0.55, 0.5, 0.42), density=1.6, aniso=0.35):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001 - always on in newer versions
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*color, 1)
    v.inputs['Anisotropy'].default_value = aniso
    # Wisps: the grid's density broken up by noise, so a puff is never a clean ball.
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    att = nt.nodes.new('ShaderNodeAttribute')
    att.attribute_name = 'density'
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.35
    mr.inputs['From Max'].default_value = 0.75
    mr.inputs['To Min'].default_value = 0.0
    mr.inputs['To Max'].default_value = density
    nt.links.new(nz.outputs[0], mr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(att.outputs['Fac'], mul.inputs[0])
    nt.links.new(mr.outputs['Result'], mul.inputs[1])
    nt.links.new(mul.outputs[0], v.inputs['Density'])
    nt.links.new(v.outputs['Volume'], out.inputs['Volume'])
    return m


def puffs(name, events, mat, seed=1, voxel=0.025):
    """Dust thrown up by an impact. events: (time s, position, strength). Each puff is a few dozen
    grains of air flung outward and up, slowed by drag (k), settling at G_DUST, each lasting its
    own lifetime so the puff thins out instead of vanishing. Rendered as a volume."""
    rng = random.Random(seed)
    pts, tb, v0, life, r0 = [], [], [], [], []
    for at, pos, strength in events:
        for _ in range(int(28 * strength) + 6):
            a = rng.uniform(0, 2 * math.pi)
            sp = rng.uniform(0.35, 1.2) * strength
            pts.append(Vector(pos) + Vector((rng.gauss(0, 0.04), rng.gauss(0, 0.04), 0.02)))
            tb.append(at + rng.uniform(0.0, 0.06))
            v0.append((sp * math.cos(a), sp * math.sin(a), rng.uniform(0.15, 0.55) * strength))
            life.append(rng.uniform(0.9, 2.6))
            r0.append(rng.uniform(0.035, 0.075) * (0.7 + 0.3 * strength))
    if not pts:
        return None
    ob = points_object(name, pts, {'tb': ('FLOAT', tb), 'v0': ('FLOAT_VECTOR', v0),
                                   'life': ('FLOAT', life), 'r0': ('FLOAT', r0)})
    ng, g, gin, gout = tree(name)
    tau = g.sub(g.time(), g.attr('tb'))
    alive = g.math('MULTIPLY', g.math('GREATER_THAN', tau, 0.0),
                   g.math('LESS_THAN', tau, g.attr('life')))
    k = 3.2  # 1/s: air drag on fine dust
    tt = g.math('MAXIMUM', tau, 0.0)
    flung = g.div(g.sub(1.0, g.math('EXPONENT', g.mul(tt, -k))), k)
    offset = g.vmath('ADD', g.vscale(g.attr('v0', 'FLOAT_VECTOR'), flung),
                     g.xyz(0.0, 0.0, g.mul(tt, -G_DUST)))
    # Turbulence: the grains wander as the puff spreads.
    offset = g.vmath('ADD', offset, g.vscale(g.noise3(g.position(), g.mul(tau, 0.6), 3.0), g.mul(tt, 0.25)))
    m2p = g.new('GeometryNodeMeshToPoints')
    g.L.new(gin, m2p.inputs['Mesh'])
    sp = g.new('GeometryNodeSetPosition')
    g.L.new(m2p.outputs['Points'], sp.inputs['Geometry'])
    g.put(sp.inputs['Offset'], offset)
    grow = g.math('MULTIPLY_ADD', g.sub(1.0, g.math('EXPONENT', g.mul(tt, -1.8))), 1.6, 0.4)
    radius = g.mul(g.mul(g.attr('r0'), grow), alive)
    p2v = g.new('GeometryNodePointsToVolume')
    g.L.new(sp.outputs['Geometry'], p2v.inputs['Points'])
    try:
        p2v.inputs['Resolution Mode'].default_value = 'Size'
    except (TypeError, KeyError):
        p2v.resolution_mode = 'VOXEL_SIZE'
    p2v.inputs['Voxel Size'].default_value = voxel
    p2v.inputs['Density'].default_value = 1.0
    g.put(p2v.inputs['Radius'], radius)
    sm = g.new('GeometryNodeSetMaterial')
    g.L.new(p2v.outputs['Volume'], sm.inputs['Geometry'])
    sm.inputs['Material'].default_value = mat
    g.L.new(sm.outputs['Geometry'], gout)
    ob.modifiers.new(name, 'NODES').node_group = ng
    return ob


def motes(name, lo, hi, count, seed=2, radius=0.0008, color=(0.85, 0.82, 0.75)):
    """Dust motes hanging in a room's air, drifting on slow currents, a little falling. They only
    show where light crosses them."""
    rng = random.Random(seed)
    pts = [Vector((rng.uniform(lo[0], hi[0]), rng.uniform(lo[1], hi[1]), rng.uniform(lo[2], hi[2])))
           for _ in range(count)]
    size = [radius * rng.uniform(0.5, 1.6) for _ in pts]
    ob = points_object(name, pts, {'size': ('FLOAT', size)})
    ng, g, gin, gout = tree(name)
    t = g.time()
    drift = g.vscale(g.noise3(g.vscale(g.position(), 0.6), g.mul(t, 0.04), 1.0, 2.0), 0.9)
    offset = g.vmath('ADD', drift, g.xyz(0.0, 0.0, g.mul(t, -0.012)))
    m2p = g.new('GeometryNodeMeshToPoints')
    g.L.new(gin, m2p.inputs['Mesh'])
    g.put(m2p.inputs['Radius'], g.attr('size'))
    sp = g.new('GeometryNodeSetPosition')
    g.L.new(m2p.outputs['Points'], sp.inputs['Geometry'])
    g.put(sp.inputs['Offset'], offset)
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001
        pass
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = 0.9
    sm = g.new('GeometryNodeSetMaterial')
    g.L.new(sp.outputs['Geometry'], sm.inputs['Geometry'])
    sm.inputs['Material'].default_value = m
    g.L.new(sm.outputs['Geometry'], gout)
    ob.modifiers.new(name, 'NODES').node_group = ng
    return ob


# ---------------------------------------------------------------------------------------------
# Footsteps: where and when each foot comes down, read off the posed figure.

class Steps:
    """Call sample(time) once per frame after posing the figure; events() then lists each foot's
    landings (the lowest point of each swing, when it is near the ground). ground and strength are
    numbers or functions of the foot's position: the floor's height there, and how much dust it
    holds (0 for none)."""

    def __init__(self, fig, ground=0.0, strength=1.0):
        self.feet = [fig.j['ankleL'], fig.j['ankleR']]
        self.ground = ground if callable(ground) else (lambda p, z=ground: z)
        self.strength = strength if callable(strength) else (lambda p, s=strength: s)
        self.track = {0: [], 1: []}

    def sample(self, t):
        bpy.context.view_layer.update()
        for i, f in enumerate(self.feet):
            self.track[i].append((t, f.matrix_world.translation.copy()))

    def slide(self, contact=0.11):
        """How much planted feet skate: the mean and the 95th-percentile ground speed (m/s) of a
        foot while it is down. A clean walk is near zero."""
        speeds = []
        for tr in self.track.values():
            for (t0, p0), (t1, p1) in zip(tr, tr[1:]):
                if p0.z - self.ground(p0) < contact and p1.z - self.ground(p1) < contact:
                    speeds.append((p1 - p0).xy.length / (t1 - t0))
        if not speeds:
            return 0.0, 0.0
        speeds.sort()
        return sum(speeds) / len(speeds), speeds[int(0.95 * (len(speeds) - 1))]

    def events(self, gap=0.4, contact=0.095):
        """Each landing: the frame a foot comes down to the ground (its ankle within contact of
        the floor) from the air."""
        out = []
        for tr in self.track.values():
            last = -1e9
            for (_, p0), (t1, p1) in zip(tr, tr[1:]):
                base = self.ground(p1)
                if p0.z - self.ground(p0) > contact >= p1.z - base and t1 - last > gap:
                    last = t1
                    s = self.strength(p1)
                    if s > 0:
                        out.append((t1, Vector((p1.x, p1.y, base)), s))
        return out


# ---------------------------------------------------------------------------------------------
# The landing's dust cloud, simulated.

def landing_dust(center, size, cache_dir, res, mat_color=(0.68, 0.62, 0.53), sectors=8):
    """A gas domain over the landing site (bounded by the street's walls) and ground emitters in a
    ring under the engines, blowing outward. Returns (domain, [flow settings]) so the shot can key
    how much dust the blast lifts each frame."""
    cx, cy, cz = center
    sx, sy, sz = size
    me = bpy.data.meshes.new('dust-domain')
    me.from_pydata([(cx + x * sx / 2, cy + y * sy / 2, cz + z * sz / 2)
                    for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    dom = bpy.data.objects.new('dust-domain', me)
    bpy.context.scene.collection.objects.link(dom)
    fm = dom.modifiers.new('Fluid', 'FLUID')
    fm.fluid_type = 'DOMAIN'
    d = fm.domain_settings
    d.domain_type = 'GAS'
    d.resolution_max = res
    d.use_adaptive_domain = False
    d.alpha = 0.04  # dust barely rises on its own
    d.beta = 0.0
    d.vorticity = 0.45
    d.use_dissolve_smoke = True
    d.dissolve_speed = 45
    d.use_dissolve_smoke_log = True
    d.use_noise = res >= 96
    d.noise_scale = 2
    for border, on in (('use_collision_border_bottom', True), ('use_collision_border_left', True),
                       ('use_collision_border_right', True), ('use_collision_border_top', False),
                       ('use_collision_border_front', False), ('use_collision_border_back', False)):
        if hasattr(d, border):
            setattr(d, border, on)
    d.cache_type = 'ALL'
    d.cache_directory = cache_dir
    d.cache_data_format = 'OPENVDB'
    d.openvdb_cache_compress_type = 'BLOSC'
    try:
        d.openvdb_data_depth = '16'
    except TypeError:
        pass
    m = dust_mat('dust-cloud', mat_color, density=1.8, aniso=0.3)
    dom.data.materials.append(m)
    flows = []
    r0, r1 = 1.2, 6.5
    # The emitters sit just above the floor's layer of cells (the boundary clears anything in it).
    z0 = 1.5 * max(size) / res
    for k in range(sectors):
        a0, a1 = 2 * math.pi * k / sectors, 2 * math.pi * (k + 1) / sectors
        verts, faces = [], []
        n = 6
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            verts += [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0),
                      (cx + r1 * math.cos(a), cy + r1 * math.sin(a), z0)]
            if i:
                faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
        fme = bpy.data.meshes.new(f'dust-flow{k}')
        fme.from_pydata(verts, [], faces)
        fob = bpy.data.objects.new(f'dust-flow{k}', fme)
        bpy.context.scene.collection.objects.link(fob)
        fob.hide_render = True
        ff = fob.modifiers.new('Fluid', 'FLUID')
        ff.fluid_type = 'FLOW'
        f = ff.flow_settings
        f.flow_type = 'SMOKE'
        f.flow_behavior = 'INFLOW'
        f.flow_source = 'MESH'
        f.use_plane_init = True  # a flat sheet on the ground, not a closed solid
        f.surface_distance = 0.6
        f.density = 0.0
        f.smoke_color = mat_color
        f.temperature = 0.0
        f.use_initial_velocity = True
        mid = (a0 + a1) / 2
        f.velocity_coord = (5.5 * math.cos(mid), 5.5 * math.sin(mid), 0.5)
        f.subframes = 1
        flows.append(f)
    return dom, flows


def bake_fluid(dom):
    with bpy.context.temp_override(scene=bpy.context.scene, object=dom, active_object=dom,
                                   selected_objects=[dom], selected_editable_objects=[dom]):
        bpy.ops.fluid.bake_all()
