import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.import_scene.gltf(filepath=r"C:\Users\vedan\Downloads\website\public\models\saarthi.glb")
except Exception as e:
    print("IMPORT-FAIL", e)
objs=[o for o in bpy.context.scene.objects]
print("OBJECTS", len(objs), sum(1 for o in objs if o.type=='MESH'))
import mathutils
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    if o.type!='MESH': continue
    for c in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(c)
        for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
print("BOUNDS", mn, mx)
print("VERTS", sum(len(o.data.vertices) for o in objs if o.type=='MESH'))
