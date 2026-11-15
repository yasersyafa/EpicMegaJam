"""Apply Maya's isolated rig and reaction library to existing L01/L02 take tracks.
Preserves cameras, event tracks, scene configuration, prop transforms and bindings.
"""
import unreal, math
P='/Game/Game/Characters/Maya/'
mesh=unreal.load_asset(P+'SK_Maya')
anims={n:unreal.load_asset(P+'Animations/A_Maya_'+n) for n in ['Idle','Walk','LookAround','LookAtDirector','Hesitate','Inspect','Surprised','Waiting','Turn']}
assert mesh and all(anims.values())
BP='/Game/Game/Blueprints/Characters/BP_Maya'
bp=unreal.load_asset(BP);cdo=unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class(BP))
cdo.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
cdo.skeletal_mesh_component.set_material(0,mesh.get_editor_property('materials')[0].material_interface)
cdo.set_editor_property('IdleAnim',anims['Idle']);cdo.set_editor_property('WaitingAnim',anims['Waiting'])
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
maya=next(a for a in actors if a.get_actor_label()=='MAYA_Take')
comp=maya.get_component_by_class(unreal.SkeletalMeshComponent)
comp.set_skeletal_mesh_asset(mesh);comp.set_material(0,mesh.get_editor_property('materials')[0].material_interface);comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE);comp.set_animation(anims['Idle']);comp.set_update_animation_in_editor(True)
maya.set_editor_property('IdleAnim',anims['Idle'])
maya.set_actor_hidden_in_game(True)  # Revealed only by the intro handoff.
# Same +Y mesh forward as the former Quinn: keep existing -90 degree facing offset.
maya.set_editor_property('MeshYawOffset',-90.0)
clips={
 'Interlude01':[(0,238,'Idle'),(238,320,'LookAtDirector'),(320,456,'Hesitate'),(456,615,'Idle')],
 'L01_Opening':[(0,180,'LookAround'),(180,225,'Walk')],
 'L01_Blocked':[(0,15,'Walk'),(15,65,'Hesitate'),(65,125,'LookAtDirector'),(125,150,'Waiting')],
 'L01_MissedClue':[(0,120,'Walk'),(120,170,'LookAround'),(170,195,'Hesitate')],
 'L01_Perfect':[(0,120,'Walk'),(120,150,'Turn'),(150,390,'Inspect')],
 'L02_Opening':[(0,90,'LookAround'),(90,195,'Walk')],
 'L02_Obstructed':[(0,12,'Walk'),(12,70,'Hesitate'),(70,120,'LookAtDirector'),(120,150,'Waiting')],
 'L02_Dark':[(0,230,'Walk'),(230,255,'Turn'),(255,315,'Inspect'),(315,345,'Hesitate')],
 'L02_Perfect':[(0,230,'Walk'),(230,255,'Turn'),(255,465,'Inspect'),(465,525,'Surprised')],
}
for name,parts in clips.items():
 folder='Interludes' if name=='Interlude01' else name[:3]
 seq=unreal.load_asset('/Game/Game/Cinematics/'+folder+'/LS_'+name)
 binding=next(b for b in seq.get_bindings() if any(isinstance(t,unreal.MovieSceneSkeletalAnimationTrack) for t in b.get_tracks()))
 for track in list(binding.get_tracks()):
  if isinstance(track,unreal.MovieSceneSkeletalAnimationTrack):binding.remove_track(track)
 track=binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
 for index,(start,end,kind) in enumerate(parts):
  sec=track.add_section();first=index==0;last=index==len(parts)-1
  a0=max(0,start-(0 if first else 4));a1=min(seq.get_playback_end(),end+(0 if last else 4))
  sec.set_range(a0,a1);sec.set_row_index(index%2);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
  params=sec.get_editor_property('params');params.set_editor_property('animation',anims[kind]);params.set_editor_property('skip_anim_notifiers',True)
  # Let sustained inspections/look reactions span their segment, rather than restart halfway.
  if kind not in ['Walk','Turn','Waiting']:
   rate=params.get_editor_property('play_rate');rate.set_fixed_play_rate(anims[kind].get_play_length()/((end-start)/30));params.set_editor_property('play_rate',rate)
  sec.set_editor_property('params',params)
  channel=sec.get_all_channels()[0]
  if not first:
   channel.add_key(unreal.FrameNumber(a0),0.0,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
   channel.add_key(unreal.FrameNumber(start+4),1.0,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
  if not last:
   channel.add_key(unreal.FrameNumber(end-4),1.0,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
   channel.add_key(unreal.FrameNumber(a1),0.0,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 # Constant intervals must remain stationary; auto tangents can drift before the walk starts.
 for t in binding.get_tracks():
  if isinstance(t,unreal.MovieScene3DTransformTrack):
   for sec in t.get_sections():
    for channel in sec.get_all_channels()[:3]:
     for key in channel.get_keys():key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
    if name=='Interlude01':
     for key in sec.get_all_channels()[5].get_keys():key.set_value(0.0)
 unreal.EditorAssetLibrary.save_loaded_asset(seq)
 print('STAGED',name)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('MAYA_STAGING_COMPLETE')
