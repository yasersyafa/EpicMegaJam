"""Apply private-map presentation and input flags after graph authoring."""
import unreal,json
from pathlib import Path
P=Path(unreal.Paths.project_dir());ROOT='/Game/Game/Isolated/IbraCampaign';E=unreal.EditorAssetLibrary
bp=unreal.load_asset(ROOT+'/Blueprints/BP_CampaignDirector')
for name in ['Crew1','Crew2','Crew3']:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
count=0
for i in range(500):
    node=unreal.find_object(None,bp.get_path_name()+':EventGraph.K2Node_InputKey_'+str(i))
    if node:
        node.set_editor_property('bConsumeInput',False)
        if str(node.get_editor_property('InputKey').get_editor_property('KeyName')) in ['P','Escape']:node.set_editor_property('bExecuteWhenPaused',True)
        count+=1
unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
director=actors['CAMPAIGN_Director'];director.set_editor_property('PlaybackSettings',unreal.MovieSceneSequencePlaybackSettings(finish_completion_state_override=unreal.MovieSceneCompletionModeOverride.FORCE_KEEP_STATE))
for i,pos in [(1,(400,-500,0)),(2,(350,-500,0)),(3,(450,-400,0))]:
    actor=actors['CAMPAIGN_Crew'+str(i)];director.set_editor_property('Crew'+str(i),actor);actor.set_actor_location(unreal.Vector(*pos),False,True)
surya=actors['CAMPAIGN_FinalPose0'];surya.skeletal_mesh_component.override_animation_data(unreal.load_asset('/Game/Characters/Surya/Anims/MM_Idle_Surya'),is_looping=False,is_playing=False)
master=actors['CAMPAIGN_MasterConfession'].get_cine_camera_component()
for key in ['Opening','Interlude01','Interlude02','Interlude03','Confession']:
    seq=unreal.load_asset(ROOT+'/Cinematics/LS_'+key)
    for binding in list(seq.get_bindings()):
        if str(binding.get_display_name())=='Master crop reset':binding.remove()
    binding=seq.add_possessable(master);binding.set_display_name('Master crop reset')
    for prop,value in [('Filmback.SensorWidth',36.),('Filmback.SensorHeight',20.25)]:
        track=binding.add_track(unreal.MovieSceneFloatTrack);track.set_property_name_and_path(prop.split('.')[-1],prop)
        section=track.add_section();section.set_range(0,seq.get_playback_end());section.get_all_channels()[0].set_default(value);section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    E.save_loaded_asset(seq)
seq=unreal.load_asset(ROOT+'/Cinematics/LS_FinalPickup');end=seq.get_playback_end()
for binding in list(seq.get_bindings()):
    for track in list(binding.get_tracks()):
        if isinstance(track,unreal.MovieSceneVisibilityTrack):binding.remove_track(track)
for label in ['CAMPAIGN_Maya','CAMPAIGN_ConfessionMaya']+[f'CAMPAIGN_FinalPose{i}' for i in range(4)]:
    actor=actors[label];b=seq.add_possessable(actor);tr=b.add_track(unreal.MovieSceneVisibilityTrack);tr.set_property_name_and_path('bHidden','bHidden');s=tr.add_section();s.set_range(0,end);s.get_all_channels()[0].set_default(label=='CAMPAIGN_ConfessionMaya');s.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
E.save_loaded_asset(seq)
recordings=['Opening','Interlude01','Interlude02','Interlude03','Confession','Reveal']
for path in E.list_assets(ROOT+'/Cinematics',recursive=False,include_folder=False):
    seq=unreal.load_asset(path)
    if not isinstance(seq,unreal.LevelSequence):continue
    key=seq.get_name().removeprefix('LS_');end=seq.get_playback_end()
    if key!='BlackEllipsis':
        for track in list(seq.get_tracks()):
            if isinstance(track,unreal.MovieSceneFadeTrack):seq.remove_track(track)
        tr=seq.add_track(unreal.MovieSceneFadeTrack);s=tr.add_section();s.set_range(0,end);s.get_all_channels()[0].set_default(0.);s.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    for binding in list(seq.get_bindings()):
        if str(binding.get_display_name()).startswith('Crew framing / '):binding.remove()
    for i in [1,2,3]:
        b=seq.add_possessable(actors['CAMPAIGN_Crew'+str(i)]);b.set_display_name('Crew framing / '+str(i));tr=b.add_track(unreal.MovieSceneVisibilityTrack);tr.set_property_name_and_path('bHidden','bHidden');s=tr.add_section();s.set_range(0,end)
        s.get_all_channels()[0].set_default(key not in recordings and '_Perfect' not in key and '_Fail' not in key);s.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    E.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
(P/'Saved/QA/CampaignFinalize.json').write_text(json.dumps({'input_nodes':count,'final_pickup_single_maya':True,'master_crop_reset':True},indent=2))
