"""The lab's hardware, real where it can be.

Downloaded: NASA 3D Resources (public domain): the Ingenuity Mars helicopter, the RASSOR excavator
robot, a Perseverance scale model, CubeSats; Poly Haven (CC0): scanned bench gear and tools.
Made here only what no free, realistic model exists for:
  printer     an FDM 3D printer (a bed-slinger like a Prusa MK4): black extrusion frame, rods and
              lead screws, a gold PEI bed with a part half printed (its layer lines), the print head
              and its fan, a lit screen, an orange filament spool above
  board       the Saarthi flight controller as a real board, its own render as the surface

lab.py calls build(). Everything is built where it stands (no object scale), Z up, metres.
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'blender', 'assets', 'models')


# ---- building blocks ------------------------------------------------------------------------

def _link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    return ob


def _smooth(me):
    for p in me.polygons:
        p.use_smooth = True


def box(name, size, mat, at=(0, 0, 0), rot=(0, 0, 0), parent=None, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = _link(bpy.data.objects.new(name, me), parent)
    ob.location, ob.rotation_euler = at, rot
    if bevel:
        b = ob.modifiers.new('bevel', 'BEVEL')
        b.width, b.segments, b.limit_method = bevel, 3, 'ANGLE'
        _smooth(me)
    return ob


def cyl(name, r, h, mat, at=(0, 0, 0), rot=(0, 0, 0), parent=None, segs=32, r2=None, cap=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me)
    bm.free()
    _smooth(me)
    me.materials.append(mat)
    ob = _link(bpy.data.objects.new(name, me), parent)
    ob.location, ob.rotation_euler = at, rot
    # Sharp caps, smooth sides.
    ob.data.polygons.foreach_set('use_smooth', [len(p.vertices) == 4 for p in ob.data.polygons])
    return ob


def tube(name, pts, r, mat, parent=None):
    """A cable through points (a curve with a round bevel)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for pt, c in zip(sp.points, pts):
        pt.co = (*c, 1.0)
    sp.order_u = min(4, len(pts))
    sp.use_endpoint_u = True
    cu.materials.append(mat)
    return _link(bpy.data.objects.new(name, cu), parent)


def empty(name, at=(0, 0, 0), rot=(0, 0, 0), parent=None):
    ob = _link(bpy.data.objects.new(name, None), parent)
    ob.location, ob.rotation_euler = at, rot
    return ob


# ---- materials ------------------------------------------------------------------------------

_M = {}


def _mat(name):
    m = bpy.data.materials.new('hw-' + name)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def plain(name, color, rough=0.5, metal=0.0, coat=0.0):
    if name in _M:
        return _M[name]
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    # A little wear and dust everywhere: nothing in a real lab is clean.
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 60.0
    n.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = rough * 0.8
    mr.inputs['To Max'].default_value = min(1.0, rough * 1.25 + 0.05)
    nt.links.new(n.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs[0], b.inputs['Roughness'])
    _M[name] = m
    return m


def emit(name, color, strength):
    if name in _M:
        return _M[name]
    m, nt, b = _mat(name)
    b.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    b.inputs['Emission Color'].default_value = (*color, 1)
    b.inputs['Emission Strength'].default_value = strength
    b.inputs['Roughness'].default_value = 0.2
    _M[name] = m
    return m


def pcb(name, image=None):
    """A circuit board: green solder mask, gold pads and copper traces showing through, or a real
    board's own render as its face."""
    if name in _M:
        return _M[name]
    m, nt, b = _mat(name)
    b.inputs['Roughness'].default_value = 0.32
    b.inputs['Coat Weight'].default_value = 0.4
    tc = nt.nodes.new('ShaderNodeTexCoord')
    if image and os.path.exists(image):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(image, check_existing=True)
        nt.links.new(tc.outputs['UV'], t.inputs['Vector'])
        # A render is lit for the screen; a real board's solder mask is far darker: the picture
        # brought down to it, its detail kept.
        hsv = nt.nodes.new('ShaderNodeHueSaturation')
        hsv.inputs['Saturation'].default_value = 1.35
        hsv.inputs['Value'].default_value = 0.42
        nt.links.new(t.outputs['Color'], hsv.inputs['Color'])
        nt.links.new(hsv.outputs['Color'], b.inputs['Base Color'])
    else:
        v = nt.nodes.new('ShaderNodeTexVoronoi')
        v.inputs['Scale'].default_value = 140.0
        v.feature = 'DISTANCE_TO_EDGE'
        nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.0
        mr.inputs['From Max'].default_value = 0.04
        nt.links.new(v.outputs['Distance'], mr.inputs['Value'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        nt.links.new(mr.outputs[0], mix.inputs[0])
        mix.inputs[6].default_value = (0.55, 0.42, 0.12, 1)
        mix.inputs[7].default_value = (0.02, 0.12, 0.05, 1)
        nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    _M[name] = m
    return m


# ---- the pieces -----------------------------------------------------------------------------

def printer(at, rot=0.0):
    """A bed-slinger FDM printer, ~0.5 m wide, printing a drone arm."""
    root = empty('printer', at, (0, 0, rot))
    alu = plain('extrusion', (0.035, 0.035, 0.037), 0.38, 0.6)
    rod = plain('rod', (0.75, 0.75, 0.76), 0.18, 1.0)
    black = plain('black-plastic', (0.025, 0.025, 0.027), 0.55)
    orange = plain('prusa-orange', (0.85, 0.28, 0.05), 0.45)
    pei = plain('pei', (0.48, 0.34, 0.12), 0.62, 0.55)
    # The Y frame on the bench, and the bed riding on it.
    for x in (-0.12, 0.12):
        box('printer-y-rail', (0.02, 0.42, 0.02), alu, (x, 0, 0.03), parent=root)
    box('printer-y-front', (0.3, 0.02, 0.04), alu, (0, -0.21, 0.02), parent=root)
    box('printer-y-back', (0.3, 0.02, 0.04), alu, (0, 0.21, 0.02), parent=root)
    for x in (-0.06, 0.06):
        cyl('printer-y-rod', 0.004, 0.42, rod, (x, 0, 0.052), (math.radians(90), 0, 0), parent=root)
    box('printer-bed-carriage', (0.24, 0.24, 0.006), black, (0, 0.03, 0.065), parent=root)
    bed = box('printer-bed', (0.25, 0.21, 0.004), pei, (0, 0.03, 0.072), parent=root, bevel=0.002)
    # The part on the bed: a drone arm half printed, its layer lines in the surface.
    pla = bpy.data.materials.new('hw-print')
    pla.use_nodes = True
    pb = pla.node_tree.nodes['Principled BSDF']
    pb.inputs['Base Color'].default_value = (0.08, 0.09, 0.1, 1)
    pb.inputs['Roughness'].default_value = 0.35
    wave = pla.node_tree.nodes.new('ShaderNodeTexWave')
    wave.wave_profile = 'SAW'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 600.0
    tc = pla.node_tree.nodes.new('ShaderNodeTexCoord')
    pla.node_tree.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    bump = pla.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.5
    pla.node_tree.links.new(wave.outputs['Fac'], bump.inputs['Height'])
    pla.node_tree.links.new(bump.outputs['Normal'], pb.inputs['Normal'])
    box('printer-part', (0.16, 0.026, 0.012), pla, (0.0, 0.03, 0.08), (0, 0, math.radians(35)), parent=root, bevel=0.003)
    cyl('printer-part-mount', 0.018, 0.012, pla, (0.065, 0.075, 0.08), parent=root)
    # The Z towers and the X gantry with the head.
    for x in (-0.19, 0.19):
        box('printer-z-tower', (0.02, 0.04, 0.4), alu, (x, 0.02, 0.22), parent=root)
        cyl('printer-z-rod', 0.004, 0.36, rod, (x * 0.88, -0.005, 0.22), parent=root)
        cyl('printer-z-screw', 0.004, 0.36, plain('brass', (0.62, 0.45, 0.2), 0.3, 1.0), (x * 0.88, 0.035, 0.22), parent=root)
        box('printer-z-motor', (0.042, 0.042, 0.04), black, (x * 0.88, 0.035, 0.035), parent=root)
    box('printer-z-top', (0.4, 0.04, 0.02), alu, (0, 0.02, 0.43), parent=root)
    hz = 0.17
    for z in (-0.02, 0.02):
        cyl('printer-x-rod', 0.004, 0.36, rod, (0, -0.005, hz + z), (0, math.radians(90), 0), parent=root)
    head = empty('printer-head', (0.04, -0.03, hz), parent=root)
    box('printer-head-body', (0.055, 0.045, 0.07), orange, (0, 0, 0), parent=head, bevel=0.004)
    box('printer-head-fan', (0.04, 0.008, 0.04), black, (0, -0.026, -0.005), parent=head, bevel=0.003)
    cyl('printer-head-fan-hub', 0.008, 0.003, plain('fan-hub', (0.05, 0.05, 0.05), 0.4), (0, -0.031, -0.005), (math.radians(90), 0, 0), parent=head)
    cyl('printer-nozzle', 0.004, 0.012, plain('brass', (0.62, 0.45, 0.2), 0.3, 1.0), (0, 0, -0.04), parent=head, r2=0.001)
    box('printer-heatblock', (0.018, 0.012, 0.01), plain('alu-raw', (0.7, 0.7, 0.72), 0.3, 1.0), (0, 0, -0.031), parent=head)
    # The screen box at the front, lit; the power supply under it.
    lcd = box('printer-lcd', (0.12, 0.03, 0.06), orange, (0, -0.24, 0.05), (math.radians(-20), 0, 0), parent=root, bevel=0.004)
    disp = box('printer-lcd-screen', (0.085, 0.002, 0.045), emit('printer-screen', (0.35, 0.6, 1.0), 2.5), (0, -0.016, 0.003), parent=lcd)
    box('printer-psu', (0.08, 0.12, 0.05), black, (0.24, 0.12, 0.03), parent=root, bevel=0.003)
    # The filament spool on top, its strand down to the head.
    spool = empty('printer-spool', (0.0, 0.03, 0.5), (0, math.radians(90), 0), parent=root)
    cyl('spool-flange', 0.1, 0.004, black, (0, 0, -0.03), parent=spool)
    cyl('spool-flange', 0.1, 0.004, black, (0, 0, 0.03), parent=spool)
    cyl('spool-filament', 0.085, 0.056, plain('petg-orange', (0.9, 0.35, 0.06), 0.25), parent=spool)
    cyl('spool-hub', 0.028, 0.07, black, parent=spool)
    box('spool-holder', (0.01, 0.01, 0.08), alu, (0, 0.03, 0.47), parent=root)
    tube('printer-filament', [(0.0, -0.05, 0.47), (0.03, -0.06, 0.32), (0.04, -0.035, 0.205)], 0.0009,
         plain('petg-orange', (0.9, 0.35, 0.06), 0.25), parent=root)
    tube('printer-cable', [(0.19, 0.06, 0.2), (0.12, 0.08, 0.26), (0.06, 0.0, hz + 0.04)], 0.004, black, parent=root)
    return root


def board(at, rot=0.0, image=None, size=0.09):
    """A real board on four standoffs; its face is the board's own render."""
    root = empty('saarthi-board', at, (0, 0, rot))
    me = bpy.data.meshes.new('saarthi-pcb')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(size, size, 0.0016), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.uv_layers.new()
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            co = me.vertices[vi].co
            me.uv_layers[0].data[li].uv = (co.x / size + 0.5, co.y / size + 0.5)
    me.materials.append(pcb('pcb-saarthi', image))
    b = _link(bpy.data.objects.new('saarthi-pcb', me), root)
    b.location = (0, 0, 0.021)  # on standoffs above the papers on the bench
    for x in (-1, 1):
        for y in (-1, 1):
            cyl('saarthi-standoff', 0.0025, 0.02, plain('brass', (0.62, 0.45, 0.2), 0.3, 1.0), (x * size * 0.44, y * size * 0.44, 0.01), parent=root)
    return root


# ---- scanned gear from Poly Haven ------------------------------------------------------------

_ASSETS = {}


def place_asset(mid, at, rot=0.0, scale=1.0, hires=True):
    """A Poly Haven model (blender/fetch_assets.py) at a point, standing on it, turned rot."""
    if mid not in _ASSETS:
        hi = os.path.join(ASSETS, mid, '2k', f'{mid}.gltf')
        path = hi if hires and os.path.exists(hi) else os.path.join(ASSETS, mid, f'{mid}.gltf')
        if not os.path.exists(path):
            print('[hardware] missing model', mid, flush=True)
            _ASSETS[mid] = None
            return None
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        col = bpy.data.collections.new('hw:' + mid)
        lo, hi_ = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            if o.type == 'MESH':
                for c in o.bound_box:
                    w = o.matrix_world @ Vector(c)
                    lo = Vector(map(min, lo, w))
                    hi_ = Vector(map(max, hi_, w))
        _ASSETS[mid] = (col, lo, hi_)
    got = _ASSETS[mid]
    if got is None:
        return None
    col, lo, hi_ = got
    ob = _link(bpy.data.objects.new(mid, None))
    ob.instance_type = 'COLLECTION'
    ob.instance_collection = col
    ob.instance_collection.instance_offset = ((lo.x + hi_.x) / 2, (lo.y + hi_.y) / 2, lo.z)
    ob.location = at
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (scale,) * 3
    return ob


NASA = os.path.join(ASSETS, 'nasa')


def place_glb(name, at, rot=0.0, size=None, tilt=0.0):
    """A downloaded model (NASA 3D Resources, public domain) standing at a point, turned rot, its
    largest dimension size metres (the files are not all to scale)."""
    path = os.path.join(NASA, name + '.glb')
    if not os.path.exists(path):
        print('[hardware] missing', name, flush=True)
        return None
    key = 'nasa:' + name
    if key not in _ASSETS:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        # Leftover helpers inside the files (a bare sphere under the rover): meshes with no
        # material are not part of the hardware.
        for o in [o for o in new if o.type == 'MESH' and not o.data.materials]:
            new.remove(o)
            bpy.data.objects.remove(o)
        col = bpy.data.collections.new(key)
        lo, hi_ = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        bpy.context.view_layer.update()
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
            if o.type == 'MESH':
                for c in o.bound_box:
                    w = o.matrix_world @ Vector(c)
                    lo = Vector(map(min, lo, w))
                    hi_ = Vector(map(max, hi_, w))
        _ASSETS[key] = (col, lo, hi_)
    col, lo, hi_ = _ASSETS[key]
    ob = _link(bpy.data.objects.new(name, None))
    ob.instance_type = 'COLLECTION'
    ob.instance_collection = col
    col.instance_offset = ((lo.x + hi_.x) / 2, (lo.y + hi_.y) / 2, lo.z)
    k = size / max(hi_ - lo) if size else 1.0
    ob.location = at
    ob.rotation_euler = (tilt, 0, rot)
    ob.scale = (k,) * 3
    return ob


# ---- the lab's hardware, placed ----------------------------------------------------------------

def build(bench_z, work_dir, steel, dark, wood=None):
    """Set out in the lab (lab.py's room: 11 m by 12, the centre bench at y = 0.45; the crew's path
    runs down the left side). Downloaded wherever a real model exists: NASA's Ingenuity helicopter,
    the RASSOR excavator robot, a Perseverance scale model and CubeSats (public domain), and Poly
    Haven's scanned bench gear and tools (CC0). Made here only what no free model exists for: the
    3D printer, and the Saarthi board (its own render on a plate)."""
    made = []
    # The maker bench, to the right of the centre bench.
    BX, BY = 3.35, 0.65
    box('maker-bench-top', (2.3, 0.85, 0.05), steel, (BX, BY, bench_z - 0.025), bevel=0.006)
    for x in (BX - 1.05, BX + 1.05):
        for y in (BY - 0.37, BY + 0.37):
            box('maker-bench-leg', (0.05, 0.05, bench_z - 0.05), dark, (x, y, (bench_z - 0.05) / 2))
    box('maker-bench-shelf', (2.2, 0.75, 0.02), steel, (BX, BY, 0.18))
    z = bench_z
    made.append(printer((BX - 0.75, BY + 0.05, z), math.radians(-8)))
    # Space hardware on the bench: two CubeSats (one being built, one finished) and a scale
    # model of Perseverance.
    place_glb('CubeSat - 2 RU Generic', (BX - 0.1, BY + 0.15, z), math.radians(20), size=0.227)
    place_asset('industrial_microscope', (BX + 0.3, BY - 0.22, z), math.radians(160))
    place_asset('desk_lamp_arm_01', (BX - 0.35, BY + 0.33, z), math.radians(200))
    place_asset('circuit_board', (BX + 0.0, BY - 0.24, z + 0.002), math.radians(20))
    place_asset('vintage_spacecraft_instrument', (BX + 0.95, BY - 0.22, z), math.radians(-120))
    place_asset('pliers', (BX - 0.2, BY - 0.27, z), math.radians(70))
    place_asset('screwdrivers_02', (BX + 0.55, BY - 0.3, z), math.radians(-30))
    place_asset('measuring_tape_01', (BX - 0.5, BY - 0.3, z), math.radians(15))
    place_asset('plastic_crate_02', (BX - 0.6, BY + 0.05, 0.19), math.radians(5))
    place_asset('metal_stool_02', (BX + 0.3, BY - 0.75, 0.0), math.radians(25))
    # The centre bench, in the home page's view: Ingenuity on its left end (rotors 1.2 m across),
    # the Saarthi board beside the laptop, a 1U CubeSat at the front, the Perseverance model at the
    # back, the multimeter.
    place_glb('Ingenuity Mars Helicopter', (-0.82, 0.7, bench_z), math.radians(28), size=1.2)
    made.append(board((-0.27, -0.02, bench_z), math.radians(12),
                      os.path.join(work_dir, 'derived', 'saarthi-render-sq.jpg')))
    place_glb('CubeSat - 1 RU Generic', (0.38, 0.02, bench_z), math.radians(-30), size=0.12)
    place_glb('Mars 2020 Perseverance Rover', (0.82, 0.7, bench_z), math.radians(-145), size=0.42)
    place_asset('retro_multimeter', (0.85, 0.12, bench_z), math.radians(-25))
    # On the floor by the maker bench: the RASSOR robot (about 0.9 m long).
    place_glb('Regolith Advanced Surface Systems Operations Robot (RASSOR)', (2.05, -0.75, 0.0),
              math.radians(-115), size=0.9)
    # Along the right: the tool cart, the chest with the radio on it, a power box on the wall.
    place_asset('tool_cart', (4.85, -0.75, 0.0), math.radians(-95))
    place_asset('metal_tool_chest', (4.9, 1.95, 0.0), math.radians(-90))
    place_asset('vintage_radio_transceiver', (4.85, 1.95, 1.0), math.radians(-95))
    place_asset('power_box_01', (5.38, -2.2, 1.3), math.radians(-90))
    print(f'[hardware] built: printer and board made; {len([k for k, v in _ASSETS.items() if v])} downloaded models', flush=True)
    return made
