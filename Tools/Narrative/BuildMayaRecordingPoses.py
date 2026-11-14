import unreal,json,traceback
P=unreal.Paths.project_dir();T=unreal.AssetToolsHelpers.get_asset_tools();E=unreal.EditorAssetLibrary
try:
 idle=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle');pose=unreal.AnimPoseExtensions.get_anim_pose_at_frame(idle,0,unreal.AnimPoseEvaluationOptions());names=unreal.AnimPoseExtensions.get_bone_names(pose);local={str(n):unreal.AnimPoseExtensions.get_bone_pose(pose,n,unreal.AnimPoseSpaces.LOCAL) for n in names};world={str(n):unreal.AnimPoseExtensions.get_bone_pose(pose,n,unreal.AnimPoseSpaces.WORLD) for n in names}
 seated={k:unreal.Transform(location=v.translation,rotation=v.rotation.rotator(),scale=v.scale3d) for k,v in local.items()}
 tr=seated['pelvis'].translation;seated['pelvis'].translation=unreal.Vector(tr.x,tr.y,tr.z-35)
 for suffix in ['l','r']:
  thigh='thigh_'+suffix;calf='calf_'+suffix;parent=world['pelvis'].rotation;rot=unreal.Rotator(pitch=0,yaw=0,roll=90).quaternion()*world[thigh].rotation
  seated[thigh].rotation=unreal.MathLibrary.quat_inversed(parent)*rot;seated[calf].rotation=unreal.MathLibrary.quat_inversed(rot)*world[calf].rotation
 out=[]
 for name,standing in [('A_Maya_Record_Seated',False),('A_Maya_Record_Stand',True)]:
  folder='/Game/Game/Cinematics/Animations';path=folder+'/'+name
  if E.does_asset_exist(path):asset=unreal.load_asset(path)
  else:
   fac=unreal.AnimSequenceFactory();fac.target_skeleton=idle.get_editor_property('skeleton');asset=T.create_asset(name,folder,unreal.AnimSequence,fac)
  controller=asset.get_editor_property('controller');controller.open_bracket('Author mannequin seated blocking');controller.set_frame_rate(unreal.FrameRate(30,1));controller.set_number_of_frames(unreal.FrameNumber(30))
  for bone in names:
   k=str(bone);controller.add_bone_curve(bone);p=[];q=[];sc=[]
   for f in range(31):
    a=f/30 if standing else 0.;v=seated[k];u=local[k];p.append(v.translation*(1-a)+u.translation*a);q.append(unreal.MathLibrary.quat_slerp(v.rotation,u.rotation,a));sc.append(v.scale3d)
   controller.set_bone_track_keys(bone,p,q,sc)
  controller.close_bracket();E.save_loaded_asset(asset);out.append(path)
 json.dump({'success':True,'assets':out,'bones':len(names)},open(P+'Saved/SeatedPoseBuild.json','w'),indent=2)
except Exception:json.dump({'success':False,'error':traceback.format_exc()},open(P+'Saved/SeatedPoseBuild.json','w'),indent=2)





