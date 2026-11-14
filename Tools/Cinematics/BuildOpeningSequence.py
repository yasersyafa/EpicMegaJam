"""Author the playable opening's sequence, camera, previs actor and camera power-on sound."""
import unreal,os,json,math,wave,struct
P=unreal.Paths.project_dir();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();R={'success':False,'errors':[]}
ROOT='/Game/Game/Cinematics/Opening';seqpath=ROOT+'/LS_Opening_Maya'
S.clear_actor_selection_set()
for a in list(S.get_all_level_actors()):
 if a.get_actor_label().startswith('CINE_Opening_'):S.destroy_actor(a)
# Camera and neutral stand-in are authored in the eventual confession room.
proxy=S.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(1230,1220,-35));proxy.set_actor_label('CINE_Opening_Maya_StandIn');proxy.set_folder_path('Cinematics/Opening/Previs');proxy.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False)
c=proxy.skeletal_mesh_component;c.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'));c.set_collision_profile_name('NoCollision');c.set_editor_property('cast_shadow',True)
cam=S.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(1230,1450,122));cam.set_actor_label('CINE_Opening_Camera_Closeup');cam.set_folder_path('Cinematics/Opening/Cameras');cam.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0),False)
cc=cam.get_cine_camera_component();cc.set_editor_property('current_focal_length',75.);cc.set_editor_property('current_aperture',5.6)
focus=cc.get_editor_property('focus_settings');focus.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE);cc.set_editor_property('focus_settings',focus)
# Soft local key, ordinary interview lighting. This is not a horror reveal.
light=S.spawn_actor_from_class(unreal.RectLight,unreal.Vector(1090,1380,210));light.set_actor_label('CINE_Opening_KeyLight');light.set_folder_path('Cinematics/Opening/Lighting');light.set_actor_rotation(unreal.Rotator(pitch=-20,yaw=-45,roll=0),False)
lc=light.get_component_by_class(unreal.RectLightComponent)
for k,v in [('intensity_units',unreal.LightUnits.LUMENS),('intensity',350.),('attenuation_radius',450.),('source_width',100.),('source_height',120.),('use_temperature',True),('temperature',4500.),('cast_shadows',False)]:lc.set_editor_property(k,v)
seq=unreal.load_asset(seqpath) if E.does_asset_exist(seqpath) else T.create_asset('LS_Opening_Maya',ROOT,unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
# Rebuild only this authored sequence if the script is rerun.
for b in list(seq.get_bindings()):b.remove()
for t in list(seq.get_tracks()):seq.remove_track(t)
seq.set_display_rate(unreal.FrameRate(30,1));seq.set_playback_start(0);seq.set_playback_end(900)
b=seq.add_possessable(cam);b.set_display_name('Opening / locked close-up')
t=b.add_track(unreal.MovieScene3DTransformTrack);sec=t.add_section();sec.set_range(0,900)
for ch,v in zip(sec.get_all_channels(),[1230.,1450.,122.,0.,0.,-90.,1.,1.,1.]):ch.set_default(v)
cut=seq.add_track(unreal.MovieSceneCameraCutTrack);cs=cut.add_section();cs.set_range(0,900);bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',b.get_id());cs.set_camera_binding_id(bid)
pb=seq.add_possessable(proxy);pb.set_display_name('Maya / TEMP mannequin stand-in')
track=pb.add_track(unreal.MovieSceneSkeletalAnimationTrack);asec=track.add_section();asec.set_range(0,900);params=asec.get_editor_property('params');params.set_editor_property('animation',unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'));asec.set_editor_property('params',params)
fade=seq.add_track(unreal.MovieSceneFadeTrack);fs=fade.add_section();fs.set_range(0,900);channel=fs.get_all_channels()[0]
for frame,value in [(0,1.),(30,1.),(60,0.),(720,0.),(750,1.),(899,1.)]:channel.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
fs.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
# Original generated sound: a short camera startup click and a two-note confirmation beep.
source=os.path.join(P,'SourceArt/Audio/Cinematics');os.makedirs(source,exist_ok=True);wavpath=os.path.join(source,'S_Opening_CameraPower.wav');rate=22050;pcm=[]
for i in range(int(rate*.7)):
 t=i/rate;v=0.
 if .01<t<.07:v+=.13*math.exp(-(t-.01)*75)*math.sin(2*math.pi*1800*t)
 if .18<t<.30:v+=.12*math.sin(2*math.pi*880*t)*math.sin(math.pi*(t-.18)/.12)
 if .34<t<.47:v+=.1*math.sin(2*math.pi*1175*t)*math.sin(math.pi*(t-.34)/.13)
 pcm.append(struct.pack('<h',int(max(-1,min(1,v))*32767)))
with wave.open(wavpath,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(pcm))
soundpath='/Game/Game/Audio/Cinematics/S_Opening_CameraPower'
if not E.does_asset_exist(soundpath):
 task=unreal.AssetImportTask();task.set_editor_property('filename',wavpath);task.set_editor_property('destination_path','/Game/Game/Audio/Cinematics');task.set_editor_property('destination_name','S_Opening_CameraPower');task.set_editor_property('automated',True);task.set_editor_property('save',True);T.import_asset_tasks([task])
sound=unreal.load_asset(soundpath);at=seq.add_track(unreal.MovieSceneAudioTrack);audio=at.add_section();audio.set_sound(sound);audio.set_range(0,21)
E.save_loaded_asset(seq)
R.update(success=True,sequence=seqpath,frames=900,seconds=30,stand_in=proxy.get_path_name(),camera=cam.get_path_name(),audio=soundpath)
with open(os.path.join(P,'Saved/OpeningSequenceReport.json'),'w') as f:json.dump(R,f,indent=2)
unreal.log('OPENING_SEQUENCE_AUTHORED')


