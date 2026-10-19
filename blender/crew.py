"""The crew member: the one the camera follows (third person). A suited expedition figure built in
code: a body lofted from elliptical cross-sections (tapered like a person, not a toy), a closed
helmet with a full dark visor, a harness and a field pack, pads at the knees and elbows, dirt rising
from the boots, and a chest lamp whose beam cuts the haze. Each part hangs from a joint (an empty),
so a pose is a handful of rotations: walk(), stand(), reach().

Imported by blender/arrival.py and blender/lab.py (both add this folder to sys.path). Units are
metres; the figure stands on z = 0 at its root, facing +Y. Joint rotations are about X (pitch:
positive swings a hanging limb forward), Y (roll) and Z (yaw).
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Euler, Matrix, Quaternion, Vector

DETAIL = 0  # extra subdivision levels for the final film (set by the shot scripts)
# The real crew member (blender/human.py: a MakeHuman body in the flight suit, cap, helmet and pack):
# used when REAL is set (the shot scripts set it) and the file exists; otherwise the built figure.
REAL = False
# Real motion (blender/mocap.py): the walk's body from a recorded slow walk, standing from a recorded
# stand. TIME is the shot's clock in seconds (the shot scripts set it each frame).
WALK_CLIP, IDLE_CLIP = '07_04', '77_02'
TIME = 0.0
FACE_LIGHT = 0.25  # watts: the light inside the helmet
HUMAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'mh', 'crew-human.blend')
# The legs, for stride(): hip to knee, knee to ankle, the ankle's height over the sole, and how far
# each hip sits from the body's centre line.
THIGH, SHIN, ANKLE_H, HIP_W = 0.44, 0.41, 0.083, 0.1
UPPER, FORE = 0.3, 0.27  # shoulder to elbow, elbow to wrist


def _smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _nodes(m):
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001
        pass
    nt = m.node_tree
    nt.nodes.clear()
    return nt, nt.nodes.new('ShaderNodeOutputMaterial')


def _fabric(name, color, dark, rough=0.85, dirt=0.6, folds=0.25):
    """Coated canvas: two tones broken up by noise, folds (stretched noise as bump), a fine weave,
    and dirt that rises from the boots."""
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    L = nt.links
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value = rough
    try:
        b.inputs['Sheen Weight'].default_value = 0.25
    except KeyError:
        pass
    tc = nt.nodes.new('ShaderNodeTexCoord')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    obj = tc.outputs['Object']

    def noise(vec, scale, detail=6.0):
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        L.new(vec, n.inputs['Vector'])
        return n.outputs['Fac']

    def mix(fac, a, c):
        x = nt.nodes.new('ShaderNodeMix')
        x.data_type = 'RGBA'
        L.new(fac, x.inputs[0])
        for i, v in ((6, a), (7, c)):
            if isinstance(v, tuple):
                x.inputs[i].default_value = (*v, 1)
            else:
                L.new(v, x.inputs[i])
        return x.outputs[2]

    def ramp(v, lo, hi):
        r = nt.nodes.new('ShaderNodeMapRange')
        r.inputs['From Min'].default_value = lo
        r.inputs['From Max'].default_value = hi
        L.new(v, r.inputs['Value'])
        return r.outputs['Result']

    col = mix(ramp(noise(obj, 3.0), 0.35, 0.7), color, dark)
    # Dirt: world height (feet up), broken by noise.
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Position'], sep.inputs['Vector'])
    low = ramp(sep.outputs['Z'], 1.1, 0.05)
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.use_clamp = True
    L.new(low, mul.inputs[0])
    L.new(ramp(noise(geo.outputs['Position'], 7.0, 8.0), 0.3, 0.75), mul.inputs[1])
    amt = nt.nodes.new('ShaderNodeMath')
    amt.operation = 'MULTIPLY'
    amt.use_clamp = True
    L.new(mul.outputs[0], amt.inputs[0])
    amt.inputs[1].default_value = dirt * 1.6
    col = mix(amt.outputs[0], col, (0.075, 0.062, 0.045))
    L.new(col, b.inputs['Base Color'])
    # Folds: noise stretched across the limb (object space, squashed along Z), plus the weave.
    fold = nt.nodes.new('ShaderNodeMapping')
    fold.inputs['Scale'].default_value = (2.0, 2.0, 14.0)
    L.new(obj, fold.inputs['Vector'])
    h = nt.nodes.new('ShaderNodeMath')
    h.operation = 'ADD'
    L.new(noise(fold.outputs['Vector'], 2.2, 3.0), h.inputs[0])
    weave = nt.nodes.new('ShaderNodeMath')
    weave.operation = 'MULTIPLY'
    L.new(noise(obj, 260.0, 2.0), weave.inputs[0])
    weave.inputs[1].default_value = 0.08
    L.new(weave.outputs[0], h.inputs[1])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = folds
    L.new(h.outputs[0], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    L.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def _plain(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, scratch=0.0):
    m = bpy.data.materials.new(name)
    nt, out = _nodes(m)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Metallic'].default_value = metal
    if scratch:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = 40.0
        n.inputs['Detail'].default_value = 12.0
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        r = nt.nodes.new('ShaderNodeMapRange')
        r.inputs['To Min'].default_value = rough
        r.inputs['To Max'].default_value = rough + scratch
        nt.links.new(n.outputs['Fac'], r.inputs['Value'])
        nt.links.new(r.outputs['Result'], b.inputs['Roughness'])
    else:
        b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def _finish(ob, levels=1):
    for p in ob.data.polygons:
        p.use_smooth = True
    if levels:
        m = ob.modifiers.new('subd', 'SUBSURF')
        m.levels = levels
        m.render_levels = levels + DETAIL
    return ob


def _loft(name, rings, mat, segs=24, cap=True, levels=1):
    """A body part from elliptical cross-sections: rings = [(z, rx, ry, cx, cy), ...] in the joint's
    space, top to bottom or bottom to top."""
    me = bpy.data.meshes.new(name)
    verts, faces = [], []
    for z, rx, ry, *c in rings:
        cx, cy = (c + [0.0, 0.0])[:2]
        for k in range(segs):
            a = 2 * math.pi * k / segs
            verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    n = len(rings)
    for i in range(n - 1):
        for k in range(segs):
            a, b = i * segs + k, i * segs + (k + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    if cap:
        for i in (0, n - 1):
            z = rings[i][0]
            cx, cy = (list(rings[i][3:]) + [0.0, 0.0])[:2]
            ci = len(verts)
            verts.append((cx, cy, z))
            for k in range(segs):
                a, b = i * segs + k, i * segs + (k + 1) % segs
                faces.append((a, b, ci) if i else (b, a, ci))
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    ob = _link(bpy.data.objects.new(name, me))
    return _finish(ob, levels)


def _rbox(name, size, mat, bevel=0.02, levels=1):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = _link(bpy.data.objects.new(name, me))
    m = ob.modifiers.new('bevel', 'BEVEL')
    m.width = bevel
    m.segments = 3
    m.limit_method = 'NONE'
    return _finish(ob, levels)


def _sphere(name, r, mat, scale=(1, 1, 1), keep=None, segs=40):
    """A sphere (scaled), optionally keeping only the vertices keep(x, y, z) accepts."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=r)
    if keep:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(*v.co)], context='VERTS')
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = _link(bpy.data.objects.new(name, me))
    if keep:
        sol = ob.modifiers.new('thick', 'SOLIDIFY')
        sol.thickness = 0.006
    return _finish(ob, 0)


def _joint(name, parent, loc):
    ob = _link(bpy.data.objects.new(name, None))
    ob.empty_display_size = 0.05
    ob.parent = parent
    ob.location = loc
    ob.rotation_mode = 'XYZ'
    return ob


def _put(ob, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


class Crew:
    """The figure. root: position and heading in the world. j: the joints by name."""

    def __init__(self, name='crew', lamp=True, real=None):
        real = (REAL if real is None else real) and os.path.exists(HUMAN)
        self.real = real
        self.helm = self.face = None
        self.crouch = 0.0  # 0 → 1: knees bent, weight down and forward (the shot sets it)
        self.fog = 0.45  # how much each breath fogs the visor (cold, dark places more)
        self.fog_value = None
        self.motion = None
        if real:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import mocap
            if mocap.available():
                self.motion = (mocap, mocap.get('walk', WALK_CLIP), mocap.get('idle', IDLE_CLIP))
        D = self._human(name) if real else {
            'pelvis': (0, 0, 0.98), 'spine': (0, 0, 0.1), 'chest': (0, 0, 0.24), 'neck': (0, 0.0, 0.22),
            'head': (0, 0.025, 0.14), 'hip': (0.1, 0, -0.05), 'thigh': 0.44, 'shin': 0.41, 'ankle_h': 0.083,
            'shoulder': (0.2, -0.01, 0.15), 'upper': 0.3, 'fore': 0.27, 'lamp': (-0.085, 0.16, 0.1)}
        self.pz = D['pelvis'][2]
        self.thigh, self.shin, self.ankle_h = D['thigh'], D['shin'], D['ankle_h']
        self.hip_w = D['hip'][0]
        self.upper, self.fore = D['upper'], D['fore']
        suit = _fabric(f'{name}-suit', (0.27, 0.265, 0.24), (0.17, 0.17, 0.155), dirt=1.1, folds=0.5)
        panel = _fabric(f'{name}-panel', (0.2, 0.21, 0.2), (0.14, 0.145, 0.14), dirt=0.4, folds=0.15)
        harness = _plain(f'{name}-harness', (0.02, 0.02, 0.019), 0.7)
        pad = _plain(f'{name}-pad', (0.035, 0.036, 0.034), 0.45, scratch=0.3)
        hazard = _fabric(f'{name}-hazard', (0.55, 0.2, 0.04), (0.4, 0.14, 0.03), dirt=0.3, folds=0.1)
        shell = _plain(f'{name}-shell', (0.36, 0.36, 0.34), 0.3, scratch=0.4)
        metal = _plain(f'{name}-metal', (0.55, 0.55, 0.55), 0.3, 1.0)
        visor = _plain(f'{name}-visor', (0.08, 0.06, 0.035), 0.03, 1.0)
        self.status = _plain(f'{name}-status', (0.05, 0.05, 0.05), 0.3, emit=(0.2, 1.0, 0.4), strength=10.0)

        root = _link(bpy.data.objects.new(name, None))
        root.rotation_mode = 'XYZ'
        self.root = root
        j = {}
        j['pelvis'] = _joint('pelvis', root, D['pelvis'])
        j['spine'] = _joint('spine', j['pelvis'], D['spine'])
        j['chest'] = _joint('chest', j['spine'], D['chest'])
        j['neck'] = _joint('neck', j['chest'], D['neck'])
        j['head'] = _joint('head', j['neck'], D['head'])
        hx, hy, hz = D['hip']
        sx_, sy_, sz_ = D['shoulder']
        for s, side in ((-1, 'L'), (1, 'R')):
            j[f'hip{side}'] = _joint(f'hip{side}', j['pelvis'], (hx * s, hy, hz))
            j[f'knee{side}'] = _joint(f'knee{side}', j[f'hip{side}'], (0, 0, -self.thigh))
            j[f'ankle{side}'] = _joint(f'ankle{side}', j[f'knee{side}'], (0, 0, -self.shin))
            j[f'shoulder{side}'] = _joint(f'shoulder{side}', j['chest'], (sx_ * s, sy_, sz_))
            j[f'elbow{side}'] = _joint(f'elbow{side}', j[f'shoulder{side}'], (0, 0, -self.upper))
            j[f'wrist{side}'] = _joint(f'wrist{side}', j[f'elbow{side}'], (0, 0, -self.fore))
        self.j = j
        if real:
            self._follow()

        if not real:
            # Torso: chest wider than the waist, shoulders sloping into the neck seal.
            _put(_loft('c-torso', [(-0.36, 0.15, 0.115), (-0.24, 0.155, 0.12), (-0.1, 0.18, 0.135),
                                   (0.04, 0.2, 0.145), (0.13, 0.195, 0.13), (0.19, 0.15, 0.11),
                                   (0.23, 0.085, 0.085)], suit), j['chest'])
            _put(_loft('c-hips', [(-0.17, 0.155, 0.12), (-0.08, 0.17, 0.125), (0.06, 0.16, 0.12)], suit),
                 j['pelvis'])
            # Dark side panels on the torso, a belt, and the harness: two straps and a chest strap.
            for s in (-1, 1):
                _put(_loft(f'c-flank{s}', [(-0.3, 0.03, 0.1), (-0.1, 0.035, 0.12), (0.08, 0.03, 0.12)], panel, 12),
                     j['chest'], (0.165 * s, 0, 0))
                _put(_rbox(f'c-strap{s}', (0.045, 0.012, 0.42), harness, 0.004, 0), j['chest'],
                     (0.085 * s, 0.142, -0.02), (math.radians(-6), 0, math.radians(-4 * s)))
                _put(_rbox(f'c-strapback{s}', (0.045, 0.012, 0.36), harness, 0.004, 0), j['chest'],
                     (0.085 * s, -0.142, 0.0))
                _put(_rbox(f'c-strapover{s}', (0.045, 0.3, 0.012), harness, 0.004, 0), j['chest'],
                     (0.085 * s, 0.0, 0.2), (math.radians(4), 0, 0))
            _put(_rbox('c-chestbelt', (0.27, 0.012, 0.04), harness, 0.004, 0), j['chest'], (0, 0.148, 0.02))
            _put(_rbox('c-buckle', (0.05, 0.02, 0.05), metal, 0.006, 0), j['chest'], (0, 0.155, 0.02))
            _put(_loft('c-belt', [(-0.03, 0.172, 0.13), (0.03, 0.172, 0.13)], harness, 24, False, 0), j['pelvis'], (0, 0, 0.0))
            for k, (x, y) in enumerate(((0.12, 0.08), (-0.12, 0.08), (0.16, -0.04))):
                _put(_rbox(f'c-beltpouch{k}', (0.07, 0.05, 0.08), panel, 0.01), j['pelvis'], (x, y, -0.03))
            # The neck seal and the helmet: a smooth shell, a full dark visor, a lamp on the brow.
            _put(_loft('c-neckseal', [(-0.03, 0.115, 0.11), (0.03, 0.105, 0.1)], metal, 32, False, 0), j['neck'])
            _put(_sphere('c-helmet', 0.142, shell, (0.94, 1.04, 1.06)), j['head'])
            _put(_sphere('c-visor', 0.146, visor, (0.95, 1.05, 1.0),
                         keep=lambda x, y, z: y > 0.035 and -0.075 < z < 0.07), j['head'])
            _put(_rbox('c-brow', (0.05, 0.04, 0.025), pad, 0.008), j['head'], (0.06, 0.12, 0.1))
            _put(_rbox('c-earpiece', (0.035, 0.06, 0.07), pad, 0.01), j['head'], (0.135, 0.0, 0.0))
            _put(_rbox('c-earpiece2', (0.035, 0.06, 0.07), pad, 0.01), j['head'], (-0.135, 0.0, 0.0))
            # The back of the helmet: a vent, a hazard stripe over the crown, a red marker light.
            _put(_rbox('c-vent', (0.12, 0.03, 0.09), pad, 0.01), j['head'], (0, -0.14, -0.02))
            _put(_sphere('c-crownstripe', 0.147, hazard, (0.24, 1.06, 1.08),
                         keep=lambda x, y, z: z > 0.06, segs=32), j['head'])
            red = _plain(f'{name}-marker', (0.05, 0.01, 0.01), 0.3, emit=(1.0, 0.06, 0.03), strength=14.0)
            _put(_sphere('c-marker', 0.009, red, segs=10), j['head'], (0.0, -0.152, 0.05))
            # The field pack: frame, lid, side pouches, a cable to the helmet, an antenna stub.
            pack = _put(_rbox('c-pack', (0.34, 0.17, 0.46), panel, 0.04), j['chest'], (0, -0.225, -0.02))
            _put(_rbox('c-packlid', (0.3, 0.05, 0.12), panel, 0.02), pack, (0, -0.02, 0.26))
            for s in (-1, 1):
                _put(_rbox(f'c-packpouch{s}', (0.06, 0.12, 0.22), panel, 0.02), pack, (0.2 * s, 0.0, -0.06))
            _put(_rbox('c-packstripe', (0.26, 0.012, 0.03), hazard, 0.004, 0), pack, (0, -0.088, 0.17))
            for s in (-1, 1):
                _put(_rbox(f'c-packstrap{s}', (0.035, 0.012, 0.42), harness, 0.004, 0), pack, (0.08 * s, -0.09, -0.02))
            _put(_loft('c-roll', [(-0.17, 0.055, 0.055), (0.17, 0.055, 0.055)], panel, 16), pack,
                 (0, 0.0, -0.27), (0, math.radians(90), 0))
            _put(_sphere('c-statuslight', 0.011, self.status, segs=12), pack, (0.12, -0.09, 0.18))
            _put(_loft('c-antenna', [(0, 0.008, 0.008), (0.24, 0.004, 0.004)], metal, 8, True, 0), pack, (-0.13, 0.02, 0.22))
            # Arms: tapered sleeves, elbow pads, gloves with a cuff.
            for s, side in ((-1, 'L'), (1, 'R')):
                _put(_loft(f'c-delt{side}', [(0.06, 0.06, 0.06), (0.0, 0.085, 0.08), (-0.08, 0.075, 0.072)], suit),
                     j[f'shoulder{side}'])
                _put(_loft(f'c-upper{side}', [(0.0, 0.07, 0.068), (-0.14, 0.062, 0.062), (-0.3, 0.052, 0.054)], suit),
                     j[f'shoulder{side}'])
                _put(_rbox(f'c-shoulderpad{side}', (0.11, 0.13, 0.05), pad, 0.02), j[f'shoulder{side}'],
                     (0.03 * s, 0, 0.05), (0, math.radians(30 * s), 0))
                _put(_rbox(f'c-elbowpad{side}', (0.07, 0.05, 0.1), pad, 0.015), j[f'elbow{side}'], (0, -0.05, -0.02))
                _put(_loft(f'c-fore{side}', [(0.0, 0.052, 0.054), (-0.09, 0.055, 0.056), (-0.26, 0.042, 0.04)], suit),
                     j[f'elbow{side}'])
                _put(_loft(f'c-cuff{side}', [(0.02, 0.052, 0.05), (-0.04, 0.054, 0.052)], hazard, 20), j[f'wrist{side}'])
                _put(_rbox(f'c-glove{side}', (0.08, 0.045, 0.1), pad, 0.02), j[f'wrist{side}'], (0, 0.008, -0.07))
                _put(_rbox(f'c-thumb{side}', (0.025, 0.03, 0.06), pad, 0.01), j[f'wrist{side}'],
                     (-0.04 * s, 0.03, -0.05), (math.radians(20), 0, math.radians(25 * s)))
                # Legs: thigh into knee into calf; pads; a thigh pocket; boots with a cuff and a sole.
                _put(_loft(f'c-thigh{side}', [(0.04, 0.09, 0.095), (-0.12, 0.088, 0.09), (-0.3, 0.074, 0.076),
                                              (-0.44, 0.062, 0.064)], suit), j[f'hip{side}'])
                _put(_rbox(f'c-thighpocket{side}', (0.04, 0.12, 0.15), panel, 0.015), j[f'hip{side}'],
                     (0.085 * s, 0.0, -0.22))
                _put(_rbox(f'c-kneepad{side}', (0.1, 0.05, 0.13), pad, 0.02), j[f'knee{side}'], (0, 0.06, -0.01))
                _put(_loft(f'c-shin{side}', [(0.02, 0.062, 0.064), (-0.12, 0.064, 0.07), (-0.3, 0.052, 0.054),
                                             (-0.38, 0.05, 0.052)], suit), j[f'knee{side}'])
                _put(_loft(f'c-bootcuff{side}', [(0.06, 0.06, 0.064), (-0.04, 0.062, 0.066)], pad, 20), j[f'ankle{side}'])
                _put(_rbox(f'c-boot{side}', (0.115, 0.27, 0.1), pad, 0.03), j[f'ankle{side}'], (0, 0.055, -0.03))
                _put(_rbox(f'c-sole{side}', (0.122, 0.28, 0.025), harness, 0.008, 0), j[f'ankle{side}'], (0, 0.055, -0.07))
        # The chest lamp, on the left strap: what lights the way.
        self.lamp = None
        self.lens = None
        if lamp:
            lens = _plain(f'{name}-lens', (0.9, 0.9, 0.85), emit=(1.0, 0.95, 0.85), strength=80.0)
            body = _put(_rbox('c-lampbody', (0.06, 0.05, 0.05), pad, 0.008), j['chest'], D['lamp'])
            _put(_sphere('c-lamplens', 0.018, lens, (1, 0.35, 1), segs=16), body, (0, 0.027, 0))
            data = bpy.data.lights.new(f'{name}-beam', 'SPOT')
            data.energy = 1100.0
            data.spot_size = math.radians(32)
            data.spot_blend = 0.6
            data.shadow_soft_size = 0.02
            data.color = (1.0, 0.95, 0.86)
            beam = _link(bpy.data.objects.new(f'{name}-beam', data))
            beam.parent = body
            beam.location = (0, 0.03, 0)
            beam.rotation_euler = (math.radians(78), 0, 0)  # forward and a little down
            self.lamp = beam
            self.lens = lens.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
        self.stand()

    # ---- the real body ------------------------------------------------------------------------

    def _human(self, name):
        """Bring in the real crew member (blender/human.py), turn it to face +Y like the figure, and
        measure its skeleton: the joints are laid out to match it, so feet and hands land true."""
        with bpy.data.libraries.load(HUMAN, link=False) as (src, dst):
            dst.objects = list(src.objects)
        parts = [o for o in dst.objects if o is not None]
        for o in parts:
            bpy.context.scene.collection.objects.link(o)
        rig = next(o for o in parts if o.type == 'ARMATURE')
        rig.name = f'{name}-rig'
        rig.location = (0.0, 0.0, rig.location.z)
        rig.rotation_euler = (0.0, 0.0, math.pi)
        bpy.context.view_layer.update()
        self.rig, self.parts = rig, parts
        # The helmet (shell, visor, gasket) hangs from a carrier of its own, so it can come off in
        # the hands: helmet() moves the carrier each frame.
        helm = [o for o in parts if o.name.startswith(('crew-helmet', 'crew-gasket'))]
        self.helm = None
        if helm:
            car = _link(bpy.data.objects.new(f'{name}-helmet', None))
            # At the middle of the shell (the meshes' own origins are at the feet).
            shell = next((o for o in helm if o.name.startswith('crew-helmet') and 'visor' not in o.name), helm[0])
            car.location = sum((shell.matrix_world @ Vector(c) for c in shell.bound_box), Vector()) / 8
            bpy.context.view_layer.update()
            for o in helm:
                mw = o.matrix_world.copy()
                o.parent, o.parent_type, o.parent_bone = car, 'OBJECT', ''
                o.matrix_parent_inverse = Matrix()
                o.matrix_world = mw
            self.helm = car
            visor = next((o for o in helm if 'visor' in o.name), None)
            if visor and visor.active_material and visor.active_material.node_tree:
                node = visor.active_material.node_tree.nodes.get('fog')
                if node:
                    self.fog_value = node.outputs[0]
            # A faint cool light inside, low in front of the chin (the helmet's displays, as films
            # do it): the face reads behind the visor instead of a black glass.
            data = bpy.data.lights.new(f'{name}-facelight', 'POINT')
            data.energy = FACE_LIGHT
            data.shadow_soft_size = 0.025
            data.color = (0.8, 0.9, 1.0)
            fl = _link(bpy.data.objects.new(f'{name}-facelight', data))
            fl.parent = car
            fl.location = (0.0, 0.14, -0.07)  # in front of the chin, inside the visor
            # Lights the face; never seen itself, nor a hotspot in the visor.
            fl.visible_glossy = fl.visible_camera = fl.visible_transmission = False
            self.face = data

        def at(bone):
            return rig.matrix_world @ rig.data.bones['mixamorig:' + bone].head_local

        hips, spine, chest, neck, head = (at(b) for b in ('Hips', 'Spine', 'Spine2', 'Neck', 'Head'))
        hip, knee, ankle = at('RightUpLeg'), at('RightLeg'), at('RightFoot')
        sho, elb, wri = at('RightArm'), at('RightForeArm'), at('RightHand')
        # The lamp sits on the suit: its front, measured just where the lamp goes (on the figure's
        # left, a little above the chest joint), plus most of the lamp's depth.
        suit = next((o for o in parts if o.name.startswith('crew-suit')), None)
        lx, lz = -0.085, 0.02
        front = 0.13
        if suit:
            dg = bpy.context.evaluated_depsgraph_get()
            ev = suit.evaluated_get(dg)
            me = ev.to_mesh()
            mw = ev.matrix_world
            ys = [w.y for w in (mw @ v.co for v in me.vertices)
                  if abs(w.x - lx) < 0.025 and abs(w.z - (chest.z + lz)) < 0.025 and w.y > chest.y]
            front = (max(ys) - chest.y + 0.017) if ys else front  # seated a little into the fabric
            ev.to_mesh_clear()
        pel = Vector((0.0, hips.y, hips.z))
        return {'pelvis': tuple(pel), 'spine': tuple(spine - pel), 'chest': tuple(chest - spine),
                'neck': tuple(neck - chest), 'head': tuple(head - neck),
                'hip': (abs(hip.x - pel.x), hip.y - pel.y, hip.z - pel.z),
                'thigh': (knee - hip).length, 'shin': (ankle - knee).length, 'ankle_h': ankle.z,
                'shoulder': (abs(sho.x), sho.y - chest.y, sho.z - chest.z),
                'upper': (elb - sho).length, 'fore': (wri - elb).length,
                'lamp': (lx, front, lz)}

    def _follow(self):
        """The real skeleton follows the joints: the trunk, head and feet take their transforms
        (through helpers that keep each bone's rest orientation), the limbs aim at the next joint."""
        rig, j = self.rig, self.j
        bpy.context.view_layer.update()
        pb = rig.pose.bones

        def copy(bone, joint):
            rest = rig.matrix_world @ rig.data.bones['mixamorig:' + bone].matrix_local
            h = _link(bpy.data.objects.new(f'{self.root.name}-{bone}-follow', None))
            h.parent = joint
            bpy.context.view_layer.update()
            h.matrix_world = Matrix.Translation(joint.matrix_world.translation) @ rest.to_3x3().normalized().to_4x4()
            c = pb['mixamorig:' + bone].constraints.new('COPY_TRANSFORMS')
            c.target = h

        def aim(bone, joint):
            c = pb['mixamorig:' + bone].constraints.new('DAMPED_TRACK')
            c.target = joint
            c.track_axis = 'TRACK_Y'

        for bone, jn in (('Hips', 'pelvis'), ('Spine', 'spine'), ('Spine2', 'chest'), ('Neck', 'neck'),
                         ('Head', 'head')):
            copy(bone, j[jn])
        aim('Spine1', j['chest'])  # the middle of the back bends evenly between the two
        # Hands at rest, not splayed: the fingers drawn in beside the middle one, the knuckles bent
        # most, then the middle joints; more towards the little finger.
        # (Each finger bone hinges on its X axis; its +Z is the back of the hand.)
        bones = rig.data.bones
        for side in ('Left', 'Right'):
            mid = bones[f'mixamorig:{side}HandMiddle1'].matrix_local.to_3x3().col[1]
            for finger, angs, draw in (('Index', (30, 26, 12), 0.6), ('Middle', (34, 30, 13), 0.0),
                                       ('Ring', (38, 32, 14), 0.6), ('Pinky', (42, 34, 15), 0.7),
                                       ('Thumb', (0, 14, 12), 0.0)):
                for n, a in enumerate(angs, 1):
                    b = pb.get(f'mixamorig:{side}Hand{finger}{n}')
                    if not b:
                        continue
                    q = Quaternion((1.0, 0.0, 0.0), -math.radians(a))
                    if n == 1 and draw:
                        rest = bones[b.name].matrix_local.to_3x3()
                        turn = rest.col[1].rotation_difference(mid)  # in the rig's space
                        local = rest.inverted() @ turn.to_matrix() @ rest
                        q = Quaternion().slerp(local.to_quaternion(), draw) @ q
                    b.rotation_mode = 'QUATERNION'
                    b.rotation_quaternion = q
        # Facing +Y, the body's left is -X: MakeHuman's Left is the figure's L.
        for side, s in (('Left', 'L'), ('Right', 'R')):
            aim(f'{side}UpLeg', j[f'knee{s}'])
            aim(f'{side}Leg', j[f'ankle{s}'])
            copy(f'{side}Foot', j[f'ankle{s}'])
            aim(f'{side}Arm', j[f'elbow{s}'])
            aim(f'{side}ForeArm', j[f'wrist{s}'])
        if self.helm:
            # The carrier rides on the head joint; helmet() moves it off.
            h = self.helm
            h.rotation_mode = 'XYZ'
            self.helm_on = j['head'].matrix_world.inverted() @ h.matrix_world
            h.parent = j['head']
            h.matrix_parent_inverse = Matrix()
            h.matrix_basis = self.helm_on

    def helmet(self, k=0.0, to=None):
        """Where the helmet is: k = 0 on the head; 0 → 0.35 eased straight up off it (along the
        head's up, past the cap), then on to `to` (a world matrix: in the hands, on the bench) by
        k = 1. Call after the body is posed; the hands are the shot's to put on it (reach_to).
        Returns the helmet's world matrix."""
        if not self.helm:
            return None
        bpy.context.view_layer.update()
        head = self.j['head'].matrix_world
        on = head @ self.helm_on
        if k <= 0 or to is None:
            m = on
        else:
            up = on.to_3x3().normalized() @ Vector((0, 0, 1))
            a = _smooth(min(1.0, k / 0.35))
            b = _smooth(max(0.0, (k - 0.35) / 0.65))
            loc = (on.translation + up * 0.17 * a).lerp(to.translation, b)
            rot = on.to_quaternion().slerp(to.to_quaternion(), b)
            m = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
        self._helmet_off = _smooth(min(1.0, k / 0.3)) if k > 0 else 0.0
        if self.face:
            self.face.energy = FACE_LIGHT * (1.0 - self._helmet_off)
        if self.fog_value is not None:
            self.fog_value.default_value *= 1.0 - self._helmet_off
        local = head.inverted() @ m
        prev = self.helm.rotation_euler.copy()
        self.helm.location = local.translation
        self.helm.rotation_euler = local.to_euler('XYZ', prev)
        return m

    # ---- poses --------------------------------------------------------------------------------

    def _zero(self):
        for ob in self.j.values():
            ob.rotation_euler = (0, 0, 0)
        self.j['pelvis'].location = (0, 0, self.pz)

    def stand(self, breath=0.0, look=(0.0, 0.0)):
        self._zero()
        j = self.j
        for s, side in ((-1, 'L'), (1, 'R')):
            j[f'shoulder{side}'].rotation_euler = (math.radians(5), math.radians(-8 * s), 0)
            j[f'elbow{side}'].rotation_euler = (math.radians(16), 0, 0)
            j[f'knee{side}'].rotation_euler = (math.radians(-5), 0, 0)
            j[f'hip{side}'].rotation_euler = (math.radians(3), 0, math.radians(-2 * s))
        j['chest'].rotation_euler = (math.radians(3 + 1.0 * math.sin(breath)), 0, 0)
        j['pelvis'].location = (0, 0, self.pz - 0.005 + 0.003 * math.sin(breath))
        j['head'].rotation_euler = (look[1], 0, look[0])

    def walk(self, phase, amount=1.0, look=(0.0, 0.0)):
        """A careful walk. phase: radians through the stride (2π = two steps). amount fades the
        stride in or out (0 = standing). look: head yaw and pitch, radians."""
        self._zero()
        j = self.j
        a = amount
        for s, side, off in ((-1, 'L', 0.0), (1, 'R', math.pi)):
            p = phase + off
            swing = math.sin(p)
            # Thigh forward and back; the knee bends through the swing (just after toe-off).
            j[f'hip{side}'].rotation_euler = (math.radians(23 * swing * a + 3), 0, math.radians(-2 * s))
            knee = 5 + 50 * max(0.0, math.sin(p + 1.2)) ** 1.6
            j[f'knee{side}'].rotation_euler = (-math.radians(knee * a + 4), 0, 0)
            # The foot stays near flat: heel strike, then roll.
            ankle = -(23 * swing - knee) * 0.6 * a
            j[f'ankle{side}'].rotation_euler = (math.radians(ankle - 3), 0, 0)
            # Arms swing against the legs; more elbow on the back swing.
            arm = -math.sin(p)
            j[f'shoulder{side}'].rotation_euler = (math.radians(14 * arm * a + 6), math.radians(-7 * s), math.radians(2 * s))
            j[f'elbow{side}'].rotation_euler = (math.radians(20 + 12 * max(0.0, -arm) * a), 0, 0)
        # The body: down at each foot strike, rolling side to side, hips and shoulders counter-turning.
        j['pelvis'].location = (0.016 * math.sin(phase) * a, 0, self.pz - 0.005 - 0.026 * a * (1 - math.cos(2 * phase)) / 2)
        j['pelvis'].rotation_euler = (math.radians(4 * a), math.radians(-2.5 * math.sin(phase) * a), math.radians(6 * math.sin(phase) * a))
        j['chest'].rotation_euler = (math.radians(5 * a), math.radians(1.5 * math.sin(phase) * a), math.radians(-9 * math.sin(phase) * a))
        j['head'].rotation_euler = (look[1], 0, look[0] + math.radians(3 * math.sin(phase) * a))

    def stride(self, d, path, S=1.4, amount=1.0, look=(0.0, 0.0), ground=None, breath=0.0, phase0=0.3):
        """A walk whose feet stay where they land. d: metres walked along the path; path(dist)
        gives (ground point, heading) there; S: metres per stride (two steps). Each foot is down for
        60% of its stride on a footprint beside the path, then swings to the next one in an arc;
        the legs reach their feet by inverse kinematics, so a planted foot never slides. The body
        (arms, sway, head) is walk()'s. amount < 1 is stopping: the swinging foot comes down beside
        the planted one and the body settles over both. phase0 = 0.3 starts (d = 0) with the left
        foot under the body and the right one lifting, so a walk can begin from standing; breath
        moves the chest at rest. Call after place()."""
        ground = ground or (lambda p: 0.0)
        a = max(0.0, min(1.0, amount))
        self.walk(2 * math.pi * (d / S + phase0), a, look)
        j = self.j
        j['chest'].rotation_euler.x += math.radians(3 * (1 - a) + 1.0 * math.sin(breath)) * (1 - a)
        # The pelvis rides highest over a planted foot and lowest when both are down.
        phl = (d / S + phase0) % 1.0
        dip = (1 - math.cos(4 * math.pi * (phl - 0.3))) / 2
        px, py, _ = j['pelvis'].location
        j['pelvis'].location = (px, py, self.pz - 0.005 - a * (0.02 + 0.05 * dip))
        if self.motion:
            self._recorded(d / S + phase0, a, look, breath)
        if self.fog_value is not None:
            # A breath every 3.4 s: the exhale blooms on the glass over a second, then clears.
            ph = (TIME / 3.4) % 1.0
            bloom = _smooth(ph / 0.3) if ph < 0.3 else math.exp(-(ph - 0.3) / 0.16)
            self.fog_value.default_value = self.fog * (0.12 + 0.88 * bloom) * (1.0 - getattr(self, '_helmet_off', 0.0))
        if self.crouch:
            c = self.crouch
            px, py, pz_ = j['pelvis'].location
            j['pelvis'].location = (px, py - 0.03 * c, pz_ - 0.085 * c)
            j['pelvis'].rotation_euler.x += math.radians(10) * c
            j['chest'].rotation_euler.x += math.radians(8) * c
            j['head'].rotation_euler.x -= math.radians(12) * c

        def foot_at(dist, s):
            p, h = path(dist)
            q = Vector(p) + Vector((math.cos(h), math.sin(h), 0.0)) * (self.hip_w * s)
            q.z = ground(q) + self.ankle_h
            return q

        feet = {}
        for s, side, off in ((-1, 'L', 0.0), (1, 'R', 0.5)):
            ph = (d / S + off + phase0) % 1.0
            base = d - ph * S + 0.3 * S  # this cycle's footprint: where the foot is, or last was, down
            if ph < 0.6:
                heel = _smooth((ph - 0.42) / 0.18)  # the heel lifts before the push-off
                feet[side] = (True, base, foot_at(base, s) + Vector((0, 0, 0.035 * heel)),
                              -math.radians(16) * heel)
            else:
                u = (ph - 0.6) / 0.4
                q = foot_at(base, s).lerp(foot_at(base + S, s), _smooth(u))
                q.z += 0.1 * math.sin(math.pi * u) + 0.03 * (1 - u) ** 2
                feet[side] = (False, base, q, math.radians(-16 * (1 - u) ** 2 + 9 * u * u))
        if a < 1.0:
            # Stopping: a swinging foot comes down beside the one that is planted.
            for side, other, s in (('L', 'R', -1), ('R', 'L', 1)):
                down, _, q, toe = feet[side]
                if not down and feet[other][0]:
                    feet[side] = (False, 0, foot_at(feet[other][1], s).lerp(q, a), toe * a)
            mid = (feet['L'][2] + feet['R'][2]) / 2
            r = self.root.location
            self.root.location = (r.x + (mid.x - r.x) * (1 - a), r.y + (mid.y - r.y) * (1 - a), r.z)
        # Never a locked knee dragging a foot: if a leg cannot reach its footprint without
        # straightening fully, the hips drop just enough (as a body does: the knee gives).
        for _ in range(3):
            bpy.context.view_layer.update()
            over = max((feet[s_][2] - j[f'hip{s_}'].matrix_world.translation).length
                       - 0.985 * (self.thigh + self.shin) for s_ in ('L', 'R'))
            if over <= 0:
                break
            px, py, pz_ = j['pelvis'].location
            j['pelvis'].location = (px, py, pz_ - over * 1.15)
        bpy.context.view_layer.update()
        inv = j['pelvis'].matrix_world.inverted()
        tilt = j['pelvis'].rotation_euler.x
        for s, side in ((-1, 'L'), (1, 'R')):
            _, _, target, toe = feet[side]
            hip = j[f'hip{side}']
            t = inv @ target - Vector(hip.location)
            fwd, down, lat = t.y, -t.z, t.x
            T, Sh = self.thigh, self.shin
            reach = min(t.length, (T + Sh) * 0.999)
            bend = math.pi - math.acos(max(-1.0, min(1.0, (T ** 2 + Sh ** 2 - reach ** 2) / (2 * T * Sh))))
            line = math.atan2(fwd, math.hypot(down, lat))
            pitch = line + math.acos(max(-1.0, min(1.0, (T ** 2 + reach ** 2 - Sh ** 2) / (2 * T * reach))))
            hip.rotation_euler = (pitch, -math.atan2(lat, down), 0.0)
            j[f'knee{side}'].rotation_euler = (-bend, 0.0, 0.0)
            # The sole level with the ground (less the push-off and the toe-up before landing).
            j[f'ankle{side}'].rotation_euler = (-(tilt + pitch - bend) + toe, 0.0, math.radians(-3 * s))

    def _recorded(self, cycles, a, look, breath):
        """The body from real motion: the recorded walk at this point of the step cycle (cycles:
        strides walked, + phase), blended with recorded standing as the walk fades (a). The legs
        are solved after this to the footprints; look turns the head on top of the recording."""
        mocap, walk, idle = self.motion
        j = self.j
        p = mocap.blend(idle.pose(TIME), walk.pose(cycles % 1.0), a)

        def put(name, q):
            j[name].rotation_euler = q.to_euler('XYZ', j[name].rotation_euler)

        put('pelvis', p['pelvis'])
        for name in ('spine', 'chest', 'neck'):
            put(name, p[name])
        put('head', p['head'] @ Euler((look[1], 0.0, look[0])).to_quaternion())
        for s in ('L', 'R'):
            put('shoulder' + s, p['shoulder' + s])
            put('elbow' + s, p['elbow' + s])
            j['wrist' + s].rotation_euler = (0.0, 0.0, 0.0)
        j['chest'].rotation_euler.x += math.radians(1.0 * math.sin(breath)) * (1 - a)
        # The hips: their recorded bob and sway, round the height the legs can reach both feet from.
        j['pelvis'].location = (p['sway'] * a, 0.0, self.pz - 0.008 - 0.045 * a + p['lift'])

    def reach_to(self, side, target, k=1.0, pole=(0.6, -0.4, -1.0)):
        """Put a hand on a world point: the arm solved by inverse kinematics (shoulder, elbow),
        the elbow bending towards pole (in the chest's frame, x outward for this side), blended
        k of the way from the pose the arm already has. Call after the body is posed."""
        if k <= 0:
            return
        j = self.j
        s = -1 if side == 'L' else 1
        bpy.context.view_layer.update()
        sh, el = j[f'shoulder{side}'], j[f'elbow{side}']
        S = Vector(sh.location)
        T = j['chest'].matrix_world.inverted() @ Vector(target)
        D = T - S
        U, F = self.upper, self.fore
        L = max(1e-4, min(D.length, (U + F) * 0.999))
        dh = D.normalized()
        p = Vector((pole[0] * s, pole[1], pole[2]))
        n = (p - dh * p.dot(dh)).normalized()
        a = (U ** 2 - F ** 2 + L ** 2) / (2 * L)
        E = S + dh * a + n * math.sqrt(max(0.0, U ** 2 - a * a))
        u = (E - S).normalized()
        f = (S + dh * L - E).normalized()
        b = f - u * f.dot(u)
        b = b.normalized() if b.length > 1e-6 else n
        # The shoulder's frame: the arm (local -Z) along u, the elbow's bend (local +Y) towards b.
        z = -u
        x = b.cross(z)
        m = Matrix((x, b, z)).transposed()
        q = sh.rotation_euler.to_quaternion().slerp(m.to_quaternion(), k)
        sh.rotation_euler = q.to_euler('XYZ')
        bend = math.acos(max(-1.0, min(1.0, u.dot(f))))
        el.rotation_euler = (el.rotation_euler.x * (1 - k) + bend * k, 0.0, 0.0)
        j[f'wrist{side}'].rotation_euler = (math.radians(-10) * k, 0.0, 0.0)

    def reach(self, k, side='R', target_pitch=70.0):
        """Lift one arm forward (to push a door, to wake the projector); k: 0 → 1."""
        j = self.j
        j[f'shoulder{side}'].rotation_euler = (math.radians(5 + (target_pitch - 5) * k), 0, math.radians(-6 * k))
        j[f'elbow{side}'].rotation_euler = (math.radians(16 + 8 * k), 0, 0)
        j[f'wrist{side}'].rotation_euler = (math.radians(-25 * k), 0, 0)

    def light(self, k):
        """The chest lamp at k of full (0 = switched off)."""
        if self.lamp:
            self.lamp.data.energy = 1100.0 * k
            self.lens.default_value = 80.0 * k

    def keys(self):
        """What changes from frame to frame (for keyframing)."""
        out = [(self.root, 'location'), (self.root, 'rotation_euler'), (self.j['pelvis'], 'location')]
        out += [(ob, 'rotation_euler') for ob in self.j.values()]
        if self.lamp:
            out += [(self.lamp.data, 'energy'), (self.lens, 'default_value')]
        if self.helm:
            out += [(self.helm, 'location'), (self.helm, 'rotation_euler')]
        if self.face:
            out += [(self.face, 'energy')]
        if self.fog_value is not None:
            out += [(self.fog_value, 'default_value')]
        return out


def place(crew, pos, heading):
    """Put the figure at pos (x, y, z) facing heading (radians, 0 = +Y)."""
    crew.root.location = pos
    crew.root.rotation_euler = (0, 0, heading)
