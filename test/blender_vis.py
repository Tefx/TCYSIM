import bpy, pickle, os, random

log_path = "D:\\Dropbox\\Projects\\TCYSIM\\test\\log"
#log_path = "/home/tefx/Dropbox/Projects/TCYSIM/test/.log"

fps = 24
speedup = 60
start_time = 3600 * 24

sample_box = {1:None, 2:None}
sample_yc = None
box_objs = {}
yc_objs = {}

def mk_box_sample(name, teu=1):
    if teu == 1:
        bpy.ops.mesh.primitive_cube_add()
        sample = bpy.context.selected_objects[0]
        sample.name =  "box_{}".format(name)
        sample.scale = 6.1 / 2, 2.44 / 2, 2.59 / 2
    elif teu == 2:
        bpy.ops.mesh.primitive_cube_add()
        sample = bpy.context.selected_objects[0]
        sample.name =  "box_{}".format(name)
        sample.scale =  6.1, 2.44 / 2, 2.59 / 2
    return sample

def mk_yc_sample(name):
    bpy.ops.mesh.primitive_cube_add()
    sample = bpy.context.selected_objects[0]
    sample.scale = 1, 1, 0.5
    sample.name = "YC_{}".format(name)
    return sample

def get_yc(name):
    global sample_yc, yc_objs
    if name not in yc_objs:
        if sample_yc is None:
            sample_yc = mk_yc_sample(name)
            yc = sample_yc
        else:
            yc = sample_yc.copy()
            yc.animation_data_clear()
            bpy.context.collection.objects.link(yc)
            yc.name = "YC_{}".format(name)
        yc_objs[name] = yc
    return yc_objs[name]
    
def get_box(name, teu):
    global sample_box, box_objs
    if name not in box_objs:
        if sample_box[teu] is None:
            sample_box[teu] = mk_box_sample(name, teu)
            box = sample_box[teu]
        else:
            box = sample_box[teu].copy()
            box.animation_data_clear()
            bpy.context.collection.objects.link(box)
            box.name = "box_{}".format(name)
        box_objs[name] = box
    return box_objs[name]

        
with open(log_path, "rb") as f:
    log = pickle.load(f)
    
for time, ycs, boxes in log:
    time -= start_time
    for k, (x, y, z) in ycs.items():
        yc = get_yc(k)
        yc.location = x, y, z + 0.5
        yc.keyframe_insert(data_path="location", index=-1, frame=time * fps / speedup)
        
    for bid, (teu, (x, y, z)) in boxes.items():
        box = get_box(bid, teu)
        box.location = x, y, z 
        box.keyframe_insert(data_path="location", index=-1, frame=time * fps / speedup)
        
for objs in (box_objs, yc_objs):
    for obj in objs.values():
        for fc in obj.animation_data.action.fcurves:
            fc.extrapolation = 'CONSTANT'
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'