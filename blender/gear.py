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


def _suit_mat():
    """White fabric with charcoal panels, seams, a zip, a fine weave, and the trip's grime."""
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
    grime = _n(nt, 'ShaderNodeTexNoise', Vector=rest, Scale=6.0, Detail=8.0).outputs[0]
    low = _n(nt, 'ShaderNodeMapRange', Value=z, **{'From Min': 0.55, 'From Max': 0.1}).outputs[0]
    dirt = _math(nt, 'MULTIPLY', _n(nt, 'ShaderNodeMapRange', Value=grime, **{'From Min': 0.45, 'From Max': 0.7}).outputs[0],
                 _math(nt, 'ADD', 0.25, low))
    col = _n(nt, 'ShaderNodeMix')
    col.data_type = 'RGBA'
    nt.links.new(panel, col.inputs[0])
    col.inputs[6].default_value = (0.8, 0.8, 0.78, 1)
    col.inputs[7].default_value = (0.055, 0.057, 0.06, 1)
    dark = _n(nt, 'ShaderNodeMix')
    dark.data_type = 'RGBA'
    nt.links.new(_math(nt, 'MINIMUM', _math(nt, 'ADD', zip_, _math(nt, 'MULTIPLY', seam, 0.7)), 1.0), dark.inputs[0])
    nt.links.new(col.outputs[2], dark.inputs[6])
    dark.inputs[7].default_value = (0.02, 0.02, 0.02, 1)
    soil = _n(nt, 'ShaderNodeMix')
    soil.data_type = 'RGBA'
    soil.blend_type = 'MULTIPLY'
    nt.links.new(_math(nt, 'MULTIPLY', dirt, 0.55), soil.inputs[0])
    nt.links.new(dark.outputs[2], soil.inputs[6])
    soil.inputs[7].default_value = (0.55, 0.47, 0.38, 1)
    bsdf = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.78)
    bsdf.inputs['Sheen Weight'].default_value = 0.35
    nt.links.new(soil.outputs[2], bsdf.inputs['Base Color'])
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', weave, 0.15), _math(nt, 'ADD', _math(nt, 'MULTIPLY', folds, 0.9),
                                                                    _math(nt, 'MULTIPLY', seam, -0.6)))
    bump = _n(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.004, Height=h)
    nt.links.new(bump.outputs[0], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m


def _plain(name, color, rough, metal=0.0, coat=0.0):
    m, nt, out = _new_mat(name)
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=rough, Metallic=metal)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Coat Weight'].default_value = coat
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


def _glass():
    m, nt, out = _new_mat('crew-visor')
    b = _n(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.02, IOR=1.49)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Base Color'].default_value = (0.92, 0.95, 1.0, 1)
    nt.links.new(b.outputs[0], out.inputs['Surface'])
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
    suit.data.materials.append(_suit_mat())
    _rig(suit, rig, 0.007)
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
    visor.data.materials.append(_glass())
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

    # ---- the pack, against the back at the shoulder blades ----
    mw = body.matrix_world
    back = max((mw @ v.co).y for v, ww in zip(body.data.vertices, w)
               if 1.22 < (mw @ v.co).z < 1.45 and abs((mw @ v.co).x) < 0.1)
    me = bpy.data.meshes.new('crew-pack')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.31, 0.15, 0.42), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    pack = bpy.data.objects.new('crew-pack', me)
    bpy.context.scene.collection.objects.link(pack)
    pack.location = (0.0, back + 0.085, 1.31)
    bev = pack.modifiers.new('bevel', 'BEVEL')
    bev.width = 0.03
    bev.segments = 4
    sub = pack.modifiers.new('smooth', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    for p in me.polygons:
        p.use_smooth = True
    pack.data.materials.append(_plain('crew-pack', (0.11, 0.115, 0.11), 0.85))
    for s in (-1, 1):
        strap = _sphere(f'crew-strap{s}', Vector((0.085 * s, back - 0.03, 1.47)), 0.06, (0.35, 1.55, 0.35), 24)
        strap.data.materials.append(_plain('crew-strap', (0.03, 0.03, 0.03), 0.7))
        _bone_parent(strap, rig, 'mixamorig:Spine2')
    _bone_parent(pack, rig, 'mixamorig:Spine2')
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
