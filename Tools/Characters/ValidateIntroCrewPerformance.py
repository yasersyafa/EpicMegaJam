"""Check binding compatibility, all crew proportions, and live intro/interlude deformation."""
import unreal,json,traceback,math
from pathlib import Path
OUT=Path(unreal.Paths.project_saved_dir())/'CharacterPolish/IntroCrewValidation';OUT.mkdir(parents=True,exist_ok=True)
r={'binding_checks':[],'pose_checks':[],'runtime_checks':[],'errors':[]}
def save(): (OUT/'report.json').write_text(json.dumps(r,indent=2))
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert editor is not None,'Run this before starting PIE'
for data in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path('/Game/Game/Cinematics',recursive=True):
 if str(data.asset_class_path.asset_name)!='LevelSequence':continue
 seq=data.get_asset()
 for binding in seq.get_bindings():
  tracks=[t for t in binding.get_tracks() if isinstance(t,unreal.MovieSceneSkeletalAnimationTrack)]
  if not tracks:continue
  bound=unreal.MovieSceneSequenceExtensions.locate_bound_objects(seq,binding,editor)
  for actor in bound:
   components=[actor] if isinstance(actor,unreal.SkeletalMeshComponent) else actor.get_components_by_class(unreal.SkeletalMeshComponent)
   for component in components:
    mesh=component.get_editor_property('skeletal_mesh_asset')
    if not mesh:continue
    if mesh.get_path_name().startswith('/Game/Game/Characters/'):
     root=mesh.get_editor_property('skeleton').get_reference_pose().get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
     assert root.scale3d.distance(unreal.Vector(1,1,1))<.001,(mesh.get_name(),'nonunit bind scale')
    for track in tracks:
     for section in track.get_sections():
      anim=section.get_editor_property('params').animation
      assert anim and anim.get_editor_property('skeleton')==mesh.get_editor_property('skeleton'),(seq.get_name(),actor.get_name(),anim,'skeleton mismatch')
      r['binding_checks'].append({'sequence':seq.get_name(),'actor':actor.get_name(),'animation':anim.get_name(),'passed':True})
for folder,meshes,animations in [('/Game/Game/Characters/Maya/',['SK_Maya'],['ReadScript','WalkWithScript','Confession','TurnLeft','TurnRight']),('/Game/Game/Characters/Crew/',['SK_Crew_Camera','SK_Crew_Boom','SK_Crew_Base'],['Idle','Walk','Focused'])]:
 for mesh_name in meshes:
  mesh=unreal.load_asset(folder+mesh_name);options=unreal.AnimPoseEvaluationOptions();options.optional_skeletal_mesh=mesh
  for name in animations:
   anim=unreal.load_asset(folder+'Animations/'+('A_Maya_' if 'Maya/' in folder else 'A_Crew_')+name);count=round(anim.get_play_length()*30)
   minimum=10000;maximum=0
   for frame in range(count+1):
    pose=anim.get_anim_pose_at_frame(frame,options)
    head=pose.get_bone_pose('head',unreal.AnimPoseSpaces.WORLD).translation
    foot=pose.get_bone_pose('foot_l',unreal.AnimPoseSpaces.WORLD).translation
    assert 110<head.z<195 and -25<foot.z<70,(mesh_name,name,frame,head,foot)
    for bone in ['hand_l','hand_r','lowerarm_l','lowerarm_r']:
     p=pose.get_bone_pose(bone,unreal.AnimPoseSpaces.WORLD).translation
     assert abs(p.x)<130 and abs(p.y)<130 and -20<p.z<220,(mesh_name,name,frame,bone,p)
    minimum=min(minimum,head.z);maximum=max(maximum,head.z)
   r['pose_checks'].append({'mesh':mesh_name,'animation':name,'frames':count+1,'head_height_cm':[minimum,maximum],'passed':True})
save()
st={'step':0,'wait':0,'deadline':None,'handle':None,'samples':0,'seen_stages':set()}
def tick(dt):
 try:
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  unreal.GameplayStatics.set_global_time_dilation(w,3)
  now=unreal.SystemLibrary.get_game_time_in_seconds(w)
  if st['deadline'] is None:st['deadline']=now+110
  assert now<st['deadline'],'Intro runtime validation timed out'
  actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
  by_label={a.get_actor_label():a for a in actors}
  arrival=next(a for a in actors if a.get_class().get_name()=='BP_ArrivalDirector_C')
  manager=next(a for a in actors if a.get_class().get_name()=='BP_FilmSceneManager_C')
  stage=int(arrival.get_editor_property('Stage'));st['seen_stages'].add(stage)
  maya=by_label['MAYA_Take']
  for a in actors:
   if a.get_editor_property('hidden'):continue
   for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
    mesh=c.get_editor_property('skeletal_mesh_asset')
    if not mesh or not mesh.get_path_name().startswith('/Game/Game/Characters/'):continue
    root=c.get_bone_transform('root',unreal.RelativeTransformSpace.RTS_COMPONENT)
    assert root.scale3d.distance(unreal.Vector(1,1,1))<.01,(a.get_actor_label(),'live nonunit root')
    h=c.get_bone_transform('head',unreal.RelativeTransformSpace.RTS_COMPONENT).translation
    f=c.get_bone_transform('foot_l',unreal.RelativeTransformSpace.RTS_COMPONENT).translation
    assert c.get_material(0) is not None,(a.get_actor_label(),'missing material')
    assert 105<h.z<200 and -30<f.z<75,(a.get_actor_label(),'live deformation',h,f)
    st['samples']+=1
  def shot(name):unreal.SystemLibrary.execute_console_command(w,'Shot filename="'+str(OUT/(name+'.png'))+'" -nosuffix',None)
  if st['step']==0:
   # The opening was playing before PIE; allow a rendered shot before leaving it.
   if now<2:return
   assert all(by_label[n].get_editor_property('hidden') for n in ['Crew_Camera','Crew_Boom','Crew_Gaffer','Crew_Script','NPC_Intro_CrewC_Lobby']), 'take cast visible before intro handoff'
   r['runtime_checks'].append({'check':'no_take_cast_during_tutorial','passed':True})
   shot('opening');st['step']=1;st['wait']=now+1
  elif st['step']==1 and now>st['wait']:
   opening=next(a for a in actors if a.get_class().get_name()=='BP_OpeningDirector_C');opening.call_method('FinishOpening')
   st['wait']=now+1;st['step']=2
  elif st['step']==2 and now>st['wait']:
   arrival.call_method('StartConversation');st['step']=3
  elif st['step']==3:
   if stage==7:
    st['step']=31;st['wait']=now+4
   elif stage==8:raise AssertionError('Intro skipped script-reading stage')
  elif st['step']==31 and now>st['wait']:
    paper=by_label['PROP_Intro_Maya_Script'];origin,extent=paper.get_actor_bounds(False)
    assert max(extent.x,extent.y,extent.z)<60,'script inherited bone scale'
    shot('intro_script');r['runtime_checks'].append({'check':'intro_read_script_and_prop_scale','passed':True});st['step']=4
  elif st['step']==4 and stage==8:
   r['runtime_checks'].append({'check':'intro_completes_without_deformation','passed':True})
   arrival.set_actor_tick_enabled(False);manager.call_method('OnIntroFinished')
   for label in ['Crew_Camera','Crew_Boom','Crew_Gaffer','Crew_Script']:by_label[label].call_method('SetCrewFocus',args=(True,))
   st['wait']=now+1;st['step']=5
  elif st['step']==5 and now>st['wait']:
   for label in ['Crew_Camera','Crew_Boom','Crew_Gaffer','Crew_Script']:
    assert by_label[label].get_editor_property('bFocused')
    assert not by_label[label].get_editor_property('hidden')
    assert by_label[label].get_component_by_class(unreal.SkeletalMeshComponent).get_material(0) is not None
    by_label[label].call_method('SetCrewFocus',args=(False,))
   assert all(by_label[n].get_editor_property('hidden') for n in ['NPC_Intro_CrewA_PropMaster','NPC_Intro_CrewB_SetDresser','NPC_Intro_CrewC_Lobby']), 'intro extras survived handoff'
   r['runtime_checks'].append({'check':'four_crew_focus_relax_transitions','passed':True})
   manager.call_method('PlaySequenceAsset',args=(unreal.load_asset('/Game/Game/Cinematics/Interludes/LS_Interlude01'),))
   st['wait']=now+5;st['step']=6
  elif st['step']==6 and now>st['wait']:
   shot('interlude_fixed');r['runtime_checks'].append({'check':'interlude_live_no_deformation','passed':True})
   st['wait']=now+1;st['step']=61
  elif st['step']==61 and now>st['wait']:
   manager.call_method('ResetTake');st['wait']=now+1;st['step']=7
  elif st['step']==7 and now>st['wait']:
   assert maya.get_actor_location().distance(maya.get_editor_property('StartTransform').translation)<.1
   r['runtime_checks'].append({'check':'interlude_reset_returns_maya','passed':True})
   r['live_pose_samples']=st['samples'];r['intro_stages_seen']=sorted(st['seen_stages']);save()
   unreal.GameplayStatics.set_global_time_dilation(w,1);unreal.unregister_slate_post_tick_callback(st['handle']);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
 except Exception:
  r['errors'].append(traceback.format_exc());r['live_pose_samples']=st['samples'];save();unreal.unregister_slate_post_tick_callback(st['handle'])
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
st['handle']=unreal.register_slate_post_tick_callback(tick)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
print('Intro/crew validation started')
