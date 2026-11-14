import unreal,json,os,wave,struct,math
P=unreal.Paths.project_dir();E=unreal.EditorAssetLibrary;S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);T=unreal.AssetToolsHelpers.get_asset_tools();A={a.get_actor_label():a for a in S.get_all_level_actors()};root=P+'SourceArt/Audio/Cinematics';os.makedirs(root,exist_ok=True)
rate=22050;pcm=[]
for i in range(rate):
 t=i/rate;v=0
 for offset in [.12,.48]:
  d=t-offset
  if 0<d<.15:v+=.28*math.exp(-d*35)*(math.sin(2*math.pi*110*d)+.3*math.sin(2*math.pi*190*d))
 pcm.append(struct.pack('<h',int(max(-1,min(1,v))*32767)))
file=root+'/S_Building_SoftKnock.wav'
with wave.open(file,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(pcm))
path='/Game/Game/Audio/Cinematics/S_Building_SoftKnock'
if not E.does_asset_exist(path):
 t=unreal.AssetImportTask();t.filename=file;t.destination_path='/Game/Game/Audio/Cinematics';t.destination_name='S_Building_SoftKnock';t.automated=True;t.save=True;T.import_asset_tasks([t])
report=json.load(open(P+'Saved/NarrativeBuildReport.json'))
for idx,sound,offset in [(7,path,15.),(22,'/Game/Game/Audio/Cinematics/S_Opening_CameraPower',22.9)]:
 seq=unreal.load_asset(report['sequences'][idx]['path'])
 for tr in list(seq.get_tracks()):
  if isinstance(tr,unreal.MovieSceneAudioTrack):seq.remove_track(tr)
 tr=seq.add_track(unreal.MovieSceneAudioTrack);sec=tr.add_section();sec.set_sound(unreal.load_asset(sound));sec.set_range(round(offset*30),round((offset+.7)*30));E.save_loaded_asset(seq)
# Soft illumination for the evidence call sheet, outside playable space.
a=A.get('NAR_Light_EvidenceInsert') or S.spawn_actor_from_class(unreal.RectLight,unreal.Vector(3200,0,220));a.set_actor_label('NAR_Light_EvidenceInsert');a.set_actor_rotation(unreal.Rotator(pitch=-20,yaw=180,roll=0),False);c=a.get_component_by_class(unreal.RectLightComponent);c.set_editor_property('intensity',350.);c.set_editor_property('attenuation_radius',500.);c.set_editor_property('cast_shadows',False)
# The two aborted capture actors have no target and were temporary editor helpers.
for x in S.get_all_level_actors():
 if isinstance(x,unreal.SceneCapture2D) and not x.capture_component2d.texture_target:S.destroy_actor(x)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
