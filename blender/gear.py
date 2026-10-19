"""The crew member's gear, made to fit the MakeHuman body (blender/human.py calls build()).

  suit    a one-piece flight suit in the modern style: the body's own surface from the ankles to
          the collar and the wrists, stood off a few millimetres, so it bends exactly with the
          skeleton; white fabric with charcoal side, shoulder and knee panels, seams, a front zip
          and grime from the trip. The skin under it is hidden.
  cap     a fitted comms cap over the skull and the ears, with earcups (no hair to fake)
  helmet  a sleek shell with a large clear visor, so the face shows inside; a neck ring
  pack    a compact expedition pack on the back
The body faces -Y here (MakeHuman's convention); crew.py turns it round.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

HEAD, HANDS, FEET = ('Head',), ('Hand',), ('Foot', 'ToeBase')


def _new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001 - always on in newer Blender
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def _n(nt, kind, **inputs):
    nd = nt.nodes.new(kind)
    for k, v in inputs.items():
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, nd.inputs[k])
        else:
            nd.inputs[k].default_value = v
    return nd


def _math(nt, op, a, b=None):
    nd = nt.nodes.new('ShaderNodeMath')
    nd.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, nd.inputs[i])
        else:
            nd.inputs[i].default_value = v
    return nd.outputs[0]


def _band(nt, v, lo, hi, soft=0.006):
    """1 inside [lo, hi] along a value, soft-edged."""
    a = _n(nt, 'ShaderNodeMapRange', Value=v, **{'From Min': lo - soft, 'From Max': lo + soft}).outputs[0]
    b = _n(nt, 'ShaderNodeMapRange', Value=v, **{'From Min': hi + soft, 'From Max': hi - soft}).outputs[0]
    return _math(nt, 'MULTIPLY', a, b)


def _weights(ob):
    """Per vertex: the summed weight of the head, hand and foot bones."""
    idx = {g.index: g.name for g in ob.vertex_groups}
    out = []
    for v in ob.data.vertices:
        w = [0.0, 0.0, 0.0]
        for g in v.groups:
            name = idx.get(g.group, '')
            for k, keys in enumerate((HEAD, HANDS, FEET)):
                if any(key in name for key in keys) and 'Neck' not in name:
                    w[k] += g.weight
        out.append(w)
    return out


def _copy_groups(src, dst):
    for g in src.vertex_groups:
        dst.vertex_groups.new(name=g.name)


def _rest_mesh(body, name):
    """The body as it stands (shape applied, helpers masked out), as a new object rigged the same."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = name
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    _copy_groups(body, ob)
    ob.parent = body.parent
    ob.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    ob.matrix_world = body.matrix_world.copy()
    return ob


def _rig(ob, rig, offset, levels=2):
    """Stand the surface off by `offset`, bend it with the skeleton, smooth it at render."""
    if offset:
        d = ob.modifiers.new('standoff', 'DISPLACE')
        d.strength = offset
        d.mid_level = 0.0
    a = ob.modifiers.new('Armature', 'ARMATURE')
    a.object = rig
    a.use_vertex_groups = True
    s = ob.modifiers.new('smooth', 'SUBSURF')
    s.levels = 0
    s.render_levels = levels
    for p in ob.data.polygons:
        p.use_smooth = True


def _keep(ob, keep):
    """Delete every vertex keep(index, world position) refuses."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    mw = ob.matrix_world
    gone = [v for v in bm.verts if not keep(v.index, mw @ v.co)]
    bmesh.ops.delete(bm, geom=gone, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()


def _store_rest(ob):
    """The rest position of every vertex, for shaders: panels stay put on a moving body."""
    mw = ob.matrix_world
    a = ob.data.attributes.new('rest', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', [c for v in ob.data.vertices for c in (mw @ v.co)])


def _bone_parent(ob, rig, bone):
    """Hang an object from a bone where it already is (the bone's matrix must be current first)."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def _suit_mat(joints=()):
    """White fabric with charcoal panels, seams, a zip, a fine weave, and the trip's grime. The
    fabric folds round the limbs (real displacement, not just shading), deepest at the joints
    (joints: (rest position, radius) for the elbows, knees and hips), where cloth bunches."""
    m, nt, out = _new_mat('crew-suit')
    rest = _n(nt, 'ShaderNodeAttribute').outputs['Vector']
    rest.node.attribute_name = 'rest'
    sep = _n(nt, 'ShaderNodeSeparateXYZ', Vector=rest)
    x, y, z = sep.outputs
    ax = _math(nt, 'ABSOLUTE', x)
    side = _math(nt, 'MULTIPLY', _n(nt, 'ShaderNodeMapRange', Value=ax, **{'From Min': 0.118, 'From Max': 0.128}).outputs[0],
                 _band(nt, z, 0.98, 1.44))
    shoulder = _math(nt, 'MULTIPLY', _n(nt, 'ShaderNodeMapRange', Value=z, **{'From Min': 1.43, 'From Max': 1.45}).outputs[0],
                     _n(nt, 'ShaderNodeMapRange', Value=ax, **{'From Min': 0.11, 'From Max': 0.12}).outputs[0])
    front = _n(nt, 'ShaderNodeMapRange', Value=y, **{'From Min': 0.0, 'From Max': -0.03}).outputs[0]
    knee = _math(nt, 'MULTIPLY', _band(nt, z, 0.47, 0.63), front)
    panel = _math(nt, 'MINIMUM', _math(nt, 'ADD', _math(nt, 'ADD', side, shoulder), knee), 1.0)
    zip_ = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', _band(nt, x, -0.004, 0.004, 0.002), front), _band(nt, z, 0.92, 1.56))
    # Seams: where a panel meets the white, a thin dark line and a crease.
    seam = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', panel, _math(nt, 'SUBTRACT', 1.0, panel)), 4.0)
    weave = _n(nt, 'ShaderNodeTexNoise', Vector=rest, Scale=900.0, Detail=2.0).outputs[0]
    folds = _n(nt, 'ShaderNodeTexNoise', Vector=rest, Scale=14.0, Detail=6.0, Roughness=0.6).outputs[0]
    # Folds that wrap round a limb: noise squeezed along the height, so its ridges run across.
    across = _n(nt, 'ShaderNodeVectorMath', Vector=rest)
    across.operation = 'MULTIPLY'
    across.inputs[1].default_value = (9.0, 9.0, 42.0)
    wrap = _n(nt, 'ShaderNodeTexNoise', Vector=across.outputs[0], Scale=1.0, Detail=3.0, Roughness=0.45).outputs[0]
    wrap = _n(nt, 'ShaderNodeMapRange', Value=wrap, **{'From Min': 0.35, 'From Max': 0.65}).outputs[0]
    bunch = 0.25
    for at, r in joints:
        dist = _n(nt, 'ShaderNodeVectorMath', Vector=rest)
        dist.operation = 'DISTANCE'
        dist.inputs[1].default_value = at
        near = _n(nt, 'ShaderNodeMapRange', Value=dist.outputs['Value'], **{'From Min': r, 'From Max': r * 0.35}).outputs[0]
        bunch = _math(nt, 'ADD', bunch, near)
    squash = _n(nt, 'ShaderNodeAttribute')
    squash.attribute_name = 'squash'
    bunch = _math(nt, 'ADD', bunch, _math(nt, 'MULTIPLY', squash.outputs['Fac'], 1.6))
    bunch = _math(nt, 'MINIMUM', bunch, 2.2)
    grime = _n(nt, 'ShaderNodeTexNoise', Vector=rest, Scale=6.0, Detail=8.0).outputs[0]
    low = _n(nt, 'ShaderNodeMapRange', Value=z, **{'From Min': 0.6, 'From Max': 0.08}).outputs[0]
    # Dust: everywhere a little, the lower legs most, the knees (knelt on) and the seat too.
    knees = _math(nt, 'MULTIPLY', _band(nt, z, 0.44, 0.6, 0.04), front)
    dirt = _math(nt, 'MULTIPLY', _n(nt, 'ShaderNodeMapRange', Value=grime, **{'From Min': 0.38, 'From Max': 0.68}).outputs[0],
                 _math(nt, 'ADD', _math(nt, 'ADD', 0.35, _math(nt, 'MULTIPLY', low, 1.3)), _math(nt, 'MULTIPLY', knees, 0.7)))
    col = _n(nt, 'ShaderNodeMix')
    col.data_type = 'RGBA'
    nt.links.new(panel, col.inputs[0])
    col.inputs[6].default_value = (0.72, 0.72, 0.7, 1)
    col.inputs[7].default_value = (0.055, 0.057, 0.06, 1)
    dark = _n(nt, 'ShaderNodeMix')
    dark.data_type = 'RGBA'
    nt.links.new(_math(nt, 'MINIMUM', _math(nt, 'ADD', zip_, _math(nt, 'MULTIPLY', seam, 0.7)), 1.0), dark.inputs[0])
    nt.links.new(col.outputs[2], dark.inputs[6])
    dark.inputs[7].default_value = (0.02, 0.02, 0.02, 1)
    soil = _n(nt, 'ShaderNodeMix')
    soil.data_type = 'RGBA'
    soil.blend_type = 'MULTIPLY'
    nt.links.new(_math(nt, 'MINIMUM', _math(nt, 'MULTIPLY', dirt, 0.6), 0.85), soil.inputs[0])
    nt.links.new(dark.outputs[2], soil.inputs[6])
    soil.inputs[7].default_value = (0.5, 0.42, 0.33, 1)
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.78)
    bsdf.inputs['Sheen Weight'].default_value = 0.35
    nt.links.new(soil.outputs[2], bsdf.inputs['Base Color'])
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', weave, 0.15), _math(nt, 'ADD', _math(nt, 'MULTIPLY', folds, 0.9),
                                                                    _math(nt, 'MULTIPLY', seam, -0.6)))
    bump = _n(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.004, Height=h)
    nt.links.new(bump.outputs[0], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    # The folds as real geometry (the suit is subdivided at render): a few millimetres, deeper at
    # the joints, so they catch light and break the outline as cloth does.
    fold = _math(nt, 'MULTIPLY', _math(nt, 'ADD', _math(nt, 'MULTIPLY', wrap, 0.75), _math(nt, 'MULTIPLY', folds, 0.25)), bunch)
    disp = _n(nt, 'ShaderNodeDisplacement', Height=fold, Midlevel=0.5, Scale=0.007)
    nt.links.new(disp.outputs[0], out.inputs['Displacement'])
    try:
        m.displacement_method = 'BOTH'
    except AttributeError:
        m.cycles.displacement_method = 'BOTH'
    return m


def _tension(ob):
    """How squashed the cloth is at each point, frame by frame: every edge's length now against its
    length at rest (the 'rest' attribute), averaged to the points and stored as 'squash' (0 = as
    made or stretched, 1 = squashed by a sixth or more). The suit's folds deepen with it, so the
    fabric creases where a joint bends and smooths where it is pulled."""
    ng = bpy.data.node_groups.new('crew-tension', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    rest = N.new('GeometryNodeInputNamedAttribute')
    rest.data_type = 'FLOAT_VECTOR'
    rest.inputs['Name'].default_value = 'rest'
    ev = N.new('GeometryNodeInputMeshEdgeVertices')
    ends = []
    for k in ('Vertex Index 1', 'Vertex Index 2'):
        si = N.new('GeometryNodeSampleIndex')
        si.data_type = 'FLOAT_VECTOR'
        si.domain = 'POINT'
        L.new(gi.outputs[0], si.inputs['Geometry'])
        L.new(rest.outputs['Attribute'], si.inputs['Value'])
        L.new(ev.outputs[k], si.inputs['Index'])
        ends.append(si.outputs[0])
    was = N.new('ShaderNodeVectorMath')
    was.operation = 'DISTANCE'
    L.new(ends[0], was.inputs[0])
    L.new(ends[1], was.inputs[1])
    now = N.new('ShaderNodeVectorMath')
    now.operation = 'DISTANCE'
    L.new(ev.outputs['Position 1'], now.inputs[0])
    L.new(ev.outputs['Position 2'], now.inputs[1])
    ratio = N.new('ShaderNodeMath')
    ratio.operation = 'DIVIDE'
    L.new(now.outputs['Value'], ratio.inputs[0])
    L.new(was.outputs['Value'], ratio.inputs[1])
    sq = N.new('ShaderNodeMapRange')
    sq.inputs['From Min'].default_value = 1.0
    sq.inputs['From Max'].default_value = 0.84
    L.new(ratio.outputs[0], sq.inputs['Value'])
    on_edges = N.new('GeometryNodeFieldOnDomain')
    on_edges.domain = 'EDGE'
    on_edges.data_type = 'FLOAT'
    L.new(sq.outputs[0], on_edges.inputs[0])
    store = N.new('GeometryNodeStoreNamedAttribute')
    store.data_type = 'FLOAT'
    store.domain = 'POINT'
    store.inputs['Name'].default_value = 'squash'
    L.new(gi.outputs[0], store.inputs['Geometry'])
    L.new(on_edges.outputs[0], store.inputs['Value'])
    L.new(store.outputs[0], go.inputs[0])
    mod = ob.modifiers.new('tension', 'NODES')
    mod.node_group = ng
    # After the skeleton has bent it, before it is smoothed.
    names = [m.name for m in ob.modifiers]
    ob.modifiers.move(len(names) - 1, names.index('Armature') + 1)


def _plain(name, color, rough, metal=0.0, coat=0.0):
    m, nt, out = _new_mat(name)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=rough, Metallic=metal)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Coat Weight'].default_value = coat
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


def _glass(mouth=None):
    """The visor: clear glass; in front of the mouth, breath fog (a frosted, milky patch, ragged at
    its edge) as much as the material's 'fog' value says (crew.py breathes it)."""
    m, nt, out = _new_mat('crew-visor')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.02, IOR=1.49)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Base Color'].default_value = (0.92, 0.95, 1.0, 1)
    if mouth is None:
        nt.links.new(b.outputs[0], out.inputs['Surface'])
        return m
    frost = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.42, IOR=1.33)
    frost.inputs['Transmission Weight'].default_value = 0.85
    frost.inputs['Base Color'].default_value = (0.9, 0.92, 0.94, 1)
    tc = _n(nt, 'ShaderNodeTexCoord')
    dist = _n(nt, 'ShaderNodeVectorMath')
    dist.operation = 'DISTANCE'
    nt.links.new(tc.outputs['Object'], dist.inputs[0])
    dist.inputs[1].default_value = mouth
    edge = _n(nt, 'ShaderNodeTexNoise', Scale=55.0, Detail=6.0)
    nt.links.new(tc.outputs['Object'], edge.inputs['Vector'])
    r = _math(nt, 'ADD', dist.outputs['Value'], _math(nt, 'MULTIPLY', edge.outputs[0], 0.03))
    patch = _n(nt, 'ShaderNodeMapRange', Value=r, **{'From Min': 0.085, 'From Max': 0.035}).outputs[0]
    fog = nt.nodes.new('ShaderNodeValue')
    fog.name = fog.label = 'fog'
    fog.outputs[0].default_value = 0.0
    mix = _n(nt, 'ShaderNodeMixShader')
    nt.links.new(_math(nt, 'MULTIPLY', patch, fog.outputs[0]), mix.inputs[0])
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(frost.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def _sphere(name, center, radius, scale, segs=64):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=radius)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def build(body, rig):
    bpy.context.view_layer.update()
    head_b = rig.data.bones['mixamorig:Head']
    hb = rig.matrix_world @ head_b.head_local
    ht = rig.matrix_world @ head_b.tail_local
    neck = rig.matrix_world @ rig.data.bones['mixamorig:Neck'].head_local
    hc = hb.lerp(ht, 0.45)  # the middle of the skull

    # ---- the suit ----
    w = _weights(body)
    suit = _rest_mesh(body, 'crew-suit')
    sw = _weights(suit)
    _keep(suit, lambda i, p: sw[i][0] < 0.25 and sw[i][1] < 0.45 and sw[i][2] < 0.45)
    _store_rest(suit)
    suit.data.materials.clear()
    def bone(name):
        return rig.matrix_world @ rig.data.bones['mixamorig:' + name].head_local

    joints = [(bone(f'{s}ForeArm'), 0.11) for s in ('Left', 'Right')]
    joints += [(bone(f'{s}Leg'), 0.12) for s in ('Left', 'Right')]
    joints += [(bone(f'{s}UpLeg'), 0.13) for s in ('Left', 'Right')]
    joints += [(bone(f'{s}Arm'), 0.09) for s in ('Left', 'Right')]
    suit.data.materials.append(_suit_mat([(tuple(p), r) for p, r in joints]))
    # Cloth over the body, not paint on it: the body's surface smoothed (muscle detail softened)
    # and stood a little further off.
    sm = suit.modifiers.new('drape', 'SMOOTH')
    sm.factor = 0.6
    sm.iterations = 6
    _rig(suit, rig, 0.011)
    _tension(suit)
    # The skin it covers is hidden (a little less than it covers, so there is never a gap).
    cover = body.vertex_groups.new(name='suit-covered')
    cover.add([i for i, ww in enumerate(w) if ww[0] < 0.12 and ww[1] < 0.3 and ww[2] < 0.3], 1.0, 'REPLACE')
    mk = body.modifiers.new('under suit', 'MASK')
    mk.vertex_group = 'suit-covered'
    mk.invert_vertex_group = True

    # ---- the comms cap: the skull and the ears, not the face ----
    cap = _rest_mesh(body, 'crew-cap')
    cw = _weights(cap)
    brow = hb.z + 0.115
    face_front = hc.y - 0.03

    def on_cap(i, p):
        if cw[i][0] < 0.5:
            return False
        return p.z > brow or p.y > face_front + 0.025 or (p.z > hb.z + 0.03 and abs(p.x) > 0.062)

    _keep(cap, on_cap)
    cap.data.materials.clear()
    cap.data.materials.append(_plain('crew-cap', (0.03, 0.03, 0.032), 0.8))
    _rig(cap, rig, 0.005)
    for s in (-1, 1):
        cup = _sphere(f'crew-earcup{s}', hb + Vector((0.077 * s, 0.005, 0.085)), 0.032, (0.45, 1.0, 1.15), 32)
        cup.data.materials.append(_plain('crew-earcup', (0.02, 0.02, 0.022), 0.45))
        _bone_parent(cup, rig, 'mixamorig:Head')

    # ---- the helmet: a shell, a clear visor across the front, a black gasket round it ----
    # The window is a rounded rectangle in the shell's own angles (azimuth, elevation round its
    # centre); the shell loses the faces inside it, the visor is the faces inside a slightly larger
    # one, and a rubber gasket runs along the cut, as on a real helmet.
    c = hc + Vector((0.0, -0.012, 0.012))
    shell = _sphere('crew-helmet', c, 0.158, (0.95, 1.1, 1.08), 128)
    visor = _sphere('crew-helmet-visor', c, 0.163, (0.95, 1.1, 1.08), 128)

    def window(p, grow=0.0):
        d = p - c
        az = math.degrees(math.atan2(d.x, -d.y))  # 0 straight ahead (the face looks along -Y)
        el = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        hw, hh, r = 62 + grow, 30 + grow, 18.0
        ax, ay = abs(az) - (hw - r), abs(el + 6) - (hh - r)
        return -d.y > 0 and (max(ax, ay) <= 0 or math.hypot(max(ax, 0), max(ay, 0)) <= r)

    def cut(ob, keep_inside, grow):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        mw = ob.matrix_world
        gone = [f for f in bm.faces if window(mw @ f.calc_center_median(), grow) != keep_inside]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        edge = [e for e in bm.edges if e.is_boundary]
        rim = [(mw @ e.verts[0].co, mw @ e.verts[1].co) for e in edge]
        bm.to_mesh(ob.data)
        bm.free()
        return rim

    rim = cut(shell, False, 0.0)
    cut(visor, True, 3.0)
    gasket = bpy.data.meshes.new('crew-gasket')
    verts, edges = [], []
    for a, b in rim:
        verts += [a, b]
        edges.append((len(verts) - 2, len(verts) - 1))
    gasket.from_pydata(verts, edges, [])
    gasket.validate()
    gk = bpy.data.objects.new('crew-gasket', gasket)
    bpy.context.scene.collection.objects.link(gk)
    bm = bmesh.new()
    bm.from_mesh(gasket)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(gasket)
    bm.free()
    sk = gk.modifiers.new('tube', 'SKIN')
    for v in gasket.skin_vertices[0].data:
        v.radius = (0.007, 0.007)
    sm = gk.modifiers.new('smooth', 'SUBSURF')
    sm.levels = 1
    sm.render_levels = 2
    gk.data.materials.append(_plain('crew-gasket', (0.015, 0.015, 0.016), 0.6))
    for ob, t in ((shell, 0.007), (visor, 0.003)):
        sol = ob.modifiers.new('thickness', 'SOLIDIFY')
        sol.thickness = t
        sol.offset = 1.0
        sub = ob.modifiers.new('smooth', 'SUBSURF')
        sub.levels = 0
        sub.render_levels = 1
    shell.data.materials.append(_plain('crew-helmet', (0.86, 0.86, 0.84), 0.28, coat=0.6))
    # The mouth, on the inside of the visor (the face looks along -Y here).
    visor.data.materials.append(_glass(tuple(c + Vector((0.0, -0.165, -0.075)))))
    ring = bpy.data.meshes.new('crew-neckring')
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=64, radius=0.112)
    bm.to_mesh(ring)
    bm.free()
    ring_ob = bpy.data.objects.new('crew-neckring', ring)
    bpy.context.scene.collection.objects.link(ring_ob)
    ring_ob.location = neck + Vector((0, 0.005, 0.0))
    sk = ring_ob.modifiers.new('ring', 'SKIN')
    for v in ring.skin_vertices[0].data:
        v.radius = (0.014, 0.022)
    sub = ring_ob.modifiers.new('smooth', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    ring_ob.data.materials.append(_plain('crew-ring', (0.12, 0.12, 0.13), 0.35, metal=0.8))
    for ob in (shell, visor, gk):
        _bone_parent(ob, rig, 'mixamorig:Head')
    _bone_parent(ring_ob, rig, 'mixamorig:Spine2')

    # ---- the life-support pack, its straps and hoses ----
    back = _pack(body, suit, rig, neck)
    for ob in bpy.data.objects:
        if ob.name.endswith('male_boots'):
            for slot in ob.material_slots:
                b = slot.material.node_tree.nodes.get('Principled BSDF') if slot.material else None
                if b:
                    for l in list(b.inputs['Base Color'].links):
                        slot.material.node_tree.links.remove(l)
                    b.inputs['Base Color'].default_value = (0.025, 0.025, 0.027, 1)
                    b.inputs['Roughness'].default_value = 0.42
    print('[gear] suit', len(suit.data.vertices), 'cap', len(cap.data.vertices), 'back at', round(back, 3), flush=True)


def _skin_to(ob, body, rig):
    """Rig a piece worn on the body like the body: each vertex takes the bone weights of the body
    vertex nearest it, so straps and hoses bend with the shoulders and chest under them."""
    from mathutils.kdtree import KDTree
    bw = body.matrix_world
    kd = KDTree(len(body.data.vertices))
    for v in body.data.vertices:
        kd.insert(bw @ v.co, v.index)
    kd.balance()
    names = {g.index: g.name for g in body.vertex_groups}
    groups = {}
    mw = ob.matrix_world.copy()
    # Only the trunk carries them (an arm swinging under a strap must not drag it along).
    trunk = {'mixamorig:' + b for b in ('Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'LeftShoulder', 'RightShoulder')}
    for v in ob.data.vertices:
        _, i, _ = kd.find(mw @ v.co)
        ws = {names[g.group]: g.weight for g in body.data.vertices[i].groups if names[g.group] in trunk}
        total = sum(ws.values())
        if not total:
            ws, total = {'mixamorig:Spine2': 1.0}, 1.0
        for name, wt in ws.items():
            if name not in groups:
                groups[name] = ob.vertex_groups.new(name=name)
            groups[name].add([v.index], wt / total, 'REPLACE')
    ob.parent = body.parent
    ob.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    ob.matrix_world = mw
    a = ob.modifiers.new('Armature', 'ARMATURE')
    a.object = rig
    ob.modifiers.move(len(ob.modifiers) - 1, 0)  # bent first, then thickened and rounded


def _surface(suit):
    """A copy of the suit as it stands (its outer surface, where straps lie); removed by the caller."""
    return _rest_mesh(suit, 'crew-surface-ref')


def _on(ref, p, lift):
    """The point on the body's surface nearest p, stood off by lift along the surface normal."""
    mw = ref.matrix_world
    ok, loc, nor, _ = ref.closest_point_on_mesh(mw.inverted() @ p)
    n = (mw.to_3x3() @ nor).normalized()
    return (mw @ loc) + n * lift, n


def _spline(points, n):
    """n points per span along a smooth curve through the given ones (Catmull-Rom)."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(points[-1])
    return out


def _strap(name, ref, guide, width, lift, mat, closed=False):
    """A strap of webbing laid on the body along guide points: a flat band (width) on the surface
    (lift off it), a few millimetres thick."""
    pts = _spline(guide + ([guide[0]] if closed else []), 10)
    cen, nor = [], []
    for p in pts:
        c, n = _on(ref, p, lift)
        cen.append(c)
        nor.append(n)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for i, (c, n) in enumerate(zip(cen, nor)):
        t = (cen[min(i + 1, len(cen) - 1)] - cen[max(i - 1, 0)]).normalized()
        side = t.cross(n).normalized() * (width / 2)
        rows.append((bm.verts.new(c - side), bm.verts.new(c + side)))
    for (a, b), (c, d) in zip(rows, rows[1:]):
        bm.faces.new((a, b, d, c))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    sol = ob.modifiers.new('thick', 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = 1.0
    sub = ob.modifiers.new('smooth', 'SUBSURF')
    sub.levels = 0
    sub.render_levels = 1
    ob.data.materials.append(mat)
    return ob


def _hose(name, ref, guide, radius, lift, mat):
    """A hose lying on the body along guide points: a tube of the given radius."""
    pts = [_on(ref, p, lift + radius)[0] for p in _spline(guide, 12)]
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = 4
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for pt, c in zip(sp.points, pts):
        pt.co = (c.x, c.y, c.z, 1.0)
    tmp = bpy.data.objects.new(name + '-curve', cu)
    bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    me.name = name
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.clear()
    me.materials.append(mat)
    return ob


def _hose_mat():
    """Ribbed rubber: fine rings in its surface."""
    m, nt, out = _new_mat('crew-hose')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.5)
    b.inputs['Base Color'].default_value = (0.03, 0.032, 0.035, 1)
    tc = _n(nt, 'ShaderNodeTexCoord')
    wave = _n(nt, 'ShaderNodeTexWave', Scale=55.0, Distortion=0.0)
    wave.wave_type = 'RINGS'
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    bump = _n(nt, 'ShaderNodeBump', Strength=0.5, Distance=0.002, Height=wave.outputs['Fac'])
    nt.links.new(bump.outputs[0], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


def _shell_mat():
    """The pack's hard shell: an off-white composite, a little scuffed and dusty, like the helmet."""
    m, nt, out = _new_mat('crew-packshell')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.36)
    b.inputs['Coat Weight'].default_value = 0.35
    tc = _n(nt, 'ShaderNodeTexCoord')
    grime = _n(nt, 'ShaderNodeTexNoise', Scale=7.0, Detail=8.0)
    nt.links.new(tc.outputs['Object'], grime.inputs['Vector'])
    mix = _n(nt, 'ShaderNodeMix')
    mix.data_type = 'RGBA'
    nt.links.new(_math(nt, 'MULTIPLY', _n(nt, 'ShaderNodeMapRange', Value=grime.outputs[0],
                                          **{'From Min': 0.5, 'From Max': 0.8}).outputs[0], 0.45), mix.inputs[0])
    mix.inputs[6].default_value = (0.7, 0.7, 0.68, 1)
    mix.inputs[7].default_value = (0.48, 0.44, 0.38, 1)
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    scratch = _n(nt, 'ShaderNodeTexNoise', Scale=160.0, Detail=2.0)
    nt.links.new(tc.outputs['Object'], scratch.inputs['Vector'])
    bump = _n(nt, 'ShaderNodeBump', Strength=0.08, Distance=0.001, Height=scratch.outputs[0])
    nt.links.new(bump.outputs[0], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


def _glow(name, color, strength):
    m, nt, out = _new_mat(name)
    e = _n(nt, 'ShaderNodeEmission', Strength=strength)
    e.inputs['Color'].default_value = (*color, 1)
    nt.links.new(e.outputs[0], out.inputs['Surface'])
    return m


def _box(name, center, size, mat, bevel, taper=0.0):
    """A rounded box (bevelled, smoothed), its top narrowed by taper (a fraction)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0] * (1 - taper * (v.co.z + 0.5))
        v.co.y *= size[1]
        v.co.z *= size[2]
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bev = ob.modifiers.new('bevel', 'BEVEL')
    bev.width = bevel
    bev.segments = 5
    bev.limit_method = 'NONE'
    sub = ob.modifiers.new('smooth', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return ob


def _pack(body, suit, rig, neck):
    """The life-support pack on the back (a hard shell on a dark frame, a battery module, vents, a
    handle and a status light), the webbing that holds it (shoulder straps, a chest strap with a
    buckle, a waist belt) and two lines to the front: a ribbed hose over the right shoulder into a
    chest connector, a thin comms cable over the left. The body faces -Y here; its back is +Y."""
    ref = _surface(suit)
    mw = ref.matrix_world
    vs = [mw @ v.co for v in ref.data.vertices]
    back = max(v.y for v in vs if 1.22 < v.z < 1.45 and abs(v.x) < 0.1)
    front = min(v.y for v in vs if 1.25 < v.z < 1.42 and abs(v.x) < 0.1)
    waist_z = 1.02

    shell = _shell_mat()
    dark = _plain('crew-packframe', (0.045, 0.047, 0.05), 0.6)
    web = _plain('crew-webbing', (0.035, 0.036, 0.038), 0.82)
    metal = _plain('crew-buckle', (0.5, 0.5, 0.52), 0.32, metal=1.0)
    parts = []
    cy = back + 0.1
    parts.append(_box('crew-pack', (0.0, cy, 1.33), (0.33, 0.15, 0.48), shell, 0.035, taper=0.12))
    parts.append(_box('crew-packframe', (0.0, back + 0.022, 1.32), (0.3, 0.035, 0.5), dark, 0.012))
    parts.append(_box('crew-packbattery', (0.0, cy + 0.01, 1.06), (0.27, 0.12, 0.1), dark, 0.02))
    for s in (-1, 1):
        parts.append(_box(f'crew-packvent{s}', (0.163 * s, cy + 0.01, 1.36), (0.012, 0.08, 0.2), dark, 0.004))
        parts.append(_box(f'crew-packport{s}', (0.13 * s, cy - 0.01, 1.56), (0.05, 0.05, 0.04), dark, 0.008))
    parts.append(_box('crew-packhandle', (0.0, cy + 0.035, 1.585), (0.12, 0.018, 0.018), dark, 0.006))
    parts.append(_box('crew-packled', (0.1, cy + 0.076, 1.5), (0.012, 0.006, 0.012),
                      _glow('crew-packled', (0.25, 1.0, 0.45), 12.0), 0.002))
    for ob in parts:
        _bone_parent(ob, rig, 'mixamorig:Spine2')

    # The straps: from the top of the pack over each shoulder and down the chest; a chest strap
    # across them; a belt round the waist.
    worn = []
    for s in (-1, 1):
        x = 0.095 * s
        guide = [Vector((x, back + 0.03, 1.5)), Vector((x * 1.05, neck.y + 0.03, 1.565)),
                 Vector((x * 1.05, neck.y - 0.06, 1.53)), Vector((x, front, 1.42)), Vector((x * 1.05, front, 1.24))]
        worn.append(_strap(f'crew-shoulderstrap{s}', ref, guide, 0.045, 0.003, web))
    worn.append(_strap('crew-chestbelt', ref, [Vector((-0.11, front, 1.33)), Vector((0.0, front - 0.02, 1.33)),
                                               Vector((0.11, front, 1.33))], 0.025, 0.009, web))
    ring = []
    mid = (back + front) / 2
    for k in range(10):
        a = 2 * math.pi * k / 10
        ring.append(Vector((0.2 * math.sin(a), mid - 0.2 * math.cos(a), waist_z)))
    worn.append(_strap('crew-waistbelt', ref, ring, 0.04, 0.003, web, closed=True))
    worn.append(_box('crew-chestbuckle', _on(ref, Vector((0.0, front, 1.33)), 0.03)[0], (0.05, 0.014, 0.034), metal, 0.004))
    worn.append(_box('crew-beltbuckle', _on(ref, Vector((0.0, front, waist_z)), 0.025)[0], (0.06, 0.014, 0.04), metal, 0.004))

    # The lines: oxygen over the right shoulder (the figure's right is -X here, facing -Y)...
    hose = _hose_mat()
    r = -1
    worn.append(_hose('crew-o2hose', ref, [Vector((0.13 * r, cy - 0.01, 1.58)), Vector((0.14 * r, back - 0.02, 1.6)),
                                            Vector((0.145 * r, neck.y, 1.585)), Vector((0.14 * r, neck.y - 0.08, 1.53)),
                                            Vector((0.12 * r, front, 1.43))], 0.013, 0.003, hose))
    worn.append(_box('crew-o2port', _on(ref, Vector((0.12 * r, front, 1.42)), 0.022)[0], (0.045, 0.03, 0.045), metal, 0.008))
    # ... and a thin comms cable over the left, into the neck ring.
    worn.append(_hose('crew-commscable', ref, [Vector((0.13, cy - 0.01, 1.58)), Vector((0.12, back - 0.02, 1.6)),
                                               Vector((0.1, neck.y + 0.03, 1.6))], 0.0045, 0.008, hose))
    for ob in worn:
        _skin_to(ob, body, rig)
    bpy.data.objects.remove(ref)
    return back
