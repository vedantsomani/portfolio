"""Pose sheet for the crew member (blender/crew.py): four walk phases from the side and one
third-person view from behind. Writes blender/out/crew/*.png. Test only."""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[sys.argv.index('-P') + 1])))
import crew as C
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('w'); sc.world = w
nt = w.node_tree; nt.nodes.clear()
env = nt.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(sys.argv[sys.argv.index('-P') + 1])), 'assets', 'hdri', 'kloofendal_overcast_puresky_4k.hdr'))
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 0.8
o = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(env.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], o.inputs['Surface'])
me = bpy.data.meshes.new('g'); me.from_pydata([(-20,-20,0),(20,-20,0),(20,20,0),(-20,20,0)],[],[(0,1,2,3)])
g = bpy.data.objects.new('g', me); sc.collection.objects.link(g)
gm = bpy.data.materials.new('gm'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18,0.18,0.17,1); me.materials.append(gm)
sd = bpy.data.lights.new('sun','SUN'); sd.energy = 3.0; s = bpy.data.objects.new('sun', sd); sc.collection.objects.link(s); s.rotation_euler = (math.radians(50), 0, math.radians(30))
crews = []
for k in range(4):
    c = C.Crew(f'crew{k}', lamp=False)
    C.place(c, (k * 1.1 - 1.65, 0, 0), math.radians(-90))  # facing +X: walking right in a side view
    c.walk(k * math.pi / 2)
    crews.append(c)
cd = bpy.data.cameras.new('cam'); cd.lens = 50; cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam)
sc.camera = cam
out = os.path.join(os.path.dirname(os.path.abspath(sys.argv[sys.argv.index('-P') + 1])), 'out', 'crew')
sc.render.resolution_x, sc.render.resolution_y = 1280, 640
cam.location = (0, -7.5, 1.0); cam.rotation_euler = (math.radians(88), 0, 0)
sc.render.filepath = os.path.join(out, 'side.png'); bpy.ops.render.render(write_still=True)
# Third person: behind and over the right shoulder of crew 1 (rotated to walk away from camera).
for c in crews:
    c.root.location.z = -50
c = crews[1]; C.place(c, (0, 0, 0), 0.0); c.walk(0.9)
cam.location = (0.55, -2.6, 1.75)
d = Vector((0.0, 4.0, 1.35)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cd.lens = 28
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.filepath = os.path.join(out, 'behind.png'); bpy.ops.render.render(write_still=True)
cam.location = (1.6, 2.2, 1.5)
d = Vector((0.0, 0.0, 1.15)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cd.lens = 40
sc.render.filepath = os.path.join(out, 'front.png'); bpy.ops.render.render(write_still=True)
print('done')
