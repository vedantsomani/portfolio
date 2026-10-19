"""The briefing's two people in their own clothes (blender/human.py --who vedant / recruiter calls
dress()): the clothes recoloured (keeping their weave and folds), hair that reads as hair (dark,
a soft sheen, cut-out strands), and for Vedant his short beard: a stubble layer on the jaw, chin
and upper lip, dense in the middle and thinning out at its edges.
The body faces -Y here (MakeHuman's convention)."""

import bmesh
import bpy
from mathutils import Vector


def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m and m.node_tree else None


def _recolor(ob, color):
    """The cloth's own texture as light and shade, times the colour: the weave stays, the colour
    is ours."""
    for slot in ob.material_slots:
        m = slot.material
        b = _bsdf(m)
        if not b:
            continue
        nt = m.node_tree
        src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
        if src is None:
            b.inputs['Base Color'].default_value = (*color, 1)
            continue
        bw = nt.nodes.new('ShaderNodeRGBToBW')
        nt.links.new(src, bw.inputs[0])
        lift = nt.nodes.new('ShaderNodeMapRange')
        nt.links.new(bw.outputs[0], lift.inputs['Value'])
        lift.inputs['To Min'].default_value = 0.5
        lift.inputs['To Max'].default_value = 1.0
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        mix.inputs[6].default_value = (*color, 1)
        nt.links.new(lift.outputs[0], mix.inputs[7])
        nt.links.new(mix.outputs[2], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = max(0.6, b.inputs['Roughness'].default_value)
        b.inputs['Sheen Weight'].default_value = 0.3


def _hair(ob):
    """Dark hair: near black with a warm cast, a soft sheen along the strands; the cards' alpha
    kept, so the edges are strands, not a shell."""
    for slot in ob.material_slots:
        m = slot.material
        b = _bsdf(m)
        if not b:
            continue
        nt = m.node_tree
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
        for link in list(b.inputs['Base Color'].links):
            nt.links.remove(link)
        b.inputs['Base Color'].default_value = (0.014, 0.010, 0.008, 1)
        b.inputs['Roughness'].default_value = 0.42
        b.inputs['Coat Weight'].default_value = 0.0
        b.inputs['Sheen Weight'].default_value = 0.6
        b.inputs['Sheen Tint'].default_value = (0.45, 0.35, 0.28, 1)
        b.inputs['Specular IOR Level'].default_value = 0.35
        if tex is not None and not b.inputs['Alpha'].links:
            nt.links.new(tex.outputs['Alpha'], b.inputs['Alpha'])
        # Darker at the roots: the texture's own light and shade, through to the colour.
        if tex is not None:
            bw = nt.nodes.new('ShaderNodeRGBToBW')
            nt.links.new(tex.outputs['Color'], bw.inputs[0])
            mix = nt.nodes.new('ShaderNodeMix')
            mix.data_type = 'RGBA'
            nt.links.new(bw.outputs[0], mix.inputs[0])
            mix.inputs[6].default_value = (0.006, 0.004, 0.003, 1)
            mix.inputs[7].default_value = (0.03, 0.022, 0.016, 1)
            nt.links.new(mix.outputs[2], b.inputs['Base Color'])


def _beard(body, rig):
    """A short beard: a shell over the jaw, chin, cheeks' lower half and upper lip, its hairs a
    fine dark stipple, fading out towards the edge of the beard's area."""
    mw = body.matrix_world
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    head = rig.matrix_world @ rig.data.bones['mixamorig:Head'].head_local
    pts = [(mw @ v.co, v.index) for v in me.vertices]
    face = [(p, i) for p, i in pts if p.z > head.z - 0.04 and abs(p.x) < 0.09 and p.y < head.y - 0.02]
    nose = min(face, key=lambda q: q[0].y)[0]
    chin = min((p for p, _ in face if abs(p.x) < 0.02 and p.y < head.y - 0.06), key=lambda p: p.z)
    mouth_z = nose.z - 0.032

    def weight(p):
        x = abs(p.x)
        top = nose.z - 0.016 + 0.35 * x  # the cheek line, rising towards the ears
        if p.z > top or p.z < chin.z - 0.022 or x > 0.078 or p.y > head.y + 0.035:
            return 0.0
        if x < 0.024 and abs(p.z - mouth_z) < 0.009:
            return 0.0  # the lips
        edge = min(top - p.z, 0.078 - x, p.z - (chin.z - 0.022))
        return max(0.0, min(1.0, edge / 0.012))

    ev.to_mesh_clear()
    # The shell is cut from the body as it finally stands (its shape and masks applied), keeping
    # its bone weights.
    beard = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    beard.name = 'beard'
    bm = bmesh.new()
    bm.from_mesh(beard)
    w = {v.index: weight(mw @ v.co) for v in bm.verts}
    gone = [f for f in bm.faces if not all(w[v.index] > 0 for v in f.verts)]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    layer = bm.verts.layers.float.new('beard')
    for v in bm.verts:
        v[layer] = weight(mw @ v.co)
    bm.to_mesh(beard)
    bm.free()
    beard.materials.clear()
    ob = bpy.data.objects.new(f'{body.name.split("-")[0]}-beard', beard)
    bpy.context.scene.collection.objects.link(ob)
    for g in body.vertex_groups:
        if g.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=g.name)
    ob.parent = body.parent
    ob.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    ob.matrix_world = body.matrix_world.copy()
    d = ob.modifiers.new('off', 'DISPLACE')
    d.strength = 0.0012
    d.mid_level = 0.0
    a = ob.modifiers.new('Armature', 'ARMATURE')
    a.object = rig
    s = ob.modifiers.new('smooth', 'SUBSURF')
    s.levels = 0
    s.render_levels = 1
    for p in beard.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new('beard')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.008, 0.006, 0.005, 1)
    b.inputs['Roughness'].default_value = 0.55
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'beard'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    dots = nt.nodes.new('ShaderNodeTexVoronoi')
    dots.inputs['Scale'].default_value = 2600.0
    dots.feature = 'F1'
    nt.links.new(tc.outputs['Object'], dots.inputs['Vector'])
    hairs = nt.nodes.new('ShaderNodeMapRange')
    nt.links.new(dots.outputs['Distance'], hairs.inputs['Value'])
    hairs.inputs['From Min'].default_value = 0.3
    hairs.inputs['From Max'].default_value = 0.16
    shade = nt.nodes.new('ShaderNodeMath')
    shade.operation = 'MULTIPLY'
    nt.links.new(hairs.outputs[0], shade.inputs[0])
    nt.links.new(attr.outputs['Fac'], shade.inputs[1])
    base = nt.nodes.new('ShaderNodeMath')
    base.operation = 'MULTIPLY_ADD'  # a faint shadow of the beard under the hairs
    nt.links.new(attr.outputs['Fac'], base.inputs[0])
    base.inputs[1].default_value = 0.14
    base.inputs[2].default_value = 0.0  # the hairs themselves are strands (strands.py)
    clamp = nt.nodes.new('ShaderNodeClamp')
    nt.links.new(base.outputs[0], clamp.inputs['Value'])
    nt.links.new(clamp.outputs[0], b.inputs['Alpha'])
    beard.materials.append(m)
    return ob


def dress(body, rig, pro):
    who = body.name.split('-')[0]
    colors = {name: col for name, col in pro['wear']}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for name, col in colors.items():
            if ob.name.endswith(name) and col is not None:
                _recolor(ob, col)
        if pro.get('hair') and ob.name.endswith(pro['hair']):
            _hair(ob)
    if pro.get('beard'):
        _beard(body, rig)  # the beard's shadow on the skin, under the hairs
    if pro.get('strands'):
        import strands
        strands.grow(body, rig, pro['strands'], beard=bool(pro.get('beard')))
    print(f'[looks] {who} dressed', flush=True)


__all__ = ['dress', 'Vector']
