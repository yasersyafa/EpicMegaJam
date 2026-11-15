"""Convert supplied VO locally and retain timed ASR for editorial verification."""
from pathlib import Path
import json,hashlib,subprocess,wave,os
import imageio_ffmpeg
from faster_whisper import WhisperModel

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('CAMPAIGN_VO_SOURCE','C:/Users/bdstd/Documents/VO Character'))
DEST=ROOT/'SourceArt/Isolated/IbraCampaign/VO'
DEST.mkdir(parents=True,exist_ok=True)
MANIFEST=ROOT/'Tools/Isolated/CampaignVO.json'
MAPPING={
 'Awal bgt masuk game - Maya cutscene':'Opening',
 'pre intro':'Intro',
 'Scene 02 - The Arrival (Living Room)':'L01_Perfect',
 'Failure - Sofa Blocking':'L01_FailBlocking',
 'Failure - Wardrobe Blocking':'L01_FailClue',
 'Crew Transition':'L01_CrewTransition',
 'Scene 03 — Interlude 01 Out of Frame':'Interlude01',
 'Scene 04 — Transition to Kitchen':'KitchenApproach',
 'Scene 05 — The Hollow Wall Kitchen ACTION — Perfect Take':'L02_Perfect',
 'Failure A — Cabinet Blocking':'L02_FailBlocking',
 'Failure B — Incorrect Lighting':'L02_FailLight',
 'Perfect Take — Aftermath':'Aftermath',
 'Crew Transition — Service Passage':'ServiceTransition',
 'Scene 06 — Interlude 02 The Edit':'Interlude02',
 'Scene 07 — Approach The Last Room':'LastRoomApproach',
 'Scene 08 — The Last Scene Failure A — Incorrect Chair':'L03_FailChair',
 'Failure B — Incorrect Lighting last':'L03_FailLight',
 'ACTION — Perfect Take last':'L03_Perfect',
 'Scene 09 — Interlude 03 The Ending':'Interlude03',
 'Scene 10 - Final Pickup':'FinalPickup',
 'Scene 11 - Final Confession':'Confession',
 'Final Reveal — The Full Frame':'Reveal',
 'Manual CUT':'ManualCut',
}
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
old=json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {'clips':{}}
result={'source_folder':str(SOURCE),'timing':'Local ASR; review text against Team Review v3.0. WAVs are normalized mono 48 kHz PCM16.','clips':{}}
model=None
for source in sorted(SOURCE.glob('*.mpeg')):
    key=MAPPING[source.stem]
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    wav=DEST/('S_VO_'+key+'.wav')
    previous=old.get('clips',{}).get(key,{})
    if not wav.exists() or previous.get('sha256')!=sha:
        subprocess.run([ffmpeg,'-y','-i',str(source),'-vn','-ac','1','-af','loudnorm=I=-18:TP=-2:LRA=11','-ar','48000','-c:a','pcm_s16le',str(wav)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    with wave.open(str(wav)) as f:duration=f.getnframes()/f.getframerate()
    clip={'source':source.name,'sha256':sha,'wav':str(wav.relative_to(ROOT)).replace('\\','/'),'duration':duration,'asset':'/Game/Game/Isolated/IbraCampaign/Audio/S_VO_'+key}
    if previous.get('sha256')==sha and previous.get('segments'):
        clip['segments']=previous['segments']
    else:
        if model is None:
            model=WhisperModel('base.en',device='cpu',compute_type='int8',cpu_threads=4,download_root=str(ROOT/'.codex/tools/whisper-models'))
        segments,info=model.transcribe(str(source),language='en',beam_size=5,word_timestamps=True,vad_filter=True)
        clip['segments']=[{'start':s.start,'end':s.end,'text':s.text.strip(),'words':[{'start':w.start,'end':w.end,'word':w.word.strip()} for w in (s.words or [])]} for s in segments]
    result['clips'][key]=clip
    MANIFEST.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(key,round(duration,2),' '.join(s['text'] for s in clip['segments']),flush=True)
assert len(result['clips'])==len(MAPPING)
result['duplicate_audio']=[[a,b] for a,ca in result['clips'].items() for b,cb in result['clips'].items() if a<b and ca['sha256']==cb['sha256']]
MANIFEST.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
