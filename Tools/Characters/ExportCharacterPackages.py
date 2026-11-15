"""Export centimeter rigs with unit root scale for Unreal skinning and IK."""
import bpy,sys
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_paths import ART_ROOT
for folder,filename,mesh_name,prefix in [('Maya','Maya_Performance.blend','SK_Maya_Polished','A_Maya_'),('Crew','Crew_Utility.blend','SK_Crew_Utility','A_Crew_'),('Crew','Crew_A.blend','SK_Crew_A',None),('Crew','Crew_B.blend','SK_Crew_B',None)]:
 out=ART_ROOT/folder;bpy.ops.wm.open_mainfile(filepath=str(out/filename));s=bpy.context.scene
 arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
 action=arm.animation_data.action if arm.animation_data else None
 if s.unit_settings.scale_length!=.01:
  factor=100*arm.scale.x
  assert max(abs(v-arm.scale.x) for v in arm.scale)<.0001,'Nonuniform armature scale'
  if arm.animation_data:arm.animation_data.action=None
  for p in arm.pose.bones:p.matrix_basis.identity()
  for v in mesh.data.vertices:v.co*=factor
  bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
  positions={b.name:(b.head.copy(),b.tail.copy()) for b in arm.data.edit_bones}
  for b in arm.data.edit_bones:b.use_connect=False
  for b in arm.data.edit_bones:b.head=positions[b.name][0]*factor;b.tail=positions[b.name][1]*factor
  bpy.ops.object.mode_set(mode='OBJECT');arm.scale=(1,1,1);mesh.scale=(1,1,1);mesh.matrix_parent_inverse=Matrix.Identity(4)
  for a in bpy.data.actions:
   for fc in a.fcurves:
    if fc.data_path.endswith('.location'):
     for k in fc.keyframe_points:
      k.co.y*=factor;k.handle_left.y*=factor;k.handle_right.y*=factor
  s.unit_settings.system='METRIC';s.unit_settings.scale_length=.01
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
 if arm.animation_data:arm.animation_data.action=None
 for p in arm.pose.bones:p.matrix_basis.identity()
 bpy.context.view_layer.update()
 kwargs=dict(use_selection=True,add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL')
 bpy.ops.export_scene.fbx(filepath=str(out/(mesh_name+'.fbx')),object_types={'ARMATURE','MESH'},bake_anim=False,**kwargs)
 if prefix:
  for a in list(bpy.data.actions):
   if not a.name.startswith(prefix):continue
   arm.animation_data.action=a;s.frame_start=int(a.frame_range.x);s.frame_end=int(a.frame_range.y);s.frame_set(s.frame_start)
   bpy.ops.export_scene.fbx(filepath=str(out/(a.name+'.fbx')),object_types={'ARMATURE'},bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,**kwargs)
 if action:
  arm.animation_data.action=action;s.frame_start=0;s.frame_end=int(action.frame_range.y);s.frame_set(0)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/filename),compress=True)
 print('CENTIMETER_EXPORT',folder,filename)
