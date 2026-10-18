"""The lab set for /projects (SITE_SPEC §5 Projects): an abandoned engineering laboratory, built
entirely in code (no downloaded assets) and rendered with Cycles.

Run with Blender 5.2 from the repository root:
  blender -b --factory-startup -P blender/lab.py -- --shots rest --samples 256
Shots (comma-separated): rest (desk + phone stills and anchors), seq (the walk-in frames for
both), close (one close-up per item), anchors (positions only, no render), all.
Options: --samples N, --scale 0.5 (resolution factor for test renders), --frames 36.
Final film (--quality ultra): the hub still and the film's lab shots at 4K, the crew subdivided
once more, finer light and volumes, and the room's physics (fx.py). The film's lab shots are
lab-enter, lab-breaker, lab-power and lab-bench, one per run; each renders in two stages so many
GPUs can share it: --shots lab-enter --stage build keys it and saves blender/out/work/lab-enter.blend;
--shots lab-enter --stage render --slice k/N renders every Nth frame from the kth as JPEGs.
--preview 1 writes quick frames to blender/out/preview/ instead.
"""

import bpy
import bmesh
import json
import math
import os
import random
import sys
import time
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(
    sys.argv[sys.argv.index('-P') + 1] if '-P' in sys.argv else __file__)))
import crew as C  # noqa: E402
import fx  # noqa: E402


def script_path():
    for flag in ('-P', '--python'):
        if flag in sys.argv:
            return os.path.abspath(sys.argv[sys.argv.index(flag) + 1])
    return os.path.abspath(__file__)


ROOT = os.path.dirname(os.path.dirname(script_path()))
OUT = os.path.join(ROOT, 'blender', 'out')
WORK = os.path.join(ROOT, 'src', 'assets', 'work')
FONT = os.path.join(ROOT, 'blender', 'fonts', 'archivo-label.ttf')  # static Archivo (the site's own font)
ANCHORS = os.path.join(ROOT, 'src', 'data', 'lab-set.json')


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    opts = {'shots': 'rest', 'samples': 128, 'scale': 1.0, 'frames': 36, 'art': 'desk,phone',
            'only': '', 'frame': -1, 'quality': 'final', 'stage': 'all', 'slice': '0/1',
            'preview': False, 'res': '', 'threshold': 0.0, 'volstep': 0.0, 'nodust': False}
    i = 0
    while i < len(argv):
        key = argv[i].lstrip('-')
        if key in opts and i + 1 < len(argv):
            kind = type(opts[key])
            opts[key] = kind(argv[i + 1])
            i += 2
        else:
            i += 1
    shots = set(opts['shots'].split(','))
    if 'all' in shots:
        shots = {'rest', 'seq', 'close'}
    opts['shots'] = shots
    return opts


OPTS = parse_args()
ULTRA = OPTS['quality'] == 'ultra'
C.DETAIL = 1 if ULTRA else 0  # the crew's extra subdivision level


def use_gpu(scene):
    """The fastest GPU backend there is (preferences are not saved in .blend files)."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            found = [d for d in prefs.devices if d.type == kind]
            if found:
                for d in prefs.devices:
                    d.use = d.type == kind
                scene.cycles.device = 'GPU'
                print('[lab] device', kind, [d.name for d in found], flush=True)
                return
        except Exception as err:  # noqa: BLE001 - fall through to the next backend
            print('[lab] no', kind, err)
    scene.cycles.device = 'CPU'


if OPTS['stage'] == 'render':
    # A shot built and keyed earlier (--stage build): open it and render this process's share of
    # its frames, skipping any already on disk. Nothing else of the set is built.
    shot = sorted(OPTS['shots'])[0]
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'work', f'{shot}.blend'))
    sc = bpy.context.scene
    use_gpu(sc)
    # --res WxH and --samples given here override what the shot was built with (a faster pass).
    if OPTS['res']:
        sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in OPTS['res'].split('x'))
    if '--samples' in sys.argv:
        sc.cycles.samples = OPTS['samples']
    if OPTS['nodust']:
        for ob in sc.objects:
            if ob.name.startswith(('footdust', 'motes')):
                ob.hide_render = True
    if OPTS['threshold']:
        sc.cycles.adaptive_threshold = OPTS['threshold']
    if OPTS['volstep']:
        sc.cycles.volume_step_rate = OPTS['volstep']
    k, every = (int(v) for v in OPTS['slice'].split('/'))
    ext = 'jpg' if sc.render.image_settings.file_format == 'JPEG' else 'png'
    d = os.path.join(OUT, shot)
    os.makedirs(d, exist_ok=True)
    for f in range(sc.frame_start - 1, sc.frame_end):
        path = os.path.join(d, f'{f:04d}.{ext}')
        if f % every != k or (os.path.exists(path) and os.path.getsize(path) > 0):
            continue
        sc.frame_set(f + 1)
        sc.render.filepath = path
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[lab] {shot} {f + 1}/{sc.frame_end} {time.time() - t:.1f}s', flush=True)
    sys.exit(0)

random.seed(7)

# ---------------------------------------------------------------------------------------------
# The records on the set. IDs and titles restate recordIds() and the content collections;
# 'kind' is the prop that holds them. Positions are filled in as the set is built.
ITEMS = [
    {'id': 'saarthi', 'record': 'R-01', 'title': 'Saarthi', 'kind': 'laptop'},
    {'id': 'tessera', 'record': 'R-02', 'title': 'TESSERA', 'kind': 'print'},
    {'id': 'anav', 'record': 'R-04', 'title': 'ANAV', 'kind': 'frame'},
    {'id': 'smriti', 'record': 'R-06', 'title': 'SMRITI', 'kind': 'tablet'},
    {'id': 'dhwani-kavach', 'record': 'R-05', 'title': 'Dhwani-Kavach', 'kind': 'box'},
    {'id': 'pitsense', 'record': 'R-07', 'title': 'PitSense', 'kind': 'box'},
    {'id': 'iot-club-website', 'record': 'R-08', 'title': 'IoT & Robotics Club website', 'kind': 'box'},
    {'id': 'vajra', 'record': 'R-03', 'title': 'VAJRA', 'kind': 'case'},
    {'id': 'skynet', 'record': 'L-01', 'title': 'SKYNET', 'kind': 'case'},
    {'id': 'prahari', 'record': 'L-02', 'title': 'PRAHARI', 'kind': 'case'},
]
ITEM = {it['id']: it for it in ITEMS}

# ---------------------------------------------------------------------------------------------
# Scene and render settings.


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    use_gpu(scene)
    c = scene.cycles
    # Settings that newer versions may have renamed are applied one at a time, never fatally.
    base = (('samples', OPTS['samples']), ('use_adaptive_sampling', True),
            ('adaptive_threshold', 0.02), ('use_denoising', True),
            ('denoiser', 'OPENIMAGEDENOISE'), ('denoising_use_gpu', True),
            ('max_bounces', 6), ('diffuse_bounces', 3), ('glossy_bounces', 3),
            ('transmission_bounces', 4), ('volume_bounces', 1),
            ('transparent_max_bounces', 12), ('caustics_reflective', False),
            ('caustics_refractive', False), ('sample_clamp_indirect', 4.0),
            ('volume_step_rate', 4.0), ('seed', 0))
    # As arrival.py's final settings (measured there): no visible difference from twice the cost.
    ultra = (('adaptive_threshold', 0.01), ('adaptive_min_samples', 64), ('max_bounces', 8),
             ('diffuse_bounces', 4), ('glossy_bounces', 4), ('transmission_bounces', 8),
             ('volume_bounces', 2), ('transparent_max_bounces', 32), ('sample_clamp_indirect', 12.0),
             ('volume_step_rate', 1.0), ('denoising_prefilter', 'ACCURATE'),
             ('denoising_quality', 'HIGH'), ('use_light_tree', True))
    for attr, val in base + (ultra if ULTRA else ()):
        try:
            setattr(c, attr, val)
        except (AttributeError, TypeError) as err:
            print('[lab] skipped cycles.' + attr, err)
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            vs.look = look
            break
        except TypeError:
            continue
    vs.exposure = -0.45
    world = bpy.data.worlds.new('Night')
    scene.world = world
    try:
        world.use_nodes = True
    except Exception:  # noqa: BLE001 - always node-based in newer versions
        pass
    bg = world.node_tree.nodes.get('Background') or world.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.004, 0.005, 0.005, 1)
    bg.inputs['Strength'].default_value = 1.0
    out = world.node_tree.nodes.get('World Output') or world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return scene


SCENE = reset_scene()


# ---------------------------------------------------------------------------------------------
# Geometry helpers. Meshes are built at real size (no object scale), so object and world
# coordinates are metres and the procedural textures keep one scale everywhere.


def link(ob):
    SCENE.collection.objects.link(ob)
    return ob


def mesh_obj(name, verts, faces, mat=None, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if uvs:
        layer = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                layer.data[li].uv = uvs[me.loops[li].vertex_index]
    if mat:
        me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))


def box(name, center, size, mat=None, rot=(0, 0, 0), bevel=0.0, parent=None):
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, mat)
    if parent:
        ob.parent = parent
    ob.location = center
    ob.rotation_euler = rot
    if bevel > 0:
        m = ob.modifiers.new('bevel', 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'NONE'
    return ob


def FLAT(spin):
    """Rotation that lays a card face-up on a horizontal surface, turned by spin."""
    return (math.radians(-90), 0, spin)


def card(name, center, w, h, mat, rot=(0, 0, 0), parent=None):
    """A plane in XZ facing -Y (towards the camera), with 0–1 UVs."""
    v = [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]
    ob = mesh_obj(name, v, [(0, 1, 2, 3)], mat, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    if parent:
        ob.parent = parent
    ob.location = center
    ob.rotation_euler = rot
    return ob


def cylinder(name, center, r, depth, mat=None, rot=(0, 0, 0), segs=20, r2=None, caps=True, parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me))
    if parent:
        ob.parent = parent
    ob.location = center
    ob.rotation_euler = rot
    for p in me.polygons:
        p.use_smooth = True
    return ob


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob = link(bpy.data.objects.new(name, None))
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------------------------------------
# Materials. Everything procedural except the real images on screens and prints.


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def plain(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m, nt, out = new_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def noise(nt, vec, scale, detail=4.0, rough=0.55, dims='3D'):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.noise_dimensions = dims
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def ramp(nt, fac, a, b, lo=0.4, hi=0.6):
    r = nt.nodes.new('ShaderNodeMapRange')
    r.inputs['From Min'].default_value = lo
    r.inputs['From Max'].default_value = hi
    r.inputs['To Min'].default_value = a
    r.inputs['To Max'].default_value = b
    nt.links.new(fac, r.inputs['Value'])
    return r.outputs['Result']


def mix_col(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    nt.links.new(fac, m.inputs['Factor'])
    for sock, val in ((6, a), (7, b)):
        if isinstance(val, tuple):
            m.inputs[sock].default_value = (*val, 1)
        else:
            nt.links.new(val, m.inputs[sock])
    return m.outputs[2]


def math_node(nt, op, a, b=None):
    m = nt.nodes.new('ShaderNodeMath')
    m.operation = op
    for i, val in enumerate((a, b)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            m.inputs[i].default_value = val
        else:
            nt.links.new(val, m.inputs[i])
    return m.outputs[0]


def worn(name, base, dark, rough=(0.55, 0.85), moss=0.0, stains=0.0, wet=0.0, dust=0.0,
         metal=0.0, rust=0.0, bump=0.12, scale=1.0):
    """Concrete, painted steel, cardboard: one layered procedural material.
    base/dark: the two tones; moss: green growth near the floor; stains: vertical water runs;
    wet: glossy puddles on horizontal faces; dust: pale on upward faces; rust: orange-brown wear."""
    m, nt, out = new_mat(name)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    pos = geo.outputs['Position']
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    patches = noise(nt, pos, 0.7 * scale, 6, 0.6)
    grain = noise(nt, pos, 9 * scale, 8, 0.65)
    col = mix_col(nt, ramp(nt, patches, 0, 1, 0.35, 0.65), dark, base)
    col = mix_col(nt, ramp(nt, grain, 0.0, 0.25, 0.3, 0.7), col, dark)
    r = ramp(nt, patches, rough[0], rough[1], 0.3, 0.7)
    if stains:
        # Vertical runs: noise stretched along Z.
        sv = nt.nodes.new('ShaderNodeMapping')
        sv.inputs['Scale'].default_value = (7 * scale, 7 * scale, 0.35 * scale)
        nt.links.new(pos, sv.inputs['Vector'])
        runs = noise(nt, sv.outputs['Vector'], 1.0, 3, 0.5)
        col = mix_col(nt, ramp(nt, runs, 0, stains, 0.55, 0.75), col, (0.03, 0.035, 0.03))
    if rust:
        rn = noise(nt, pos, 4 * scale, 10, 0.7)
        rmask = ramp(nt, rn, 0, rust, 0.58, 0.68)
        col = mix_col(nt, rmask, col, (0.16, 0.07, 0.035))
        r = mix_col(nt, rmask, r, (0.9, 0.9, 0.9))
    if moss:
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sep.inputs['Vector'])
        low = ramp(nt, sep.outputs['Z'], 1.0, 0.0, 0.0, 0.9)
        mn = noise(nt, pos, 2.2, 8, 0.7)
        mmask = math_node(nt, 'MULTIPLY', ramp(nt, mn, 0, 1, 0.48, 0.62), low)
        mmask = math_node(nt, 'MULTIPLY', mmask, moss)
        col = mix_col(nt, mmask, col, (0.035, 0.055, 0.018))
        r = mix_col(nt, mmask, r, (0.95, 0.95, 0.95))
    if dust:
        nz = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], nz.inputs['Vector'])
        up = ramp(nt, nz.outputs['Z'], 0, dust, 0.5, 0.95)
        dn = noise(nt, pos, 14, 4, 0.5)
        up = math_node(nt, 'MULTIPLY', up, ramp(nt, dn, 0.55, 1.0, 0.3, 0.7))
        col = mix_col(nt, up, col, (0.32, 0.31, 0.28))
        r = mix_col(nt, up, r, (0.95, 0.95, 0.95))
    if wet:
        nz = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(geo.outputs['Normal'], nz.inputs['Vector'])
        flat = ramp(nt, nz.outputs['Z'], 0, 1, 0.9, 0.99)
        pn = noise(nt, pos, 0.32, 3, 0.5)
        puddle = math_node(nt, 'MULTIPLY', ramp(nt, pn, 0, wet, 0.52, 0.56), flat)
        col = mix_col(nt, puddle, col, (0.012, 0.013, 0.012))
        r = mix_col(nt, puddle, r, (0.04, 0.04, 0.04))
    nt.links.new(col, b.inputs['Base Color'])
    rough_bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(r, rough_bw.inputs['Color'])
    nt.links.new(rough_bw.outputs['Val'], b.inputs['Roughness'])
    b.inputs['Metallic'].default_value = metal
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    nt.links.new(grain, bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def image_mat(name, path, emit=0.0, rough=0.4, gloss=0.0):
    """A real image: printed (diffuse) or on a screen (emission plus a faint glass sheen)."""
    m, nt, out = new_mat(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = 'Cubic'
    if emit:
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Strength'].default_value = emit
        nt.links.new(tex.outputs['Color'], em.inputs['Color'])
        gl = nt.nodes.new('ShaderNodeBsdfGlossy')
        gl.inputs['Roughness'].default_value = 0.12
        add = nt.nodes.new('ShaderNodeMixShader')
        add.inputs[0].default_value = gloss or 0.06
        nt.links.new(em.outputs['Emission'], add.inputs[1])
        nt.links.new(gl.outputs['BSDF'], add.inputs[2])
        nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    else:
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        b.inputs['Roughness'].default_value = rough
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
        nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m, tex.image


def glass_mat(name):
    """Thin dirty glass: mostly transparent, so the sun still reaches the room without caustics."""
    m, nt, out = new_mat(name)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (0.86, 0.9, 0.88, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.25
    mix = nt.nodes.new('ShaderNodeMixShader')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    grime = noise(nt, geo.outputs['Position'], 6, 6, 0.6)
    nt.links.new(ramp(nt, grime, 0.08, 0.35, 0.4, 0.7), mix.inputs[0])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(gl.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def mesh_fence_mat(name, cell=0.06):
    """Chain-link: a diamond wire grid (a brick texture turned 45°) cut out of a transparent sheet."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, math.radians(45), 0)  # the card lies in XZ
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    sw = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(mp.outputs['Vector'], sw.inputs['Vector'])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(sw.outputs['X'], comb.inputs['X'])
    nt.links.new(sw.outputs['Z'], comb.inputs['Y'])
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0 / cell
    br.inputs['Mortar Size'].default_value = 0.08
    br.offset = 0.0
    br.squash = 1.0
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.0
    nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
    metal = nt.nodes.new('ShaderNodeBsdfPrincipled')
    metal.inputs['Base Color'].default_value = (0.2, 0.21, 0.2, 1)
    metal.inputs['Metallic'].default_value = 0.9
    metal.inputs['Roughness'].default_value = 0.45
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(br.outputs['Fac'], mix.inputs[0])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(metal.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def haze_mat(name, density):
    m, nt, out = new_mat(name)
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (0.78, 0.86, 0.82, 1)
    v.inputs['Density'].default_value = density
    v.inputs['Anisotropy'].default_value = 0.55
    nt.links.new(v.outputs['Volume'], out.inputs['Volume'])
    return m


def emit_mat(name, color, strength):
    m, nt, out = new_mat(name)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], out.inputs['Surface'])
    return m


M = {
    'concrete': worn('Concrete', (0.25, 0.26, 0.24), (0.1, 0.105, 0.095), moss=1.0, stains=0.85,
                     rough=(0.7, 0.95), bump=0.2),
    'floor': worn('Floor', (0.17, 0.175, 0.165), (0.06, 0.063, 0.058), moss=0.7, wet=1.0,
                  dust=0.4, rough=(0.55, 0.9), bump=0.15, scale=0.8),
    'ceiling': worn('Ceiling', (0.16, 0.165, 0.155), (0.05, 0.052, 0.048), stains=1.0,
                    rough=(0.8, 0.95), bump=0.25),
    'steel': worn('Painted steel', (0.18, 0.21, 0.19), (0.07, 0.08, 0.075), rust=1.0, dust=0.5,
                  rough=(0.45, 0.75), metal=0.35, bump=0.05, scale=2.0),
    'darksteel': worn('Dark steel', (0.06, 0.065, 0.065), (0.025, 0.027, 0.027), rust=0.6,
                      rough=(0.35, 0.6), metal=0.8, bump=0.03, scale=3.0),
    'table': worn('Bench top', (0.05, 0.058, 0.054), (0.018, 0.02, 0.019), dust=0.45,
                  rough=(0.3, 0.7), metal=0.4, rust=0.4, bump=0.04, scale=3.0),
    'cardboard': worn('Cardboard', (0.3, 0.25, 0.18), (0.16, 0.13, 0.09), dust=0.85,
                      rough=(0.8, 0.95), bump=0.08, scale=4.0),
    'binder': worn('Binder', (0.07, 0.1, 0.11), (0.03, 0.04, 0.045), dust=0.7, rough=(0.5, 0.8),
                   bump=0.03, scale=5.0),
    'case': worn('Hard case', (0.05, 0.055, 0.055), (0.025, 0.027, 0.027), dust=0.6,
                 rough=(0.35, 0.55), bump=0.06, scale=6.0),
    'paper': plain('Paper', (0.62, 0.61, 0.56), 0.9),
    'label': plain('Label card', (0.72, 0.71, 0.66), 0.85),
    'ink': plain('Ink', (0.02, 0.02, 0.02), 0.7),
    'seal': plain('Seal tape', (0.42, 0.03, 0.03), 0.6),
    'black': plain('Black plastic', (0.012, 0.012, 0.013), 0.35),
    'alu': plain('Laptop shell', (0.09, 0.095, 0.1), 0.32, 0.9),
    'keys': plain('Keys', (0.02, 0.021, 0.022), 0.5),
    'frame': plain('Frame', (0.015, 0.015, 0.015), 0.4),
    'mat': plain('Print mat', (0.7, 0.69, 0.64), 0.9),
    'leaf': plain('Leaf', (0.03, 0.06, 0.022), 0.55),
    'vine': plain('Vine', (0.05, 0.045, 0.03), 0.8),
    'cord': plain('Cord', (0.01, 0.01, 0.01), 0.5),
    'shade': worn('Lamp shade', (0.08, 0.12, 0.1), (0.03, 0.045, 0.04), rust=0.7, rough=(0.3, 0.6),
                  metal=0.6, scale=4.0),
    'glass': glass_mat('Window glass'),
    'fence': mesh_fence_mat('Chain link'),
    'mug': plain('Mug', (0.4, 0.4, 0.38), 0.3),
    'yellow': plain('Meter body', (0.38, 0.33, 0.12), 0.55),
}

# ---------------------------------------------------------------------------------------------
# The room: 11 m wide (x), 12 m deep (y, the back wall at +5), 4.4 m to the ceiling, entered
# through a doorway in the front wall at y = -7 from a dark corridor. Daylight comes in through
# high windows over the racks, behind the bench, so its shafts fall towards the camera.

W, BACK, FRONT, H = 5.5, 5.0, -7.0, 4.4
T = 0.3  # wall thickness


def lamp(name, kind, loc, energy, color, target=None, **kw):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    for k, v in kw.items():
        setattr(data, k, v)
    ob = link(bpy.data.objects.new(name, data))
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    return ob


box('Floor', (0, -2.5, -0.1), (2 * W, BACK - FRONT + 4.0, 0.2), M['floor'])

# Ceiling with a broken panel at the back left (vines hang from it, cold light falls through).
HOLE = (-3.8, -2.2, 1.0, 2.6)  # x0, x1, y0, y1
box('Ceiling A', (0, (FRONT + HOLE[2]) / 2, H + 0.1), (2 * W, HOLE[2] - FRONT, 0.2), M['ceiling'])
box('Ceiling B', (0, (HOLE[3] + BACK) / 2, H + 0.1), (2 * W, BACK - HOLE[3], 0.2), M['ceiling'])
box('Ceiling C', ((-W + HOLE[0]) / 2, (HOLE[2] + HOLE[3]) / 2, H + 0.1),
    (HOLE[0] + W, HOLE[3] - HOLE[2], 0.2), M['ceiling'])
box('Ceiling D', ((HOLE[1] + W) / 2, (HOLE[2] + HOLE[3]) / 2, H + 0.1),
    (W - HOLE[1], HOLE[3] - HOLE[2], 0.2), M['ceiling'])
box('Roof', (0, -2.5, H + 1.2), (2 * W + 1, BACK - FRONT + 6, 0.3), M['ceiling'])
for y in (-5.0, -2.6, -0.2, 1.8, 3.6):
    box(f'Beam {y}', (0, y, H - 0.25), (2 * W, 0.35, 0.5), M['ceiling'])

# Back wall with three tall windows behind the open racks: the daylight streams through the shelves.
BWZ = (0.75, 3.95)
BWIN = [(-4.0, -1.5), (-1.25, 1.25), (1.6, 4.1)]
by = BACK + T / 2


def back_piece(name, x0, x1, z0, z1):
    box(name, ((x0 + x1) / 2, by, (z0 + z1) / 2), (x1 - x0, T, z1 - z0), M['concrete'])


back_piece('Back low', -W - T, W + T, -0.2, BWZ[0])
back_piece('Back high', -W - T, W + T, BWZ[1], H + 0.2)
edges = [-W - T] + [v for w in BWIN for v in w] + [W + T]
for i in range(0, len(edges), 2):
    back_piece(f'Back pier {i}', edges[i], edges[i + 1], BWZ[0], BWZ[1])
back_broken = {(0, 1, 2), (0, 3, 3), (0, 0, 1), (1, 0, 3), (1, 2, 2), (1, 3, 0), (1, 1, 1), (2, 0, 2), (2, 2, 3),
               (2, 3, 1)}
for wi, (x0, x1) in enumerate(BWIN):
    cols, rows = 4, 4
    pw, ph = (x1 - x0) / cols, (BWZ[1] - BWZ[0]) / rows
    for c in range(cols + 1):
        box(f'Back mullion {wi}-{c}', (x0 + c * pw, by, (BWZ[0] + BWZ[1]) / 2), (0.05, 0.08, BWZ[1] - BWZ[0]),
            M['darksteel'])
    for r in range(rows + 1):
        box(f'Back transom {wi}-{r}', ((x0 + x1) / 2, by, BWZ[0] + r * ph), (x1 - x0, 0.08, 0.05), M['darksteel'])
    for c in range(cols):
        for r in range(rows):
            if (wi, c, r) not in back_broken:
                card(f'Back pane {wi}-{c}-{r}', (x0 + (c + 0.5) * pw, by, BWZ[0] + (r + 0.5) * ph),
                     pw - 0.05, ph - 0.05, M['glass'])
sky_back = box('Sky back', (0, BACK + 9.0, 3.0), (30.0, 0.1, 14.0), emit_mat('Sky back', (0.5, 0.6, 0.58), 0.38))
sky_back.visible_shadow = False  # the sun shines through it into the windows
outside = worn('Outside', (0.03, 0.035, 0.032), (0.012, 0.014, 0.013), rough=(0.8, 0.95), bump=0.1)
box('Next building', (4.5, BACK + 7.5, 3.0), (7.0, 0.4, 9.0), outside)
box('Next building b', (-7.5, BACK + 8.0, 2.0), (6.0, 0.4, 7.0), outside)
canopy = bmesh.new()
for tx, ty, h in ((-2.6, BACK + 3.2, 6.5), (0.4, BACK + 4.5, 7.5), (2.9, BACK + 2.6, 5.5), (-5.0, BACK + 5.0, 6.0)):
    cylinder(f'Tree {tx}', (tx, ty, h / 2), 0.16, h, outside, r2=0.09, segs=10)
    for k in range(5):
        a = random.uniform(0, 6.28)
        cylinder(f'Branch {tx} {k}', (tx + 0.5 * math.cos(a), ty + 0.3 * math.sin(a), h * random.uniform(0.55, 0.9)),
                 0.04, 1.6, outside, rot=(random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9), a), segs=6)
    for k in range(260):
        c = Vector((tx + random.gauss(0, 1.1), ty + random.gauss(0, 0.8), h * 0.82 + random.gauss(0, 0.9)))
        sz = random.uniform(0.08, 0.16)
        rot = Matrix.Rotation(random.uniform(0, 6.28), 4, 'Z') @ Matrix.Rotation(random.uniform(0, 3.1), 4, 'X')
        base = Matrix.Translation(c) @ rot
        vs = [canopy.verts.new(base @ Vector(v)) for v in ((0, -sz, 0), (sz * 0.6, 0, 0), (0, sz, 0), (-sz * 0.6, 0, 0))]
        canopy.faces.new(vs)
cme = bpy.data.meshes.new('Canopy')
canopy.to_mesh(cme)
canopy.free()
cme.materials.append(M['leaf'])
link(bpy.data.objects.new('Canopy', cme))

# Right wall, and the left wall with two tall windows (side light, ivy).
box('Right wall', (W + T / 2, (BACK + FRONT) / 2, H / 2), (T, BACK - FRONT, H + 0.4), M['concrete'])
WIN = [(-3.0, -0.8), (0.4, 2.6)]
WZ = (1.3, 3.6)
lx = -W - T / 2


def wall_piece(name, y0, y1, z0, z1):
    box(name, (lx, (y0 + y1) / 2, (z0 + z1) / 2), (T, y1 - y0, z1 - z0), M['concrete'])


wall_piece('Left low', FRONT, BACK, -0.2, WZ[0])
wall_piece('Left high', FRONT, BACK, WZ[1], H + 0.2)
wall_piece('Left pier 1', FRONT, WIN[0][0], WZ[0], WZ[1])
wall_piece('Left pier 2', WIN[0][1], WIN[1][0], WZ[0], WZ[1])
wall_piece('Left pier 3', WIN[1][1], BACK, WZ[0], WZ[1])
broken = {(0, 1, 2), (0, 2, 0), (1, 0, 1), (1, 2, 2), (1, 1, 0)}  # (window, col, row) panes gone
for wi, (y0, y1) in enumerate(WIN):
    cols, rows = 3, 4
    pw, ph = (y1 - y0) / cols, (WZ[1] - WZ[0]) / rows
    for c in range(cols + 1):
        box(f'Mullion {wi}-{c}', (lx, y0 + c * pw, (WZ[0] + WZ[1]) / 2), (0.08, 0.05, WZ[1] - WZ[0]),
            M['darksteel'])
    for r in range(rows + 1):
        box(f'Transom {wi}-{r}', (lx, (y0 + y1) / 2, WZ[0] + r * ph), (0.08, y1 - y0, 0.05),
            M['darksteel'])
    for c in range(cols):
        for r in range(rows):
            if (wi, c, r) not in broken:
                card(f'Pane {wi}-{c}-{r}', (lx, y0 + (c + 0.5) * pw, WZ[0] + (r + 0.5) * ph),
                     pw - 0.05, ph - 0.05, M['glass'], rot=(0, 0, math.radians(90)))
sky_left = box('Sky left', (-W - 4.0, -1.0, 2.5), (0.1, 16.0, 10.0), emit_mat('Sky left', (0.55, 0.64, 0.6), 0.8))
sky_left.visible_shadow = False

# Front wall with the doorway, and the corridor behind it.
DOOR = (-0.8, 0.8, 2.4)
fy = FRONT - T / 2
box('Front left', ((-W + DOOR[0]) / 2, fy, H / 2), (DOOR[0] + W, T, H + 0.4), M['concrete'])
box('Front right', ((DOOR[1] + W) / 2, fy, H / 2), (W - DOOR[1], T, H + 0.4), M['concrete'])
box('Front lintel', (0, fy, (DOOR[2] + H) / 2 + 0.1), (DOOR[1] - DOOR[0], T, H - DOOR[2] + 0.2),
    M['concrete'])
for side, x in (('l', DOOR[0] - 0.04), ('r', DOOR[1] + 0.04)):
    box(f'Door jamb {side}', (x, fy, DOOR[2] / 2), (0.08, T + 0.06, DOOR[2]), M['darksteel'])
box('Door head', (0, fy, DOOR[2] + 0.04), (DOOR[1] - DOOR[0] + 0.16, T + 0.06, 0.08), M['darksteel'])
box('Corridor left', (-1.35, FRONT - 2.2, 1.4), (0.2, 4.0, 2.8), M['concrete'])
box('Corridor right', (1.35, FRONT - 2.2, 1.4), (0.2, 4.0, 2.8), M['concrete'])
box('Corridor ceiling', (0, FRONT - 2.2, 2.9), (3.0, 4.0, 0.2), M['ceiling'])
box('Corridor end', (0, FRONT - 4.3, 1.4), (3.0, 0.2, 2.8), M['concrete'])

# Pipes along the right wall, a dead fuse box, a cable tray down the room with cables sagging off it.
for i, z in enumerate((3.75, 3.95)):
    cylinder(f'Pipe {i}', (W - 0.25 - i * 0.18, -1.0, z), 0.06 + 0.02 * i, 12.0, M['darksteel'],
             rot=(math.radians(90), 0, 0))
box('Fuse box', (W - 0.1, -1.6, 1.7), (0.16, 0.6, 0.8), M['steel'], bevel=0.01)
box('Cable tray', (2.2, -1.0, H - 0.6), (0.4, 11.5, 0.06), M['darksteel'])
cables = bpy.data.curves.new('Cables', 'CURVE')
cables.dimensions = '3D'
cables.bevel_depth = 0.009
for (xa, ya, xb, yb, sag) in ((2.1, -2.4, 0.9, -0.6, 1.1), (2.3, 0.8, 3.4, 2.4, 0.8),
                              (2.1, -4.0, 1.2, -2.9, 0.7), (-1.6, 2.0, -0.6, 3.1, 0.9)):
    sp = cables.splines.new('POLY')
    n = 18
    sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1)
        sp.points[i].co = (xa + (xb - xa) * t, ya + (yb - ya) * t, H - 0.62 - sag * 4 * t * (1 - t), 1)
cab = link(bpy.data.objects.new('Cables', cables))
cab.data.materials.append(M['cord'])

# The haze that makes the light visible: thin, and scattering forwards, so the shafts from the
# back windows read towards the camera.
box('Haze', (0, -2.6, H / 2), (2 * W - 0.02, BACK - FRONT + 4.6, H - 0.02), haze_mat('Haze', 0.016))

# ---------------------------------------------------------------------------------------------
# Racks along the back wall: evidence (left), archive (middle), and the caged restricted section.
# Each record has a shelf to itself, under its own small pool of light; the dressing around it is
# sparse, so the eye finds the records first.

RACK_Y = (BACK - 0.6, BACK - 0.08)  # front, back
LEVELS = [0.14, 0.66, 1.18, 1.70, 2.22]
RACK_H = 2.62
RACKS = {'evidence': (-4.0, -1.5), 'archive': (-1.25, 1.25), 'cage': (1.6, 4.1)}


def rack(name, x0, x1):
    yf, yb = RACK_Y
    for x in (x0, x1):
        for y in (yf, yb):
            box(f'{name} post', (x, y, RACK_H / 2), (0.04, 0.04, RACK_H), M['steel'])
    for z in LEVELS:
        box(f'{name} shelf', ((x0 + x1) / 2, (yf + yb) / 2, z), (x1 - x0 + 0.04, yb - yf, 0.025),
            M['steel'], bevel=0.004)
        box(f'{name} lip', ((x0 + x1) / 2, yf, z + 0.02), (x1 - x0, 0.012, 0.05), M['steel'])
    span = x1 - x0
    ang = math.atan2(RACK_H - 0.3, span)
    for sgn, nm in ((-1, 'a'), (1, 'b')):
        box(f'{name} brace {nm}', ((x0 + x1) / 2, yb, RACK_H / 2), (math.hypot(span, RACK_H - 0.3), 0.01, 0.03),
            M['steel'], rot=(0, sgn * ang, 0))


for name, (x0, x1) in RACKS.items():
    rack(name, x0, x1)

FONT_DATA = bpy.data.fonts.load(FONT) if os.path.exists(FONT) else None


def text(body, size, loc, mat=M['ink'], align='LEFT', parent=None, rot=(math.radians(90), 0, 0)):
    cu = bpy.data.curves.new('Text', 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    if FONT_DATA:
        cu.font = FONT_DATA
    ob = link(bpy.data.objects.new('Text', cu))
    ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def wrap(s, n):
    words, lines, cur = s.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f'{cur} {w}'.strip()
    lines.append(cur)
    return lines


def label(record, title, center, w=0.2, h=0.095):
    """A record label: card, record ID large, title under it. The text restates the record."""
    card('Label', center, w, h, M['label'])
    x, y, z = center
    text(record, h * 0.34, (x - w / 2 + w * 0.07, y - 0.0015, z + h * 0.18))
    for i, line in enumerate(wrap(title.upper(), 20)[:2]):
        text(line, h * 0.15, (x - w / 2 + w * 0.07, y - 0.0015, z - h * 0.16 - i * h * 0.18))


def archive_box(name, x, z, w=0.36, d=0.42, h=0.27, tilt=0.0, mat=None):
    yf = RACK_Y[0] + 0.03
    g = empty(name, (x, yf + d / 2, z + h / 2), (0, 0, tilt))
    box(f'{name} body', (0, 0, -0.01), (w, d, h - 0.02), mat or M['cardboard'], parent=g, bevel=0.004)
    box(f'{name} lid', (0, 0, h / 2 - 0.02), (w + 0.012, d + 0.012, 0.045), mat or M['cardboard'],
        parent=g, bevel=0.004)
    box(f'{name} grip', (0, -d / 2 - 0.0005, h / 2 - 0.09), (0.09, 0.002, 0.025), M['black'], parent=g)
    return g


def binder(name, x, z, w=0.065, h=0.31, lean=0.0):
    yf = RACK_Y[0] + 0.05
    g = empty(name, (x, yf + 0.15, z + h / 2), (0, lean, 0))
    box(f'{name} body', (0, 0, 0), (w, 0.29, h), M['binder'], parent=g, bevel=0.003)
    box(f'{name} spine label', (0, -0.146, 0.06), (w * 0.6, 0.002, 0.08), M['label'], parent=g)
    return g


def fill_shelf(x0, x1, z, keep=(), density=0.6):
    """Dressing: archive boxes, binders, loose paper, and empty stretches; reserved spans stay clear."""
    x = x0 + 0.05
    while x < x1 - 0.12:
        inside = [b for a, b in keep if a <= x <= b]
        if inside:
            x = max(inside) + 0.05
            continue
        limit = min([a for a, b in keep if a > x] + [x1 - 0.03])
        if random.random() > density:
            x += random.uniform(0.15, 0.45)
            continue
        roll = random.random()
        if roll < 0.45 and x + 0.38 < limit:
            archive_box(f'Box {x:.2f} {z:.2f}', x + 0.18, z + 0.013, tilt=random.uniform(-0.06, 0.06))
            x += 0.38 + random.uniform(0.0, 0.1)
        elif roll < 0.8:
            n = random.randint(2, 5)
            for i in range(n):
                if x + 0.07 > limit:
                    break
                lean = random.uniform(0.25, 0.45) if i == n - 1 and random.random() < 0.5 else 0
                binder(f'Binder {x:.2f} {z:.2f}', x + 0.034, z + 0.013, lean=lean)
                x += 0.068
            x += random.uniform(0.06, 0.16)
        elif x + 0.3 < limit:
            for i in range(random.randint(3, 9)):
                card(f'Paper {x:.2f}', (x + 0.15, RACK_Y[0] + 0.25, z + 0.016 + i * 0.002), 0.21, 0.297,
                     M['paper'], rot=FLAT(random.uniform(-0.2, 0.2)))
            x += 0.32
        else:
            x += 0.1


# Where each record sits: rack, level index, x centre.
SLOTS = {
    'tessera': ('evidence', 3, -2.85),
    'anav': ('evidence', 2, -2.45),
    'smriti': ('evidence', 1, -3.0),
    'dhwani-kavach': ('archive', 3, -0.45),
    'pitsense': ('archive', 2, 0.5),
    'iot-club-website': ('archive', 4, 0.05),
    'vajra': ('cage', 2, 2.55),
    'skynet': ('cage', 1, 3.2),
    'prahari': ('cage', 3, 2.95),
}
DENSITY = {'evidence': 0.55, 'archive': 0.65, 'cage': 0.22}
for rname, (x0, x1) in RACKS.items():
    for li, z in enumerate(LEVELS):
        keep = [(sx - 0.48, sx + 0.48) for sid, (r, l, sx) in SLOTS.items() if r == rname and l == li]
        fill_shelf(x0, x1, z, keep, DENSITY[rname])

ANCHOR = {}  # item id → (anchor world position, [objects to bound])


def pool(item, target, color=(0.78, 0.9, 0.88), energy=48.0, size=24):
    """A small spot from above and in front: the record's own pool of light."""
    t = Vector(target)
    lamp(f'{item} pool', 'SPOT', t + Vector((0.15, -1.3, 1.45)), energy, color, t,
         spot_size=math.radians(size), spot_blend=0.55, shadow_soft_size=0.05)


def place_print(item, image, slot):
    rname, li, x = slot
    z = LEVELS[li] + 0.013
    mat, img = image_mat(f'{item} print', os.path.join(WORK, image), rough=0.75)
    iw, ih = img.size
    s = min(0.42 / iw, 0.36 / ih)
    w, h = iw * s, ih * s
    g = empty(item, (x, RACK_Y[0] + 0.32, z), (math.radians(-13), 0, 0))
    board = box(f'{item} board', (0, 0.006, h / 2 + 0.035), (w + 0.04, 0.008, h + 0.07), M['steel'], parent=g)
    clip = box(f'{item} clip', (0, -0.004, h + 0.055), (0.1, 0.016, 0.034), M['darksteel'], parent=g)
    pr = card(f'{item} image', (0, -0.0005, h / 2 + 0.03), w, h, mat, parent=g)
    label(ITEM[item]['record'], ITEM[item]['title'], (x + w / 2 + 0.14, RACK_Y[0] + 0.004, z + 0.075))
    anchor = Vector((x, RACK_Y[0] + 0.28, z + h / 2 + 0.03))
    ANCHOR[item] = (anchor, [board, pr, clip])
    pool(item, anchor)


def place_frame(item, image, slot):
    rname, li, x = slot
    z = LEVELS[li] + 0.013
    mat, img = image_mat(f'{item} photo', os.path.join(WORK, image), rough=0.5)
    iw, ih = img.size
    w = 0.44
    h = w * ih / iw
    m = 0.03
    g = empty(item, (x, RACK_Y[0] + 0.3, z), (math.radians(-10), 0, 0))
    zc = h / 2 + m + 0.012
    fr = box(f'{item} frame', (0, 0.008, zc), (w + 2 * m + 0.03, 0.022, h + 2 * m + 0.03), M['frame'], parent=g,
             bevel=0.003)
    mt = card(f'{item} mat', (0, -0.0035, zc), w + 2 * m, h + 2 * m, M['mat'], parent=g)
    ph = card(f'{item} image', (0, -0.004, zc), w, h, mat, parent=g)
    gl = card(f'{item} glass', (0, -0.006, zc), w + 2 * m, h + 2 * m, M['glass'], parent=g)
    label(ITEM[item]['record'], ITEM[item]['title'], (x + w / 2 + 0.17, RACK_Y[0] + 0.004, z + 0.075))
    anchor = Vector((x, RACK_Y[0] + 0.26, z + zc))
    ANCHOR[item] = (anchor, [fr])
    pool(item, anchor)


def place_tablet(item, image, slot):
    rname, li, x = slot
    z = LEVELS[li] + 0.013
    mat, img = image_mat(f'{item} screen', os.path.join(WORK, image), emit=1.8)
    iw, ih = img.size
    sw = 0.34
    sh = sw * ih / iw
    g = empty(item, (x, RACK_Y[0] + 0.26, z + 0.02), (math.radians(-20), 0, 0))
    body = box(f'{item} body', (0, 0.005, sh / 2 + 0.02), (sw + 0.03, 0.009, sh + 0.03), M['black'], parent=g,
               bevel=0.005)
    scr = card(f'{item} image', (0, -0.0004, sh / 2 + 0.02), sw, sh, mat, parent=g)
    box(f'{item} stand', (x, RACK_Y[0] + 0.32, z + 0.012), (0.2, 0.14, 0.014), M['darksteel'])
    label(ITEM[item]['record'], ITEM[item]['title'], (x + sw / 2 + 0.15, RACK_Y[0] + 0.004, z + 0.075))
    anchor = Vector((x, RACK_Y[0] + 0.22, z + sh / 2 + 0.04))
    ANCHOR[item] = (anchor, [body])
    pool(item, anchor, energy=26)


def place_box(item, slot):
    rname, li, x = slot
    z = LEVELS[li] + 0.013
    g = archive_box(item, x, z, w=0.46, h=0.32)
    label(ITEM[item]['record'], ITEM[item]['title'], (x, RACK_Y[0] + 0.03 - 0.0008, z + 0.14), w=0.26, h=0.12)
    anchor = Vector((x, RACK_Y[0] + 0.05, z + 0.16))
    ANCHOR[item] = (anchor, list(g.children))
    pool(item, anchor)


def place_case(item, slot):
    rname, li, x = slot
    z = LEVELS[li] + 0.013
    w, d, h = 0.6, 0.38, 0.25
    yf = RACK_Y[0] + 0.05
    g = empty(item, (x, yf + d / 2, z + h / 2))
    body = box(f'{item} case', (0, 0, 0), (w, d, h), M['case'], parent=g, bevel=0.02)
    box(f'{item} seam', (0, -d / 2 - 0.001, 0.025), (w - 0.03, 0.004, 0.012), M['black'], parent=g)
    for sx in (-0.21, 0.21):
        box(f'{item} latch', (sx, -d / 2 - 0.006, 0.025), (0.06, 0.012, 0.045), M['darksteel'], parent=g)
    for hx_ in (-0.12, 0.12):
        box(f'{item} handle', (hx_, 0, h / 2 + 0.012), (0.03, 0.12, 0.022), M['black'], parent=g)
    # The seal: a strap of tape across the lid and the latch; the case stays shut.
    box(f'{item} seal', (0.21, -d / 2 - 0.0135, 0.0), (0.035, 0.002, h + 0.006), M['seal'], parent=g)
    box(f'{item} seal top', (0.21, -0.02, h / 2 + 0.0015), (0.035, d - 0.02, 0.002), M['seal'], parent=g)
    label(ITEM[item]['record'], ITEM[item]['title'], (x - 0.06, yf - 0.0025, z + h / 2 - 0.01), w=0.22, h=0.09)
    anchor = Vector((x, yf, z + h / 2))
    ANCHOR[item] = (anchor, [body])
    pool(item, anchor, color=(1.0, 0.16, 0.12), energy=22, size=28)


place_print('tessera', 'tessera-grid.jpg', SLOTS['tessera'])
place_frame('anav', 'anav-cover.jpg', SLOTS['anav'])
place_tablet('smriti', 'smriti-cover.jpg', SLOTS['smriti'])
for bid in ('dhwani-kavach', 'pitsense', 'iot-club-website'):
    place_box(bid, SLOTS[bid])
for cid in ('vajra', 'skynet', 'prahari'):
    place_case(cid, SLOTS[cid])

# The cage around the restricted rack: chain-link panels on a steel frame, a padlocked door.
cx0, cx1 = RACKS['cage'][0] - 0.12, RACKS['cage'][1] + 0.12
cyf = RACK_Y[0] - 0.55
CH = 2.9
for x in (cx0, cx1, (cx0 + cx1) / 2):
    box('Cage post', (x, cyf, CH / 2), (0.05, 0.05, CH), M['darksteel'])
box('Cage top rail', ((cx0 + cx1) / 2, cyf, CH), ((cx1 - cx0) + 0.05, 0.05, 0.05), M['darksteel'])
box('Cage mid rail', ((cx0 + cx1) / 2, cyf, 1.0), ((cx1 - cx0) + 0.05, 0.04, 0.04), M['darksteel'])
for x in (cx0, cx1):
    box('Cage side rail', (x, (cyf + BACK) / 2, CH), (0.05, BACK - cyf, 0.05), M['darksteel'])
mid = (cx0 + cx1) / 2
card('Cage panel L', ((cx0 + mid) / 2, cyf, CH / 2), mid - cx0, CH, M['fence'])
card('Cage door', ((mid + cx1) / 2, cyf - 0.01, CH / 2 - 0.05), cx1 - mid - 0.04, CH - 0.12, M['fence'])
for x in (cx0, cx1):
    card('Cage side', (x, (cyf + BACK) / 2, CH / 2), BACK - cyf, CH, M['fence'], rot=(0, 0, math.radians(90)))
box('Padlock', (mid + 0.06, cyf - 0.04, 1.05), (0.05, 0.025, 0.06), M['darksteel'], bevel=0.006)
# The emergency light over the cage: the room's only red.
cylinder('Beacon', ((cx0 + cx1) / 2, cyf + 0.1, CH + 0.12), 0.06, 0.12, emit_mat('Beacon', (1.0, 0.05, 0.04), 10.0))

# ---------------------------------------------------------------------------------------------
# The worktable and the laptop: Saarthi, the centrepiece, under the strongest light. The screen
# shows the two real images from the board file side by side: the KiCad render and the copper plot.

TY = 0.45  # table centre
TZ = 0.92
box('Bench top', (0, TY, TZ - 0.025), (2.4, 1.1, 0.05), M['table'], bevel=0.006)
# A steel workbench: drawer pedestals at both ends, a modesty panel between them.
for x in (-0.86, 0.86):
    box('Bench pedestal', (x, TY + 0.02, (TZ - 0.05) / 2), (0.62, 1.0, TZ - 0.05), M['steel'], bevel=0.006)
    for k in range(3):
        z = 0.16 + k * 0.26
        box('Drawer front', (x, TY - 0.482, z + 0.11), (0.56, 0.012, 0.22), M['darksteel'], bevel=0.004)
        box('Drawer pull', (x, TY - 0.492, z + 0.18), (0.16, 0.012, 0.018), M['steel'])
box('Bench panel', (0, TY + 0.3, 0.52), (1.1, 0.03, 0.7), M['steel'])

laptop = empty('Laptop', (0.0, TY - 0.2, TZ), (0, 0, math.radians(-9)))
LW, LD = 0.38, 0.26
laptop_base = box('Laptop base', (0, 0, 0.01), (LW, LD, 0.02), M['alu'], parent=laptop, bevel=0.004)
box('Laptop keys', (0, 0.02, 0.0205), (LW - 0.05, 0.11, 0.001), M['keys'], parent=laptop)
box('Laptop pad', (0, -0.085, 0.0205), (0.12, 0.07, 0.0008), M['black'], parent=laptop)
lid = empty('Laptop lid', (0, LD / 2, 0.02), (math.radians(-14), 0, 0))
lid.parent = laptop
LH = 0.25
box('Laptop lid shell', (0, 0.004, LH / 2), (LW, 0.006, LH), M['alu'], parent=lid, bevel=0.003)
box('Laptop bezel', (0, -0.0005, LH / 2), (LW - 0.01, 0.002, LH - 0.01), M['black'], parent=lid)
screen = card('Laptop screen', (0, -0.0016, LH / 2 + 0.004), LW - 0.03, LH - 0.04,
              emit_mat('Screen field', (0.02, 0.024, 0.023), 1.0), parent=lid)
SQ = 0.158
for side, img_name in ((-1, 'saarthi-render-sq.jpg'), (1, 'saarthi-plot-sq.jpg')):
    mat, _ = image_mat(f'Saarthi {img_name}', os.path.join(WORK, 'derived', img_name), emit=2.4, gloss=0.04)
    card(f'Screen {img_name}', (side * (SQ / 2 + 0.006), -0.0022, LH / 2 + 0.004), SQ, SQ, mat, parent=lid)
cylinder('Laptop cable', (0.42, TY - 0.05, TZ + 0.005), 0.004, 0.5, M['cord'], rot=(0, math.radians(90), 0.6))

# Generic bench dressing (tools, not project hardware).
box('Solder station', (-0.72, TY + 0.15, TZ + 0.05), (0.19, 0.16, 0.1), M['darksteel'], bevel=0.008)
cylinder('Iron holder', (-0.52, TY + 0.15, TZ + 0.06), 0.03, 0.11, M['darksteel'], r2=0.02)
box('Multimeter', (0.62, TY - 0.05, TZ + 0.02), (0.09, 0.18, 0.04), M['yellow'], rot=(0, 0, 0.4), bevel=0.008)
cylinder('Mug', (0.9, TY + 0.25, TZ + 0.05), 0.042, 0.1, M['mug'])
box('Toolbox', (-1.0, TY + 0.32, TZ + 0.09), (0.42, 0.2, 0.18), M['steel'], bevel=0.01)
for i in range(9):
    card(f'Bench paper {i}', (random.uniform(-0.75, 0.75), TY + random.uniform(-0.25, 0.35), TZ + 0.001 + i * 0.0015),
         0.21, 0.297, M['paper'], rot=FLAT(random.uniform(-0.9, 0.9)))

# The bench lamp: a hanging enamel shade on a cord, its pool falling on the laptop.
LAMP = Vector((0.0, TY - 0.12, 1.8))
cylinder('Lamp cord', (LAMP.x, LAMP.y, (LAMP.z + H) / 2 + 0.12), 0.005, H - LAMP.z - 0.2, M['cord'])
cylinder('Lamp shade', (LAMP.x, LAMP.y, LAMP.z + 0.08), 0.24, 0.18, M['shade'], r2=0.05, caps=False, segs=32)
cylinder('Lamp bulb', (LAMP.x, LAMP.y, LAMP.z + 0.03), 0.035, 0.06, emit_mat('Bulb', (1.0, 0.9, 0.78), 14.0))

# A broken fluorescent fitting hanging by one chain over the evidence rack.
fit = empty('Fitting', (-2.6, 3.0, 3.2), (0, math.radians(18), math.radians(6)))
box('Fitting body', (0, 0, 0), (1.25, 0.12, 0.06), M['steel'], parent=fit)
box('Fitting tube', (0, 0, -0.04), (1.18, 0.03, 0.03), emit_mat('Tube', (0.75, 0.9, 0.85), 2.5), parent=fit)
cylinder('Fitting chain', (-2.0, 3.0, 3.75), 0.004, 0.9, M['darksteel'])

# A stool on its side, a box fallen from the archive rack, debris under the broken ceiling.
stool = empty('Stool', (1.45, -0.75, 0.2), (math.radians(80), 0, math.radians(35)))
cylinder('Stool seat', (0, 0, 0.0), 0.18, 0.04, M['steel'], parent=stool)
for a in range(3):
    ang = a * 2 * math.pi / 3
    cylinder('Stool leg', (0.12 * math.cos(ang), 0.12 * math.sin(ang), -0.3), 0.015, 0.6, M['steel'],
             rot=(0.12 * math.sin(ang), -0.12 * math.cos(ang), 0), parent=stool)
fallen = archive_box('Fallen box', -0.9, -0.02, tilt=0.5)
fallen.location = (-1.6, 3.2, 0.13)
fallen.rotation_euler = (0.25, 0.1, 0.7)
for i in range(16):
    card(f'Floor paper {i}', (random.uniform(-2.6, 1.6), random.uniform(1.3, 3.9), 0.003 + i * 0.001),
         0.21, 0.297, M['paper'], rot=FLAT(random.uniform(0, math.pi)))

me = bpy.data.meshes.new('Debris')
bm = bmesh.new()
for i in range(170):
    if i < 90:
        p = Vector((random.uniform(HOLE[0] - 0.6, HOLE[1] + 0.6), random.uniform(HOLE[2] - 0.6, HOLE[3] + 0.4), 0))
    else:
        side = random.choice((-1, 1))
        p = Vector((side * random.uniform(W - 0.8, W - 0.2), random.uniform(FRONT + 0.5, BACK - 0.8), 0))
    r = random.uniform(0.015, 0.09) * (1.6 if i < 12 else 1.0)
    mat = (Matrix.Translation(p + Vector((0, 0, r * 0.4)))
           @ Matrix.Rotation(random.uniform(0, 6.28), 4, 'Z')
           @ Matrix.Diagonal((random.uniform(0.7, 1.4), random.uniform(0.7, 1.4), random.uniform(0.4, 0.8), 1)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=mat)
bm.to_mesh(me)
bm.free()
me.materials.append(M['concrete'])
link(bpy.data.objects.new('Debris', me))

# ---------------------------------------------------------------------------------------------
# Overgrowth: vines through the broken ceiling, ivy at the side windows, and ivy hanging down
# over the tall windows behind the racks.


def grow(name, starts, steps, step_len, drift, gravity, wall=None, leaf_every=2, leaf_size=0.05):
    """Random-walk vines with leaves. wall: ('x', value) or ('y', value) keeps them on a wall."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.007
    cu.bevel_resolution = 2
    leaves = bmesh.new()
    for s in starts:
        p = Vector(s)
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), -1)).normalized()
        pts = [p.copy()]
        for i in range(steps):
            d = (d + Vector((random.uniform(-drift, drift), random.uniform(-drift, drift),
                             random.uniform(-drift, drift) - gravity))).normalized()
            p = p + d * step_len
            if wall and wall[0] == 'x':
                p.x = wall[1] + random.uniform(0.0, 0.03)
            elif wall and wall[0] == 'y':
                p.y = wall[1] - random.uniform(0.0, 0.03)
            if p.z < 0.05:
                break
            pts.append(p.copy())
            if i % leaf_every:
                continue
            for _ in range(random.randint(1, 3)):
                sz = leaf_size * random.uniform(0.6, 1.35)
                spin = Matrix.Rotation(random.uniform(0, 6.28), 4, 'Z')
                if wall and wall[0] == 'x':
                    rot = Matrix.Rotation(math.radians(90), 4, 'Y') @ spin
                elif wall and wall[0] == 'y':
                    rot = Matrix.Rotation(math.radians(90), 4, 'X') @ spin
                else:
                    rot = spin @ Matrix.Rotation(random.uniform(-1.2, 1.2), 4, 'X')
                off = Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03)))
                base = Matrix.Translation(p + off) @ rot
                vs = [leaves.verts.new(base @ Vector(c)) for c in
                      ((0, -sz * 0.5, 0), (sz * 0.4, -sz * 0.05, 0), (sz * 0.18, sz * 0.5, 0), (0, sz * 0.78, 0),
                       (-sz * 0.18, sz * 0.5, 0), (-sz * 0.4, -sz * 0.05, 0))]
                leaves.faces.new(vs)
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for i, q in enumerate(pts):
            sp.points[i].co = (q.x, q.y, q.z, 1)
    vine = link(bpy.data.objects.new(name, cu))
    vine.data.materials.append(M['vine'])
    lm = bpy.data.meshes.new(f'{name} leaves')
    leaves.to_mesh(lm)
    leaves.free()
    lm.materials.append(M['leaf'])
    return vine, link(bpy.data.objects.new(f'{name} leaves', lm))


hx, hy = (HOLE[0] + HOLE[1]) / 2, (HOLE[2] + HOLE[3]) / 2
grow('Ceiling vines', [(hx + random.uniform(-0.75, 0.75), hy + random.uniform(-0.75, 0.75), H) for _ in range(28)],
     steps=46, step_len=0.065, drift=0.38, gravity=0.85, leaf_every=1, leaf_size=0.075)
ivy_starts = []
for (y0, y1) in WIN:
    ivy_starts += [(-W + 0.02, random.uniform(y0 - 0.4, y1 + 0.4), WZ[0] + random.uniform(-0.1, 0.3)) for _ in range(8)]
    ivy_starts += [(-W + 0.02, random.uniform(y0, y1), WZ[1] + random.uniform(0.0, 0.6)) for _ in range(6)]
grow('Window ivy', ivy_starts, steps=45, step_len=0.06, drift=0.6, gravity=0.35, wall=('x', -W + 0.012),
     leaf_every=1, leaf_size=0.06)
sill_starts = []
for (x0, x1) in BWIN:
    sill_starts += [(random.uniform(x0 - 0.2, x1 + 0.2), BACK - 0.012, BWZ[1] + random.uniform(0.0, 0.35))
                    for _ in range(9)]
grow('Window ivy back', sill_starts, steps=34, step_len=0.055, drift=0.45, gravity=0.6, wall=('y', BACK - 0.012),
     leaf_every=1, leaf_size=0.065)

# ---------------------------------------------------------------------------------------------
# Light: low sun through the tall side windows (shafts slanting across the room in the haze), sky
# glow at the high windows over the racks, the bench lamp on the laptop, each record's pool, light
# through the broken ceiling, and red in the cage.

sun_dir = Vector((0.12, -1.0, -0.42)).normalized()
sun = lamp('Sun', 'SUN', (0, 0, 10), 4.0, (0.86, 0.97, 0.93), angle=math.radians(0.8))
sun.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()
lamp('Bench pool', 'SPOT', (LAMP.x, LAMP.y, LAMP.z), 420, (1.0, 0.9, 0.78), (0.0, TY - 0.2, TZ),
     spot_size=math.radians(40), spot_blend=0.4, shadow_soft_size=0.04)
lamp('Rack fill', 'AREA', (0.0, 1.6, 3.9), 22, (0.72, 0.86, 0.84), (0.0, BACK - 0.4, 1.3), size=5.0)
lamp('Breach', 'AREA', (hx, hy, H + 0.9), 650, (0.7, 0.84, 0.82), (hx, hy, 0), size=1.4)
lamp('Cage red', 'POINT', ((cx0 + cx1) / 2, cyf + 0.25, CH - 0.1), 30, (1.0, 0.07, 0.05), shadow_soft_size=0.05)
lamp('Cage spill', 'SPOT', ((cx0 + cx1) / 2, cyf - 0.6, 3.6), 35, (1.0, 0.1, 0.08), ((cx0 + cx1) / 2, BACK - 0.4, 1.4),
     spot_size=math.radians(50), spot_blend=0.8, shadow_soft_size=0.1)
lamp('Doorway fill', 'AREA', (0, FRONT + 1.0, 2.2), 20, (0.6, 0.7, 0.68), (0, 2, 1.2), size=2.0)

# ---------------------------------------------------------------------------------------------
# Cameras. Desk 16:9 and phone 9:16 rest on the same composition: the bench and its laptop in
# front, the racks behind under the high windows, the cage at the right. Both walk in from the
# corridor through the doorway. Focus sits at 3 m at f/8, so the laptop and the racks both read.

SHOTS = {
    'desk': {
        'res': (2400, 1350), 'seq_res': (1280, 720), 'lens': 28,
        'start': ((0.0, FRONT - 1.9, 1.62), (0.0, 2.0, 1.4)),
        'rest': ((0.0, -1.85, 1.42), (0.0, 3.0, 1.2)),
    },
    'phone': {
        'res': (1080, 1920), 'seq_res': (720, 1280), 'lens': 31,
        'start': ((0.0, FRONT - 1.9, 1.6), (0.0, 2.0, 1.5)),
        'rest': ((0.0, -2.9, 1.55), (0.0, 3.0, 1.35)),
    },
}
FOCUS = 3.0


def make_camera(name, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    data.sensor_fit = 'HORIZONTAL'
    data.clip_start = 0.05
    data.clip_end = 60
    data.dof.use_dof = True
    data.dof.aperture_fstop = 8.0
    return link(bpy.data.objects.new(name, data))


def ease(t):
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def pose(cam, loc, target, focus=None):
    cam.location = loc
    look_at(cam, target)
    cam.data.dof.focus_distance = focus or FOCUS


def set_res(res):
    SCENE.render.resolution_x = max(16, int(res[0] * OPTS['scale']))
    SCENE.render.resolution_y = max(16, int(res[1] * OPTS['scale']))
    SCENE.render.resolution_percentage = 100


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    SCENE.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'[lab] {os.path.relpath(path, ROOT)} {time.time() - t:.1f}s', flush=True)


def laptop_focus():
    bpy.context.view_layer.update()
    return screen.matrix_world.translation


def anchors_for(cam, res):
    set_res(res)
    bpy.context.view_layer.update()
    out = {}
    ANCHOR['saarthi'] = (laptop_focus().copy(), [screen, laptop_base])
    for it in ITEMS + ([{'id': 'transmission'}] if 'transmission' in ANCHOR else []):
        pos, obs = ANCHOR[it['id']]
        v = world_to_camera_view(SCENE, cam, pos)
        xs, ys = [], []
        for ob in obs:
            for c in ob.bound_box:
                w = ob.matrix_world @ Vector(c)
                p = world_to_camera_view(SCENE, cam, w)
                xs.append(p.x)
                ys.append(1 - p.y)
        out[it['id']] = {
            'x': round(v.x, 4),
            'y': round(1 - v.y, 4),
            'box': [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)],
        }
    return out


# ---------------------------------------------------------------------------------------------
# The projector and its hologram. The projector is always on the bench (the room's hotspot for the
# transmission); the hologram itself is only in the shots that show it (--shots holo, holoanim): it
# throws Vedant's portrait into the air beside the laptop. The image is the real photo
# (src/assets/portrait/vedant.jpg), cropped to him and drawn as light: dark parts of the photo add
# nothing, so the background falls away by itself.

PORTRAIT = os.path.join(ROOT, 'src', 'assets', 'portrait', 'vedant.jpg')
HOLO = Vector((-0.5, TY - 0.14, TZ))
CYAN = (0.25, 0.75, 1.0)
puck = cylinder('Projector', HOLO + Vector((0, 0, 0.018)), 0.075, 0.036, M['darksteel'], segs=32)
cylinder('Projector lens', HOLO + Vector((0, 0, 0.037)), 0.05, 0.003, emit_mat('Projector lens', CYAN, 6.0), segs=32)
ANCHOR['transmission'] = (HOLO + Vector((0, 0, 0.03)), [puck])
HOLO_CTRL = {}
if OPTS['shots'] & {'holo', 'holoanim', 'lab-bench', 'hub'}:
    m, nt, out = new_mat('Hologram')
    tc = nt.nodes.new('ShaderNodeTexCoord')

    def value(name, v):
        n = nt.nodes.new('ShaderNodeValue')
        n.name = name
        n.outputs[0].default_value = v
        HOLO_CTRL[name] = n.outputs[0]
        return n.outputs[0]

    gain, phase, shift = value('gain', 1.0), value('phase', 0.0), value('shift', 0.0)
    x0 = 0.47
    # The crop, nudged sideways on a glitch frame.
    uv = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['UV'], uv.inputs['Vector'])
    band = math_node(nt, 'GREATER_THAN', math_node(nt, 'SINE', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', uv.outputs['Y'], 23.0), phase)), 0.93)
    ux = math_node(nt, 'ADD', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', uv.outputs['X'], 1 - x0 - 0.02), x0),
                   math_node(nt, 'MULTIPLY', band, shift))
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(ux, comb.inputs['X'])
    nt.links.new(uv.outputs['Y'], comb.inputs['Y'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(PORTRAIT, check_existing=True)
    tex.interpolation = 'Cubic'
    nt.links.new(comb.outputs['Vector'], tex.inputs['Vector'])
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(tex.outputs['Color'], bw.inputs['Color'])
    lum = ramp(nt, bw.outputs['Val'], 0.0, 1.0, 0.06, 0.5)
    # Soft oval around him, so the frame's edge never shows.
    dx = math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', uv.outputs['X'], 0.47), 1.6)
    dy = math_node(nt, 'SUBTRACT', uv.outputs['Y'], 0.5)
    d = math_node(nt, 'SQRT', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', dx, dx), math_node(nt, 'MULTIPLY', dy, dy)))
    oval = ramp(nt, d, 1.0, 0.0, 0.32, 0.62)
    # Scan lines that drift upward, and a fade toward the projector.
    lines = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', math_node(nt, 'SINE', math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', uv.outputs['Y'], 360.0), math_node(nt, 'MULTIPLY', phase, 6.0))), 0.35), 0.65)
    base = ramp(nt, uv.outputs['Y'], 0.35, 1.0, 0.0, 0.18)
    k = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', lum, oval), lines), base)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*CYAN, 1)
    nt.links.new(math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', k, 6.0), gain), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs['BSDF'], add.inputs[0])
    nt.links.new(em.outputs['Emission'], add.inputs[1])
    nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    hw, hh = 0.46, 0.46 * 1460 / (2624 * (1 - x0 - 0.02))
    holo = card('Hologram', HOLO + Vector((0, 0, 0.06 + hh / 2)), hw, hh, m, rot=(0, 0, math.radians(-14)))
    # The beam: a faint cone of lit dust from the lens up to the image.
    vm, vnt, vout = new_mat('Hologram beam')
    pv = vnt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (*CYAN, 1)
    pv.inputs['Density'].default_value = 0.3
    pv.inputs['Emission Color'].default_value = (*CYAN, 1)
    pv.inputs['Emission Strength'].default_value = 0.05
    vnt.links.new(pv.outputs['Volume'], vout.inputs['Volume'])
    HOLO_CTRL['beam'] = pv.inputs['Density']
    cylinder('Hologram beam', HOLO + Vector((0, 0, 0.04 + (0.06 + hh) / 2)), 0.05, 0.06 + hh - 0.02, vm,
             r2=0.2, segs=32)
    HOLO_CTRL['light'] = lamp('Hologram light', 'POINT', HOLO + Vector((0.1, -0.3, 0.12)), 2.5, CYAN,
                              shadow_soft_size=0.2)

# ---------------------------------------------------------------------------------------------
# The mains. Fluorescent fittings on the ceiling (one failing, one dead) and a breaker panel on
# the left wall by the door. Everything electric hangs off it: the tubes, each record's pool, the
# bench lamp, the laptop, the cage's red light and the projector's standby glow. The film keys it
# (the crew resets the tripped main); stills render with the power on. The transmitter's beacon
# runs on its own battery.

FITTINGS = [(-2.6, -3.9), (2.6, -3.9), (-2.6, -1.4), (2.6, -1.4), (2.6, 0.9)]
for i, (x, y) in enumerate(FITTINGS):
    fit_ = empty(f'Ceiling fitting {i}', (x, y, H - 0.5))
    box(f'Ceiling fitting body {i}', (0, 0, 0.03), (1.25, 0.16, 0.06), M['steel'], parent=fit_)
    box(f'Ceiling tube {i}', (0, 0, -0.012), (1.18, 0.028, 0.028),
        emit_mat(f'Ceiling tube {i}', (0.78, 0.92, 0.88), 9.0), parent=fit_)
    for sx in (-0.5, 0.5):
        cylinder(f'Ceiling fitting chain {i}{sx}', (x + sx, y, H - 0.33), 0.003, 0.3, M['darksteel'])
    lamp(f'Ceiling light {i}', 'AREA', (x, y, H - 0.54), 75.0, (0.78, 0.92, 0.88), (x, y, 0.0),
         shape='RECTANGLE', size=1.15, size_y=0.06)

# The panel: a steel box on the wall, its door hinged at the left edge (seen from the room), a row
# of breakers inside and the main in the middle, tripped (lever down). A red lamp says no mains.
PANEL = Vector((-W + 0.075, -5.6, 1.45))
PX = -W + 0.15  # the panel's open front
PW, PH = 0.5, 0.7
box('Panel back', (-W + 0.005, PANEL.y, PANEL.z), (0.01, PW, PH), M['darksteel'])
for name, c, size in (('top', (PANEL.x, PANEL.y, PANEL.z + PH / 2), (0.15, PW, 0.012)),
                      ('bottom', (PANEL.x, PANEL.y, PANEL.z - PH / 2), (0.15, PW, 0.012)),
                      ('left', (PANEL.x, PANEL.y - PW / 2, PANEL.z), (0.15, 0.012, PH)),
                      ('right', (PANEL.x, PANEL.y + PW / 2, PANEL.z), (0.15, 0.012, PH))):
    box(f'Panel {name}', c, size, M['steel'])
for row, z in enumerate((PANEL.z + 0.19, PANEL.z - 0.19)):
    for k in range(9):
        y = PANEL.y - 0.2 + k * 0.05
        box(f'Breaker {row}{k}', (-W + 0.035, y, z), (0.05, 0.04, 0.08), M['black'])
        box(f'Breaker toggle {row}{k}', (-W + 0.065, y, z + 0.012), (0.014, 0.012, 0.022), M['black'])
box('Main breaker', (-W + 0.04, PANEL.y, PANEL.z), (0.06, 0.1, 0.11), M['black'])
LEVER = empty('Main lever', (-W + 0.075, PANEL.y, PANEL.z))
LEVER.rotation_mode = 'XYZ'
box('Main lever handle', (0.0, 0.0, 0.035), (0.016, 0.03, 0.07), M['yellow'], parent=LEVER)
LEVER_OFF, LEVER_ON = math.radians(150), math.radians(30)  # down and out (tripped), up and out
LEVER.rotation_euler = (0.0, LEVER_ON, 0.0)
DOOR = empty('Panel hinge', (PX + 0.006, PANEL.y - PW / 2, PANEL.z))
DOOR.rotation_mode = 'XYZ'
box('Panel door', (0.0, PW / 2, 0.0), (0.012, PW, PH - 0.01), M['steel'], parent=DOOR)
box('Panel latch', (0.012, PW - 0.05, 0.0), (0.014, 0.02, 0.07), M['darksteel'], parent=DOOR)
HANDLE = Vector((0.02, PW - 0.05, 0.0))  # where a hand takes the door, in the hinge's frame
text('MAINS', 0.035, (0.008, PW / 2, PH / 2 - 0.08), M['ink'], align='CENTER', parent=DOOR,
     rot=(math.radians(90), 0, math.radians(90)))
LED = {}
for col, dz, rgb in (('red', 0.025, (1.0, 0.04, 0.02)), ('green', -0.025, (0.1, 1.0, 0.25))):
    LED[col] = emit_mat(f'Panel lamp {col}', rgb, 8.0)
    cylinder(f'Panel lamp {col}', (0.014, PW - 0.08, PH / 2 - 0.07 + dz), 0.008, 0.012, LED[col],
             rot=(0, math.radians(90), 0), segs=16, parent=DOOR)

POWER = []  # (owner, attribute, full value, group)


def wire(owner, attr, group):
    POWER.append((owner, attr, getattr(owner, attr), group))


def strength(mat):
    return bpy.data.materials[mat].node_tree.nodes['Emission'].inputs['Strength']


for i in range(len(FITTINGS)):
    wire(bpy.data.objects[f'Ceiling light {i}'].data, 'energy', f'tube{i}')
    wire(strength(f'Ceiling tube {i}'), 'default_value', f'tube{i}')
wire(strength('Tube'), 'default_value', 'old tube')
pools = sorted((o for o in bpy.data.objects if o.name.endswith(' pool') and o.type == 'LIGHT'
                and o.name != 'Bench pool'), key=lambda o: o.location.x)
for k, o in enumerate(pools):
    wire(o.data, 'energy', f'pool{k}')
wire(bpy.data.objects['Bench pool'].data, 'energy', 'bench')
wire(strength('Bulb'), 'default_value', 'bench')
wire(strength('Screen field'), 'default_value', 'screen')
for m in bpy.data.materials:
    if m.name.startswith('Saarthi '):
        wire(m.node_tree.nodes['Emission'].inputs['Strength'], 'default_value', 'screen image')
for name in ('Cage red', 'Cage spill'):
    wire(bpy.data.objects[name].data, 'energy', 'cage')
wire(strength('Projector lens'), 'default_value', 'standby')
wire(strength('Panel lamp red'), 'default_value', 'no mains')
wire(strength('Panel lamp green'), 'default_value', 'mains')
BEACON = strength('Beacon')


def _hash(n, seed):
    x = math.sin(n * 12.9898 + seed * 78.233) * 43758.5453
    return x - math.floor(x)


def _tube(u, seed, failing=False, dead=False):
    """A fluorescent tube u seconds after it is switched on: blinks while it strikes, then holds.
    A failing tube keeps dropping out; a dead one blinks twice and gives up."""
    if u < 0:
        return 0.0
    if dead:
        return 0.6 if u < 0.5 and _hash(int(u * 20), seed) > 0.75 else 0.0
    if u < 0.55:
        return 1.0 if _hash(int(u * 28), seed) > 0.55 else 0.06
    if failing and _hash(int(u * 9), seed) < 0.18:
        return 0.15
    return 1.0


def mains(s):
    """How much of each group is on s seconds after the main goes back on (s < 0: off)."""
    lv = {g: 0.0 for _, _, _, g in POWER}
    lv['no mains'] = 1.0
    if s < 0:
        return lv
    lv['no mains'], lv['mains'] = 0.0, 1.0
    for i in range(len(FITTINGS)):
        lv[f'tube{i}'] = _tube(s - 1.6 - 0.4 * i, i, failing=i == 3, dead=i == 4)
    lv['old tube'] = _tube(s - 1.0, 9, failing=True)
    lv['cage'] = 1.0 if s > 1.4 else 0.0
    for k in range(len(pools)):
        lv[f'pool{k}'] = min(1.0, max(0.0, (s - 2.6 - 0.16 * k) / 0.12))
    lv['bench'] = 1 - math.exp(-max(0.0, s - 3.6) / 0.35) if s > 3.6 else 0.0
    lv['screen'] = min(1.0, max(0.0, (s - 4.0) / 0.2))
    lv['screen image'] = min(1.0, max(0.0, (s - 4.6) / 0.5))
    lv['standby'] = 0.25 if s > 4.3 else 0.0
    return lv


def power(levels):
    for owner, attr, full, group in POWER:
        setattr(owner, attr, full * levels.get(group, 1.0))


# The room at rest, for every still (the hub, the close-ups, the hologram loop): the power on, the
# tubes low (two of them failing anyway), so the record pools and the windows keep the light.
REST = mains(99.0)
REST.update({f'tube{i}': 0.35 for i in range(len(FITTINGS))})
power(REST)


cams = {k: make_camera(f'Cam {k}', s['lens']) for k, s in SHOTS.items()}
shots = OPTS['shots']
anchors = {}
prev = {}
if os.path.exists(ANCHORS):
    with open(ANCHORS, encoding='utf-8') as fh:
        prev = json.load(fh)

for key, s in SHOTS.items():
    cam = cams[key]
    SCENE.camera = cam
    pose(cam, *s['rest'])
    anchors[key] = {'width': s['res'][0], 'height': s['res'][1], 'items': anchors_for(cam, s['res'])}
    if key not in OPTS['art'].split(','):
        continue
    if 'rest' in shots or 'still' in shots:
        set_res(s['res'])
        render_to(os.path.join(OUT, f'rest-{key}.png'))
    if 'rest' in shots or 'door' in shots:
        # The doorway: the walk-in's first frame at full size, the page's first paint.
        set_res(s['res'])
        pose(cam, *s['start'])
        render_to(os.path.join(OUT, f'door-{key}.png'))
        pose(cam, *s['rest'])
    if 'seq' in shots:
        set_res(s['seq_res'])
        n = OPTS['frames']
        (l0, t0), (l1, t1) = s['start'], s['rest']
        for i in range(n):
            k = ease(i / (n - 1))
            loc = Vector(l0).lerp(Vector(l1), k)
            tgt = Vector(t0).lerp(Vector(t1), k)
            # A slight hand-held settle as the camera arrives.
            loc.z += 0.025 * math.sin(k * math.pi)
            pose(cam, loc, tgt)
            render_to(os.path.join(OUT, f'seq-{key}', f'{i:03d}.png'))
        pose(cam, *s['rest'])

with open(ANCHORS, 'w', encoding='utf-8') as fh:
    keep = {k: prev[k] for k in ('frames', 'close') if k in prev}
    json.dump({'note': 'Generated by blender/lab.py: on-screen anchors per camera, as fractions.',
               **anchors, **keep}, fh, indent=2)
print('[lab] anchors →', os.path.relpath(ANCHORS, ROOT))

if 'close' in shots:
    cam = make_camera('Cam close', 50)
    cam.data.dof.aperture_fstop = 2.8
    SCENE.camera = cam
    set_res((1600, 900))
    for it in ITEMS:
        if OPTS['only'] and it['id'] not in OPTS['only'].split(','):
            continue
        pos, _ = ANCHOR[it['id']]
        if it['id'] == 'saarthi':
            loc = pos + Vector((-0.2, -0.62, 0.16))
        else:
            loc = pos + Vector((0.16, -1.05, 0.05))
        pose(cam, loc, pos, focus=(pos - loc).length)
        render_to(os.path.join(OUT, 'close', f'{it["id"]}.png'))

def span01(t, a, b):
    return min(1.0, max(0.0, (t - a) / (b - a)))


def holo_camera():
    cam = make_camera('Cam holo', 38)
    cam.data.dof.aperture_fstop = 2.8
    SCENE.camera = cam
    target = HOLO + Vector((0.06, 0, 0.24))
    pose(cam, HOLO + Vector((0.95, -1.0, 0.42)), target, focus=(Vector((0.95, -1.0, 0.18))).length)
    return cam


def encode(frames_dir, out_path, res, crf, frames, fps):
    vs = bpy.data.scenes.new('Encode')
    vs.render.resolution_x, vs.render.resolution_y = res
    vs.render.resolution_percentage = 100
    vs.render.fps = fps
    vs.frame_start, vs.frame_end = 1, frames
    vs.view_settings.view_transform = 'Standard'  # the frames are already graded
    se = vs.sequence_editor_create()
    strips = se.strips if hasattr(se, 'strips') else se.sequences
    files = sorted(f for f in os.listdir(frames_dir) if f[:4].isdigit() and f.endswith('.png'))
    try:
        strip = strips.new_image('frames', os.path.join(frames_dir, files[0]), 1, 1, fit_method='FIT')
    except TypeError:
        strip = strips.new_image('frames', os.path.join(frames_dir, files[0]), 1, 1)
    for f in files[1:]:
        strip.elements.append(f)
    try:
        vs.render.image_settings.media_type = 'VIDEO'
    except (AttributeError, TypeError):
        pass
    vs.render.image_settings.file_format = 'FFMPEG'
    ff = vs.render.ffmpeg
    ff.format = 'MPEG4'
    ff.codec = 'H264'
    ff.constant_rate_factor = crf
    ff.ffmpeg_preset = 'BEST'
    ff.gopsize = fps
    ff.audio_codec = 'NONE'
    vs.render.use_sequencer = True
    vs.render.filepath = out_path
    bpy.ops.render.render(animation=True, scene=vs.name)
    bpy.data.scenes.remove(vs)
    print(f'[lab] encoded {os.path.relpath(out_path, ROOT)} {os.path.getsize(out_path) / 1e6:.2f} MB', flush=True)


if 'holo' in shots:
    holo_camera()
    set_res((1920, 1080))
    render_to(os.path.join(OUT, 'holo.png'))

if 'holoanim' in shots:
    # A four-second loop: the scan lines drift, the image breathes, and now and then a band of it
    # slips sideways. The camera holds still, so the last frame runs into the first.
    holo_camera()
    set_res((1600, 900))
    n, fps = 96, 24
    d = os.path.join(OUT, 'holo')
    os.makedirs(d, exist_ok=True)
    rng = random.Random(3)
    glitches = {rng.randrange(n) for _ in range(5)}
    for f in range(n):
        t = f / n
        HOLO_CTRL['phase'].default_value = 2 * math.pi * 2 * t
        flick = 1.0 + 0.06 * math.sin(2 * math.pi * 7 * t) + 0.04 * math.sin(2 * math.pi * 13 * t)
        glitch = f in glitches or (f - 1) in glitches
        HOLO_CTRL['gain'].default_value = flick * (0.7 if glitch else 1.0)
        HOLO_CTRL['shift'].default_value = (rng.choice((-1, 1)) * 0.012) if glitch else 0.0
        HOLO_CTRL['beam'].default_value = 0.3 * flick
        HOLO_CTRL['light'].data.energy = 2.5 * flick
        render_to(os.path.join(d, f'{f:04d}.png'))
    for tag, res, crf in (('desk', (1600, 900), 'MEDIUM'), ('phone', (1280, 720), 'LOW')):
        encode(d, os.path.join(OUT, f'holo-{tag}.mp4'), res, crf, n, fps)

if 'hub' in shots:
    # The lab as the site's interface: the room at rest, the hologram awake on the bench.
    cam = cams['desk']
    SCENE.camera = cam
    pose(cam, *SHOTS['desk']['rest'])
    set_res((3840, 2160) if ULTRA else SHOTS['desk']['res'])  # same 16:9, so the anchors hold
    render_to(os.path.join(OUT, 'rest-desk.png'))

# ---------------------------------------------------------------------------------------------
# The film's lab shots (blender/film.py strings them together), third person, each keyed frame by
# frame (motion blur; any frame renders on its own), with the room's physics: dust motes in the
# light and dust from every footstep. The lab is dark when they come in; they find the breaker
# panel by the door, reset the main, and the room comes back, tube by tube; at the bench the
# projector wakes under their hand. One shot per run (they key the same figure and lights).
#   lab-enter    5.5 s  into the dark, the chest lamp cutting the dust, to the panel
#   lab-breaker  3.5 s  over the shoulder: the panel door, the main pushed up, the first tubes
#   lab-power    5 s    the room lighting up as they turn and step into it
#   lab-bench    7 s    to the bench; a hand on the projector; the hologram stutters on
FILM_FPS = 24
FLIP = 2.17  # seconds into lab-breaker that the main goes back on
STAND = Vector((-4.93, -5.6, 0.0))  # where they stand at the panel
FACE_PANEL = math.radians(90)  # facing -X, the wall
ENTER = [(0.15, FRONT - 0.8), (-0.3, -6.4), (STAND.x, STAND.y)]
INTO = [(STAND.x, STAND.y), (-3.9, -4.9), (-2.9, -4.2)]
BENCH = [(-2.9, -4.2), (-1.9, -2.4), (-0.75, -0.45)]


def length(route):
    return sum((Vector(b) - Vector(a)).length for a, b in zip(route, route[1:]))


def walked(n, speed, total):
    """Distance along a route at each frame for a speed profile speed(t), scaled to end at total."""
    out, d = [], 0.0
    for f in range(n):
        out.append(d)
        d += speed(f / (n - 1)) / FILM_FPS
    scale = total / out[-1] if out[-1] else 0.0
    return [x * scale for x in out]


def follow(pos, face, back=2.4, right=0.55, up=1.5, ahead=6.0, look=1.1):
    fwd = Vector((-math.sin(face), math.cos(face), 0))
    side = Vector((math.cos(face), math.sin(face), 0))
    return pos - fwd * back + side * right + Vector((0, 0, up)), pos + fwd * ahead + Vector((0, 0, look))


class Aim:
    """Points the camera, its angles kept continuous from frame to frame (no wrap)."""

    def __init__(self, cam):
        self.cam, self.prev = cam, None

    def __call__(self, eye, target, focus):
        self.cam.location = eye
        q = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y')
        self.cam.rotation_euler = q.to_euler('XYZ', self.prev) if self.prev else q.to_euler()
        self.prev = self.cam.rotation_euler.copy()
        self.cam.data.dof.focus_distance = focus


def handheld(t, amp):
    return Vector((math.sin(t * 7.1) + 0.5 * math.sin(t * 13.7), math.sin(t * 5.3 + 1.0),
                   0.6 * math.sin(t * 9.1 + 2.0))) * amp


def blend_angle(a, b, k):
    return a + math.remainder(b - a, math.tau) * k


def film_camera(lens, fstop):
    cam = make_camera('Cam film', lens)
    cam.data.dof.aperture_fstop = fstop
    SCENE.camera = cam
    return cam


def shot_enter():
    fig = C.Crew('crew')
    cam = film_camera(30, 4.0)
    aim = Aim(cam)
    n = 132
    total = length(ENTER)
    pace = lambda t: 1.0 - ease(span01(t, 0.72, 1.0))  # noqa: E731
    dist = walked(n, pace, total)
    path = lambda x: fx.route(ENTER, x, 0.8)  # noqa: E731

    SCENE.view_settings.exposure = -0.1  # exposed for the lamp: the room is dark

    def step(t, f):
        pos, hd = path(dist[f])
        face = blend_angle(hd, FACE_PANEL, ease(span01(t, 0.8, 1.0)))
        C.place(fig, pos, face)
        # Searching the dark: the head (and so the lamp's pool, which the chest follows) roams.
        look = (math.radians(24) * math.sin(t * 6.1) * (1 - span01(t, 0.7, 0.9)), math.radians(-4))
        fig.stride(dist[f], path, 1.4, pace(t), look)
        # Waiting inside: they appear in the doorway, the lamp cutting the dust towards us, come in,
        # pass, and go to the panel; the camera turns with them and ends behind them.
        head = pos + Vector((0, 0, 1.35))
        # Off the lamp's axis, so the beam passes the lens instead of whiting it out.
        eye = Vector((-2.5, -4.85, 1.45)).lerp(Vector((-2.9, -4.55, 1.5)), ease(span01(t, 0.4, 1.0)))
        target = head.lerp(PANEL + Vector((0.1, 0.0, 0.0)), 0.35 * ease(span01(t, 0.7, 1.0)))
        aim(eye + handheld(t * 8, 0.006), target, (head - eye).length)
        power(mains(-1.0))
        BEACON.default_value = 10.0 if (t * 5.5) % 1.5 < 0.12 else 0.6

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'), (BEACON, 'default_value')]
    return n, step, keys, fig


def shot_breaker():
    fig = C.Crew('crew')
    cam = film_camera(32, 2.8)
    aim = Aim(cam)
    n = 84
    SCENE.view_settings.exposure = 0.1  # exposed for the lamp-lit panel
    total = length(ENTER)
    path = lambda x: fx.route(ENTER, x, 0.8)  # noqa: E731
    spark = lamp('Spark', 'POINT', LEVER.location + Vector((0.04, 0, 0.02)), 0.0, (0.75, 0.85, 1.0),
                 shadow_soft_size=0.01)

    def step(t, f):
        s = t * 3.5
        C.place(fig, STAND, FACE_PANEL)
        fig.stride(total, path, 1.4, 0.0, (math.radians(-6), math.radians(-8)), breath=s * 1.6)
        # The door: pulled open by its latch, then let swing; the main: pushed up, and it holds.
        DOOR.rotation_euler = (0, 0, -math.radians(65) * ease(span01(t, 0.12, 0.35))
                               - math.radians(40) * ease(span01(t, 0.35, 0.5)))
        LEVER.rotation_euler = (0, LEVER_OFF + (LEVER_ON - LEVER_OFF) * ease(span01(t, 0.55, 0.62)), 0)
        bpy.context.view_layer.update()
        latch = DOOR.matrix_world @ HANDLE
        tip = LEVER.matrix_world @ Vector((0.0, 0.0, 0.06)) + Vector((0.012, 0.0, -0.01))
        if t < 0.35:
            target = latch
        elif t < 0.5:  # let go of the door where it was at 0.35 (65 degrees open), on to the main
            let_go = DOOR.location + Matrix.Rotation(-math.radians(65), 3, 'Z') @ HANDLE
            target = let_go.lerp(tip, ease(span01(t, 0.35, 0.5)))
        else:
            target = tip
        k = ease(span01(t, 0.0, 0.12)) * (1 - ease(span01(t, 0.75, 0.95)))
        fig.reach_to('R', target, k)
        power(mains(s - FLIP))
        spark.data.energy = 60.0 * math.exp(-((s - FLIP) / 0.04) ** 2)
        BEACON.default_value = 10.0 if (5.5 + s) % 1.5 < 0.12 else 0.6
        # Along the wall from the panel's open side: the panel, their arm reaching in, their visor.
        eye = Vector((-5.12, -4.6, 1.56)).lerp(Vector((-5.14, -4.75, 1.53)), ease(t))
        look = PANEL + Vector((0.12, 0.05, -0.03))
        aim(eye + handheld(t * 6, 0.004), look, (look - eye).length)

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'),
            (DOOR, 'rotation_euler'), (LEVER, 'rotation_euler'), (spark.data, 'energy'),
            (BEACON, 'default_value')]
    return n, step, keys, fig


def shot_power():
    fig = C.Crew('crew')
    cam = film_camera(22, 5.6)
    aim = Aim(cam)
    n = 120
    total = length(INTO)
    pace = lambda t: ease(span01(t, 0.3, 0.45)) * 0.8  # noqa: E731
    dist = walked(n, pace, total)
    path = lambda x: fx.route(INTO, x, 0.5)  # noqa: E731

    def step(t, f):
        s = 3.5 - FLIP + t * 5.0
        pos, hd = path(dist[f])
        face = blend_angle(FACE_PANEL, hd, ease(span01(t, 0.22, 0.5)))
        C.place(fig, pos, face)
        # The tubes strike behind them: they turn to the room, look up at the lights, step in.
        look = (-math.radians(55) * ease(span01(t, 0.05, 0.2)) * (1 - ease(span01(t, 0.25, 0.5))),
                math.radians(16) * math.sin(math.pi * span01(t, 0.05, 0.9)))
        fig.stride(dist[f], path, 1.4, pace(t) / 0.8, look)
        power(mains(s))
        BEACON.default_value = 10.0 if (9.0 + s) % 1.5 < 0.12 else 0.6
        k = ease(t)
        eye = Vector((-4.35, -6.55, 1.8)).lerp(Vector((-3.85, -6.1, 1.7)), k) + handheld(t * 5, 0.005)
        aim(eye, Vector((0.3, 2.5, 1.5)).lerp(Vector((0.0, 2.0, 1.3)), k), 6.0)

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'), (BEACON, 'default_value')]
    return n, step, keys, fig


def shot_bench():
    fig = C.Crew('crew')
    cam = film_camera(30, 4.0)
    aim = Aim(cam)
    n = 168
    total = length(BENCH)
    pace = lambda t: 1.0 if t < 0.45 else 1.0 - ease(span01(t, 0.45, 0.56))  # noqa: E731
    dist = walked(n, pace, total)
    path = lambda x: fx.route(BENCH, x, 0.8)  # noqa: E731
    proj = Vector((HOLO.x, HOLO.y, 0))
    touch = HOLO + Vector((0.0, 0.0, 0.045))
    rng = random.Random(8)
    flick = [rng.random() for _ in range(n)]

    def step(t, f):
        pos, hd = path(dist[f])
        face = blend_angle(hd, fx.heading(proj - pos), ease(span01(t, 0.42, 0.58)))
        C.place(fig, pos, face)
        sweep = math.sin(2 * math.pi * span01(t, 0.56, 0.66)) * math.radians(26)
        up = math.radians(12) * span01(t, 0.76, 0.86)
        fig.stride(dist[f], path, 1.4, pace(t), (sweep, up), breath=t * 20)
        fig.reach_to('R', touch, ease(span01(t, 0.6, 0.7)) * (1 - ease(span01(t, 0.78, 0.9))))
        # The hologram: dark, then a stutter of light as the hand comes off it, then on.
        k = span01(t, 0.71, 0.85)
        on = 0.0 if k == 0 else (1.0 if k == 1 else (1.0 if flick[f] < 0.35 + 0.65 * k else 0.15))
        HOLO_CTRL['gain'].default_value = on
        HOLO_CTRL['phase'].default_value = 2 * math.pi * 2 * t
        HOLO_CTRL['beam'].default_value = 0.3 * on
        HOLO_CTRL['light'].data.energy = 2.5 * on
        lv = mains(99.0)
        lv['standby'] = 0.25 + 0.75 * on
        power(lv)
        BEACON.default_value = 10.0 if (14.0 + t * 7.0) % 1.5 < 0.12 else 0.6
        follow_eye, follow_at = follow(pos, face)
        end_eye, end_at = Vector((0.55, -1.75, 1.45)), Vector((HOLO.x, HOLO.y, 1.1))
        m = ease(span01(t, 0.5, 0.9))
        eye = follow_eye.lerp(end_eye, m) + handheld(t * 7, 0.004 * (1 - m))
        aim(eye, follow_at.lerp(end_at, m),
            ((end_at if m > 0.5 else pos + Vector((0, 0, 1.3))) - eye).length)

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'), (BEACON, 'default_value')]
    keys += [(HOLO_CTRL[k], 'default_value') for k in ('gain', 'phase', 'beam')]
    keys += [(HOLO_CTRL['light'].data, 'energy')]
    return n, step, keys, fig


FILM_SHOTS = {'lab-enter': shot_enter, 'lab-breaker': shot_breaker, 'lab-power': shot_power,
              'lab-bench': shot_bench}
film_shots = [s for s in FILM_SHOTS if s in shots]
if len(film_shots) > 1:
    sys.exit('[lab] one film shot per run: ' + ', '.join(film_shots))
for name in film_shots:
    n, step, keys, fig = FILM_SHOTS[name]()
    set_res((3840, 2160) if ULTRA else (1920, 1080))
    keys = keys + fig.keys() + [(owner, attr) for owner, attr, _, _ in POWER]
    steps = fx.Steps(fig, 0.0, 0.7)
    for f in range(n):
        step(f / (n - 1), f)
        for owner, path in keys:
            owner.keyframe_insert(path, frame=f + 1)
        steps.sample((f + 1) / FILM_FPS)
    mean, worst = steps.slide()
    print(f'[lab] {name}: planted feet skate {mean:.3f} m/s on average, {worst:.3f} at worst', flush=True)
    ev = steps.events()
    if ev:
        fx.puffs('footdust', ev, fx.dust_mat('footdust', (0.5, 0.5, 0.48), 1.2))
    # Dust hanging in the room's air: it shows where light crosses it.
    fx.motes('motes', (-W + 0.3, FRONT + 0.3, 0.15), (W - 0.3, BACK - 0.7, H - 0.3), 70000 if ULTRA else 15000)
    SCENE.frame_start, SCENE.frame_end = 1, n
    SCENE.render.fps = FILM_FPS
    SCENE.render.use_motion_blur = True
    SCENE.render.motion_blur_shutter = 0.5 if ULTRA else 0.35
    if ULTRA:
        SCENE.render.image_settings.file_format = 'JPEG'
        SCENE.render.image_settings.quality = 95
    if OPTS['stage'] == 'build':
        os.makedirs(os.path.join(OUT, 'work'), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'work', f'{name}.blend'))
        print(f'[lab] {name}: built blender/out/work/{name}.blend', flush=True)
        continue
    d = os.path.join(OUT, 'preview' if OPTS['preview'] else '', name)
    os.makedirs(d, exist_ok=True)
    ext = 'jpg' if ULTRA else 'png'
    k, every = (int(v) for v in OPTS['slice'].split('/'))
    for f in range(n):
        if (OPTS['frame'] >= 0 and f != OPTS['frame']) or f % every != k:
            continue
        SCENE.frame_set(f + 1)
        render_to(os.path.join(d, f'{f:04d}.{ext}'))

print('[lab] done')
