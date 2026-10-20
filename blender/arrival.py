"""The arrival (the experience's opening after the intro): a crew coming home finds one signal still
transmitting from a dead Earth, comes down through the cloud deck over an overgrown city the machines
took, lands, and walks to the building the signal comes from: the lab.

Run with Blender 5.2 from the repository root, after `python blender/fetch_assets.py`:
  blender -b --factory-startup -P blender/arrival.py -- --shot orbit --samples 64 --scale 0.5
Shots: orbit, descent, ramp, street, approach, door. --inspect prints each asset's size instead of
rendering. PNGs go to blender/out/arrival/.

Final film (--quality ultra): 4K, up to 1024 samples, real surface displacement, finer volumes,
4K textures and 2K models, and the physics (fx.py). Rendered in two stages so many GPUs can share a
shot: --stage build builds and keys the shot, bakes its simulation, and saves it to
blender/out/work/<shot>.blend; --stage render opens that file and renders the frames of --slice k/N
(every Nth frame from the kth) as JPEGs, skipping frames already on disk.

Real material: NASA's Blue Marble Earth and cloud layer, Poly Haven's photo-scanned plants, props and
surfaces (CC0), and the beacon's position, which is Greater Noida. Everything else (the ship, the
machines, the city's layout) is set dressing, and the page says the sequence is rendered.
"""

import bpy
import bmesh
import math
import os
import random
import sys
import time
from mathutils import Euler, Matrix, Vector

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
ASSETS = os.path.join(ROOT, 'blender', 'assets')
OUT = os.path.join(ROOT, 'blender', 'out', 'arrival')


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    opts = {'shot': 'orbit', 'samples': 64, 'scale': 0.5, 'inspect': False, 'tag': '', 'anim': False,
            't': 1.0, 'start': 0, 'res': '1920x1080', 'encode_only': False, 'quality': 'final',
            'stage': 'all', 'slice': '0/1', 'frames': '', 'fluid_res': 0, 'preview': False,
            'threshold': 0.0, 'volstep': 0.0, 'max': False, 'nodust': False, 'exr': False, 'outdir': '', 'fast': False}
    i = 0
    while i < len(argv):
        key = argv[i].lstrip('-')
        if key in ('inspect', 'anim', 'encode_only', 'preview', 'max', 'nodust', 'exr', 'fast'):
            opts[key] = True
            i += 1
        elif key in opts and i + 1 < len(argv):
            opts[key] = type(opts[key])(argv[i + 1])
            i += 2
        else:
            i += 1
    return opts


OPTS = parse_args()
RES = (1920, 1080)
if OPTS['anim']:
    RES = tuple(int(v) for v in OPTS['res'].split('x'))
    OPTS['scale'] = 1.0
ULTRA = OPTS['quality'] == 'ultra'
SEGS = 2 if ULTRA else 1  # facets on round parts
C.DETAIL = 1 if ULTRA else 0  # the crew's extra subdivision level
C.REAL = '--toy' not in sys.argv  # the real crew member (blender/human.py); --toy: the built figure
WORK = os.path.join(ROOT, 'blender', 'out', 'work')


# ---------------------------------------------------------------------------------------------
# Scene, render settings, geometry and material helpers.


def use_gpu(scene):
    """The fastest GPU backend there is (preferences are not saved in .blend files)."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    device = 'CPU'
    # OptiX first where it has RT cores to run on (the laptop); ARCHIVE_GPU=CUDA puts CUDA first, which
    # on a GPU without them (the H200s) renders the same picture several times faster.
    order = ('CUDA', 'OPTIX') if os.environ.get('ARCHIVE_GPU') == 'CUDA' else ('OPTIX', 'CUDA')
    for kind in order:
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            found = [d for d in prefs.devices if d.type == kind]
            if found:
                for d in prefs.devices:
                    d.use = d.type == kind
                device = 'GPU'
                break
        except Exception:  # noqa: BLE001 - fall through to the next backend
            continue
    scene.cycles.device = device
    return device


# The final film's settings. Measured on a 4K street frame: half the samples of the first try, a
# coarser volume step, two-pixel dicing and eight bounces render in a third of the time and cannot
# be told apart at 1:1 (blender/out/work/prof-*.jpg).
ULTRA_CYCLES = (('adaptive_threshold', 0.01), ('adaptive_min_samples', 64), ('max_bounces', 8),
                ('diffuse_bounces', 4), ('glossy_bounces', 4), ('transmission_bounces', 8),
                ('volume_bounces', 2), ('transparent_max_bounces', 32), ('sample_clamp_indirect', 12.0),
                ('volume_step_rate', 1.0), ('volume_max_steps', 1024), ('denoising_prefilter', 'ACCURATE'),
                ('denoising_quality', 'HIGH'), ('use_light_tree', True), ('dicing_rate', 1.0),
                ('offscreen_dicing_scale', 8.0), ('max_subdivisions', 10))


# The uncompromised settings (--max at render time): what the measured ones above are cut from.
MAX_CYCLES = (('adaptive_threshold', 0.006), ('max_bounces', 16), ('diffuse_bounces', 6),
              ('glossy_bounces', 6), ('transmission_bounces', 12), ('volume_bounces', 3),
              ('transparent_max_bounces', 64), ('volume_step_rate', 0.5), ('volume_max_steps', 2048))


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    device = use_gpu(scene)
    c = scene.cycles
    base = (('samples', OPTS['samples']), ('use_adaptive_sampling', True),
            ('adaptive_threshold', 0.02), ('use_denoising', True),
            ('denoiser', 'OPENIMAGEDENOISE'), ('denoising_use_gpu', True),
            ('max_bounces', 6), ('diffuse_bounces', 3), ('glossy_bounces', 2),
            ('transmission_bounces', 4), ('volume_bounces', 1),
            ('transparent_max_bounces', 16), ('caustics_reflective', False),
            ('caustics_refractive', False), ('sample_clamp_indirect', 6.0),
            ('volume_step_rate', 2.0), ('volume_max_steps', 512), ('seed', 0))
    for attr, val in base + (ULTRA_CYCLES if ULTRA else ()):
        try:
            setattr(c, attr, val)
        except (AttributeError, TypeError):
            pass
    scene.render.use_persistent_data = True
    if ULTRA and OPTS['anim']:
        # 4K frames as near-lossless JPEGs: a twentieth of the PNGs' size, for a film that is
        # compressed again anyway.
        scene.render.image_settings.file_format = 'JPEG'
        scene.render.image_settings.quality = 95
    else:
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.resolution_x = int(RES[0] * OPTS['scale'])
    scene.render.resolution_y = int(RES[1] * OPTS['scale'])
    scene.render.resolution_percentage = 100
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            vs.look = look
            break
        except TypeError:
            continue
    world = bpy.data.worlds.new('World')
    scene.world = world
    try:
        world.use_nodes = True
    except Exception:  # noqa: BLE001
        pass
    world.node_tree.nodes.clear()
    print('[arrival] device', device, flush=True)
    return scene


SCENE = None


def link(ob):
    SCENE.collection.objects.link(ob)
    return ob


def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
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


def cylinder(name, center, r, depth, mat=None, rot=(0, 0, 0), segs=24, r2=None, caps=True,
             parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs * SEGS,
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


def sphere(name, center, r, mat=None, segs=64, rings=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs * SEGS, v_segments=rings * SEGS, radius=r)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    ob = link(bpy.data.objects.new(name, me))
    ob.location = center
    return ob


def true_sphere(name, r, mat):
    """A perfect sphere: one point of a point cloud, which Cycles renders analytically (no facets,
    so a planet's terminator stays clean at any distance)."""
    ob = link(bpy.data.objects.new(name, bpy.data.meshes.new(name)))
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    pts = ng.nodes.new('GeometryNodePoints')
    pts.inputs['Count'].default_value = 1
    pts.inputs['Radius'].default_value = r
    sm = ng.nodes.new('GeometryNodeSetMaterial')
    sm.inputs['Material'].default_value = mat
    go = ng.nodes.new('NodeGroupOutput')
    ng.links.new(pts.outputs[0], sm.inputs['Geometry'])
    ng.links.new(sm.outputs[0], go.inputs[0])
    ob.modifiers.new(name, 'NODES').node_group = ng
    return ob


def segment(name, a, b, r, mat=None, segs=16, r2=None):
    """A cylinder from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = cylinder(name, (a + b) / 2, r, d.length, mat, segs=segs, r2=r2)
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return ob


def empty(name, loc=(0, 0, 0)):
    ob = link(bpy.data.objects.new(name, None))
    ob.location = loc
    return ob


def look_at(ob, target):
    d = Vector(target) - Vector(ob.location)
    # Compatible with the current rotation: keyed frame to frame, an angle that wrapped from +180°
    # to -180° would spin the camera a full turn between two frames (and smear the motion blur).
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler('XYZ', ob.rotation_euler)


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:  # noqa: BLE001
        pass
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, nt.nodes.new('ShaderNodeOutputMaterial')


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[k])
        else:
            n.inputs[k].default_value = v
    return n


def math_op(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def map_range(nt, v, lo, hi, a=0.0, b=1.0):
    n = nt.nodes.new('ShaderNodeMapRange')
    n.inputs['From Min'].default_value = lo
    n.inputs['From Max'].default_value = hi
    n.inputs['To Min'].default_value = a
    n.inputs['To Max'].default_value = b
    nt.links.new(v, n.inputs['Value'])
    return n.outputs['Result']


def noise(nt, vec, scale, detail=4.0, rough=0.55):
    n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=detail, Roughness=rough)
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def mix_rgb(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    for sock, val in ((0, fac), (6, a), (7, b)):
        if isinstance(val, bpy.types.NodeSocket):
            nt.links.new(val, m.inputs[sock])
        elif isinstance(val, tuple):
            m.inputs[sock].default_value = (*val, 1) if len(val) == 3 else val
        else:
            m.inputs[sock].default_value = val
    return m.outputs[2]


def mix_float(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'FLOAT'
    for sock, val in ((0, fac), (2, a), (3, b)):
        if isinstance(val, bpy.types.NodeSocket):
            nt.links.new(val, m.inputs[sock])
        else:
            m.inputs[sock].default_value = val
    return m.outputs[0]


def load_image(path, data=False):
    img = bpy.data.images.load(path, check_existing=True)
    if data:
        img.colorspace_settings.name = 'Non-Color'
    return img


def plain(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m, nt, out = new_mat(name)
    b = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=rough, Metallic=metal)
    b.inputs['Base Color'].default_value = (*color, 1)
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def emit_mat(name, color, strength):
    m, nt, out = new_mat(name)
    e = node(nt, 'ShaderNodeEmission', Strength=strength)
    e.inputs['Color'].default_value = (*color, 1)
    nt.links.new(e.outputs['Emission'], out.inputs['Surface'])
    return m


def tex_set(tid):
    """A scanned surface's maps: 4K for the final film when they have been fetched, else 2K."""
    d = os.path.join(ASSETS, 'textures', tid)
    out = {}
    for k in ('diff', 'nor_gl', 'rough', 'disp'):
        hi = os.path.join(d, f'{tid}_{k}_4k.jpg')
        out[k] = hi if ULTRA and os.path.exists(hi) else os.path.join(d, f'{tid}_{k}_2k.jpg')
    return out


class Layer:
    """One scanned surface (Poly Haven, 2k): colour, roughness and normal sockets."""

    def __init__(self, nt, tid, vec, tint=(1, 1, 1), rough_add=0.0):
        t = tex_set(tid)

        def img(key, data):
            n = nt.nodes.new('ShaderNodeTexImage')
            n.image = load_image(t[key], data)
            n.projection = 'BOX'
            n.projection_blend = 0.25
            nt.links.new(vec, n.inputs['Vector'])
            return n

        self.col = img('diff', False).outputs['Color']
        if tint != (1, 1, 1):
            self.col = mix_rgb_mul(nt, self.col, tint)
        r = img('rough', True).outputs['Color']
        self.rough = math_op(nt, 'ADD', r, rough_add, clamp=True) if rough_add else r
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(img('nor_gl', True).outputs['Color'], nm.inputs['Color'])
        self.normal = nm.outputs['Normal']
        self.height = img('disp', True).outputs['Color']


def mix_rgb_mul(nt, a, tint):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    m.inputs[0].default_value = 1.0
    nt.links.new(a, m.inputs[6])
    m.inputs[7].default_value = (*tint, 1)
    return m.outputs[2]


def mix_vec(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'VECTOR'
    nt.links.new(fac, m.inputs[0])
    nt.links.new(a, m.inputs[4])
    nt.links.new(b, m.inputs[5])
    return m.outputs[1]


# Relief of each scanned surface, in metres from its lowest to its highest point: in the final film
# the height maps really move the surface (adaptive subdivision, dicing to about a pixel).
DISP = {'road_damaged': 0.04, 'brown_mud_leaves_01': 0.05, 'forest_leaves_02': 0.05,
        'dirty_concrete': 0.012, 'concrete_wall_008': 0.01, 'concrete_moss': 0.02,
        'worn_mossy_plasterwall': 0.015, 'painted_metal_shutter': 0.006, 'rusty_metal_02': 0.004,
        'metal_plate': 0.003, 'mossy_brick': 0.02}
DISPLACED = set()  # materials with real displacement: their meshes get adaptive subdivision


def surface(name, base, size=2.0, over=None, over_size=None, over_amount=0.0, over_lo=0.5,
            up_bias=0.0, low_bias=0.0, wet=0.0, tint=(1, 1, 1), over_tint=(1, 1, 1),
            normal_strength=1.0, rough_add=0.0, disp=True):
    """A scanned base surface, optionally grown over by a second one (moss, leaves): where noise says,
    more on upward faces (up_bias) and near the ground (low_bias). wet: puddles on flat ground."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    obj = tc.outputs['Object']
    vec = node(nt, 'ShaderNodeMapping').outputs['Vector']
    mp = vec.node
    mp.inputs['Scale'].default_value = (1 / size,) * 3
    nt.links.new(obj, mp.inputs['Vector'])
    a = Layer(nt, base, vec, tint, rough_add)
    col, rough, nrm = a.col, a.rough, a.normal
    height, relief = a.height, DISP.get(base, 0.01)
    if over:
        mp2 = node(nt, 'ShaderNodeMapping')
        mp2.inputs['Scale'].default_value = (1 / (over_size or size),) * 3
        nt.links.new(obj, mp2.inputs['Vector'])
        b = Layer(nt, over, mp2.outputs['Vector'], over_tint)
        wpos = geo.outputs['Position']
        n = noise(nt, wpos, 0.35, 6, 0.62)
        f = map_range(nt, n, over_lo - 0.08, over_lo + 0.08)
        # Grows from the cracks: the base's own height map pulls growth into the low parts.
        f = math_op(nt, 'MULTIPLY', f, map_range(nt, a.height, 0.75, 0.2, 0.4, 1.4), clamp=True)
        if up_bias:
            sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Normal'])
            f = math_op(nt, 'ADD', f, math_op(nt, 'MULTIPLY', map_range(nt, sep.outputs['Z'], 0.3, 0.95), up_bias), clamp=True)
        if low_bias:
            sp = node(nt, 'ShaderNodeSeparateXYZ', Vector=wpos)
            f = math_op(nt, 'ADD', f, math_op(nt, 'MULTIPLY', map_range(nt, sp.outputs['Z'], 2.5, 0.0), low_bias), clamp=True)
        f = math_op(nt, 'MULTIPLY', f, over_amount, clamp=True)
        col = mix_rgb(nt, f, col, b.col)
        rough = mix_float(nt, f, rough, b.rough)
        nrm = mix_vec(nt, f, nrm, b.normal)
        height = mix_float(nt, f, height, b.height)
        relief = max(relief, DISP.get(over, 0.01))
    if wet:
        sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Normal'])
        flat = map_range(nt, sep.outputs['Z'], 0.9, 0.99)
        pn = noise(nt, geo.outputs['Position'], 0.18, 4, 0.55)
        puddle = map_range(nt, pn, 0.6, 0.63)
        puddle = math_op(nt, 'MULTIPLY', puddle, map_range(nt, a.height, 0.55, 0.3), clamp=True)
        puddle = math_op(nt, 'MULTIPLY', math_op(nt, 'MULTIPLY', puddle, flat), wet, clamp=True)
        col = mix_rgb(nt, puddle, col, mix_rgb_mul(nt, col, (0.25, 0.25, 0.25)))
        rough = mix_float(nt, puddle, rough, 0.02)
        nrm = mix_vec(nt, puddle, nrm, geo.outputs['Normal'])
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(rough, b.inputs['Roughness'])
    nt.links.new(nrm, b.inputs['Normal'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    if ULTRA and disp:
        dn = node(nt, 'ShaderNodeDisplacement', Midlevel=0.5, Scale=relief)
        nt.links.new(height, dn.inputs['Height'])
        nt.links.new(dn.outputs['Displacement'], out.inputs['Displacement'])
        m.displacement_method = 'BOTH'
        DISPLACED.add(m)
    return m


def adaptive():
    """Adaptive subdivision for every mesh wearing a displaced surface: Cycles dices each to two
    pixels on screen (coarser off screen), so relief costs only what the camera sees."""
    for ob in SCENE.objects:
        if ob.type != 'MESH' or not any(s.material in DISPLACED for s in ob.material_slots):
            continue
        if any(md.type == 'SUBSURF' for md in ob.modifiers):
            continue
        md = ob.modifiers.new('relief', 'SUBSURF')
        md.subdivision_type = 'SIMPLE'
        md.levels = 0
        md.use_adaptive_subdivision = True
        md.adaptive_space = 'PIXEL'
        md.adaptive_pixel_size = 2.0


def haze_box(name, center, size, density, color=(0.8, 0.85, 0.82), aniso=0.6, falloff=None):
    """Atmosphere: a volume, optionally thinning with height (falloff = metres per e-fold)."""
    m, nt, out = new_mat(name)
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*color, 1)
    v.inputs['Anisotropy'].default_value = aniso
    dv = nt.nodes.new('ShaderNodeValue')
    dv.name = 'density'
    dv.outputs[0].default_value = density
    if falloff:
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=geo.outputs['Position'])
        e = math_op(nt, 'EXPONENT', math_op(nt, 'DIVIDE', sep.outputs['Z'], -falloff))
        nt.links.new(math_op(nt, 'MULTIPLY', e, dv.outputs[0]), v.inputs['Density'])
    else:
        nt.links.new(dv.outputs[0], v.inputs['Density'])
    nt.links.new(v.outputs['Volume'], out.inputs['Volume'])
    ob = box(name, center, size, m)
    ob.visible_shadow = True
    return ob


def world_hdri(hid, strength=1.0, rotate=0.0, tint=(1, 1, 1)):
    nt = SCENE.world.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = node(nt, 'ShaderNodeMapping', Vector=tc.outputs['Generated'])
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rotate))
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = load_image(os.path.join(ASSETS, 'hdri', f'{hid}_4k.hdr'))
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    col = env.outputs['Color']
    if tint != (1, 1, 1):
        col = mix_rgb_mul(nt, col, tint)
    bg = node(nt, 'ShaderNodeBackground', Strength=strength)
    nt.links.new(col, bg.inputs['Color'])
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def sun(direction, strength, color=(1.0, 0.9, 0.78), angle=1.5):
    data = bpy.data.lights.new('sun', 'SUN')
    data.energy = strength
    data.color = color
    data.angle = math.radians(angle)
    ob = link(bpy.data.objects.new('sun', data))
    ob.rotation_euler = Vector(direction).to_track_quat('-Z', 'Y').to_euler()
    return ob


def point(name, loc, energy, color, radius=0.05):
    data = bpy.data.lights.new(name, 'POINT')
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    ob = link(bpy.data.objects.new(name, data))
    ob.location = loc
    return ob


def camera(loc, target, lens=32, fstop=5.6, focus=None, roll=0.0):
    data = bpy.data.cameras.new('cam')
    data.lens = lens
    data.sensor_width = 36
    data.sensor_fit = 'HORIZONTAL'
    data.clip_start = 0.05
    data.clip_end = 20000
    data.dof.use_dof = fstop > 0
    data.dof.aperture_fstop = max(fstop, 0.5)
    ob = link(bpy.data.objects.new('cam', data))
    ob.location = loc
    look_at(ob, target)
    if roll:
        ob.rotation_euler.rotate(Euler((0, 0, 0)))
        ob.matrix_world = ob.matrix_world @ Matrix.Rotation(math.radians(roll), 4, 'Z')
    data.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    SCENE.camera = ob
    return ob


# ---------------------------------------------------------------------------------------------
# Scanned assets: each model is imported once into its own collection, kept out of the scene, and
# placed as instances (cheap: one mesh in memory however many times it appears).

_ASSETS = {}


def asset(mid):
    if mid in _ASSETS:
        return _ASSETS[mid]
    path = os.path.join(ASSETS, 'models', mid, f'{mid}.gltf')
    hi = os.path.join(ASSETS, 'models', mid, '2k', f'{mid}.gltf')
    if ULTRA and os.path.exists(hi):
        path = hi  # the same model with 2K textures
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new('asset:' + mid)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    # Bounds in the asset's own space, for placing it.
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o in new:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    _ASSETS[mid] = (col, lo, hi)
    return _ASSETS[mid]


def place(mid, loc, rot_z=0.0, scale=1.0, tilt=(0.0, 0.0)):
    col, _, _ = asset(mid)
    ob = link(bpy.data.objects.new(mid, None))
    ob.instance_type = 'COLLECTION'
    ob.instance_collection = col
    ob.location = loc
    ob.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(rot_z))
    ob.scale = (scale,) * 3
    return ob


def scatter(mid, pts):
    """Many instances of one asset through geometry nodes. pts: (location, (rx, ry, rz) radians, scale)."""
    col, _, _ = asset(mid)
    name = 'scatter:' + mid
    me = bpy.data.meshes.new(name)
    me.from_pydata([p[0] for p in pts], [], [])
    rot = me.attributes.new('rot', 'FLOAT_VECTOR', 'POINT')
    scl = me.attributes.new('scl', 'FLOAT_VECTOR', 'POINT')
    rot.data.foreach_set('vector', [c for p in pts for c in p[1]])
    scl.data.foreach_set('vector', [c for p in pts for c in ((p[2],) * 3)])
    ob = link(bpy.data.objects.new(name, me))
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, L = ng.nodes, ng.links
    gi, go = n.new('NodeGroupInput'), n.new('NodeGroupOutput')
    m2p = n.new('GeometryNodeMeshToPoints')
    iop = n.new('GeometryNodeInstanceOnPoints')
    ci = n.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = col
    ci.transform_space = 'ORIGINAL'
    ra = n.new('GeometryNodeInputNamedAttribute')
    ra.data_type = 'FLOAT_VECTOR'
    ra.inputs['Name'].default_value = 'rot'
    sa = n.new('GeometryNodeInputNamedAttribute')
    sa.data_type = 'FLOAT_VECTOR'
    sa.inputs['Name'].default_value = 'scl'
    e2r = n.new('FunctionNodeEulerToRotation')
    L.new(gi.outputs[0], m2p.inputs['Mesh'])
    L.new(m2p.outputs['Points'], iop.inputs['Points'])
    L.new(ci.outputs['Instances'], iop.inputs['Instance'])
    L.new(ra.outputs['Attribute'], e2r.inputs['Euler'])
    L.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    L.new(sa.outputs['Attribute'], iop.inputs['Scale'])
    L.new(iop.outputs['Instances'], go.inputs[0])
    ob.modifiers.new(name, 'NODES').node_group = ng
    return ob


def render(shot):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{shot}{OPTS["tag"]}.png')
    SCENE.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'[arrival] {os.path.relpath(path, ROOT)} {time.time() - t:.1f}s', flush=True)


# ---------------------------------------------------------------------------------------------
# Shot 1, the signal: Earth from 1,500 km, the Indian subcontinent at dusk. No city lights anywhere:
# the night side is black, except one red point at Greater Noida. Units are kilometres; the camera
# sits at the origin and the planet is moved to it, so nothing near the camera loses precision.

R_EARTH = 6371.0
AIR_H, AIR_D, AIR_TOP = 22.0, 0.007, 220.0
NOIDA = (28.47, 77.50)


def geo(lat, lon, r=R_EARTH):
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))


def latlon_uv(nt, pos):
    """Equirectangular UV from a position on the sphere (object space)."""
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=pos)
    lon = math_op(nt, 'ARCTAN2', sep.outputs['Y'], sep.outputs['X'])
    ln = node(nt, 'ShaderNodeVectorMath', Vector=pos)
    ln.operation = 'LENGTH'
    lat = math_op(nt, 'ARCSINE', math_op(nt, 'DIVIDE', sep.outputs['Z'], ln.outputs['Value']))
    u = math_op(nt, 'ADD', math_op(nt, 'DIVIDE', lon, 2 * math.pi), 0.5)
    v = math_op(nt, 'ADD', math_op(nt, 'DIVIDE', lat, math.pi), 0.5)
    comb = node(nt, 'ShaderNodeCombineXYZ', X=u, Y=v)
    return comb.outputs['Vector']


def earth_mats():
    # The ground: Blue Marble colour; water is glossy (the sun's glint), land is not.
    m, nt, out = new_mat('earth')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    uv = latlon_uv(nt, tc.outputs['Object'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = load_image(os.path.join(ASSETS, 'earth', 'blue_marble_21600.jpg'))
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    nt.links.new(uv, tex.inputs['Vector'])
    sep = node(nt, 'ShaderNodeSeparateColor', Color=tex.outputs['Color'])
    water = map_range(nt, math_op(nt, 'SUBTRACT', sep.outputs['Blue'], sep.outputs['Red']), 0.02, 0.08)
    b = node(nt, 'ShaderNodeBsdfPrincipled')
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(mix_float(nt, water, 0.85, 0.32), b.inputs['Roughness'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    earth = m

    # Clouds: white where the cloud map says, see-through elsewhere; they cast their shadows.
    m, nt, out = new_mat('clouds')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    uv = latlon_uv(nt, tc.outputs['Object'])
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = load_image(os.path.join(ASSETS, 'earth', 'clouds_8192.tif'), data=True)
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    nt.links.new(uv, tex.inputs['Vector'])
    dens = map_range(nt, tex.outputs['Color'], 0.08, 0.95)
    dens = math_op(nt, 'POWER', dens, 1.25)
    b = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=1.0)
    b.inputs['Base Color'].default_value = (0.9, 0.9, 0.92, 1)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(dens, mx.inputs[0])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1])
    nt.links.new(b.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    clouds = m

    # Air: scattering that falls off with height (scale height exaggerated so the thin shell
    # samples cleanly), stronger for blue, so the
    # limb is blue and the light through it at the terminator turns orange.
    m, nt, out = new_mat('air')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ln = node(nt, 'ShaderNodeVectorMath', Vector=tc.outputs['Object'])
    ln.operation = 'LENGTH'
    h = math_op(nt, 'SUBTRACT', ln.outputs['Value'], R_EARTH)
    d = math_op(nt, 'MULTIPLY', math_op(nt, 'EXPONENT', math_op(nt, 'DIVIDE', h, -AIR_H)), AIR_D)
    vs = node(nt, 'ShaderNodeVolumeScatter', Density=d, Anisotropy=0.0)
    vs.inputs['Color'].default_value = (0.2, 0.48, 1.0, 1)
    nt.links.new(vs.outputs['Volume'], out.inputs['Volume'])
    air = m
    return earth, clouds, air


def shot_orbit():
    """Six seconds: drifting down toward the dark; the beacon blinks."""
    global SCENE
    SCENE = reset_scene()
    SCENE.unit_settings.scale_length = 1000.0  # 1 unit = 1 km (for depth of field)
    SCENE.view_settings.exposure = 0.3
    for attr, val in (('volume_step_rate', 1.0), ('volume_max_steps', 1024), ('max_bounces', 4)):
        setattr(SCENE.cycles, attr, val)
    earth_m, clouds_m, air_m = earth_mats()
    planet = empty('planet', (0, 0, 0))
    for name, r, mat in (('earth', R_EARTH, earth_m), ('clouds', R_EARTH + 5, clouds_m)):
        true_sphere(name, r, mat).parent = planet
    sphere('air', (0, 0, 0), R_EARTH + AIR_TOP, air_m, 512, 256).parent = planet
    # Sun: 8° below the horizon at Greater Noida (night there), day to the west.
    sub = geo(-9.0, NOIDA[1] - 98, 1.0)
    sun(-sub, 4.2, (1.0, 0.97, 0.93), angle=0.53)
    # Moonlight: just enough to find the land in the dark.
    sun(-geo(20.0, NOIDA[1] + 70, 1.0), 0.008, (0.55, 0.65, 0.9), angle=0.5)
    # The signal: a red point on the ground, blinking.
    bmat = emit_mat('beacon', (1.0, 0.07, 0.05), 4000.0)
    beacon = sphere('beacon', geo(*NOIDA, R_EARTH + 0.3), 0.9, bmat, 16, 8)
    beacon.parent = planet
    glow = bmat.node_tree.nodes['Emission'].inputs['Strength']

    # Stars, faint (they would be, against a lit limb).
    nt = SCENE.world.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = node(nt, 'ShaderNodeTexVoronoi', Scale=900.0, Vector=tc.outputs['Generated'])
    star = map_range(nt, vor.outputs['Distance'], 0.06, 0.0, 0.0, 1.0)
    star = math_op(nt, 'POWER', star, 8.0)
    wn = noise(nt, tc.outputs['Generated'], 40.0, 2, 0.5)
    star = math_op(nt, 'MULTIPLY', star, map_range(nt, wn, 0.55, 0.75, 0.0, 0.6))
    bg = node(nt, 'ShaderNodeBackground', Strength=1.0)
    nt.links.new(star, bg.inputs['Color'])
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    # Camera: over the Bay of Bengal, looking west across the dark plains to the last of the
    # daylight on the horizon; Greater Noida lies between, in the dark. The camera stays at the
    # origin (precision) and the planet moves.
    cam = camera((0, 0, 0), (0, 1, 0), lens=30, fstop=0)
    cam.data.clip_start = 0.0005
    cam.data.clip_end = 30000

    def step(t):
        e = ease(t)
        cam_geo = geo(24.0 + 1.2 * e, 89.5 - 2.3 * e, R_EARTH + 1500 - 180 * e)
        planet.location = -cam_geo
        look = geo(29.5 - 0.5 * e, 69.0 + 3.5 * e, R_EARTH) - cam_geo
        up = cam_geo.normalized()
        fwd = look.normalized()
        right = fwd.cross(up).normalized()
        up2 = right.cross(fwd)
        prev = cam.rotation_euler.copy()
        cam.rotation_euler = Matrix((right, up2, -fwd)).transposed().to_euler('XYZ', prev)
        phase = (t * 5) % 1.0  # five blinks in six seconds
        glow.default_value = 4000.0 * (0.12 + 0.88 * math.exp(-((phase - 0.15) / 0.07) ** 2))

    return 144, step, [(planet, 'location'), (cam, 'location'), (cam, 'rotation_euler'),
                       (glow, 'default_value')]


def ease(t):
    t = min(1.0, max(0.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - pow(1 - t, 3)


def span(t, a, b):
    return min(1.0, max(0.0, (t - a) / (b - a)))


def shake(t, amp, seed=0.0):
    """Hand-held: a few slow sines, never a jitter."""
    return Vector((amp * (math.sin(7.1 * t + seed) + 0.5 * math.sin(17.3 * t + 2 * seed)),
                   0.0,
                   amp * (math.sin(5.3 * t + 1.3 + seed) + 0.5 * math.sin(13.1 * t + seed))))


# ---------------------------------------------------------------------------------------------
# Variants: Poly Haven's plant sets hold several plants side by side in one file. Each becomes its
# own instance source, its origin moved to the plant's base.

_VARIANTS = {}


def variants(mid):
    if mid in _VARIANTS:
        return _VARIANTS[mid]
    col, _, _ = asset(mid)
    out = []
    for o in list(col.objects):
        if o.type != 'MESH':
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector(map(min, *ws))
        hi = Vector(map(max, *ws))
        sub = bpy.data.collections.new(f'{mid}:{o.name}')
        sub.objects.link(o)
        sub.instance_offset = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
        out.append((sub, hi - lo))
    _VARIANTS[mid] = out
    return out


PLANT_WIND = (math.radians(3.0), math.radians(3.0))  # lean in a gust, own flutter
LEAF_WIND = (math.radians(2.0), math.radians(12.0))


def scatter_variants(mid, pts, rng, wind=PLANT_WIND):
    """pts: (location, rotation z, scale); each point gets a random variant of the set."""
    groups = {}
    for loc, rz, sc in pts:
        groups.setdefault(rng.randrange(len(variants(mid))), []).append((loc, rz, sc))
    for i, group in groups.items():
        sub, _ = variants(mid)[i]
        scatter_col(f'{mid}.{i}', sub, [(l, (0, 0, rz), sc) for l, rz, sc in group], wind)


def scatter_col(name, col, pts, wind=None):
    """Instances of a collection on points. wind: (gust lean, flutter) in radians, for plants and
    leaves (fx.wind_euler: gusts, flutter and the lander's downwash, evaluated every frame)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([p[0] for p in pts], [], [])
    rot = me.attributes.new('rot', 'FLOAT_VECTOR', 'POINT')
    scl = me.attributes.new('scl', 'FLOAT_VECTOR', 'POINT')
    rot.data.foreach_set('vector', [c for p in pts for c in p[1]])
    scl.data.foreach_set('vector', [c for p in pts for c in ((p[2],) * 3)])
    ob = link(bpy.data.objects.new('scatter:' + name, me))
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, L = ng.nodes, ng.links
    gi, go = n.new('NodeGroupInput'), n.new('NodeGroupOutput')
    m2p = n.new('GeometryNodeMeshToPoints')
    iop = n.new('GeometryNodeInstanceOnPoints')
    ci = n.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = col
    ci.transform_space = 'ORIGINAL'
    ra = n.new('GeometryNodeInputNamedAttribute')
    ra.data_type = 'FLOAT_VECTOR'
    ra.inputs['Name'].default_value = 'rot'
    sa = n.new('GeometryNodeInputNamedAttribute')
    sa.data_type = 'FLOAT_VECTOR'
    sa.inputs['Name'].default_value = 'scl'
    e2r = n.new('FunctionNodeEulerToRotation')
    L.new(gi.outputs[0], m2p.inputs['Mesh'])
    L.new(m2p.outputs['Points'], iop.inputs['Points'])
    L.new(ci.outputs['Instances'], iop.inputs['Instance'])
    euler = ra.outputs['Attribute']
    if wind:
        euler = fx.wind_euler(fx.Nodes(ng), euler, *wind, seed=len(name))
    L.new(euler, e2r.inputs['Euler'])
    L.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    L.new(sa.outputs['Attribute'], iop.inputs['Scale'])
    L.new(iop.outputs['Instances'], go.inputs[0])
    ob.modifiers.new(name, 'NODES').node_group = ng
    return ob


def wire(name, pts, r, mat):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1)
    cu.materials.append(mat)
    return link(bpy.data.objects.new(name, cu))


def sag(a, b, drop, n=24):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, t) - Vector((0, 0, drop * 4 * t * (1 - t))) for t in (i / (n - 1) for i in range(n))]


def facade_mat(name, base, size=3.0, cell=(3.6, 3.3), win=(1.7, 1.6), sill=0.9, broken=0.3):
    """Concrete with a grid of windows: dark glass that reflects the sky, some panes gone."""
    m, nt, out = new_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    mp = node(nt, 'ShaderNodeMapping', Vector=obj)
    mp.inputs['Scale'].default_value = (1 / size,) * 3
    wall = Layer(nt, base, mp.outputs['Vector'], (0.9, 0.9, 0.88))
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=obj)
    u = math_op(nt, 'ADD', sep.outputs['X'], sep.outputs['Y'])
    v = sep.outputs['Z']

    def band(coord, period, width, offset):
        f = math_op(nt, 'FRACT', math_op(nt, 'DIVIDE', math_op(nt, 'SUBTRACT', coord, offset), period))
        d = math_op(nt, 'ABSOLUTE', math_op(nt, 'SUBTRACT', f, 0.5))
        return math_op(nt, 'LESS_THAN', d, width / period / 2)

    win_mask = math_op(nt, 'MULTIPLY', band(u, cell[0], win[0], 0.0),
                       band(v, cell[1], win[1], sill + win[1] / 2 - cell[1] / 2))
    cellid = node(nt, 'ShaderNodeCombineXYZ',
                  X=math_op(nt, 'FLOOR', math_op(nt, 'DIVIDE', u, cell[0])),
                  Y=math_op(nt, 'FLOOR', math_op(nt, 'DIVIDE', v, cell[1])))
    wn = node(nt, 'ShaderNodeTexWhiteNoise', Vector=cellid.outputs['Vector'])
    gone = math_op(nt, 'LESS_THAN', wn.outputs['Value'], broken)
    glass = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.08)
    grime = noise(nt, obj, 3.0, 6, 0.6)
    nt.links.new(map_range(nt, grime, 0.3, 0.8, 0.04, 0.45), glass.inputs['Roughness'])
    glass.inputs['Base Color'].default_value = (0.015, 0.018, 0.018, 1)
    hole = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=1.0)
    hole.inputs['Base Color'].default_value = (0.004, 0.004, 0.004, 1)
    pane = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gone, pane.inputs[0])
    nt.links.new(glass.outputs['BSDF'], pane.inputs[1])
    nt.links.new(hole.outputs['BSDF'], pane.inputs[2])
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(wall.rough, b.inputs['Roughness'])
    nt.links.new(wall.normal, b.inputs['Normal'])
    # Water stains run down from each sill.
    sv = node(nt, 'ShaderNodeMapping', Vector=obj)
    sv.inputs['Scale'].default_value = (2.5, 2.5, 0.12)
    runs = noise(nt, sv.outputs['Vector'], 1.0, 4, 0.5)
    stain = map_range(nt, runs, 0.55, 0.75, 0.0, 0.65)
    dark = mix_rgb_mul(nt, wall.col, (0.35, 0.36, 0.33))
    nt.links.new(mix_rgb(nt, stain, wall.col, dark), b.inputs['Base Color'])
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(win_mask, mx.inputs[0])
    nt.links.new(b.outputs['BSDF'], mx.inputs[1])
    nt.links.new(pane.outputs['Shader'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return m


# ---------------------------------------------------------------------------------------------
# Buildings: the plastered concrete blocks of a north Indian town, four to six floors over a row
# of shop shutters, with recessed windows, balconies, AC boxes and a water tank on the roof. Each
# building is one mesh (boxes collected, then built at once), in a local frame: the street face
# runs along +X at y = 0, the building extends to +Y, the ground is z = 0.


class Builder:
    def __init__(self):
        self.verts, self.faces, self.mats = [], [], []

    def box(self, center, size, mat, rz=0.0):
        cx, cy, cz = center
        sx, sy, sz = (s / 2 for s in size)
        c, s = math.cos(rz), math.sin(rz)
        base = len(self.verts)
        for x, y, z in ((-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)):
            self.verts.append((cx + x * c - y * s, cy + x * s + y * c, cz + z))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append(tuple(base + i for i in f))
            self.mats.append(mat)

    def cyl(self, center, r, h, mat, segs=16):
        cx, cy, cz = center
        base = len(self.verts)
        for k in range(segs):
            a = 2 * math.pi * k / segs
            self.verts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz - h / 2))
            self.verts.append((cx + r * math.cos(a), cy + r * math.sin(a), cz + h / 2))
        for k in range(segs):
            a, b = base + 2 * k, base + 2 * ((k + 1) % segs)
            self.faces.append((a, b, b + 1, a + 1))
            self.mats.append(mat)
        self.faces.append(tuple(base + 2 * k + 1 for k in range(segs)))
        self.mats.append(mat)

    def build(self, name, materials, loc, rot_z):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        for m in materials:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mats)
        me.update()
        ob = link(bpy.data.objects.new(name, me))
        ob.location = loc
        ob.rotation_euler = (0, 0, math.radians(rot_z))
        return ob


_BMATS = {}


def building_mats(tint):
    key = tint
    if key not in _BMATS:
        _BMATS[key] = [
            surface(f'plaster{tint}', 'worn_mossy_plasterwall', size=3.0, tint=tint,
                    over='concrete_moss', over_size=2.0, over_amount=0.9, over_lo=0.58,
                    low_bias=0.5),
            plain('interior', (0.006, 0.006, 0.006), 1.0),
            glass_mat(),
            surface('shutter', 'painted_metal_shutter', size=2.0, over='rusty_metal_02',
                    over_amount=0.9, over_lo=0.5, tint=(0.55, 0.55, 0.5)),
            surface('slab', 'concrete_wall_008', size=2.0, over='concrete_moss', over_amount=1.0,
                    over_lo=0.45, up_bias=0.8),
            plain('tank', (0.02, 0.022, 0.02), 0.55),
            plain('ac', (0.42, 0.42, 0.4), 0.5),
        ]
    return _BMATS[key]


def glass_mat():
    if 'glass' in _BMATS:
        return _BMATS['glass']
    m, nt, out = new_mat('pane')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    g = node(nt, 'ShaderNodeBsdfPrincipled')
    g.inputs['Base Color'].default_value = (0.01, 0.012, 0.012, 1)
    grime = noise(nt, geo.outputs['Position'], 2.5, 6, 0.6)
    nt.links.new(map_range(nt, grime, 0.3, 0.75, 0.03, 0.5), g.inputs['Roughness'])
    nt.links.new(g.outputs['BSDF'], out.inputs['Surface'])
    _BMATS['glass'] = m
    return m


PLASTER, INTERIOR, PANE, SHUTTER, SLAB, TANK, AC = range(7)


def building(rng, loc, rot_z, width, floors, tint, depth=14.0, shops=True):
    b = Builder()
    gh, fh, cw = 3.9, 3.2, 3.5
    ww, wh, sill = 1.6, 1.5, 0.95
    t = 0.3  # wall thickness
    n = max(1, int(width // cw))
    cw = width / n
    top = gh + floors * fh
    # Side and back walls, roof.
    b.box((width / 2, depth / 2, top / 2), (width, depth - 0.4, top), PLASTER)
    # Ground floor: shop bays behind roller shutters, piers between them.
    bays = max(1, int(width // 4.2))
    bw = width / bays
    for k in range(bays + 1):
        b.box((k * bw, -0.05, gh / 2), (0.45, 0.5, gh), PLASTER)
    b.box((width / 2, -0.05, gh - 0.35), (width, 0.5, 0.7), PLASTER)
    for k in range(bays):
        x = (k + 0.5) * bw
        open_to = rng.choice((0.0, 0.0, 0.35, 0.6, 1.0))
        h = gh - 0.7
        b.box((x, 0.35, h / 2), (bw - 0.45, 0.1, h), INTERIOR)
        if open_to < 1.0:
            sh = h * (1 - open_to)
            b.box((x, 0.12, h - sh / 2), (bw - 0.45, 0.06, sh), SHUTTER)
        b.box((x, -0.42, gh - 0.1), (bw - 0.1, 0.12, 0.55), SHUTTER if rng.random() < 0.5 else SLAB)
    # Upper floors: spandrels, piers, recessed windows; balconies on some bays; AC boxes.
    balcony_cols = {k for k in range(n) if rng.random() < 0.35}
    for f in range(floors):
        z0 = gh + f * fh
        b.box((width / 2, -t / 2, z0 + sill / 2), (width, t, sill), PLASTER)
        lint = fh - sill - wh
        b.box((width / 2, -t / 2, z0 + sill + wh + lint / 2), (width, t, lint), PLASTER)
        for k in range(n + 1):
            pw = cw - ww if 0 < k < n else (cw - ww) / 2
            px = k * cw if 0 < k < n else (pw / 2 if k == 0 else width - pw / 2)
            b.box((px, -t / 2, z0 + sill + wh / 2), (pw, t, wh), PLASTER)
        b.box((width / 2, 0.6, z0 + fh / 2), (width, 0.1, fh), INTERIOR)
        b.box((width / 2, -0.12, z0 + fh - 0.02), (width + 0.1, 0.5, 0.12), SLAB)
        for k in range(n):
            x = (k + 0.5) * cw
            if rng.random() > 0.3:
                b.box((x, 0.02, z0 + sill + wh / 2), (ww, 0.03, wh), PANE)
            b.box((x, -t - 0.05, z0 + sill - 0.04), (ww + 0.2, 0.16, 0.08), SLAB)
            if k in balcony_cols:
                b.box((x, -0.65, z0 + 0.08), (cw - 0.2, 1.3, 0.16), SLAB)
                b.box((x, -1.25, z0 + 0.6), (cw - 0.2, 0.12, 0.9), PLASTER)
                for sx in (-1, 1):
                    b.box((x + sx * (cw / 2 - 0.16), -0.65, z0 + 0.6), (0.12, 1.3, 0.9), PLASTER)
            elif rng.random() < 0.3:
                b.box((x + 0.3, -t - 0.3, z0 + sill - 0.45), (0.85, 0.32, 0.55), AC)
    # Roof: parapet, stair head, water tanks, rebar left for a floor never built.
    b.box((width / 2, -0.05, top + 0.5), (width, 0.25, 1.0), PLASTER)
    b.box((width * 0.7, depth * 0.6, top + 1.4), (3.0, 3.5, 2.8), PLASTER)
    for k in range(rng.randint(1, 3)):
        b.cyl((rng.uniform(2, width - 2), rng.uniform(3, depth - 3), top + 0.75), 0.6, 1.5, TANK)
    for k in range(rng.randint(4, 10)):
        b.cyl((rng.uniform(0.5, width - 0.5), rng.uniform(0.3, 1.0), top + 1.2), 0.02, 2.4, SLAB, 6)
    ob = b.build('building', building_mats(tint), loc, rot_z)
    return ob, top


# ---------------------------------------------------------------------------------------------
# The machine: a war machine sat down against a wall years ago and never got up. Moss on its
# shoulders, ferns at its feet, one sensor still faintly lit. Built facing -Y, sitting on z = 0.


def machine(origin, rot_z, scale, eye=0.6):
    plate = surface('machine-plate', 'metal_plate', size=1.6, over='rusty_metal_02',
                    over_amount=0.85, over_lo=0.52, tint=(0.3, 0.32, 0.29))
    joint = surface('machine-joint', 'rusty_metal_02', size=1.0, over='concrete_moss',
                    over_amount=0.9, over_lo=0.55, up_bias=0.7, tint=(0.5, 0.45, 0.4))
    armor = surface('machine-armor', 'metal_plate', size=2.2, over='concrete_moss',
                    over_size=1.2, over_amount=1.0, over_lo=0.6, up_bias=0.9,
                    tint=(0.2, 0.22, 0.2))
    rubber = plain('machine-rubber', (0.02, 0.02, 0.02), 0.7)
    lens = plain('machine-lens', (0.01, 0.01, 0.01), 0.05, emit=(1.0, 0.05, 0.03), strength=eye)
    root = empty('machine', origin)
    root.rotation_euler = (0, 0, math.radians(rot_z))
    root.scale = (scale,) * 3

    def P(ob):
        ob.parent = root
        return ob

    tilt = math.radians(18)
    P(box('m-pelvis', (0, 0.3, 0.75), (1.9, 1.3, 0.8), joint, bevel=0.06))
    P(box('m-torso', (0, 0.05, 2.15), (2.6, 1.7, 2.0), plate, rot=(tilt, 0, 0), bevel=0.1))
    P(box('m-chest', (0, -0.85, 2.35), (2.2, 0.3, 1.3), armor, rot=(tilt, 0, 0), bevel=0.08))
    P(box('m-chest2', (0, -0.95, 1.6), (1.6, 0.25, 0.5), plate, rot=(tilt + 0.1, 0, 0), bevel=0.05))
    P(box('m-pack', (0, 1.05, 2.35), (2.0, 0.8, 1.7), joint, rot=(tilt, 0, 0), bevel=0.08))
    P(box('m-collar', (0, -0.2, 3.05), (1.3, 1.1, 0.35), joint, rot=(tilt, 0, 0), bevel=0.05))
    head_rot = (math.radians(38), 0, math.radians(-12))
    P(box('m-head', (0.1, -0.75, 3.2), (0.95, 1.05, 0.62), armor, rot=head_rot, bevel=0.1))
    P(box('m-visor', (0.07, -1.25, 3.0), (0.78, 0.12, 0.26), plate, rot=head_rot, bevel=0.03))
    P(cylinder('m-eye', (0.12, -1.32, 2.97), 0.085, 0.06, lens,
               rot=(math.radians(38 + 90), 0, math.radians(-12))))
    for sx in (-1, 1):
        P(sphere(f'm-shoulder{sx}', (1.55 * sx, 0.1, 2.8), 0.58, armor, 32, 16))
        P(box(f'm-pauldron{sx}', (1.7 * sx, 0.05, 3.15), (1.0, 1.3, 0.3), armor,
              rot=(0, math.radians(-20 * sx), 0), bevel=0.06))
        P(segment(f'm-upper{sx}', (1.6 * sx, 0.1, 2.7), (1.95 * sx, -0.45, 1.3), 0.3, joint))
        P(sphere(f'm-elbow{sx}', (1.95 * sx, -0.45, 1.3), 0.34, joint, 24, 12))
        P(segment(f'm-fore{sx}', (1.95 * sx, -0.45, 1.3), (2.05 * sx, -1.45, 0.38), 0.4, plate, r2=0.3))
        P(segment(f'm-piston{sx}', (1.75 * sx, 0.15, 2.4), (1.75 * sx, -0.75, 1.0), 0.07, rubber))
        P(box(f'm-hand{sx}', (2.1 * sx, -1.8, 0.17), (0.55, 0.7, 0.3), plate,
              rot=(0, 0, math.radians(10 * sx)), bevel=0.05))
        for k in range(3):
            P(box(f'm-finger{sx}{k}', ((1.92 + 0.17 * k) * sx, -2.25, 0.08), (0.11, 0.42, 0.13),
                  joint, bevel=0.02))
        P(segment(f'm-thigh{sx}', (0.65 * sx, 0.0, 0.7), (0.95 * sx, -2.0, 1.45), 0.45, plate, r2=0.38))
        P(sphere(f'm-knee{sx}', (0.95 * sx, -2.0, 1.45), 0.42, armor, 24, 12))
        P(segment(f'm-shin{sx}', (0.95 * sx, -2.0, 1.45), (1.05 * sx, -3.25, 0.35), 0.38, armor, r2=0.32))
        P(segment(f'm-shinpiston{sx}', (1.25 * sx, -1.9, 1.2), (1.3 * sx, -3.0, 0.4), 0.06, rubber))
        P(box(f'm-foot{sx}', (1.05 * sx, -3.55, 0.2), (0.85, 1.25, 0.38), plate, bevel=0.06))
        for k in range(3):
            P(segment(f'm-cable{sx}{k}', (0.35 * sx + 0.1 * k * sx, 0.9, 3.0),
                      (0.25 * sx + 0.05 * k * sx, -0.4, 3.45 - 0.05 * k), 0.045, rubber))
        # Vents down the torso's flanks, armour over the forearm, a second sensor on the cheek.
        for k in range(5):
            P(box(f'm-vent{sx}{k}', (1.31 * sx, 0.05 - 0.05 * k, 1.75 + 0.17 * k), (0.06, 0.9, 0.05), rubber,
                  rot=(tilt, 0, 0)))
        P(box(f'm-bracer{sx}', (2.02 * sx, -0.95, 0.85), (0.62, 0.9, 0.5), armor,
              rot=(math.radians(-50), 0, math.radians(4 * sx)), bevel=0.05))
        P(cylinder(f'm-sensor{sx}', (0.1 + 0.32 * sx, -1.27, 3.13), 0.035, 0.05, lens,
                   rot=(math.radians(38 + 90), 0, math.radians(-12))))
        P(box(f'm-thighplate{sx}', (0.85 * sx, -1.0, 1.4), (0.75, 1.6, 0.18), armor,
              rot=(math.radians(-20), 0, 0), bevel=0.04))
    # Layered chest plates, a segmented spine down the pack, exhaust stacks, a bent antenna.
    for k in range(3):
        P(box(f'm-plate{k}', (0, -1.0 - 0.04 * k, 2.85 - 0.42 * k), (2.0 - 0.25 * k, 0.12, 0.42), armor,
              rot=(tilt + 0.08 * k, 0, 0), bevel=0.03))
    for k in range(6):
        P(cylinder(f'm-spine{k}', (0, 1.5, 1.55 + 0.32 * k), 0.16, 0.22, joint, rot=(tilt, 0, 0), segs=12))
    for sx in (-1, 1):
        P(cylinder(f'm-stack{sx}', (0.55 * sx, 1.25, 3.35), 0.14, 0.7, rubber, rot=(tilt, 0, 0), segs=12))
    P(segment('m-antenna', (-0.25, -0.5, 3.45), (-0.55, -0.2, 4.3), 0.02, rubber))
    P(segment('m-antenna2', (-0.55, -0.2, 4.3), (-0.75, -0.6, 4.5), 0.015, rubber))

    # What grew on it: leaves on everything that faces up, vines hanging off the shoulders.
    bpy.context.view_layer.update()
    rng = random.Random(9)
    leaves, stems = [], []
    stem = plain('m-stem', (0.05, 0.04, 0.03), 0.8)
    tops = [o for o in root.children if any(k in o.name for k in ('pauldron', 'shoulder', 'head', 'pack', 'thigh', 'collar', 'knee'))]
    for o in tops:
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector(map(min, *ws))
        hi = Vector(map(max, *ws))
        for _ in range(int(40 * (hi.x - lo.x) * (hi.y - lo.y)) + 8):
            p = Vector((rng.uniform(lo.x, hi.x), rng.uniform(lo.y, hi.y), hi.z - rng.uniform(0, 0.08)))
            leaves.append((p, (rng.uniform(-1.9, -1.2), rng.uniform(-3.1, 3.1), rng.uniform(-3.1, 3.1)), rng.uniform(1.2, 2.2)))
    for o in [o for o in root.children if 'pauldron' in o.name or 'pack' in o.name]:
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector(map(min, *ws))
        hi = Vector(map(max, *ws))
        for _ in range(7):
            x, y, z = rng.uniform(lo.x, hi.x), rng.uniform(lo.y, hi.y), hi.z
            pts = []
            for i in range(int(rng.uniform(8, 22))):
                pts.append((x, y, z))
                x += rng.gauss(0, 0.02)
                y += rng.gauss(0, 0.02)
                z -= 0.12
                for _ in range(3):
                    leaves.append(((x + rng.gauss(0, 0.07), y + rng.gauss(0, 0.07), z + rng.gauss(0, 0.05)),
                                   (rng.uniform(-0.7, 0.7), rng.uniform(-3.1, 3.1), rng.uniform(-3.1, 3.1)),
                                   rng.uniform(1.1, 1.9)))
            stems.append(wire(f'm-vine{len(stems)}', pts, 0.007, stem))
    scatter_col(f'machine-leaves{origin[1]}', leaf_col(), leaves, LEAF_WIND)
    # The head turns on its neck: everything on it re-hangs from a pivot.
    neck = empty('machine-neck', (0.0, -0.35, 3.0))
    neck.parent = root
    neck.rotation_mode = 'XYZ'
    bpy.context.view_layer.update()
    for o in [o for o in root.children if o.name.split('.')[0] in
              ('m-head', 'm-visor', 'm-eye', 'm-sensor-1', 'm-sensor1', 'm-antenna', 'm-antenna2')]:
        mw = o.matrix_world.copy()
        o.parent = neck
        o.matrix_world = mw
    # The scanner: a narrow red beam out of the eye (which looks along its own +Z), dark until the
    # machine wakes.
    eye_ob = next(o for o in neck.children if o.name.startswith('m-eye'))
    data = bpy.data.lights.new('m-scan', 'SPOT')
    data.energy = 0.0
    data.spot_size = math.radians(9)
    data.spot_blend = 0.35
    data.shadow_soft_size = 0.01
    data.color = (1.0, 0.08, 0.04)
    scan = link(bpy.data.objects.new('m-scan', data))
    scan.parent = eye_ob
    scan.location = (0.0, 0.0, 0.04)
    scan.rotation_euler = (math.pi, 0.0, 0.0)
    return {'root': root, 'neck': neck, 'scan': data, 'eye_ob': eye_ob,
            'eye': lens.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']}


def aim(m, target, amount=1.0):
    """Turn the machine's head so its eye (and scanner) points straight at a world point. The eye
    sits a metre in front of the neck's pivot, so the angles are found by measuring where the eye
    actually looks and correcting, a few times over."""
    neck, eye = m['neck'], m['eye_ob']
    target = Vector(target)
    turn = m['root'].matrix_world.to_3x3().normalized().inverted()  # world into the machine's frame

    def heading(v):  # the machine faces -Y; positive yaw turns it towards +X
        return math.atan2(v.x, -v.y)

    def elevation(v):
        return math.atan2(v.z, math.hypot(v.x, v.y))

    pitch, yaw = math.radians(-16), 0.0
    for _ in range(4):
        neck.rotation_euler = (pitch, 0, yaw)
        bpy.context.view_layer.update()
        mw = eye.matrix_world
        have = turn @ (mw.to_3x3() @ Vector((0, 0, 1)))
        want = turn @ (target - mw.translation)
        yaw += heading(want) - heading(have)
        pitch -= elevation(want) - elevation(have)
    neck.rotation_euler = (pitch * amount, 0, yaw * amount)


def watch(m, target, amount=1.0):
    """Turn the machine's head toward a world point (amount 0 → 1 of the way)."""
    neck = m['neck']
    bpy.context.view_layer.update()
    d = m['root'].matrix_world.inverted() @ Vector(target) - neck.location
    yaw = math.atan2(d.x, -d.y) + math.radians(12)
    neck.rotation_euler = (math.radians(-16) * amount, 0, yaw * amount)


# ---------------------------------------------------------------------------------------------
# Shot 4, the street: ground level, morning haze. Grass through the asphalt, trees where the
# road split, covered cars that never moved again, cables sagging across. At the far end, across
# the junction, the building with the red light on its roof. Units are metres; the road runs +Y.

ROAD_W, WALK = 5.0, 3.6  # half the carriageway; sidewalk width
LAB_Y = 96.0
IVY_RNG = random.Random(5)  # its own stream, so more ivy never moves the buildings


def build_street(rng):
    road = surface('road', 'road_damaged', size=4.0, over='forest_leaves_02', over_size=2.5,
                   over_amount=1.0, over_lo=0.47, wet=1.0, tint=(0.32, 0.32, 0.31), rough_add=0.35)
    walk = surface('walk', 'dirty_concrete', size=2.5, over='concrete_moss', over_size=2.0,
                   over_amount=1.0, over_lo=0.42, up_bias=0.3)
    curb = surface('curb', 'concrete_wall_008', size=1.5, over='concrete_moss', over_amount=1.0,
                   over_lo=0.4)
    mesh_obj('road', [(-60, -130, 0), (60, -130, 0), (60, 180, 0), (-60, 180, 0)], [(0, 1, 2, 3)], road)
    start = -120.0
    length = LAB_Y - 12 - start
    for sx in (-1, 1):
        x0 = ROAD_W * sx
        x1 = (ROAD_W + WALK) * sx
        box(f'walk{sx}', ((x0 + x1) / 2, start + length / 2, 0.075), (WALK, length, 0.15), walk)
        box(f'curb{sx}', (x0 + 0.12 * sx, start + length / 2, 0.09), (0.24, length, 0.18), curb)
    # Buildings, fronts on the sidewalk's back edge. Faded paint: cream, ochre, pale green, grey.
    edge = ROAD_W + WALK
    tints = [(0.95, 0.88, 0.72), (0.9, 0.75, 0.55), (0.75, 0.85, 0.76), (0.82, 0.82, 0.8),
             (0.95, 0.8, 0.7), (0.7, 0.75, 0.8)]
    for sx in (-1, 1):
        y = -24.0
        while y < LAB_Y - 14:
            w = rng.choice((10.5, 14.0, 17.5, 21.0))
            w = min(w, LAB_Y - 12 - y)
            floors = rng.choice((3, 4, 4, 5, 6))
            tint = rng.choice(tints)
            if sx < 0:  # street face toward +X
                _, top = building(rng, (-edge, y, 0), 90, w, floors, tint)
            else:  # street face toward -X
                _, top = building(rng, (edge, y + w, 0), -90, w, floors, tint)
            if rng.random() < 0.8:
                ivy(IVY_RNG, sx * edge, -sx, y, y + w, top, int(w * rng.uniform(1.5, 3.0)))
            y += w + rng.choice((0.0, 0.0, 2.5, 4.0))
    # Behind the start (seen when looking back down the street), from its own random stream so the
    # street ahead keeps its layout.
    back = random.Random(21)
    for sx in (-1, 1):
        y = -24.0
        while y > -125:
            w = back.choice((10.5, 14.0, 17.5, 21.0))
            floors = back.choice((3, 4, 4, 5, 6))
            tint = back.choice(tints)
            y0 = y - w
            if sx < 0:
                _, top = building(back, (-edge, y0, 0), 90, w, floors, tint)
            else:
                _, top = building(back, (edge, y0 + w, 0), -90, w, floors, tint)
            if back.random() < 0.8:
                ivy(IVY_RNG, sx * edge, -sx, y0, y, top, int(w * back.uniform(1.5, 3.0)))
            y = y0 - back.choice((0.0, 0.0, 2.5, 4.0))


LAB_W, LAB_D, LAB_H = 46.0, 22.0, 14.4
DOOR_X = -4.0  # the entrance's centre, world x


def build_lab(rng, beacon=60.0):
    """The lab: a brutalist research block across the junction. Concrete fins, ribbon windows
    (most panes gone), a deep entrance under a slab canopy with a red beacon blinking inside, and
    on the roof the mast that has been transmitting the whole time."""
    conc = surface('lab-conc', 'concrete_wall_008', size=3.0, over='concrete_moss', over_size=2.0,
                   over_amount=1.0, over_lo=0.56, low_bias=0.6, tint=(0.82, 0.82, 0.8))
    mats = [conc, plain('lab-dark', (0.005, 0.005, 0.005), 1.0), glass_mat(),
            surface('lab-slab', 'concrete_wall_008', size=2.0, over='concrete_moss',
                    over_amount=1.0, over_lo=0.45, up_bias=0.8),
            plain('lab-frame', (0.05, 0.05, 0.048), 0.45, 0.8)]
    C, DARK, GLASS, SLAB, FRAME = range(5)
    b = Builder()
    w, d, fh = LAB_W, LAB_D, 4.8
    ex = DOOR_X + w / 2  # entrance x in the local frame
    # The block is a shell (walls, the roof below), so the corridor from the entrance runs into it
    # and the lab (lab.py's room, placed by the door shot) sits inside: an opening 3 m wide.
    t = 0.3
    for x0, x1 in ((0, ex - 1.5), (ex + 1.5, w)):
        b.box(((x0 + x1) / 2, 3.2 + t / 2, LAB_H / 2), (x1 - x0, t, LAB_H), C)
    b.box((ex, 3.2 + t / 2, (3.0 + LAB_H) / 2), (3.0, t, LAB_H - 3.0), C)
    b.box((w / 2, d - t / 2, LAB_H / 2), (w, t, LAB_H), C)
    for x in (t / 2, w - t / 2):
        b.box((x, (3.2 + d) / 2, LAB_H / 2), (t, d - 3.2, LAB_H), C)
    b.box((w / 2, (3.2 + d) / 2, 0.05), (w, d - 3.2, 0.1), C)
    for f in range(3):
        z0 = f * fh
        if f == 0:
            # Ground floor: solid wall with the entrance recess.
            for x0, x1 in ((0, ex - 3.4), (ex + 3.4, w)):
                b.box(((x0 + x1) / 2, 0.3, 2.4), (x1 - x0, 0.6, 4.8), C)
            b.box((ex, 0.3, 4.3), (6.8, 0.6, 1.0), C)
            # The lobby's back wall, open in the middle where the corridor goes in.
            for x0, x1 in ((ex - 3.4, ex - 1.5), (ex + 1.5, ex + 3.4)):
                b.box(((x0 + x1) / 2, 3.0, 1.9), (x1 - x0, 0.2, 3.8), DARK)
            b.box((ex, 3.0, 3.4), (3.0, 0.2, 0.8), DARK)
            for sx in (-1, 1):
                b.box((ex + sx * 3.3, 1.6, 1.9), (0.2, 2.8, 3.8), C)
            # Glass doors: frames, one leaf gone, one ajar.
            b.box((ex, 1.2, 3.62), (6.4, 0.12, 0.12), FRAME)
            for k in range(5):
                b.box((ex - 3.0 + k * 1.5, 1.2, 1.8), (0.08, 0.1, 3.6), FRAME)
            for k in (0, 3):
                b.box((ex - 2.25 + k * 1.5, 1.22, 1.8), (1.38, 0.02, 3.5), GLASS)
        else:
            # Ribbon window, set back behind the fins.
            b.box((w / 2, 0.3, z0 + 0.55), (w, 0.6, 1.1), C)
            b.box((w / 2, 0.3, z0 + fh - 0.9), (w, 0.6, 1.8), C)
            b.box((w / 2, 1.4, z0 + 1.1 + 1.05), (w, 0.1, 2.1), DARK)
            for k in range(int(w / 1.5)):
                x = (k + 0.5) * 1.5
                b.box((x, 0.45, z0 + 2.15), (0.06, 0.08, 2.1), FRAME)
                if rng.random() > 0.55:
                    b.box((x, 0.47, z0 + 2.15), (1.42, 0.02, 2.06), GLASS)
        b.box((w / 2, -0.15, z0 + 0.06), (w + 0.4, 0.5, 0.12), SLAB)
    # Fins: vertical concrete blades every 3.8 m, the full height.
    for k in range(int(w / 3.8) + 1):
        x = k * (w / int(w / 3.8))
        if abs(x - ex) < 3.6:
            continue
        b.box((x, -0.35, LAB_H / 2 + 0.3), (0.35, 0.9, LAB_H + 0.6), C)
    b.box((w / 2, d / 2, LAB_H + 0.45), (w + 0.3, d + 0.3, 0.9), SLAB)
    # Canopy and its columns.
    b.box((ex, -1.9, 4.05), (8.0, 4.4, 0.4), SLAB)
    for sx in (-1, 1):
        b.cyl((ex + sx * 3.6, -3.7, 1.95), 0.2, 3.9, C)
    # Plant room on the roof.
    b.box((w * 0.25, d * 0.55, LAB_H + 2.0), (8.0, 6.0, 3.2), C)
    b.build('lab', mats, (-w / 2, LAB_Y, 0), 0)
    hinge = empty('lab-door-hinge', (DOOR_X + 1.5, LAB_Y + 1.2, 0.0))
    hinge.rotation_mode = 'XYZ'
    leaf = box('lab-door-leaf', (-0.72, 0.0, 1.8), (1.42, 0.04, 3.5), mats[GLASS])
    leaf.parent = hinge
    frame_mat = mats[FRAME]
    for x in (-0.02, -1.42):
        box(f'lab-door-stile{x}', (x, 0.0, 1.8), (0.06, 0.06, 3.5), frame_mat).parent = hinge
    box('lab-door-rail', (-0.72, 0.0, 0.08), (1.42, 0.06, 0.16), frame_mat).parent = hinge
    hinge.rotation_euler = (0, 0, math.radians(-38))  # ajar, inward

    # The sign: the archive's own name in cast letters on the canopy's face.
    font = os.path.join(ROOT, 'blender', 'fonts', 'archivo-heavy.ttf')
    if os.path.exists(font):
        cu = bpy.data.curves.new('sign', 'FONT')
        cu.body = 'THE ARCHIVE'
        cu.font = bpy.data.fonts.load(font, check_existing=True)
        cu.size = 0.42
        cu.extrude = 0.025
        cu.align_x = 'CENTER'
        cu.materials.append(surface('letters', 'rusty_metal_02', size=0.6, tint=(0.6, 0.55, 0.5),
                                    disp=False))
        sign = link(bpy.data.objects.new('sign', cu))
        sign.location = (DOOR_X, LAB_Y - 4.12, 3.92)
        sign.rotation_euler = (math.radians(90), 0, 0)

    # The mast and the beacon.
    steel = plain('mast', (0.12, 0.12, 0.11), 0.5, 0.9)
    mx, my = 4.0, LAB_Y + 6.0
    cylinder('mast', (mx, my, LAB_H + 5.5), 0.12, 11.0, steel)
    for k in range(4):
        box(f'mast-rung{k}', (mx, my, LAB_H + 2.0 + k * 2.2), (1.4 - 0.25 * k, 0.06, 0.06), steel)
    sphere('beacon-lamp', (mx, my, LAB_H + 11.1), 0.18, emit_mat('beacon', (1.0, 0.06, 0.03), 160.0), 16, 8)
    point('beacon-light', (mx, my, LAB_H + 11.1), beacon, (1.0, 0.08, 0.04), 0.12)
    cylinder('dish', (mx - 0.9, my, LAB_H + 6.5), 0.7, 0.12, steel,
             rot=(0, math.radians(70), math.radians(200)), r2=0.2)
    box('junction-walk', (0, LAB_Y - 2.5, 0.075), (70, 5.0, 0.15),
        surface('walk2', 'dirty_concrete', size=2.5, over='concrete_moss', over_amount=1.0,
                over_lo=0.4))
    return (mx, my, LAB_H + 11.1)


def overgrowth(rng):
    """Plants where the city cracked: along the curbs, in the road's seams, around the trees."""
    trees = [(-6.4, 7, 2.5), (6.8, 33, 2.3), (-7.4, 40, 2.4), (7.6, 64, 2.1), (-6.5, 72, 2.6),
             (7.2, 84, 2.2), (16.0, LAB_Y - 4, 2.6), (-17.0, LAB_Y - 5, 2.4)]
    for x, y, s in trees:
        place('island_tree_01', (x, y, 0), rng.uniform(0, 360), s,
              (rng.uniform(-4, 4), rng.uniform(-4, 4)))
    grass, ferns, weeds, shrubs = [], [], [], []
    for _ in range(9000):
        y = rng.uniform(-6, LAB_Y + 1)
        r = rng.random()
        if r < 0.45:  # along the curbs and the walls
            sx = rng.choice((-1, 1))
            x = sx * rng.choice((ROAD_W + rng.uniform(-0.25, 0.4), ROAD_W + WALK - rng.uniform(0, 0.8)))
        elif r < 0.75:  # the road's seams: lanes and the centre line
            x = rng.choice((-2.5, 0.0, 2.5)) + rng.gauss(0, 0.35)
        else:  # anywhere, more towards the far end
            x = rng.uniform(-ROAD_W - WALK, ROAD_W + WALK)
            if rng.random() < 0.5 and y < 40:
                continue
        z = 0.15 if abs(x) > ROAD_W else 0.0
        grass.append(((x, y, z), rng.uniform(0, 6.28), rng.uniform(1.3, 2.8)))
        if rng.random() < 0.18:
            weeds.append(((x + rng.gauss(0, 0.3), y + rng.gauss(0, 0.3), z), rng.uniform(0, 6.28),
                          rng.uniform(1.5, 3.0)))
        if rng.random() < 0.07:
            ferns.append(((x, y + rng.gauss(0, 0.4), z), rng.uniform(0, 6.28), rng.uniform(0.9, 1.6)))
        if rng.random() < 0.025:
            shrubs.append(((x, y, z), rng.uniform(0, 6.28), rng.uniform(0.6, 1.1)))
    for x, y, s in trees:
        for _ in range(30):
            a, d = rng.uniform(0, 6.28), rng.uniform(0.3, 2.6)
            grass.append(((x + d * math.cos(a), y + d * math.sin(a), 0), rng.uniform(0, 6.28),
                          rng.uniform(1.4, 2.6)))
        place('root_cluster_01', (x, y, 0), rng.uniform(0, 360), s * 0.45)
    back = random.Random(23)
    for _ in range(4000):
        y = back.uniform(-120, -6)
        sx = back.choice((-1, 1))
        x = back.choice((sx * (ROAD_W + back.uniform(-0.25, 0.4)), sx * (ROAD_W + WALK - back.uniform(0, 0.8)),
                         back.choice((-2.5, 0.0, 2.5)) + back.gauss(0, 0.35), back.uniform(-ROAD_W, ROAD_W)))
        z = 0.15 if abs(x) > ROAD_W else 0.0
        grass.append(((x, y, z), back.uniform(0, 6.28), back.uniform(1.3, 2.8)))
        if back.random() < 0.15:
            weeds.append(((x, y, z), back.uniform(0, 6.28), back.uniform(1.5, 3.0)))
    for x, y, sc in ((-6.8, -40, 2.4), (7.0, -62, 2.2), (-6.4, -88, 2.6), (6.6, -108, 2.3)):
        place('island_tree_01', (x, y, 0), back.uniform(0, 360), sc)
    scatter_variants('grass_medium_01', grass, rng)
    scatter_variants('nettle_plant', weeds, rng)
    scatter_variants('fern_02', ferns, rng)
    scatter_variants('shrub_02', shrubs, rng)


_LEAF = {}


def leaf_col():
    """One ivy leaf: a card with a leaf-shaped cut-out, lit through from behind. Each instance gets
    its own shade of green from its random number."""
    if 'col' in _LEAF:
        return _LEAF['col']
    m, nt, out = new_mat('leaf')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=tc.outputs['UV'])
    # Leaf outline: an ellipse narrowing to the tip.
    u = math_op(nt, 'SUBTRACT', sep.outputs['X'], 0.5)
    v = sep.outputs['Y']
    half = math_op(nt, 'MULTIPLY', math_op(nt, 'SINE', math_op(nt, 'MULTIPLY', v, math.pi)), 0.5)
    half = math_op(nt, 'MULTIPLY', half, map_range(nt, v, 0.0, 1.0, 1.0, 0.6))
    inside = math_op(nt, 'LESS_THAN', math_op(nt, 'ABSOLUTE', u), half)
    info = nt.nodes.new('ShaderNodeObjectInfo')
    shade = node(nt, 'ShaderNodeValToRGB', Fac=info.outputs['Random'])
    cr = shade.color_ramp
    cr.elements[0].color = (0.035, 0.07, 0.015, 1)
    cr.elements[1].color = (0.12, 0.16, 0.03, 1)
    e = cr.elements.new(0.75)
    e.color = (0.09, 0.075, 0.02, 1)
    b = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.55)
    nt.links.new(shade.outputs['Color'], b.inputs['Base Color'])
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    nt.links.new(shade.outputs['Color'], tl.inputs['Color'])
    mx = nt.nodes.new('ShaderNodeMixShader')
    mx.inputs[0].default_value = 0.3
    nt.links.new(b.outputs['BSDF'], mx.inputs[1])
    nt.links.new(tl.outputs['BSDF'], mx.inputs[2])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    cut = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(inside, cut.inputs[0])
    nt.links.new(tr.outputs['BSDF'], cut.inputs[1])
    nt.links.new(mx.outputs['Shader'], cut.inputs[2])
    nt.links.new(cut.outputs['Shader'], out.inputs['Surface'])
    me = bpy.data.meshes.new('leaf')
    w, h = 0.09, 0.13
    me.from_pydata([(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for li, c in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    me.materials.append(m)
    ob = bpy.data.objects.new('leaf', me)
    col = bpy.data.collections.new('leaf')
    col.objects.link(ob)
    _LEAF['col'] = col
    return col


def ivy(rng, x0, facing, y0, y1, top, count, axis='x', out=0.36):
    """Ivy on a wall: climbing from the ground and hanging from the roof, leaves along every stem.
    axis 'x': the wall is the plane x = x0 facing +X (facing = 1) or -X, running y0..y1.
    axis 'y': the wall is y = x0 facing -Y (facing = -1), running x from y0 to y1."""
    stem = plain('stem', (0.05, 0.04, 0.03), 0.8)
    leaves = []
    if axis == 'x':
        rz = math.radians(90 if facing > 0 else -90)
        to = lambda off, u, z: (x0 + facing * off, u, z)  # noqa: E731
    else:
        rz = 0.0 if facing < 0 else math.pi
        to = lambda off, u, z: (u, x0 + facing * off, z)  # noqa: E731
    for k in range(count):
        hang = rng.random() < 0.4
        y = rng.uniform(y0, y1)
        z = top + 0.8 if hang else 0.1
        length = rng.uniform(3, 9) if hang else rng.uniform(2.5, min(top, 14))
        pts = []
        dy = rng.uniform(-0.05, 0.05)
        steps = int(length / 0.15)
        for i in range(steps):
            pts.append(to(out, y, z))
            dy = max(-0.08, min(0.08, dy + rng.gauss(0, 0.025)))
            y += dy
            z += (-0.14 if hang else 0.13) + rng.gauss(0, 0.02)
            n = 3 if hang else 2
            spread = 0.18 if hang else 0.25 + 0.15 * math.sin(i * 0.3)
            for _ in range(n):
                leaves.append((to(rng.uniform(out - 0.02, out + 0.24), y + rng.gauss(0, spread),
                                  z + rng.gauss(0, spread * 0.6)),
                               (rng.uniform(-0.7, 0.7), rng.uniform(-3.14, 3.14), rz + rng.uniform(-0.5, 0.5)),
                               rng.uniform(1.2, 2.2)))
            if z < 0.05 or z > top + 1:
                break
        if len(pts) > 1:
            wire(f'ivy{x0}{k}', pts, 0.008, stem)
    scatter_col(f'leaves{x0}{y0}', leaf_col(), leaves, LEAF_WIND)


def props(rng):
    for x, y, rz in ((-3.0, 11.5, 8), (2.7, 24.0, 172), (-2.6, 41.0, -18), (3.7, 63.5, 186),
                     (-3.3, 73.0, 4)):
        place('covered_car', (x, y, 0), rz, 1.0)
    for i, (x, y, rz) in enumerate(((-1.4, 36.0, 20), (0.3, 36.6, 12), (1.9, 37.4, 28))):
        place('concrete_road_barrier', (x, y, 0), rz, 1.0, (0, 6 if i == 1 else 0))
    for x, y in ((-4.2, 14.5), (2.0, 27.5), (4.4, 51.0)):
        place('old_tyre', (x, y, 0.08), rng.uniform(0, 360), 1.0, (90, 0))
    for sx in (-1, 1):
        for k, y in enumerate(range(6, 90, 21)):
            tilt = (rng.uniform(-6, 6), rng.uniform(-10, 10) if k % 2 else 0)
            place('street_lamp_01', (sx * (ROAD_W + 0.6), y + (5 if sx > 0 else 0), 0.15),
                  90 if sx < 0 else -90, 1.6, tilt)
    for y in (19.0, 63.0):
        place('utility_box_01', (-(ROAD_W + WALK - 0.4), y, 0.15), 90, 1.4)
    # Poles and the cables they still hold up.
    steel = plain('pole', (0.16, 0.16, 0.15), 0.6, 0.4)
    cable = plain('cable', (0.015, 0.015, 0.015), 0.6)
    tops = []
    for k, y in enumerate((3.0, 24.0, 45.0, 66.0, 87.0)):
        x = ROAD_W + WALK - 0.6
        lean = rng.uniform(-3, 3) if k != 2 else 9
        pole = cylinder(f'pole{k}', (x, y, 4.5), 0.14, 9.0, steel, r2=0.11)
        pole.rotation_euler = (math.radians(rng.uniform(-2, 2)), math.radians(-lean), 0)
        box(f'arm{k}', (x - 0.5, y, 8.3), (1.6, 0.1, 0.1), steel)
        tops.append(Vector((x - 0.2, y, 8.3)))
    for a, b in zip(tops, tops[1:]):
        for j in range(4):
            off = Vector((-0.5 + j * 0.3, 0, -0.1 * j))
            wire(f'w{a.y}{j}', sag(a + off, b + off, 1.2 + 0.35 * j), 0.012, cable)
    for k, t in enumerate(tops):
        for j in range(2):
            far = Vector((-(ROAD_W + WALK) + 0.1, t.y + rng.uniform(-6, 6), 6.5 + rng.uniform(-1.5, 2)))
            wire(f'x{k}{j}', sag(t + Vector((-0.6, 0, -0.2 * j)), far, 1.4 + 0.5 * j), 0.014, cable)
    # One cable came down and lies across the road.
    wire('down', [(ROAD_W + 2.4, 45.2, 8.0), (ROAD_W, 44.0, 3.0), (2.5, 42.0, 0.05),
                  (-1.0, 41.5, 0.04), (-3.0, 43.5, 0.05)], 0.016, cable)


# ---------------------------------------------------------------------------------------------
# The lander: the crew's craft. Squat, practical, scorched underneath from the way down: an
# octagonal hull on four legs, three engines, floodlights, a ramp on the +Y side. Built with its
# feet on z = 0; 'open' lowers the ramp to the ground.

HULL_R, HULL_Z0, HULL_Z1 = 3.4, 2.3, 6.5


def hull_mat():
    m, nt, out = new_mat('hull')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    mp = node(nt, 'ShaderNodeMapping', Vector=obj)
    mp.inputs['Scale'].default_value = (1 / 1.6,) * 3
    a = Layer(nt, 'metal_plate', mp.outputs['Vector'], (0.78, 0.78, 0.75))
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=obj)
    soot = map_range(nt, sep.outputs['Z'], HULL_Z0 + 2.2, HULL_Z0, 0.0, 1.0)
    streak = node(nt, 'ShaderNodeMapping', Vector=obj)
    streak.inputs['Scale'].default_value = (3.0, 3.0, 0.25)
    sn = noise(nt, streak.outputs['Vector'], 1.0, 5, 0.6)
    soot = math_op(nt, 'MULTIPLY', soot, map_range(nt, sn, 0.3, 0.7, 0.5, 1.2), clamp=True)
    col = mix_rgb(nt, soot, a.col, (0.03, 0.028, 0.025))
    # A safety-orange band round the hull, worn at the edges.
    band = math_op(nt, 'MULTIPLY', math_op(nt, 'GREATER_THAN', sep.outputs['Z'], HULL_Z1 - 0.9),
                   math_op(nt, 'LESS_THAN', sep.outputs['Z'], HULL_Z1 - 0.55))
    wear = map_range(nt, noise(nt, obj, 6.0, 6, 0.6), 0.45, 0.6)
    col = mix_rgb(nt, math_op(nt, 'MULTIPLY', band, wear), col, (0.55, 0.16, 0.02))
    b = node(nt, 'ShaderNodeBsdfPrincipled', Metallic=0.35)
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(mix_float(nt, soot, a.rough, 0.85), b.inputs['Roughness'])
    nt.links.new(a.normal, b.inputs['Normal'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m


def lander(origin, rot_z, open_ramp=False, burn=0.0, lights=True, interior=False):
    hull = hull_mat()
    dark = plain('l-dark', (0.02, 0.02, 0.02), 0.6, 0.5)
    steel = plain('l-steel', (0.35, 0.35, 0.34), 0.35, 0.9)
    shield = surface('l-shield', 'rusty_metal_02', size=1.2, tint=(0.12, 0.1, 0.09))
    win = plain('l-window', (0.01, 0.01, 0.01), 0.05, emit=(1.0, 0.72, 0.45), strength=2.5)
    root = empty('lander', origin)
    root.rotation_euler = (0, 0, math.radians(rot_z))

    def P(ob):
        ob.parent = root
        return ob

    b = Builder()
    segs = 8
    t = 0.18
    H, D, S, ST = range(4)
    # The hull as eight wall panels, so it can be entered; the +Y panel has the ramp opening.
    apothem = HULL_R * math.cos(math.pi / segs)
    side = 2 * HULL_R * math.sin(math.pi / segs)
    for k in range(segs):
        a = 2 * math.pi * k / segs + math.pi / 2  # k = 0 faces +Y
        cx, cy = apothem * math.cos(a), apothem * math.sin(a)
        rz = a - math.pi / 2
        hh = HULL_Z1 - HULL_Z0
        if k == 0:
            door_w, door_h = 2.2, 2.5
            jam = (side - door_w) / 2
            for sx in (-1, 1):
                off = sx * (door_w / 2 + jam / 2)
                b.box((cx + off * math.cos(rz), cy + off * math.sin(rz), HULL_Z0 + hh / 2),
                      (jam + 0.02, t, hh), H, rz)
            b.box((cx, cy, HULL_Z0 + door_h + (hh - door_h) / 2), (door_w, t, hh - door_h), H, rz)
        else:
            b.box((cx, cy, HULL_Z0 + hh / 2), (side + 0.02, t, hh), H, rz)
    # Shoulder and roof: a stepped frustum, then the top deck.
    b.cyl((0, 0, HULL_Z1 + 0.5), HULL_R * 0.92, 1.0, H, 8)
    b.cyl((0, 0, HULL_Z1 + 1.25), HULL_R * 0.66, 0.5, H, 8)
    b.box((0, 0, HULL_Z0 + 0.08), (2 * apothem, 2 * apothem, 0.16), D)  # the hold's floor
    ob = P(b.build('l-hull', [hull, dark, shield, steel], (0, 0, 0), 0))
    ob.parent = root
    # Heat shield underneath and the engines.
    P(cylinder('l-shield', (0, 0, HULL_Z0 - 0.15), HULL_R + 0.12, 0.3, shield, segs=8))
    handles = {'root': root, 'jets': []}
    glow = emit_mat('l-burn', (1.0, 0.55, 0.25), 60.0 * burn)
    handles['glow'] = glow.node_tree.nodes['Emission'].inputs['Strength']
    for k in range(3):
        a = 2 * math.pi * k / 3
        x, y = 1.2 * math.cos(a), 1.2 * math.sin(a)
        P(cylinder(f'l-bell{k}', (x, y, HULL_Z0 - 0.75), 0.25, 0.9, steel, r2=0.55, caps=False))
        P(cylinder(f'l-throat{k}', (x, y, HULL_Z0 - 1.1), 0.48, 0.05, glow))
    handles['plume_light'] = P(point('l-plume', (0, 0, HULL_Z0 - 2.4), 9000.0 * burn, (1.0, 0.62, 0.38), 0.8))
    plume = plume_mat(burn)
    handles['burn'] = plume.node_tree.nodes['burn'].outputs[0]
    for k in range(3):
        a = 2 * math.pi * k / 3
        handles['jets'].append(P(cylinder(f'l-jet{k}', (1.2 * math.cos(a), 1.2 * math.sin(a), HULL_Z0 - 3.2),
                                          0.42, 4.2, plume, r2=0.8, caps=False, segs=24)))
    # Propellant tanks between the legs, a thrust frame, equipment bays and conduits on the hull.
    for k in range(4):
        a = k * math.pi / 2
        P(sphere(f'l-tank{k}', (2.9 * math.cos(a), 2.9 * math.sin(a), HULL_Z0 - 0.35), 0.62, hull, 32, 16))
        P(segment(f'l-truss{k}', (0.6 * math.cos(a), 0.6 * math.sin(a), HULL_Z0 - 0.3),
                  (2.5 * math.cos(a + 0.4), 2.5 * math.sin(a + 0.4), HULL_Z0 - 0.3), 0.05, steel))
    bay_rng = random.Random(4)
    for k in range(1, 8):
        a = 2 * math.pi * k / 8 + math.pi / 2
        rz = a - math.pi / 2
        for j in range(bay_rng.randint(1, 3)):
            w_, h_ = bay_rng.uniform(0.35, 0.9), bay_rng.uniform(0.3, 0.8)
            off = bay_rng.uniform(-0.5, 0.5)
            z = bay_rng.uniform(HULL_Z0 + 0.6, HULL_Z1 - 0.9)
            r = apothem + 0.1
            P(box(f'l-bay{k}{j}', (r * math.cos(a) + off * math.cos(rz), r * math.sin(a) + off * math.sin(rz), z),
                  (w_, 0.12, h_), steel if j % 2 else dark, rot=(0, 0, rz), bevel=0.01))
        P(cylinder(f'l-conduit{k}', ((apothem + 0.06) * math.cos(a + 0.33), (apothem + 0.06) * math.sin(a + 0.33),
                                     (HULL_Z0 + HULL_Z1) / 2), 0.035, HULL_Z1 - HULL_Z0, dark, segs=8))
    # Navigation lights: red to port, green to starboard, a white strobe on the mast.
    for sx, col in ((-1, (1.0, 0.05, 0.03)), (1, (0.1, 1.0, 0.25))):
        P(sphere(f'l-nav{sx}', (sx * (HULL_R + 0.05), 0.0, HULL_Z1 + 0.15), 0.07, emit_mat(f'nav{sx}', col, 40.0), 8, 4))
    handles['strobe'] = emit_mat('strobe', (1.0, 1.0, 1.0), 0.0)
    P(sphere('l-strobe', (0.8, -0.6, HULL_Z1 + 3.55), 0.06, handles['strobe'], 8, 4))
    # Hardware that makes it a working craft: RCS quads, radiators, a docking ring, a ladder.
    for k in range(4):
        a = math.pi / 8 + k * math.pi / 2
        c = Vector((HULL_R * 0.97 * math.cos(a), HULL_R * 0.97 * math.sin(a), HULL_Z1 - 0.35))
        P(box(f'l-rcs{k}', c, (0.4, 0.4, 0.36), steel, rot=(0, 0, a)))
        for j, d in enumerate(((0, 0, 1), (0, 0, -1), (-math.sin(a), math.cos(a), 0))):
            q = c + Vector(d) * 0.25
            P(cylinder(f'l-rcsn{k}{j}', q, 0.05, 0.14, dark, r2=0.09,
                       rot=Vector(d).to_track_quat('Z', 'Y').to_euler()))
    for sx in (-1, 1):
        P(box(f'l-rad{sx}', (sx * (HULL_R + 0.25), -0.6, HULL_Z0 + 2.2), (0.05, 2.0, 2.4), steel))
        for j in range(5):
            P(box(f'l-radfin{sx}{j}', (sx * (HULL_R + 0.25), -1.4 + j * 0.4, HULL_Z0 + 2.2),
                  (0.12, 0.04, 2.3), dark))
    P(cylinder('l-ring', (0, 0, HULL_Z1 + 1.62), 0.95, 0.24, steel, segs=32))
    P(cylinder('l-ringin', (0, 0, HULL_Z1 + 1.75), 0.75, 0.06, dark, segs=32))
    a = math.pi / 4 + math.pi / 2
    for j in range(7):
        t = j / 7
        p0 = Vector((3.0 * math.cos(a), 3.0 * math.sin(a), HULL_Z0 + 1.2)).lerp(
            Vector((5.0 * math.cos(a), 5.0 * math.sin(a), 0.12)), t)
        P(box(f'l-rung{j}', p0 + Vector((0, 0, 0.1)), (0.5, 0.04, 0.04), steel, rot=(0, 0, a + math.pi / 2)))
    # Legs: a main strut and a brace to each pad.
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        foot = (5.0 * ca, 5.0 * sa, 0.12)
        P(segment(f'l-leg{k}', (3.0 * ca, 3.0 * sa, HULL_Z0 + 1.2), foot, 0.13, steel))
        P(segment(f'l-brace{k}', (3.2 * ca, 3.2 * sa, HULL_Z0 - 0.1), foot, 0.08, steel))
        P(segment(f'l-damper{k}', (3.1 * ca, 3.1 * sa, HULL_Z0 + 0.6),
                  (4.2 * ca, 4.2 * sa, 1.0), 0.1, dark))
        P(cylinder(f'l-pad{k}', foot, 0.55, 0.14, steel))
    # Windows on the flight deck, antennas, floodlights.
    for k in (-1, 0, 1):
        a = math.pi / 2 + k * 0.32
        P(box(f'l-win{k}', (HULL_R * 0.86 * math.cos(a), HULL_R * 0.86 * math.sin(a), HULL_Z1 + 0.55),
              (0.55, 0.06, 0.32), win, rot=(0, 0, a - math.pi / 2)))
    P(cylinder('l-mast', (0.8, -0.6, HULL_Z1 + 2.4), 0.04, 2.2, steel))
    P(cylinder('l-dish', (-0.9, 0.4, HULL_Z1 + 1.65), 0.5, 0.08, steel, rot=(0.5, 0.3, 0), r2=0.15))
    if lights:
        for k in range(4):
            a = k * math.pi / 2
            loc = (3.3 * math.cos(a), 3.3 * math.sin(a), HULL_Z0 + 0.2)
            P(sphere(f'l-flood{k}', loc, 0.12, emit_mat('flood', (1.0, 0.97, 0.9), 40.0), 12, 6))
            data = bpy.data.lights.new(f'flood{k}', 'SPOT')
            data.energy = 9000.0
            data.spot_size = math.radians(38)
            data.spot_blend = 0.4
            data.shadow_soft_size = 0.1
            data.color = (1.0, 0.96, 0.9)
            sp = link(bpy.data.objects.new(f'flood{k}', data))
            sp.parent = root
            sp.location = loc
            sp.rotation_euler = (math.radians(28), 0, a + math.pi / 2)
    # The ramp: a plate hinged at the door's sill.
    sill = Vector((0, apothem, HULL_Z0))
    ramp_len = 4.6
    angle = math.asin(min(1.0, (HULL_Z0) / ramp_len)) if open_ramp else math.radians(-90)
    ramp = P(box('l-ramp', (0, 0, 0), (2.1, ramp_len, 0.14), hull))

    def set_ramp(angle):
        ramp.location = sill + Vector((0, math.cos(angle) * ramp_len / 2, -math.sin(angle) * ramp_len / 2))
        ramp.rotation_euler = (-angle, 0, 0)

    set_ramp(angle)
    handles['ramp'] = set_ramp
    handles['ramp_open'] = math.asin(min(1.0, HULL_Z0 / ramp_len))
    if interior:
        red = (1.0, 0.12, 0.06)
        ribs = plain('l-rib', (0.08, 0.08, 0.08), 0.5, 0.7)
        for k in range(4):
            y = -2.4 + k * 1.4
            for sx in (-1, 1):
                P(box(f'l-rib{k}{sx}', (sx * (apothem - 0.35), y, HULL_Z0 + 2.1), (0.18, 0.18, 4.0), ribs))
            P(box(f'l-ribtop{k}', (0, y, HULL_Z1 - 0.1), (2 * apothem - 0.6, 0.18, 0.18), ribs))
        for sx in (-1, 1):
            P(box(f'l-seat{sx}', (sx * (apothem - 0.75), -0.6, HULL_Z0 + 0.65), (0.55, 3.6, 0.12), ribs))
            P(box(f'l-locker{sx}', (sx * (apothem - 0.45), -2.2, HULL_Z0 + 1.6), (0.6, 1.2, 2.6), dark))
            P(point(f'l-red{sx}', (sx * 2.2, -1.5, HULL_Z1 - 0.6), 70.0, red, 0.08))
            P(sphere(f'l-redlamp{sx}', (sx * 2.3, -1.5, HULL_Z1 - 0.45), 0.06, emit_mat('redlamp', red, 30.0), 8, 4))
        for k in range(6):
            P(box(f'l-strap{k}', (-1.2 + 0.5 * k, -0.8, HULL_Z1 - 0.3 - 0.4 * (k % 2)), (0.05, 0.02, 0.6), dark))
        # A working hold: strip lights, cargo lashed down, helmets on the bench, a lit panel by the door.
        # Lining: quilted grey panels inside the hull and a ceiling, so the hold reads as a cabin.
        lining = surface('l-lining', 'painted_metal_shutter', size=0.9, tint=(0.36, 0.37, 0.36))
        for k in range(1, 8):
            a = 2 * math.pi * k / 8 + math.pi / 2
            r = apothem - 0.14
            P(box(f'l-lining{k}', (r * math.cos(a), r * math.sin(a), (HULL_Z0 + HULL_Z1) / 2),
                  (side - 0.1, 0.04, HULL_Z1 - HULL_Z0 - 0.2), lining, rot=(0, 0, a - math.pi / 2)))
        P(box('l-ceiling', (0, 0, HULL_Z1 - 0.04), (2 * apothem - 0.3, 2 * apothem - 0.3, 0.04), lining))
        hh = HULL_Z1 - HULL_Z0
        P(box('l-lining-head', (0, apothem - 0.14, HULL_Z0 + 2.5 + (hh - 2.5) / 2), (side - 0.1, 0.04, hh - 2.5), lining))
        for sx in (-1, 1):
            P(box(f'l-lining-jamb{sx}', (sx * (1.1 + (side / 2 - 1.1) / 2), apothem - 0.14, HULL_Z0 + 1.25),
                  (side / 2 - 1.1, 0.04, 2.5), lining))
        P(point('l-fill', (0, -1.4, HULL_Z1 - 0.5), 60.0, (0.8, 0.86, 1.0), 0.6))
        strip = emit_mat('l-strip', (0.85, 0.9, 1.0), 5.0)
        for sx in (-1, 1):
            P(box(f'l-striplight{sx}', (sx * 1.6, -0.4, HULL_Z1 - 0.12), (0.08, 4.4, 0.04), strip))
        crate = surface('l-crate', 'painted_metal_shutter', size=0.8, tint=(0.32, 0.36, 0.26))
        for j, (x, y, z, w_, d_, h_) in enumerate(((-2.0, -2.2, 0.35, 0.9, 0.7, 0.7), (-2.0, -1.4, 0.3, 0.8, 0.7, 0.6),
                                                    (-1.95, -2.2, 1.05, 0.7, 0.6, 0.55), (2.0, 0.6, 0.3, 0.7, 0.9, 0.6))):
            P(box(f'l-crate{j}', (x, y, HULL_Z0 + 0.16 + z), (w_, d_, h_), crate, bevel=0.02))
        visor = plain('l-visor', (0.02, 0.02, 0.025), 0.05, 0.6)
        shell = plain('l-helmet', (0.75, 0.74, 0.7), 0.4)
        for j, y in enumerate((-1.6, -0.9)):
            P(sphere(f'l-helmet{j}', (2.45, y, HULL_Z0 + 0.92), 0.17, shell, 24, 12))
            P(sphere(f'l-visor{j}', (2.35, y, HULL_Z0 + 0.93), 0.13, visor, 24, 12))
        panel = plain('l-panel', (0.04, 0.04, 0.04), 0.5, 0.5)
        P(box('l-panel', (-1.35, apothem - 0.35, HULL_Z0 + 1.45), (0.5, 0.12, 0.7), panel))
        for j, col in enumerate(((1.0, 0.55, 0.1), (0.2, 1.0, 0.4), (1.0, 0.55, 0.1))):
            P(box(f'l-screen{j}', (-1.35 + (j - 1) * 0.14, apothem - 0.42, HULL_Z0 + 1.55 - 0.12 * (j % 2)),
                  (0.1, 0.01, 0.07), emit_mat(f'screen{j}', col, 6.0)))
        floor = surface('l-floor', 'metal_plate', size=0.8, tint=(0.25, 0.25, 0.24))
        P(box('l-deck', (0, 0, HULL_Z0 + 0.17), (2 * apothem - 0.4, 2 * apothem - 0.4, 0.02), floor))
    return handles


def plume_mat(burn):
    """Exhaust in air: hot and white at the throat, orange and thinning away from it, see-through."""
    m, nt, out = new_mat('plume')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=tc.outputs['Object'])
    t = map_range(nt, sep.outputs['Z'], 2.1, -2.1)  # 0 at the throat, 1 at the tail
    col = mix_rgb(nt, t, (1.0, 0.9, 0.75), (1.0, 0.35, 0.08))
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.4
    edge = math_op(nt, 'SUBTRACT', 1.0, lw.outputs['Facing'])
    bv = nt.nodes.new('ShaderNodeValue')
    bv.name = 'burn'
    bv.outputs[0].default_value = burn
    strength = math_op(nt, 'MULTIPLY', math_op(nt, 'MULTIPLY', math_op(nt, 'SUBTRACT', 1.0, t), edge),
                       math_op(nt, 'MULTIPLY', bv.outputs[0], 16.0))
    flick = noise(nt, tc.outputs['Object'], 3.0, 4, 0.6)
    strength = math_op(nt, 'MULTIPLY', strength, map_range(nt, flick, 0.3, 0.7, 0.5, 1.3))
    em = node(nt, 'ShaderNodeEmission', Strength=strength)
    nt.links.new(col, em.inputs['Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs['BSDF'], add.inputs[0])
    nt.links.new(em.outputs['Emission'], add.inputs[1])
    nt.links.new(add.outputs['Shader'], out.inputs['Surface'])
    return m


def walker(origin, rot_z, scale, eye=2.0):
    """A machine still standing where it stopped: tall, two-legged, head down."""
    armor = surface('w-armor', 'metal_plate', size=2.4, over='concrete_moss',
                    over_size=1.5, over_amount=1.0, over_lo=0.62, up_bias=0.9, tint=(0.2, 0.21, 0.2))
    joint = surface('w-joint', 'rusty_metal_02', size=1.5, tint=(0.4, 0.36, 0.32))
    lens = plain('w-lens', (0.01, 0.01, 0.01), 0.05, emit=(1.0, 0.05, 0.03), strength=eye)
    root = empty('walker', origin)
    root.rotation_euler = (0, 0, math.radians(rot_z))
    root.scale = (scale,) * 3

    def P(ob):
        ob.parent = root
        return ob

    for sx in (-1, 1):
        P(box(f'w-foot{sx}', (0.9 * sx, -0.3, 0.2), (0.9, 1.6, 0.4), armor, bevel=0.06))
        P(segment(f'w-shin{sx}', (0.9 * sx, 0, 0.4), (0.85 * sx, -0.5, 2.6), 0.32, armor, r2=0.38))
        P(sphere(f'w-knee{sx}', (0.85 * sx, -0.5, 2.6), 0.4, joint, 20, 10))
        P(segment(f'w-thigh{sx}', (0.85 * sx, -0.5, 2.6), (0.65 * sx, 0.2, 4.6), 0.42, armor))
        P(sphere(f'w-shoulder{sx}', (1.55 * sx, 0.1, 6.6), 0.5, joint, 20, 10))
        P(segment(f'w-arm{sx}', (1.6 * sx, 0.1, 6.5), (1.8 * sx, -0.2, 4.6), 0.28, armor))
        P(segment(f'w-fore{sx}', (1.8 * sx, -0.2, 4.6), (1.7 * sx, -0.8, 3.0), 0.32, armor, r2=0.24))
    P(box('w-pelvis', (0, 0.15, 4.75), (1.7, 1.1, 0.8), joint, bevel=0.05))
    P(box('w-torso', (0, 0.0, 5.9), (2.4, 1.5, 1.9), armor, rot=(0.25, 0, 0), bevel=0.1))
    P(box('w-pack', (0, 0.95, 6.0), (1.8, 0.7, 1.5), joint, rot=(0.25, 0, 0), bevel=0.06))
    hr = (math.radians(30), 0, 0)
    P(box('w-head', (0, -0.55, 7.05), (0.85, 0.95, 0.55), armor, rot=hr, bevel=0.08))
    P(cylinder('w-eye', (0, -1.0, 6.88), 0.08, 0.06, lens, rot=(math.radians(120), 0, 0)))
    return root


def city(rng, keep_out):
    """Blocks of the town around the street, for the aerial shot: plastered blocks of three to eight
    floors in one mesh, water tanks on the roofs, trees where the courtyards went wild."""
    plaster = facade_mat('city-plaster', 'worn_mossy_plasterwall', size=4.0, cell=(3.5, 3.2),
                         win=(1.6, 1.5), broken=0.4)
    roof = surface('city-roof', 'concrete_moss', size=6.0, over='forest_leaves_02', over_size=4.0,
                   over_amount=0.9, over_lo=0.55)
    tank = plain('city-tank', (0.02, 0.022, 0.02), 0.55)
    b = Builder()
    trees = []
    pitch, street = 68.0, 16.0
    for gx in range(-10, 11):
        for gy in range(-7, 16):
            x0, y0 = gx * pitch, gy * pitch
            if any(a <= x0 + pitch / 2 <= b2 and c <= y0 + pitch / 2 <= d for a, b2, c, d in keep_out):
                continue
            size = pitch - street
            park = rng.random() < 0.12
            if park:
                for _ in range(rng.randint(10, 22)):
                    trees.append(((x0 + rng.uniform(0, size), y0 + rng.uniform(0, size), 0),
                                  (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(0, 6.28)),
                                  rng.uniform(1.8, 3.2)))
                continue
            n = rng.choice((2, 3, 3, 4))
            cell = size / n
            for i in range(n):
                for j in range(n):
                    if 0 < i < n - 1 and 0 < j < n - 1:
                        if rng.random() < 0.6:
                            trees.append(((x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell, 0),
                                          (0, 0, rng.uniform(0, 6.28)), rng.uniform(2.0, 3.0)))
                        continue
                    if rng.random() < 0.12:
                        continue
                    floors = rng.choice((3, 4, 4, 5, 6, 8))
                    h = 3.9 + floors * 3.2
                    if rng.random() < 0.07:  # collapsed
                        h *= rng.uniform(0.25, 0.5)
                    cx, cy = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
                    bw, bd = cell * rng.uniform(0.8, 0.95), cell * rng.uniform(0.8, 0.95)
                    b.box((cx, cy, h / 2), (bw, bd, h), 0)
                    b.box((cx, cy, h + 0.4), (bw + 0.3, bd + 0.3, 0.8), 1)
                    for _ in range(rng.randint(0, 3)):
                        b.cyl((cx + rng.uniform(-bw / 3, bw / 3), cy + rng.uniform(-bd / 3, bd / 3), h + 1.2), 0.65, 1.5, 2, 10)
            for k in range(rng.randint(2, 6)):
                trees.append(((x0 - street / 2 + rng.uniform(-3, 3), y0 + rng.uniform(0, pitch), 0),
                              (0, 0, rng.uniform(0, 6.28)), rng.uniform(1.8, 2.8)))
    b.build('city', [plaster, roof, tank], (0, 0, 0), 0)
    scatter('island_tree_01', trees)
    ground = surface('ground', 'brown_mud_leaves_01', size=6.0, over='forest_leaves_02', over_size=5.0,
                     over_amount=1.0, over_lo=0.5, tint=(0.6, 0.6, 0.55))
    mesh_obj('ground', [(-900, -700, -0.02), (900, -700, -0.02), (900, 1300, -0.02), (-900, 1300, -0.02)],
             [(0, 1, 2, 3)], ground)
    # The river, east of town.
    m, nt, out = new_mat('river')
    geo_n = nt.nodes.new('ShaderNodeNewGeometry')
    w = node(nt, 'ShaderNodeBsdfPrincipled', Roughness=0.06)
    w.inputs['Base Color'].default_value = (0.02, 0.03, 0.025, 1)
    bump = node(nt, 'ShaderNodeBump', Strength=0.15, Height=noise(nt, geo_n.outputs['Position'], 0.08, 4, 0.5))
    nt.links.new(bump.outputs['Normal'], w.inputs['Normal'])
    nt.links.new(w.outputs['BSDF'], out.inputs['Surface'])
    mesh_obj('river', [(560, -700, 0.05), (820, -700, 0.05), (760, 1300, 0.05), (520, 1300, 0.05)],
             [(0, 1, 2, 3)], m)


def clouds_box(center, size, density, scale, cover):
    """A cloud deck: noise thresholded into separate masses, thinning at its top and bottom."""
    m, nt, out = new_mat('clouds-deck')
    geo_n = nt.nodes.new('ShaderNodeNewGeometry')
    pos = geo_n.outputs['Position']
    n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=8.0, Roughness=0.55)
    nt.links.new(pos, n.inputs['Vector'])
    d = map_range(nt, n.outputs['Fac'], cover, cover + 0.12)
    sep = node(nt, 'ShaderNodeSeparateXYZ', Vector=pos)
    z0, z1 = center[2] - size[2] / 2, center[2] + size[2] / 2
    edge = math_op(nt, 'MINIMUM', map_range(nt, sep.outputs['Z'], z0, z0 + size[2] * 0.3),
                   map_range(nt, sep.outputs['Z'], z1, z1 - size[2] * 0.4))
    d = math_op(nt, 'MULTIPLY', math_op(nt, 'MULTIPLY', d, edge), density)
    v = node(nt, 'ShaderNodeVolumePrincipled', Anisotropy=0.5, Density=d)
    v.inputs['Color'].default_value = (0.92, 0.93, 0.95, 1)
    nt.links.new(v.outputs['Volume'], out.inputs['Volume'])
    return box('clouds', center, size, m)


LAND = Vector((0.0, 52.0, 0.0))  # where the lander touches down
MACH = (ROAD_W + 1.8, 72.0, 0.15)  # the machine sat against the right-hand wall
WALK = 1.35  # metres per second
STRIDE = 1.4  # metres per full stride (two steps): a careful walk, about 115 steps a minute


def street_world(rng, lights=False, lander_z=0.0, interior=False, open_ramp=True):
    """Everything the street shots share: the street, the lab, the props, what grew, the machine,
    the lander where it came down, and the haze."""
    world_hdri('kloofendal_misty_morning_puresky', 0.9, rotate=150, tint=(0.92, 0.97, 1.0))
    sun((0.45, -0.35, -0.82), 4.5, (1.0, 0.86, 0.68), angle=1.0)
    build_street(rng)
    build_lab(rng)
    props(rng)
    overgrowth(rng)
    m = machine(MACH, -90, 1.25, eye=3.0)
    L = lander((LAND.x, LAND.y, lander_z), 0, open_ramp=open_ramp, lights=lights, interior=interior)
    haze_box('haze', (0, 60, 19), (90, 200, 40), 0.009, (0.82, 0.88, 0.86), 0.6, falloff=22.0)
    return m, L


def heading_of(d):
    """Heading (radians, 0 = +Y) of a direction in the ground plane."""
    return math.atan2(-d.x, d.y)


TURN = 1.2  # metres either side of a corner over which a walker turns


def path_at(points, dist):
    """Position and heading at a distance along a route (fx.route: corners rounded, stops at the
    end)."""
    return fx.route(points, dist, TURN)


def distances(frames, speed):
    """Distance walked at each frame for a speed profile speed(t) in m/s."""
    out, d = [], 0.0
    for f in range(frames):
        out.append(d)
        d += speed(f / (frames - 1)) / FPS
    return out


def behind(pos, heading, back=2.6, right=0.6, up=1.55, ahead=7.0, look=1.15):
    """A third-person camera: over the right shoulder, looking down the way the figure goes."""
    fwd = Vector((-math.sin(heading), math.cos(heading), 0.0))
    side = Vector((math.cos(heading), math.sin(heading), 0.0))
    eye = pos - fwd * back + side * right + Vector((0, 0, up))
    target = pos + fwd * ahead + Vector((0, 0, look))
    return eye, target


def shot_descent():
    """Six seconds: the lander comes down into the street on its engines and touches down; the
    machine in the foreground lifts its head to watch it."""
    global SCENE
    SCENE = reset_scene()
    rng = random.Random(11)
    SCENE.view_settings.exposure = -0.3
    m, L = street_world(rng, lights=True, lander_z=20.0, open_ramp=False)
    root = L['root']
    dust = haze_box('dust', (LAND.x, LAND.y, 3.0), (30, 30, 6.0), 0.02, (0.75, 0.66, 0.55), 0.35, falloff=2.2)
    dust_d = dust.data.materials[0].node_tree.nodes['density'].outputs[0]
    cam = camera((1.2, 80.0, 1.5), (0.2, LAND.y, 7.0), lens=28, fstop=4, focus=28.0)
    strobe = L['strobe'].node_tree.nodes['Emission'].inputs['Strength']
    wash = fx.downwash()
    flows = []
    if ULTRA or OPTS['fluid_res']:
        # Between the facades (the domain's walls are the street's), over the pad and down the road.
        half = ROAD_W + 3.6
        res = OPTS['fluid_res'] or 256
        dom, flows = fx.landing_dust((0.0, LAND.y, 8.0), (2 * half, 44.0, 16.0),
                                     os.path.join(WORK, 'descent-dust'), res)
        dom.modifiers['Fluid'].domain_settings.cache_frame_start = 1
        dom.modifiers['Fluid'].domain_settings.cache_frame_end = 144
        BAKE.append(dom)

    def step(t):
        land = ease_out(span(t, 0.0, 0.82))
        root.location = (0.9 * (1 - land), LAND.y, 20.0 * (1 - land))
        root.rotation_euler = (0, 0, math.radians(8 * (1 - land)))
        burn = 0.9 * (1 - span(t, 0.8, 0.9))
        L['burn'].default_value = burn
        L['glow'].default_value = 60.0 * burn
        L['plume_light'].data.energy = 9000.0 * burn
        for j in L['jets']:
            j.scale = (1.0, 1.0, max(0.01, burn / 0.9))
        dust_d.default_value = 0.02 + 0.07 * span(t, 0.25, 0.85) - 0.02 * span(t, 0.9, 1.0)
        # The blast reaches the ground below ~14 m: the plants flatten away from it and the pad
        # throws up dust, both as strong as the burn and as close as the engines.
        z = root.location.z
        near = max(0.0, min(1.0, (14.0 - z) / 10.0))
        push = (burn / 0.9) * near
        wash.location = (root.location.x, root.location.y, 0.0)
        wash.scale = (math.radians(38) * push,) * 3
        for f in flows:
            f.density = 0.7 * push
        strobe.default_value = 300.0 if (t * 6) % 1.0 < 0.06 else 0.0
        cam.location = Vector((1.2, 80.0, 1.5)) + shake(t * 6, 0.02 + 0.03 * span(t, 0.6, 0.85))
        look_at(cam, (0.2, LAND.y, 4.6 + 0.55 * root.location.z))
        watch(m, Vector(root.location) + Vector((0, 0, 4.0)), ease(span(t, 0.2, 0.55)))
        m['eye'].default_value = 3.0 + 9.0 * span(t, 0.45, 0.7)

    keys = [(root, 'location'), (root, 'rotation_euler'), (L['burn'], 'default_value'),
            (L['glow'], 'default_value'), (L['plume_light'].data, 'energy'), (dust_d, 'default_value'),
            (strobe, 'default_value'), (cam, 'location'), (cam, 'rotation_euler'),
            (m['eye'], 'default_value'), (m['neck'], 'rotation_euler')]
    keys += [(j, 'scale') for j in L['jets']]
    keys += [(wash, 'location'), (wash, 'scale')] + [(f, 'density') for f in flows]
    return 144, step, keys


def shot_ramp():
    """Eight seconds in the hold, over the crew member's shoulder: the ramp goes down, daylight comes
    in, and they walk down it into the street."""
    global SCENE
    SCENE = reset_scene()
    rng = random.Random(11)
    SCENE.view_settings.exposure = -0.2
    m, L = street_world(rng, interior=True, open_ramp=False)
    ramp_ob = next(o for o in L['root'].children if o.name.startswith('l-ramp'))
    haze_box('dust', (LAND.x, LAND.y, 4.4), (6.0, 6.0, 4.0), 0.06, (0.9, 0.88, 0.84), 0.7)
    fig = C.Crew('crew')
    apothem = HULL_R * math.cos(math.pi / 8)
    deck = HULL_Z0 + 0.18
    foot = apothem + 4.6 * math.cos(L['ramp_open'])
    walk_from = 0.4
    n = 192
    dist = distances(n, lambda t: 0.0 if t < walk_from else WALK * min(1.0, (t - walk_from) / 0.08))
    cam = camera((0.5, LAND.y - 1.2, deck + 1.45), (0.0, 90.0, 2.8), lens=26, fstop=4.0, focus=3.0)

    def ground(y_local):
        """Height of the floor under the figure: the deck, the ramp, the street."""
        if y_local <= apothem:
            return deck
        if y_local <= foot:
            return HULL_Z0 - (y_local - apothem) * math.tan(L['ramp_open']) + 0.06
        return 0.0

    global STEPS
    # Dust only off the street: the deck and the ramp are swept metal.
    STEPS = fx.Steps(fig, lambda p: ground(p.y - LAND.y),
                     lambda p: 0.8 if p.y - LAND.y > foot else 0.0)

    def step(t):
        f = round(t * (n - 1))
        k = ease(span(t, 0.05, 0.42))
        L['ramp'](math.radians(-90) + (L['ramp_open'] + math.radians(90)) * k)
        y = 1.0 + dist[f]
        z = ground(y)
        C.place(fig, (LAND.x + 0.1, LAND.y + y, z), 0.0)
        amount = min(1.0, max(0.0, (t - walk_from) / 0.08))
        fig.stride(dist[f], lambda x: (Vector((LAND.x + 0.1, LAND.y + 1.0 + x, 0.0)), 0.0), STRIDE,
                   amount, (math.radians(-6) * (1 - amount), math.radians(-6) * (1 - amount)),
                   ground=lambda p: ground(p.y - LAND.y), breath=t * 14)
        pos = Vector((LAND.x + 0.1, LAND.y + y, z))
        eye, target = behind(pos, 0.0, back=2.2, right=0.55, up=1.5, ahead=8.0, look=0.6)
        cam.location = eye + shake(t * 8, 0.008)
        look_at(cam, target)
        cam.data.dof.focus_distance = (pos + Vector((0, 0, 1.3)) - cam.location).length

    keys = [(ramp_ob, 'location'), (ramp_ob, 'rotation_euler'), (cam, 'location'),
            (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance')] + fig.keys()
    return n, step, keys


def shot_street():
    """Twelve seconds, following up the street. The machine against the wall wakes as they pass:
    its eye flares, its head turns, and a red scan beam sweeps the road. They freeze and kill
    their lamp; the beam crosses them and holds on them; then the machine loses interest and
    powers down, and they go on."""
    global SCENE, STEPS
    SCENE = reset_scene()
    rng = random.Random(11)
    SCENE.view_settings.exposure = -0.45
    m, L = street_world(rng)
    # Denser air round the machine, so its beam shows.
    haze_box('scan-haze', (3.0, 67.5, 2.6), (11.0, 13.0, 5.2), 0.022, (0.8, 0.82, 0.8), 0.5)
    fig = C.Crew('crew')
    n = 288
    route = [(0.2, LAND.y + 7.6), (0.9, 66.0), (1.4, 72.0), (1.0, 80.0)]

    def pace(t):
        """Walking, slowing to a stop, frozen while the beam is up, then walking on."""
        if t < 0.30:
            return 1.0
        if t < 0.36:
            return 1.0 - ease(span(t, 0.30, 0.36))
        if t < 0.64:
            return 0.0
        return ease(span(t, 0.64, 0.70))

    dist = distances(n, lambda t: WALK * pace(t))
    cam = camera((0.8, 57.0, 1.6), (0.0, 90.0, 1.5), lens=28, fstop=4.0, focus=3.0)
    STEPS = fx.Steps(fig, 0.0, 0.8)
    head_at = Vector((MACH[0], MACH[1], 3.6))
    scan = m['scan']

    def step(t):
        f = round(t * (n - 1))
        pos, hd = path_at(route, dist[f])
        C.place(fig, pos, hd)
        # They look at it as it wakes, keep their eyes on it while frozen, and kill the lamp.
        look = math.radians(-50) * ease(span(t, 0.24, 0.32)) * (1 - ease(span(t, 0.66, 0.78)))
        # As the beam comes they sink, weight down, and hold it; they come up once it has gone.
        fig.crouch = 0.55 * ease(span(t, 0.33, 0.40)) * (1 - ease(span(t, 0.63, 0.71)))
        fig.stride(dist[f], lambda x: path_at(route, x), STRIDE, pace(t), (look, math.radians(6)), breath=t * 18)
        fig.light(1.0 - ease(span(t, 0.34, 0.37)) + ease(span(t, 0.66, 0.70)))
        # Behind them; closer and lower while they hold still, half turned to the machine.
        hold = ease(span(t, 0.30, 0.38)) * (1 - ease(span(t, 0.64, 0.74)))
        eye, target = behind(pos, hd, back=2.7 - 0.5 * hold, right=0.65 + 0.15 * hold,
                             up=1.55 - 0.15 * hold)
        cam.location = eye + shake(t * 10, 0.01)
        look_at(cam, target.lerp(head_at, 0.38 * hold))
        cam.data.dof.focus_distance = (pos + Vector((0, 0, 1.3)) - cam.location).length
        # The machine wakes and turns to them, sweeps the road across them, holds on them, then
        # loses interest: the beam goes out and the head sinks.
        side = Vector((math.cos(hd), math.sin(hd), 0.0))
        road = pos + side * (3.2 * math.cos(math.pi * span(t, 0.38, 0.58))) + Vector((0, 0, 0.3))
        them = pos + Vector((0, 0, 1.4))
        if t < 0.58:
            tgt = them.lerp(road, ease(span(t, 0.34, 0.38)))
        else:
            tgt = road.lerp(them, ease(span(t, 0.58, 0.62)))
        aim(m, tgt, ease(span(t, 0.22, 0.34)) * (1 - 0.55 * ease(span(t, 0.62, 0.72))))
        k = span(t, 0.22, 0.30)
        on = (3.0 + 15.0 * k) * (1.0 if k in (0.0, 1.0) else 0.3 + 0.7 * (math.sin(k * 61.0) > 0.2))
        if t > 0.62:
            d = span(t, 0.62, 0.68)
            on = (18.0 * (1 - d) + 1.2 * d) * (0.25 if 0 < d < 1 and math.sin(d * 47.0) < -0.3 else 1.0)
        m['eye'].default_value = on
        beam = ease(span(t, 0.34, 0.37)) * (1 - span(t, 0.60, 0.63))
        scan.energy = 5000.0 * beam * (0.92 + 0.08 * math.sin(t * 90.0))

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'),
            (m['eye'], 'default_value'), (m['neck'], 'rotation_euler'), (scan, 'energy')] + fig.keys()
    return n, step, keys


def shot_approach():
    """Eight seconds, the camera ahead of them looking back: the lamp beam in the haze, the lander's
    lights far behind down the street, and the machine that went dark lighting again and turning
    its head after them."""
    global SCENE
    SCENE = reset_scene()
    rng = random.Random(11)
    SCENE.view_settings.exposure = -0.4
    m, L = street_world(rng, lights=True)
    fig = C.Crew('crew')
    n = 192
    route = [(1.0, 76.0), (0.2, 84.0), (-0.6, 88.0)]
    dist = distances(n, lambda t: WALK)
    cam = camera((0.0, 82.0, 1.3), (0.0, 70.0, 1.3), lens=32, fstop=2.8, focus=4.0)
    global STEPS
    STEPS = fx.Steps(fig, 0.0, 0.8)

    def step(t):
        f = round(t * (n - 1))
        pos, hd = path_at(route, dist[f])
        C.place(fig, pos, hd)
        fig.stride(dist[f], lambda x: path_at(route, x), STRIDE, 1.0, (math.radians(8) * math.sin(t * 3), 0.0))
        fwd = Vector((-math.sin(hd), math.cos(hd), 0.0))
        side = Vector((math.cos(hd), math.sin(hd), 0.0))
        cam.location = pos + fwd * 4.0 - side * 1.1 + Vector((0, 0, 1.2)) + shake(t * 8, 0.012)
        look_at(cam, pos + Vector((0, 0, 1.25)) - fwd * 1.5)
        cam.data.dof.focus_distance = (pos + Vector((0, 0, 1.3)) - cam.location).length
        # Behind them the machine that went dark lights again and turns to follow.
        watch(m, pos + Vector((0, 0, 1.7)), 0.45 + 0.55 * ease(span(t, 0.35, 0.95)))
        k = span(t, 0.5, 0.9)
        m['eye'].default_value = 1.2 + 10.0 * k * (1.0 if k in (0.0, 1.0) else 0.4 + 0.6 * (math.sin(k * 53.0) > 0))

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'),
            (m['neck'], 'rotation_euler'), (m['eye'], 'default_value')] + fig.keys()
    return n, step, keys


LAB_ROOM = (DOOR_X, LAB_Y + 14.2)  # where lab.py's origin sits: its corridor starts at the lobby's back


def place_lab_room():
    """The lab itself behind the entrance (lab.py --shots room): its corridor runs from the lobby
    into the room, dark but for the daylight from its high windows and the transmitter's beacon,
    so from the street the doors look into the real place the next shots are in. Returns the
    beacon's strength (to blink it) and a red light at it (its spill)."""
    path = os.path.join(WORK, 'lab-room.blend')
    if not os.path.exists(path):
        print('[arrival] no lab room (run lab.py --shots room); the doors show a dark lobby', flush=True)
        return None, point('lab-inside', (DOOR_X + 0.8, LAB_Y + 2.4, 2.8), 3.0, (1.0, 0.07, 0.04), 0.06)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    root = link(bpy.data.objects.new('lab-room', None))
    root.location = (LAB_ROOM[0], LAB_ROOM[1], 0.0)
    beacon, at = None, None
    for ob in dst.objects:
        if ob is None:
            continue
        SCENE.collection.objects.link(ob)
        if ob.parent is None:
            ob.parent = root
        for slot in getattr(ob, 'material_slots', []):
            m = slot.material
            if m and m.get('archive_beacon') and m.node_tree:
                for nd in m.node_tree.nodes:
                    if nd.type == 'EMISSION':
                        beacon = nd.inputs['Strength']
                at = ob
    bpy.context.view_layer.update()
    spot = (sum((at.matrix_world @ Vector(c) for c in at.bound_box), Vector()) / 8) if at else         Vector((DOOR_X, LAB_Y + 14.0, 2.5))
    return beacon, point('lab-inside', tuple(spot + Vector((0, -0.3, 0.1))), 1.5, (1.0, 0.07, 0.04), 0.05)


def shot_door():
    """Nine seconds: under the canopy to the door with the light behind it; a hand on the glass,
    the door swings in, and they step through. The camera stays outside."""
    global SCENE
    SCENE = reset_scene()
    rng = random.Random(11)
    SCENE.view_settings.exposure = -0.4
    m, L = street_world(rng)
    ivy(IVY_RNG, LAB_Y, -1, -LAB_W / 2, DOOR_X - 4.2, LAB_H, 26, axis='y', out=0.8)
    ivy(IVY_RNG, LAB_Y, -1, DOOR_X + 4.2, LAB_W / 2, LAB_H, 30, axis='y', out=0.8)
    beacon, inside = place_lab_room()
    hinge = bpy.data.objects['lab-door-hinge']
    fig = C.Crew('crew')
    n = 216
    door_x = DOOR_X + 0.75
    route = [(-0.5, 88.0), (door_x + 0.3, 93.5), (door_x, LAB_Y + 0.4), (door_x, LAB_Y + 3.0)]
    stop = (Vector((-0.5, 88.0, 0)) - Vector((door_x + 0.3, 93.5, 0))).length + \
        (Vector((door_x + 0.3, 93.5, 0)) - Vector((door_x, LAB_Y + 0.4, 0))).length

    def speed(t):
        if t < 0.66:
            return WALK
        if t < 0.8:  # at the door: the push
            return 0.15
        return WALK * 0.9

    dist = distances(n, speed)
    cam = camera((0.0, 85.0, 1.6), (door_x, LAB_Y + 2, 1.6), lens=28, fstop=4.0, focus=4.0)
    sign = Vector((DOOR_X, LAB_Y - 4.12, 3.7))
    global STEPS
    STEPS = fx.Steps(fig, 0.0, 0.6)

    def step(t):
        f = round(t * (n - 1))
        d = dist[f]
        pos, hd = path_at(route, d)
        C.place(fig, pos, hd)
        # They look up at the name over the door as they come in under it, then down to the door.
        up = 1.0 - ease(span(t, 0.12, 0.42))
        # At the door they all but stop, push it with the left hand, and walk through.
        slow = math.sin(math.pi * span(t, 0.6, 0.88))
        fig.stride(d, lambda x: path_at(route, x), STRIDE, 1.0 - 0.75 * slow,
                   (math.radians(-10) * up, math.radians(24) * up))
        fig.reach(math.sin(math.pi * span(t, 0.64, 0.84)), 'L', 80.0)
        # The door: ajar, then pushed wide.
        hinge.rotation_euler = (0, 0, math.radians(-38 - 57 * ease(span(t, 0.7, 0.86))))
        # The camera follows, then holds outside the canopy as they go in.
        eye, target = behind(pos, hd, back=2.8, right=0.7, up=1.5, ahead=5.0, look=1.2)
        hold = Vector((door_x + 0.9, LAB_Y - 3.6, 1.65))
        k = ease(span(t, 0.62, 0.9))
        cam.location = eye.lerp(hold, k) + shake(t * 9, 0.01)
        look_at(cam, target.lerp(sign, 0.55 * up).lerp(Vector((door_x, LAB_Y + 3.0, 1.4)), k))
        cam.data.dof.focus_distance = (pos + Vector((0, 0, 1.3)) - cam.location).length
        # The transmitter's beacon deep in the room, blinking as it does in the lab's own shots.
        on = (t * 9.0) % 1.5 < 0.12
        inside.data.energy = 18.0 if on else 1.5
        if beacon is not None:
            beacon.default_value = 10.0 if on else 0.6
        # Under the canopy the camera opens up, as an eye does in the dark.
        SCENE.view_settings.exposure = -0.4 + 0.75 * ease(span(t, 0.3, 0.62))

    keys = [(cam, 'location'), (cam, 'rotation_euler'), (cam.data.dof, 'focus_distance'),
            (hinge, 'rotation_euler'), (inside.data, 'energy'), (SCENE.view_settings, 'exposure')] + fig.keys()
    if beacon is not None:
        keys.append((beacon, 'default_value'))
    return n, step, keys


# ---------------------------------------------------------------------------------------------
# Running a shot: a still at time t (0 = first frame, 1 = last), or the whole move as frames,
# keyed so the camera and anything moving get motion blur, then encoded for the web.

FPS = 24


STEPS = None  # the walking shots' footstep tracker (fx.Steps), sampled every frame by run()
BAKE = []  # simulation domains to bake before rendering


def frames_to_render(frames):
    """--frames a-b (or from --start) to the end, then every Nth of them for --slice k/N."""
    if OPTS['frames']:
        a, b = (int(v) for v in OPTS['frames'].split('-'))
        sel = range(a, min(b, frames - 1) + 1)
    else:
        sel = range(OPTS['start'], frames)
    k, n = (int(v) for v in OPTS['slice'].split('/'))
    return [f for f in sel if f % n == k]


def exr(scene):
    """The HDR masters' frames: scene-linear OpenEXR, half float, DWAA (visually lossless, a tenth of
    the size), the film look composited in; the view transform is applied when they are graded
    for each display (blender/master.py)."""
    s = scene.render.image_settings
    s.file_format = 'OPEN_EXR'
    s.color_depth = '16'
    s.exr_codec = 'DWAA'
    scene.render.use_compositing = True
    fx.bake_exposure(scene)


def render_frames(name, d, frames):
    os.makedirs(d, exist_ok=True)
    ext = {'JPEG': 'jpg', 'OPEN_EXR': 'exr'}.get(SCENE.render.image_settings.file_format, 'png')
    for f in frames_to_render(frames):
        path = os.path.join(d, f'{f:04d}.{ext}')
        if OPTS['stage'] == 'render' and os.path.exists(path) and os.path.getsize(path) > 0:
            continue  # done by an earlier run
        SCENE.frame_set(f + 1)
        SCENE.render.filepath = path
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[arrival] {name} {f + 1}/{frames} {time.time() - t:.1f}s', flush=True)


def finish_scene():
    """What comes after the shot is built and keyed: the dust of every footstep, relief."""
    if STEPS:
        ev = STEPS.events()
        if ev:
            fx.puffs('footdust', ev, fx.dust_mat('footdust', (0.5, 0.45, 0.38), 1.4))
            print(f'[arrival] {len(ev)} footsteps raise dust', flush=True)
    if ULTRA:
        adaptive()
    fx.film_look(SCENE)  # the same grade, bloom and lens on every shot


def run(name):
    global SCENE, STEPS
    # --preview: quick frames for checking the motion, kept apart from the film's.
    d = os.path.join(OUT, 'preview', name) if OPTS['preview'] else os.path.join(OUT, name)
    blend = os.path.join(WORK, f'{name}.blend')
    if OPTS['stage'] == 'render':
        # A shot built (and baked) earlier: open it and render this process's share of frames.
        bpy.ops.wm.open_mainfile(filepath=blend)
        SCENE = bpy.context.scene
        if not SCENE.compositing_node_group:
            fx.film_look(SCENE)  # built before the film look existed: it gets it now
        SCENE.render.compositor_device = 'CPU'  # never a graphics context on another GPU
        SCENE.render.use_persistent_data = True  # the scene stays loaded from frame to frame
        print('[arrival] device', use_gpu(SCENE), flush=True)
        # --res and --samples given here override what the shot was built with (a faster pass).
        argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
        if '--res' in argv:
            SCENE.render.resolution_x, SCENE.render.resolution_y = RES
        if '--samples' in argv:
            SCENE.cycles.samples = OPTS['samples']
        if OPTS['max']:
            # The first, uncompromised settings (twice the cost, for when there is time).
            for attr, val in MAX_CYCLES:
                try:
                    setattr(SCENE.cycles, attr, val)
                except (AttributeError, TypeError):
                    pass
            for ob in SCENE.objects:
                for md in ob.modifiers:
                    if md.type == 'SUBSURF' and md.use_adaptive_subdivision:
                        md.adaptive_pixel_size = 1.0
        if OPTS['nodust']:
            for ob in SCENE.objects:
                if ob.name.startswith(('footdust', 'motes')):
                    ob.hide_render = True
        if OPTS['threshold']:
            SCENE.cycles.adaptive_threshold = OPTS['threshold']
        if OPTS['volstep']:
            SCENE.cycles.volume_step_rate = OPTS['volstep']
        if OPTS['fast']:
            # Neighbouring pixels share their sampling patterns: the GPU works coherently, the
            # picture is the same at these sample counts.
            SCENE.cycles.auto_scrambling_distance = True
        if OPTS['exr']:
            exr(SCENE)
        if OPTS['outdir']:
            d = os.path.join(OPTS['outdir'], 'arrival', name)
        render_frames(name, d, SCENE.frame_end)
        return
    STEPS = None
    BAKE.clear()
    frames, step, keys = SHOTS[name]()
    if not OPTS['anim']:
        step(OPTS['t'])
        finish_scene()
        render(name)
        return
    os.makedirs(d, exist_ok=True)
    if not OPTS['encode_only']:
        for f in range(frames):
            C.TIME = f / FPS  # the clock the recorded motion plays to
            step(f / (frames - 1))
            for owner, path in keys:
                owner.keyframe_insert(path, frame=f + 1)
            if STEPS:
                STEPS.sample((f + 1) / FPS)
        cam = SCENE.camera
        if cam.animation_data and cam.animation_data.action:
            # Guard: no frame-to-frame jump in the camera's angles (a wrapped angle would spin it).
            eul = []
            for f in range(frames):
                SCENE.frame_set(f + 1)
                eul.append(cam.rotation_euler.copy())
            jump = max((max(abs(a - b) for a, b in zip(e0, e1)) for e0, e1 in zip(eul, eul[1:])), default=0)
            print(f'[arrival] {name}: largest camera turn between frames {math.degrees(jump):.2f} deg', flush=True)
            assert jump < math.radians(20), 'camera rotation wraps between frames'
        if STEPS:
            mean, worst = STEPS.slide()
            print(f'[arrival] {name}: planted feet skate {mean:.3f} m/s on average, {worst:.3f} at worst', flush=True)
            STEPS.save(os.path.join(ROOT, 'blender', 'out', 'steps', f'{name}.json'))
        SCENE.frame_start, SCENE.frame_end = 1, frames
        SCENE.render.fps = FPS
        SCENE.render.use_motion_blur = not OPTS['preview']
        SCENE.render.motion_blur_shutter = 0.5 if ULTRA else 0.35  # a film camera's 180 degrees
        finish_scene()
        SCENE.frame_set(1)
        for dom in BAKE:
            t = time.time()
            fx.bake_fluid(dom)
            print(f'[arrival] {name}: dust simulated in {time.time() - t:.0f}s', flush=True)
        if OPTS['stage'] == 'build':
            os.makedirs(WORK, exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=blend)
            print(f'[arrival] {name}: built {os.path.relpath(blend, ROOT)}', flush=True)
            return
        render_frames(name, d, frames)
    if not ULTRA and not OPTS['preview']:
        for tag, res, crf in (('desk', RES, 'MEDIUM'), ('phone', (1280, 720), 'LOW')):
            encode(d, os.path.join(OUT, f'{name}-{tag}.mp4'), res, crf, frames)


def encode(frames_dir, out_path, res, crf, frames):
    vs = bpy.data.scenes.new('Encode')
    vs.render.resolution_x, vs.render.resolution_y = res
    vs.render.resolution_percentage = 100
    vs.render.fps = FPS
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
    ff.gopsize = FPS
    ff.audio_codec = 'NONE'
    vs.render.use_sequencer = True
    vs.render.filepath = out_path
    bpy.ops.render.render(animation=True, scene=vs.name)
    bpy.data.scenes.remove(vs)
    print(f'[arrival] encoded {os.path.relpath(out_path, ROOT)} '
          f'{os.path.getsize(out_path) / 1e6:.2f} MB', flush=True)


# ---------------------------------------------------------------------------------------------

def inspect():
    global SCENE
    SCENE = reset_scene()
    for mid in sorted(os.listdir(os.path.join(ASSETS, 'models'))):
        col, lo, hi = asset(mid)
        size = hi - lo
        print(f'[asset] {mid:34s} size {size.x:6.2f} {size.y:6.2f} {size.z:6.2f}  '
              f'min {lo.x:6.2f} {lo.y:6.2f} {lo.z:6.2f}  objects {len(col.objects)}', flush=True)


SHOTS = {'orbit': shot_orbit, 'descent': shot_descent, 'ramp': shot_ramp, 'street': shot_street,
         'approach': shot_approach, 'door': shot_door}

if OPTS['inspect']:
    inspect()
else:
    names = list(SHOTS) if OPTS['shot'] == 'all' else OPTS['shot'].split(',')
    for s in names:
        run(s)
