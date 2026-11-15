"""Background editor bootstrap: tests only PIE runtime; no editor-world unit tests."""
import unreal,types,sys,time,json,traceback
from pathlib import Path
m=types.ModuleType('graybox_audio_runtime');sys.modules[m.__name__]=m
m.__dict__.update(unreal=unreal,time=time,json=json,traceback=traceback,Path=Path)
exec(r'''
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()));OUT=ROOT/'Saved/GrayBoxAudio/Runtime';OUT.mkdir(parents=True,exist_ok=True)
installation=json.loads((ROOT/'Saved/GrayBoxAudio/installation.json').read_text())
report={'mode':'offscreen PIE runtime','deterministic_audio':True,'checks':[],'errors':[],'recordings':[]}
st={'phase':'boot','at':time.monotonic(),'deadline':time.monotonic()+600,'index':0,'cut_index':0,'recording':False}
def save(): (OUT/'report.json').write_text(json.dumps(report,indent=2))
def check(name,ok):
 report['checks'].append({'name':name,'passed':bool(ok)});save();assert ok,name

def voices(w):
 result=[]
 for c in unreal.ObjectIterator(unreal.AudioComponent):
  if c.get_world()!=w:continue
  sound=c.get_editor_property('sound')
  if sound and sound.get_name().startswith('S_VO_') and c.is_playing():result.append(c)
 return result

def start_record(w,name):
 unreal.AudioMixerLibrary.start_recording_output(w,40);st['recording']=True;st['record_name']=name

def stop_record(w):
 if st['recording']:
  unreal.AudioMixerLibrary.stop_recording_output(w,unreal.AudioRecordingExportType.WAV_FILE,st['record_name'],str(OUT));report['recordings'].append(st['record_name']+'.wav');st['recording']=False;save()

def play(w,seq):
 settings=unreal.MovieSceneSequencePlaybackSettings();settings.set_editor_property('disable_camera_cuts',True)
 player,actor=unreal.LevelSequencePlayer.create_level_sequence_player(w,seq,settings);st['player']=player;st['actor']=actor;player.play();st['at']=unreal.SystemLibrary.get_game_time_in_seconds(w);st['saw_voice']=False

def cleanup_player():
 player=st.get('player')
 if player:player.stop()
 actor=st.get('actor')
 if actor:actor.destroy_actor()
 st['player']=None;st['actor']=None

def tick(dt):
 try:
  now=time.monotonic();assert now<st['deadline'],'runtime timeout'
  if st['phase']=='boot':
   if now-st['at']<3:return
   unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play();st.update(phase='wait_pie',at=now);return
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  if st['phase']=='wait_pie':
   if now-st['at']<2:return
   actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
   for a in actors:
    if a.get_class().get_name()=='BP_OpeningDirector_C':a.call_method('FinishOpening')
    if a.get_class().get_name()=='BP_ArrivalDirector_C':a.set_actor_tick_enabled(False)
   manager=next(a for a in actors if a.get_class().get_name()=='BP_FilmSceneManager_C');st['manager']=manager;manager.call_method('OnIntroFinished');manager.call_method('StopDialogue');st.update(phase='normal_start',at=unreal.SystemLibrary.get_game_time_in_seconds(w));check('SB_GrayBox PIE world', 'SB_GrayBox' in w.get_name());return
  now=unreal.SystemLibrary.get_game_time_in_seconds(w)
  if st['phase']=='normal_start':
   if st['index']>=len(installation['installed']):st.update(phase='cut_start',at=now);return
   entry=installation['installed'][st['index']];seq=unreal.load_asset(entry['sequence']);start_record(w,seq.get_name());play(w,seq);st.update(phase='normal',entry=entry);return
  if st['phase']=='normal':
   player=st['player'];st['saw_voice']=st['saw_voice'] or bool(voices(w))
   if not player.is_playing() and now-st['at']>.3:
    check(st['entry']['sequence']+' audible VO component',st['saw_voice']);check('sequence completion stops VO',not voices(w));stop_record(w);cleanup_player();st['index']+=1;st.update(phase='normal_start',at=now)
   return
  manager=st['manager']
  if st['phase']=='cut_start':
   if st['cut_index']>=3:st.update(phase='skip_start',at=now);return
   # Production manager owns this player; CUT is routed through RequestActionCut.
   seq=unreal.load_asset('/Game/Game/Cinematics/'+['L01/LS_L01_Opening','L02/LS_L02_Opening','L01/LS_L01_Blocked'][st['cut_index']])
   start_record(w,'CUT_'+str(st['cut_index']));manager.call_method('PlaySequenceAsset',args=(seq,));st['player']=manager.get_editor_property('SequencePlayer');manager.set_editor_property('TakeState',type(manager.get_editor_property('TakeState')).TAKE_PLAYING);st.update(phase='cut_playing',at=now);return
  if st['phase']=='cut_playing' and now-st['at']>1.1:
   check('VO active before CUT '+str(st['cut_index']),bool(voices(w)));old_player=st['player'];manager.call_method('RequestActionCut');check('CUT stops SequencePlayer synchronously',not old_player.is_playing());check('CUT stops sequence VO synchronously',not voices(w));cut=manager.get_editor_property('CutAudio');check('CUT shout playing',cut is not None and cut.is_playing());st['cut']=cut;st.update(phase='cut_repeat',at=now);return
  if st['phase']=='cut_repeat' and now-st['at']>.15:
   manager.call_method('RequestActionCut')
   cuts=[c for c in unreal.ObjectIterator(unreal.AudioComponent) if c.get_world()==w and c.get_editor_property('sound') and c.get_editor_property('sound').get_name()=='S_Director_Cut' and c.is_playing()]
   check('repeat action never stacks CUT audio',len(cuts)<=1);check('retake clears previous CUT shout',manager.get_editor_property('CutAudio') is None);manager.call_method('ResetTake');st.update(phase='cut_tail',at=now);return
  if st['phase']=='cut_tail' and now-st['at']>.8:
   check('old VO remains stopped',not voices(w));stop_record(w);manager.call_method('ResetTake');check('reset clears CutAudio',manager.get_editor_property('CutAudio') is None);st['cut_index']+=1;st.update(phase='cut_start',at=now);return
  if st['phase']=='skip_start':
   seq=unreal.load_asset('/Game/Game/Cinematics/Opening/LS_Opening_Maya');play(w,seq);st.update(phase='skip_playing',at=now);return
  if st['phase']=='skip_playing' and now-st['at']>2.5:
   check('opening VO active before skip',bool(voices(w)));cleanup_player();check('opening stop/skip stops VO',not voices(w));start_record(w,'CutShoutFull');manager.call_method('PlayCutAudio');check('shout exists before reset',manager.get_editor_property('CutAudio').is_playing());st.update(phase='shout_full',at=now);return
  if st['phase']=='shout_full' and now-st['at']>.85:
   stop_record(w);manager.call_method('PlayCutAudio');manager.call_method('StopDialogue');check('new take dialogue cleanup stops shout',manager.get_editor_property('CutAudio') is None);manager.call_method('PlayCutAudio');st['end_cut']=manager.get_editor_property('CutAudio');unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();st.update(phase='end_pie',at=now);return
 except Exception:
  report['errors'].append(traceback.format_exc());report['failed_phase']=st['phase'];save()
  try:
   w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
   if w:stop_record(w)
  except:pass
  unreal.unregister_slate_post_tick_callback(st['handle']);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();unreal.SystemLibrary.quit_editor()

def after_tick(dt):
 if st['phase']=='end_pie' and unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None:
  try:alive=unreal.SystemLibrary.is_valid(st.get('end_cut'))
  except Exception as e:
   if 'ObjectInstance is null' not in str(e):raise
   alive=False
  check('EndPlay destroys CUT component',not alive);report['completed']=True;save();unreal.unregister_slate_post_tick_callback(st['handle']);unreal.unregister_slate_post_tick_callback(st['end_handle']);unreal.SystemLibrary.quit_editor()
st['handle']=unreal.register_slate_post_tick_callback(tick);st['end_handle']=unreal.register_slate_post_tick_callback(after_tick);save();print('GRAYBOX_AUDIO_RUNTIME_BOOTSTRAP')
''',m.__dict__)
