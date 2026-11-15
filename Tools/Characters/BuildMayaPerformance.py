import bpy, json, math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_paths import ART_ROOT
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
OUT=ART_ROOT/'Maya'
SOURCE=OUT/'Original/Maya.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SOURCE))
s=bpy.context.scene; s.render.fps=30
arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
source_actions={a.name.split('|')[-1].split('.')[0]:a for a in bpy.data.actions}
# Bake evaluated local poses, keeping the imported bind pose and weights together.
# World translation belongs to Sequencer, so root stays at bind pose in every clip.
specs={'Idle':(6,'idle'),'Walk':(2.333333333,'walk'),'LookAround':(4,'idle'),'LookAtDirector':(3,'idle'),'Hesitate':(3.5,'idle'),'Inspect':(5,'idle'),'Surprised':(2.5,'idle'),'Waiting':(4,'idle'),'Turn':(2.333333333,'walk')}
cache={}
for name,(duration,base) in specs.items():
 count=round(duration*30)
 samples=[]
 for i in range(count+1):
  action=source_actions[base];arm.animation_data.action=action
  f=action.frame_range.x+(action.frame_range.y-action.frame_range.x)*i/count
  s.frame_set(int(f),subframe=f-int(f))
  samples.append({p.name:p.matrix_basis.copy() for p in arm.pose.bones})
 cache[name]=samples
arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis.identity()
# Model source height is 0.979m. Apply one uniform scale to mesh + rig for 1.68m stature.
bpy.context.view_layer.update()
factor=1.68/mesh.dimensions.z
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
# Leave object scale shared and let FBX bake unit conversion consistently.
arm.scale*=factor
# Mesh is parented to Armature: scaling armature scales mesh once.
print('PARENT',mesh.parent.name if mesh.parent else None,'FACTOR',factor)
if mesh.parent is None:mesh.scale*=factor
s.frame_set(0)
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_Maya_Polished.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,axis_forward='-Y',axis_up='Z',apply_scale_options='FBX_SCALE_ALL',use_armature_deform_only=False)
created=[]
def delta(p,axis,angle):
 # Convert global axis to the bone rest basis; preserve source motion beneath the gesture.
 local=p.bone.matrix_local.to_quaternion().inverted()@Vector(axis)
 p.rotation_quaternion=Quaternion(local,math.radians(angle))@p.rotation_quaternion
for name,(duration,base) in specs.items():
 action=bpy.data.actions.new('A_Maya_'+name);arm.animation_data.action=action
 samples=cache[name];count=len(samples)-1
 for i,pose in enumerate(samples):
  t=i/count; envelope=math.sin(math.pi*t)**2
  for p in arm.pose.bones:
   p.rotation_mode='QUATERNION';p.matrix_basis=pose[p.name]
  arm.pose.bones['root'].matrix_basis.identity()
  if base=='walk':
   # Tripo stores locomotion on pelvis, not root. Remove endpoint travel for Sequencer.
   travel=samples[-1]['pelvis'].translation-samples[0]['pelvis'].translation
   # Pelvis parent is root: preserve vertical bob and remove only horizontal drift.
   basis=arm.pose.bones['pelvis'].bone.matrix_local.to_quaternion()
   world_travel=basis@travel;world_travel.z=0
   travel=basis.inverted()@world_travel
   arm.pose.bones['pelvis'].location-=travel*t
  if name=='LookAround':
   yaw=28*math.sin(2*math.pi*t)*envelope
   delta(arm.pose.bones['head'],(0,0,1),yaw);delta(arm.pose.bones['spine_03'],(0,0,1),yaw*.2)
  elif name=='LookAtDirector':
   delta(arm.pose.bones['head'],(0,0,1),32*envelope);delta(arm.pose.bones['spine_03'],(0,0,1),8*envelope)
  elif name=='Hesitate':
   delta(arm.pose.bones['head'],(1,0,0),10*envelope)
   delta(arm.pose.bones['head'],(0,0,1),16*math.sin(3*math.pi*t)*envelope)
   delta(arm.pose.bones['spine_03'],(1,0,0),-4*envelope)
  elif name=='Inspect':
   delta(arm.pose.bones['spine_03'],(1,0,0),9*envelope);delta(arm.pose.bones['neck_01'],(1,0,0),12*envelope)
   delta(arm.pose.bones['head'],(0,0,1),10*math.sin(2*math.pi*t)*envelope)
  elif name=='Surprised':
   pulse=math.sin(math.pi*min(1,t/.7))**2 if t<.7 else 0
   delta(arm.pose.bones['spine_03'],(1,0,0),-9*pulse);delta(arm.pose.bones['head'],(1,0,0),-10*pulse)
   delta(arm.pose.bones['upperarm_l'],(0,1,0),-10*pulse);delta(arm.pose.bones['upperarm_r'],(0,1,0),10*pulse)
  elif name=='Waiting':
   delta(arm.pose.bones['head'],(0,0,1),12*envelope);delta(arm.pose.bones['spine_03'],(0,0,1),3*envelope)
  for p in arm.pose.bones:
   p.keyframe_insert('location',frame=i);p.keyframe_insert('rotation_quaternion',frame=i);p.keyframe_insert('scale',frame=i)
 for fc in action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 action.use_fake_user=True
 s.frame_start=0;s.frame_end=count;s.frame_set(0)
 bpy.ops.export_scene.fbx(filepath=str(OUT/('A_Maya_'+name+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_scale_options='FBX_SCALE_ALL',use_armature_deform_only=False)
 created.append({'name':name,'frames':count+1,'duration':count/30})
# Keep only authored actions in the deliverable. Pack textures for portable editing.
for a in source_actions.values():
 bpy.data.actions.remove(a)
arm.animation_data.action=bpy.data.actions['A_Maya_Idle'];s.frame_end=180;s.frame_set(0)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Maya_Performance.blend'),compress=True)
(OUT/'AnimationManifest.json').write_text(json.dumps({'height_m':1.68,'fps':30,'root_motion':False,'animations':created},indent=2))
print('POLISH_EXPORT_COMPLETE')
