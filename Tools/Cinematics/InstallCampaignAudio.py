"""Add only campaign VO audio tracks; never rebuild visual tracks or save a map."""
import unreal,json,math,re,shutil,wave
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT=ROOT/'Saved/GrayBoxAudio';OUT.mkdir(exist_ok=True)
N=json.loads((ROOT/'Tools/Isolated/CampaignNarrative.json').read_text())['clips']
# (target, source clip, [(source cue index, target start seconds)])
PLAN=[
 ('Opening/LS_Opening_Maya','Opening',[(0,2),(1,7),(2,11),(3,17)]),
 ('Interludes/LS_Interlude01','Interlude01',[(0,0),(1,3.44),(2,7.95),(3,10.68),(4,15.19)]),
 ('L01/LS_L01_Opening','L01_Perfect',[(0,0),(1,2.73)]),
 ('L01/LS_L01_Blocked','L01_FailBlocking',[(0,.60)]),
 ('L01/LS_L01_MissedClue','L01_FailClue',[(0,3.20)]),
 ('L01/LS_L01_Perfect','L01_Perfect',[(2,0),(3,2.5),(4,5.59),(5,9.75)]),
 ('L02/LS_L02_Opening','L02_Perfect',[(0,0),(1,3.8)]),
 ('L02/LS_L02_Obstructed','L02_FailBlocking',[(0,.60)]),
 ('L02/LS_L02_Dark','L02_FailLight',[(0,8.60)]),
 ('L02/LS_L02_Perfect','L02_Perfect',[(2,0),(3,1.69),(4,5.13),(5,8.57)]),
]
LABEL='Campaign VO (audio only)'
def export(seq,name):
 t=unreal.AssetExportTask();t.object=seq;t.filename=str(OUT/name);t.exporter=unreal.ObjectExporterT3D();t.automated=True;t.prompt=False;t.replace_identical=True
 assert unreal.Exporter.run_asset_export_task(t)
 return (OUT/name).read_text()
def visual_text(text):
 # Exclude audio objects/references and invalidated change signatures only.
 lines=text.splitlines();result=[];skip=0
 for line in lines:
  if skip:
   if line.lstrip().startswith('Begin Object'):skip+=1
   elif line.lstrip().startswith('End Object'):skip-=1
   continue
  if line.lstrip().startswith('Begin Object') and 'MovieSceneAudio' in line:skip=1;continue
  if 'MovieSceneAudio' in line or line.strip().startswith('Signature='):continue
  result.append(line)
 return '\n'.join(result)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
report={'installed':[],'omitted':[],'visuals_identical':True}
for target,clip,placements in PLAN:
 path='/Game/Game/Cinematics/'+target;seq=unreal.load_asset(path);assert seq,path
 src=ROOT/'Content'/Path(path.removeprefix('/Game/')).with_suffix('.uasset');backup=OUT/'Backup'/src.relative_to(ROOT/'Content');backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(src,backup)
 before=export(seq,seq.get_name()+'_before.copy')
 for track in list(seq.get_tracks()):
  if isinstance(track,unreal.MovieSceneAudioTrack) and str(track.get_display_name())==LABEL:seq.remove_track(track)
 track=seq.add_track(unreal.MovieSceneAudioTrack);track.set_display_name(LABEL)
 rate=seq.get_display_rate();fps=rate.numerator/rate.denominator;tick=seq.get_tick_resolution();tps=tick.numerator/tick.denominator
 sound=unreal.load_asset(N[clip]['sound']);assert sound
 entries=[]
 for i,start in placements:
  cue=N[clip]['cues'][i];offset=max(0,cue['start']-.025);duration=cue['end']+.045-offset
  end_frame=math.ceil((start+duration)*fps)
  if end_frame>seq.get_playback_end():report['omitted'].append({'sequence':target,'text':cue['text'],'reason':'whole line exceeds fixed playback end'});continue
  sec=track.add_section();sec.set_sound(sound);sec.set_range(round(start*fps),end_frame);sec.set_editor_property('start_frame_offset',unreal.FrameNumber(round(offset*tps)));sec.set_editor_property('looping',False);sec.set_editor_property('suppress_subtitles',True)
  entries.append({'cue':i,'text':cue['text'],'start':start,'source_offset':offset,'end_frame':end_frame})
 after=export(seq,seq.get_name()+'_after.copy')
 assert visual_text(before)==visual_text(after),'NON_AUDIO_CHANGE: '+target
 assert unreal.EditorAssetLibrary.save_loaded_asset(seq,False)
 report['installed'].append({'sequence':path,'source':sound.get_path_name(),'sections':entries})
# Standalone CUT shout, ending within the silence before the next word at 0.72s.
manifest=json.loads((ROOT/'Tools/Isolated/CampaignVO.json').read_text())
source=ROOT/manifest['clips']['ManualCut']['wav'];dest=ROOT/'SourceArt/Audio/Cinematics/S_Director_Cut.wav';dest.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(source),'rb') as inp:
 params=inp.getparams();data=inp.readframes(round(.55*inp.getframerate()))
with wave.open(str(dest),'wb') as out:out.setparams(params);out.writeframes(data)
task=unreal.AssetImportTask();task.filename=str(dest);task.destination_path='/Game/Game/Audio/Cinematics';task.destination_name='S_Director_Cut';task.automated=True;task.replace_existing=True;task.save=True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
report['cut_sound']=task.imported_object_paths[0]
report['omitted'] += [{'source':x,'reason':'no matching target sequence'} for x in ['Intro','KitchenApproach','L01_CrewTransition','L02_Aftermath','L03 and finale']]
report['omitted'] += [{'source':x,'reason':'Surya hint follows outcome in gameplay; not inserted into cutscene'} for x in ['L01_FailBlocking','L01_FailClue','L02_FailBlocking','L02_FailLight']]
(OUT/'installation.json').write_text(json.dumps(report,indent=2));print('AUDIO_INSTALLED',len(report['installed']),'VISUALS_IDENTICAL')
