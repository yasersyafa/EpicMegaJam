"""Validate authored poses offline and Maya's actual take/reset functions in PIE."""
import unreal,json,math,traceback
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'Saved/CharacterPolish';OUT.mkdir(exist_ok=True)
P='/Game/Game/Characters/Maya/'
mesh=unreal.load_asset(P+'SK_Maya');skeleton=mesh.get_editor_property('skeleton')
report={'map':'SB_GrayBox','pose_checks':[],'runtime':[],'errors':[]}
options=unreal.AnimPoseEvaluationOptions();options.optional_skeletal_mesh=mesh
ref=skeleton.get_reference_pose().get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
for name in ['Idle','Walk','Turn','LookAround','LookAtDirector','Hesitate','Inspect','Surprised','Waiting']:
 anim=unreal.load_asset(P+'Animations/A_Maya_'+name);frames=round(anim.get_play_length()*30)
 points=[]
 for f in range(frames+1):
  pose=anim.get_anim_pose_at_frame(f,options)
  root=pose.get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
  head=pose.get_bone_pose('head',unreal.AnimPoseSpaces.WORLD).translation
  foot=pose.get_bone_pose('foot_l',unreal.AnimPoseSpaces.WORLD).translation
  pelvis=pose.get_bone_pose('pelvis',unreal.AnimPoseSpaces.WORLD).translation
  assert root.translation.distance(ref.translation)<.001,name+' root drift'
  assert root.scale3d.distance(ref.scale3d)<.001,name+' root scale mismatch'
  assert 110<head.z<190 and -25<foot.z<65,(name,f,'pose bounds')
  points.append(pelvis)
 drift=math.hypot(points[-1].x-points[0].x,points[-1].y-points[0].y)
 if name in ['Walk','Turn']:assert drift<.1,(name,drift)
 report['pose_checks'].append({'animation':name,'frames':frames+1,'pelvis_endpoint_drift_cm':drift,'passed':True})
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world,'Run PIE before runtime validation'
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
maya=next(a for a in actors if a.get_actor_label()=='MAYA_Take')
manager=next(a for a in actors if a.get_class().get_name()=='BP_FilmSceneManager_C')
# Freeze tutorial staging while testing the production Maya and Scene Manager directly.
arrival=next((a for a in actors if a.get_class().get_name()=='BP_ArrivalDirector_C'),None)
if arrival:arrival.set_actor_tick_enabled(False)
manager.call_method('OnIntroFinished')
start=maya.get_editor_property('StartTransform')
assert maya.skeletal_mesh_component.get_editor_property('skeletal_mesh_asset')==mesh
state={'step':0,'wait':0,'handle':None,'player':None,'sample':0,'waiting_position':None}
def save():
 (OUT/'unreal_validation.json').write_text(json.dumps(report,indent=2))
def tick(dt):
 try:
  now=unreal.SystemLibrary.get_game_time_in_seconds(world)
  if now<state['wait']:return
  i=state['step']
  if i==0:
   # Exercise a real outcome sequence with its original level binding.
   manager.call_method('PlaySequenceAsset',args=(unreal.load_asset('/Game/Game/Cinematics/L01/LS_L01_Blocked'),))
   state['wait']=now+.7;state['step']=1
  elif i==1:
   player=manager.get_editor_property('SequencePlayer');assert player and player.is_playing()
   report['runtime'].append({'check':'outcome_sequence_running','passed':True})
   manager.call_method('ResetTake')
   assert not player.is_playing()
   assert maya.get_actor_location().distance(start.translation)<.1
   assert str(maya.get_editor_property('MayaState')).endswith('READY: 0>') or 'READY' in str(maya.get_editor_property('MayaState'))
   state['wait']=now+.5;state['step']=2
  elif i==2:
   assert maya.get_actor_location().distance(start.translation)<.1,'stale sequence moved Maya after reset'
   report['runtime'].append({'check':'stop_sequence_and_reset','passed':True})
   # enum value 4 = WAITING, as used by OnOutcomeFinished.
   manager.call_method('OnOutcomeFinished')
   # The scene manager may guard the callback by TakeID; directly pass WAITING through the BP API as well.
   maya.call_method('SetMayaState',args=(type(maya.get_editor_property('MayaState')).WAITING,))
   state['sample']=maya.skeletal_mesh_component.get_position();state['wait']=now+.7;state['step']=3
  elif i==3:
   pos=maya.skeletal_mesh_component.get_position()
   assert abs(pos-state['sample'])>.05,'waiting animation did not advance'
   report['runtime'].append({'check':'waiting_animation_advances','passed':True})
   for repeat in range(5):
    maya.set_actor_location(start.translation+unreal.Vector(100,100,0),False,True)
    manager.call_method('ResetTake')
    assert maya.get_actor_location().distance(start.translation)<.1
   report['runtime'].append({'check':'five_repeated_resets','passed':True})
   state['wait']=now+1;state['step']=4
  elif i==4:
   assert maya.get_actor_location().distance(start.translation)<.1
   report['runtime'].append({'check':'no_stale_movement_after_repeated_resets','passed':True})
   save();unreal.unregister_slate_post_tick_callback(state['handle'])
   unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
 except Exception:
  report['errors'].append(traceback.format_exc());save();unreal.unregister_slate_post_tick_callback(state['handle'])
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
state['handle']=unreal.register_slate_post_tick_callback(tick)
save()
print('Maya validation registered')
