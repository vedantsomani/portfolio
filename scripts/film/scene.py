# "Inside the machine": a ray-traced macro world built around the real Saarthi board GLB.
# The camera is insect-sized: chips are buildings, pin headers are towers, smoke rolls between them,
# a red light burns behind the STM32H753, and a red scan sheet cuts the fog.
# Usage (headless):
#   blender -b --python scripts/film/scene.py -- <shot> <out.png> [width] [height] [samples]
# Shots: establish, brain, scan. Coordinates: Blender Z-up; KiCad (x, y) mm -> (x/1000, -y/1000).
import bpy
import math
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
SHOT = ARGS[0] if len(ARGS) > 0 else "establish"
OUT = ARGS[1] if len(ARGS) > 1 else "//concept.png"
W = int(ARGS[2]) if len(ARGS) > 2 else 1280
H = int(ARGS[3]) if len(ARGS) > 3 else 720
SAMPLES = int(ARGS[4]) if len(ARGS) > 4 else 96
GLB = r"C:\Users\vedan\Downloads\website\public\models\saarthi.glb"


def k(x, y, z=0.0):
    """KiCad millimetres (and height in mm) to Blender metres."""
    return Vector((x / 1000, -y / 1000, z / 1000))


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- Render ----------
scene.render.engine = "CYCLES"
cy = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences
device = "CPU"
for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == kind
            device = "GPU"
            break
    except Exception:
        continue
cy.device = device
print("DEVICE", device, prefs.compute_device_type)
cy.samples = SAMPLES
cy.use_denoising = True
cy.denoiser = "OPENIMAGEDENOISE"
cy.max_bounces = 8
cy.volume_bounces = 1
cy.volume_step_rate = 0.5
cy.caustics_reflective = False
cy.caustics_refractive = False
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT

world = bpy.data.worlds.new("Dark")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.0005, 0.0007, 0.0008, 1)
scene.world = world

# ---------- The board ----------
bpy.ops.import_scene.gltf(filepath=GLB)
board = [o for o in scene.objects if o.type == "MESH"]
for o in board:
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            # Real boards are glossy: wet solder mask, bright pin gold.
            bsdf.inputs["Roughness"].default_value = min(bsdf.inputs["Roughness"].default_value, 0.35)


def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


# The bench: black anodised metal with brushed streaks, catching the red.
bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0.065, -0.065, -0.0016))
bench = bpy.context.active_object
bm = mat("Bench", (0.012, 0.012, 0.013), rough=0.32, metal=0.85)
nt = bm.node_tree
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 900
noise.inputs["Detail"].default_value = 6
mapping = nt.nodes.new("ShaderNodeMapping")
mapping.inputs["Scale"].default_value = (1, 40, 1)
coord = nt.nodes.new("ShaderNodeTexCoord")
ramp = nt.nodes.new("ShaderNodeMapRange")
ramp.inputs["To Min"].default_value = 0.22
ramp.inputs["To Max"].default_value = 0.5
nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
nt.links.new(ramp.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Roughness"])
bench.data.materials.append(bm)

# ---------- Smoke ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.065, -0.065, 0.02))
fog = bpy.context.active_object
fog.scale = (0.5, 0.5, 0.06)
fm = bpy.data.materials.new("Smoke")
fm.use_nodes = True
fnt = fm.node_tree
fnt.nodes.remove(fnt.nodes["Principled BSDF"])
vol = fnt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Anisotropy"].default_value = 0.55
vol.inputs["Color"].default_value = (0.8, 0.85, 0.85, 1)
# Density: thick near the board, thinning with height, broken up by noise so it rolls.
geo = fnt.nodes.new("ShaderNodeNewGeometry")
sep = fnt.nodes.new("ShaderNodeSeparateXYZ")
fnt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
fall = fnt.nodes.new("ShaderNodeMapRange")
fall.inputs["From Min"].default_value = 0.0
fall.inputs["From Max"].default_value = 0.028
fall.inputs["To Min"].default_value = 1.0
fall.inputs["To Max"].default_value = 0.0
fnt.links.new(sep.outputs["Z"], fall.inputs["Value"])
fn = fnt.nodes.new("ShaderNodeTexNoise")
fn.inputs["Scale"].default_value = 60
fn.inputs["Detail"].default_value = 4
fn.inputs["Roughness"].default_value = 0.6
fnt.links.new(geo.outputs["Position"], fn.inputs["Vector"])
shape = fnt.nodes.new("ShaderNodeMapRange")
shape.inputs["From Min"].default_value = 0.42
shape.inputs["From Max"].default_value = 0.75
fnt.links.new(fn.outputs["Fac"], shape.inputs["Value"])
mul = fnt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
fnt.links.new(fall.outputs["Result"], mul.inputs[0])
fnt.links.new(shape.outputs["Result"], mul.inputs[1])
dens = fnt.nodes.new("ShaderNodeMath")
dens.operation = "MULTIPLY"
dens.inputs[1].default_value = 6.0
fnt.links.new(mul.outputs["Value"], dens.inputs[0])
fnt.links.new(dens.outputs["Value"], vol.inputs["Density"])
fnt.links.new(vol.outputs["Volume"], fnt.nodes["Material Output"].inputs["Volume"])
fog.data.materials.append(fm)

# ---------- Lights ----------
def light(kind, name, loc, color, power, size=0.002, aim=None, spot=None, blend=0.2, spread=None):
    data = bpy.data.lights.new(name, kind)
    data.color = color
    data.energy = power
    if kind in ("POINT", "SPOT"):
        data.shadow_soft_size = size
    if kind == "AREA":
        data.shape = "RECTANGLE"
        data.size, data.size_y = size if isinstance(size, tuple) else (size, size)
        if spread is not None:
            data.spread = math.radians(spread)
    if kind == "SPOT":
        data.spot_size = math.radians(spot or 30)
        data.spot_blend = blend
    o = bpy.data.objects.new(name, data)
    o.location = loc
    scene.collection.objects.link(o)
    if aim is not None:
        d = Vector(aim) - Vector(loc)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


brain = k(42, 65)
# The brain burns: red light from behind and under the STM32H753, glowing through the smoke.
light("POINT", "BrainGlow", k(52, 52, 2.5), (1.0, 0.04, 0.03), 0.035, size=0.003)
light("POINT", "BrainUnder", k(30, 70, 1.2), (1.0, 0.05, 0.03), 0.025, size=0.002)
# Cold moonlight key through the smoke from high behind: god rays and rim on every pin.
light("SPOT", "Key", k(95, 10, 70), (0.55, 0.78, 1.0), 2.6, size=0.004, aim=brain, spot=34, blend=0.5)
# Red emergency light far left, low: a wash across the bench.
light("AREA", "Emergency", k(-60, 90, 12), (1.0, 0.06, 0.04), 0.06, size=0.04, aim=k(60, 70))
# Scan: a thin, tight sheet of red light from above, across the board.
scan_y = {"establish": 82, "brain": 78, "scan": 60}[SHOT]
light(
    "AREA",
    "Scan",
    k(65, scan_y, 60),
    (1.0, 0.03, 0.04),
    2.0,
    size=(0.16, 0.00025),
    aim=k(65, scan_y, 0),
    spread=2.5,
)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
shots = {
    # Low across the servo towers towards the brain.
    "establish": (k(96, 128, 11), k(48, 66, 2), 24, 22),
    # Close on the STM32H753, the red burning behind it.
    "brain": (k(64, 90, 10), k(42, 65, 1), 35, 16),
    # High three-quarter: the scan sheet crossing the board through the smoke.
    "scan": (k(115, 120, 45), k(60, 62, 0), 24, 16),
}
loc, target, lens, fstop = shots[SHOT]
cam.location = loc
cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
cam_data.lens = lens
cam_data.sensor_width = 36
cam_data.clip_start = 0.0005
cam_data.clip_end = 5
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = (target - loc).length
cam_data.dof.aperture_fstop = fstop
cam_data.dof.aperture_blades = 7

print("SHOT", SHOT, "->", OUT, W, "x", H, SAMPLES, "samples")
bpy.ops.render.render(write_still=True)
print("DONE", OUT)
