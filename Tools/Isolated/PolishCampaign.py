"""Private-map finishing: clear final framing and a real walk out of the master frame."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());ROOT='/Game/Game/Isolated/IbraCampaign';E=unreal.EditorAssetLibrary
A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors={a.get_actor_label():a for a in A.get_all_level_actors()};world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
R={'success':False,'errors':[]}
try:
    actors['CAMPAIGN_PatchedLivingWall'].set_actor_location(unreal.Vector(-548,-440,130),False,True)
    for label in ['CAMPAIGN_SealedDoorLeft','CAMPAIGN_SealedDoorRight','CAMPAIGN_SealedDoorTop']:
        a=actors[label];pos=a.get_actor_location();a.set_actor_location(unreal.Vector(pos.x,385,pos.z),False,True)
    for label,a in actors.items():
        if label=='CAMPAIGN_ReferenceCaption' or ('CAMPAIGN_' in label and 'MarkLabel' in label):a.set_actor_hidden_in_game(True)
    light=actors.get('CAMPAIGN_RevealFill')
    if not light:
        light=A.spawn_actor_from_class(unreal.PointLight,unreal.Vector(1230,850,185));light.set_actor_label('CAMPAIGN_RevealFill');light.set_folder_path('IbraCampaign/Lighting')
    lc=light.point_light_component;lc.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);lc.set_editor_property('intensity',0.);lc.set_editor_property('attenuation_radius',650.);lc.set_editor_property('use_temperature',True);lc.set_editor_property('temperature',4300.)
    guides=[a for label,a in actors.items() if 'CAMPAIGN_S' in label and 'DirectorMark' in label and isinstance(a,unreal.StaticMeshActor)]
    for path in E.list_assets(ROOT+'/Cinematics',recursive=False,include_folder=False):
        s=unreal.load_asset(path)
        if not isinstance(s,unreal.LevelSequence):continue
        key=s.get_name().removeprefix('LS_');end=s.get_playback_end()
        for b in list(s.get_bindings()):
            if str(b.get_display_name()).startswith('Final presentation / '):b.remove()
        b=s.add_possessable(lc);b.set_display_name('Final presentation / fill')
        tr=b.add_track(unreal.MovieSceneFloatTrack);tr.set_property_name_and_path('Intensity','Intensity');sec=tr.add_section();sec.set_range(0,end);sec.get_all_channels()[0].set_default(700. if key=='Reveal' else 0.);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
        for i,a in enumerate(guides):
            b=s.add_possessable(a);b.set_display_name('Final presentation / mark '+str(i));tr=b.add_track(unreal.MovieSceneVisibilityTrack);tr.set_property_name_and_path('bHidden','bHidden');sec=tr.add_section();sec.set_range(0,end);sec.get_all_channels()[0].set_default(key not in ['Confession','Reveal']);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
        E.save_loaded_asset(s)
    seq=unreal.load_asset(ROOT+'/Cinematics/LS_Reveal');end=seq.get_playback_end();maya=actors['CAMPAIGN_ConfessionMaya'];found=0
    for binding in seq.get_bindings():
        if maya in seq.locate_bound_objects(binding,world):
            for track in list(binding.get_tracks()):
                if isinstance(track,(unreal.MovieScene3DTransformTrack,unreal.MovieSceneSkeletalAnimationTrack)):binding.remove_track(track);found+=1
    assert found>=2,'Could not locate the existing master subject tracks'
    b=seq.add_possessable(maya);sec=b.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,end);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    for frame,pos,yaw in [(0,(1230,1220,0),0),(115,(1230,1220,0),-90),(210,(1480,1220,0),-90)]:
        for ch,value in zip(sec.get_all_channels(),[*pos,0,0,yaw,1,1,1]):ch.add_key(unreal.FrameNumber(frame),float(value),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    tr=b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for start,stop,name in [(0,115,'A_Tripo_Wait'),(115,210,'A_Tripo_Walk'),(210,end,'A_Tripo_Wait')]:
        sec=tr.add_section();sec.set_range(start,stop);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE);params=sec.get_editor_property('params');params.set_editor_property('animation',unreal.load_asset('/Game/Characters/Tripo/Anims/'+name));sec.set_editor_property('params',params)
    E.save_loaded_asset(seq);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();R.update(success=True,removed_subject_tracks=found,guide_marks=len(guides))
except Exception:R['errors'].append(traceback.format_exc())
(P/'Saved/QA/CampaignPolish.json').write_text(json.dumps(R,indent=2),encoding='utf-8')
