"""Bake script-holding idle/walk over Maya's existing consistent rig."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from character_paths import ART_ROOT
OUT=ART_ROOT/'Maya'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Maya_Performance.blend'))
s=bpy.context.scene;units=1/s.unit_settings.scale_length;arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=next(o for o in s.objects if o.type=='MESH')
# Bone tails from Tripo end short of their child joints. Extend only for the IK solve;
# restore the original tails after baking, leaving the imported skeleton unchanged.
original_tails={}
bpy.context.view_layer.objects.active=arm;arm.animation_data.action=None
bpy.ops.object.mode_set(mode='EDIT')
for side in ['l','r']:
 for parent,child in [('upperarm','lowerarm'),('lowerarm','hand')]:
  b=arm.data.edit_bones[parent+'_'+side];original_tails[b.name]=b.tail.copy();b.tail=arm.data.edit_bones[child+'_'+side].head
bpy.ops.object.mode_set(mode='OBJECT')
constraints=[];helpers=[]
for side,x in [('l',.12),('r',-.12)]:
 target=bpy.data.objects.new('ScriptGrip_'+side,None);s.collection.objects.link(target);target.location=(x*units,-.24*units,1.08*units);helpers.append(target)
 pole=bpy.data.objects.new('ScriptElbow_'+side,None);s.collection.objects.link(pole);pole.location=((.45 if side=='l' else -.45)*units,-.05*units,1.05*units);helpers.append(pole)
 c=arm.pose.bones['lowerarm_'+side].constraints.new('IK');c.target=target;c.pole_target=pole;c.chain_count=2;c.use_stretch=False;c.mute=True;constraints.append(c)
for new,base,count in [('ReadScript','Idle',180),('WalkWithScript','Walk',70)]:
 old=bpy.data.actions.get('A_Maya_'+new)
 if old:bpy.data.actions.remove(old)
 source=bpy.data.actions['A_Maya_'+base];poses=[]
 for f in range(count+1):
  arm.animation_data.action=source
  for c in constraints:c.mute=False
  s.frame_set(f);bpy.context.view_layer.update()
  # Subtle downward gaze toward the script.
  p=arm.pose.bones['head'];p.rotation_mode='QUATERNION'
  from mathutils import Quaternion
  axis=p.bone.matrix_local.to_quaternion().inverted()@Vector((1,0,0));p.rotation_quaternion=Quaternion(axis,math.radians(10))@p.rotation_quaternion
  bpy.context.view_layer.update();evaluated=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
  poses.append({p.name:p.matrix.copy() for p in evaluated.pose.bones})
 for c in constraints:c.mute=True
 a=bpy.data.actions.new('A_Maya_'+new);a.use_fake_user=True;arm.animation_data.action=a
 for i,pose in enumerate(poses):
  for p in arm.pose.bones:
   parent=pose[p.parent.name]@p.parent.bone.matrix_local.inverted()@p.bone.matrix_local if p.parent else p.bone.matrix_local
   p.matrix_basis=parent.inverted()@pose[p.name]
   p.keyframe_insert('location',frame=i);p.keyframe_insert('rotation_quaternion',frame=i);p.keyframe_insert('scale',frame=i)
 for fc in a.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 s.frame_start=0;s.frame_end=count;s.frame_set(0)
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=arm
 bpy.ops.export_scene.fbx(filepath=str(OUT/('A_Maya_'+new+'.fbx')),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Y',axis_up='Z',apply_scale_options='FBX_SCALE_ALL')
for side in ['l','r']:
 for c in list(arm.pose.bones['lowerarm_'+side].constraints):
  if c.type=='IK':arm.pose.bones['lowerarm_'+side].constraints.remove(c)
for h in helpers:bpy.data.objects.remove(h,do_unlink=True)
bpy.ops.object.mode_set(mode='EDIT')
for name,tail in original_tails.items():arm.data.edit_bones[name].tail=tail
bpy.ops.object.mode_set(mode='OBJECT')
arm.animation_data.action=bpy.data.actions['A_Maya_ReadScript'];s.frame_end=180;s.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Maya_Performance.blend'),compress=True)
print('INTRO_MAYA_BAKED')
