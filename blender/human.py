"""The film's people as real humans. --who crew (the default): the crew member, a MakeHuman body and face (MPFB, Blender's human generator, with
CC0 asset packs), skin, eyes, brows, lashes, short hair, boots and gloves, on a Mixamo-compatible
skeleton. Saved to blender/assets/mh/crew-human.blend, where crew.py picks it up. --who vedant
and --who recruiter: the two people of the briefing's handover (blender/handover.py), in their own
clothes, saved to blender/assets/mh/<who>.blend.

MPFB and the packs live in their own Blender settings folder (blender/assets/mh/bres, git-ignored),
so run with it:
  BLENDER_USER_RESOURCES=<repo>/blender/assets/mh/bres blender -b -P blender/human.py -- [--skin NAME] [--test]
--test also renders a portrait to blender/out/human/portrait-<skin>.png to judge the skin by.
"""

import bpy
import addon_utils
import importlib
import math
import os
import sys
import bmesh
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(
    sys.argv[sys.argv.index('-P') + 1] if '-P' in sys.argv else __file__)))
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


WHO = arg('--who', 'crew')
# Who they are: the body (MakeHuman's macro sliders), the skin and its tone, hair, brows, and what
# they wear. Vedant from his portrait (src/assets/portrait/vedant.jpg): early twenties, slim, South
# Asian, dark wavy hair worn up, a short beard (painted into the skin), a blue-grey shirt.
PROFILES = {
    'crew': {
        'macro': {'gender': 1.0, 'age': 0.55, 'muscle': 0.64, 'weight': 0.52, 'height': 0.6, 'proportions': 0.62,
                  'race': {'african': 0.15, 'asian': 0.35, 'caucasian': 0.5}},
        'skin': 'mindfront_skin_male_african_middleage',
        'tone': {'colorMixIn': (0.5, 0.31, 0.2, 1.0), 'colorMixInStrength': 0.16, 'Brightness': 0.07,
                 'Pore strength': 0.55},
        'brows': 'mindfront_eyebrows_03', 'hair': None,
        'wear': [('culturalibre_male_boots', None), ('culturalibre_hero-heroine_gloves_1', None)],
        'iris': ((0.11, 0.06, 0.03, 1), (0.2, 0.12, 0.06, 1)), 'gear': True, 'beard': 0.0,
        'out': 'crew-human.blend',
    },
    'vedant': {
        'macro': {'gender': 1.0, 'age': 0.47, 'muscle': 0.5, 'weight': 0.44, 'height': 0.55, 'proportions': 0.6,
                  'race': {'african': 0.12, 'asian': 0.5, 'caucasian': 0.38}},
        'skin': 'mindfront_skin_male_african_middleage',
        'tone': {'colorMixIn': (0.5, 0.31, 0.2, 1.0), 'colorMixInStrength': 0.16, 'Brightness': 0.0,
                 'Pore strength': 0.5, 'Roughness': 0.55},
        'brows': 'mindfront_eyebrows_06', 'hair': None, 'strands': 'vedant',
        'wear': [('namuhekam_male_polo_shirt', (0.1, 0.145, 0.19)), ('toigo_wool_pants', (0.05, 0.05, 0.06)),
                 ('shoes02', (0.03, 0.03, 0.03))],
        'iris': ((0.07, 0.04, 0.02, 1), (0.13, 0.08, 0.04, 1)), 'gear': False, 'beard': 1.0,
        'out': 'vedant.blend',
    },
    'recruiter': {
        'macro': {'gender': 0.0, 'age': 0.6, 'muscle': 0.45, 'weight': 0.5, 'height': 0.5, 'proportions': 0.65,
                  'race': {'african': 0.1, 'asian': 0.5, 'caucasian': 0.4}},
        'skin': 'young_african_female',
        'tone': {'colorMixIn': (0.55, 0.36, 0.25, 1.0), 'colorMixInStrength': 0.22, 'Brightness': 0.03,
                 'Pore strength': 0.45},
        'brows': 'mindfront_eyebrows_02', 'hair': None, 'strands': 'ponytail',
        'wear': [('female_elegantsuit01', (0.06, 0.065, 0.075)), ('toigo_ankle_boots_female', (0.03, 0.03, 0.03))],
        'iris': ((0.08, 0.05, 0.03, 1), (0.15, 0.09, 0.05, 1)), 'gear': False, 'beard': 0.0,
        'out': 'recruiter.blend',
    },
}
PRO = PROFILES[WHO]
OUT = os.path.join(ROOT, 'blender', 'assets', 'mh', PRO['out'])
SKIN = arg('--skin', PRO['skin'])
TEST = '--test' in ARGV

addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
svc = 'bl_ext.user_default.mpfb.services.'
HS = importlib.import_module(svc + 'humanservice').HumanService
TS = importlib.import_module(svc + 'targetservice').TargetService
MS = importlib.import_module(svc + 'modifierservice').ModifierService
LS = importlib.import_module(svc + 'locationservice').LocationService
DATA = LS.get_user_data()


def asset(kind, name):
    """The .mhclo (or .mhmat for skins) of an installed asset."""
    d = os.path.join(DATA, kind, name)
    ext = '.mhmat' if kind == 'skins' else '.mhclo'
    files = sorted(f for f in os.listdir(d) if f.endswith(ext))
    if not files:
        raise IOError(f'no {ext} in {d}')
    return os.path.join(d, files[0])


# A clean scene (the settings folder's startup file has a cube and a light).
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)

macro = TS.get_default_macro_info_dict()
macro.update(PRO['macro'])
body = HS.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                       feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
body.name = f'{WHO}-body'
MS.create_subsurf_modifier(body, 'Subdivision', levels=0, render_levels=1)
body.use_shape_key_edit_mode = True

rig = HS.add_builtin_rig(body, 'mixamo', import_weights=True)
rig.name = f'{WHO}-rig'
HS.set_character_skin(asset('skins', SKIN), body, bodyproxy=None, skin_type='ENHANCED_SSS',
                      material_instances=True)
HS.add_mhclo_asset(os.path.join(DATA, 'eyes', 'high-poly', 'high-poly.mhclo'), body, asset_type='eyes',
                   subdiv_levels=1, material_type='PROCEDURAL_EYES')
for kind, name in (('eyebrows', PRO['brows']), ('eyelashes', 'mindfront_eyelashes_02')):
    HS.add_mhclo_asset(asset(kind, name), body, asset_type=kind, subdiv_levels=1, material_type='MAKESKIN')
if PRO['hair']:
    HS.add_mhclo_asset(asset('hair', PRO['hair']), body, asset_type='Hair', subdiv_levels=1, material_type='MAKESKIN')
for name, _ in PRO['wear']:
    HS.add_mhclo_asset(asset('clothes', name), body, asset_type='Clothes', subdiv_levels=1,
                       material_type='MAKESKIN')

# The look: the detailed skin (pores, sheen) lifted to a medium brown, dark brown eyes, black hair.
def group_input(mat, name):
    for n in mat.node_tree.nodes:
        if n.type == 'GROUP' and name in n.inputs:
            return n.inputs[name]
    return None


TONE = PRO['tone']
for slot in body.material_slots:
    if slot.material:
        for key, val in TONE.items():
            sock = group_input(slot.material, key)
            if sock is not None:
                sock.default_value = val
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    for slot in ob.material_slots:
        m = slot.material
        if not m or not m.node_tree:
            continue
        if ob.name.endswith('high-poly'):
            for key, val in (('IrisMajorColor', PRO['iris'][0]), ('IrisMinorColor', PRO['iris'][1])):
                sock = group_input(m, key)
                if sock is not None:
                    sock.default_value = val
        if ob.name.endswith('short02'):
            b = m.node_tree.nodes.get('Principled BSDF')
            if b:
                for l in list(b.inputs['Base Color'].links):
                    m.node_tree.links.remove(l)
                b.inputs['Base Color'].default_value = (0.02, 0.016, 0.013, 1)
                b.inputs['Roughness'].default_value = 0.45

# Feet on the ground again, now that everything is on.
bpy.context.view_layer.update()
low = min((body.matrix_world @ v.co).z for v in body.data.vertices)
rig.location.z -= low
bpy.context.view_layer.update()
sys.path.insert(0, os.path.join(ROOT, 'blender'))
import gear  # noqa: E402
import looks  # noqa: E402

if PRO['gear']:
    gear.build(body, rig)
else:
    looks.dress(body, rig, PRO)
print('[human] built', SKIN, 'height', round(max((body.matrix_world @ v.co).z for v in body.data.vertices) - low, 3),
      'bones', len(rig.data.bones), flush=True)
print('[human] parts', sorted(o.name for o in bpy.data.objects), flush=True)

if TEST:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'OPTIX'
    p.get_devices()
    for d in p.devices:
        d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = 256
    sc.render.resolution_x, sc.render.resolution_y = 1280, 1280
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    head = rig.matrix_world @ rig.data.bones['mixamorig:Head'].head_local
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.dof.use_dof = True

    def shoot(loc, target, lens, fstop, tag):
        cam.data.lens = lens
        cam.data.dof.aperture_fstop = fstop
        cam.location = loc
        d = Vector(target) - cam.location
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.dof.focus_distance = d.length
        path = os.path.join(ROOT, 'blender', 'out', 'human', f'{tag}-{SKIN}.png')
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print('[human] test', path, flush=True)

    for name, loc, energy, size, col in (('key', (1.6, -2.0, 2.6), 300, 1.2, (1.0, 0.92, 0.84)),
                                         ('rim', (-1.4, 1.6, 2.4), 260, 0.6, (0.75, 0.85, 1.0)),
                                         ('fill', (-2.0, -1.6, 1.2), 60, 2.0, (0.8, 0.85, 0.9))):
        L = bpy.data.lights.new(name, 'AREA')
        L.energy, L.size, L.color = energy, size, col
        lo = bpy.data.objects.new(name, L)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.1
    sc.render.resolution_x, sc.render.resolution_y = 1024, 1280
    shoot(Vector((1.3, -3.3, 1.15)), (0, 0, 0.95), 50, 8, 'body')
    shoot(head + Vector((0.32, -0.85, 0.1)), head + Vector((0, 0, 0.1)), 85, 5.6, 'head')
else:
    bpy.ops.file.pack_all()  # every image inside the file: it renders the same anywhere
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print('[human] saved', OUT, flush=True)
