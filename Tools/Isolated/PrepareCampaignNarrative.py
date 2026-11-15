"""Align canonical team-review subtitles to supplied recordings; no generated voices."""
from pathlib import Path
import json,re,difflib,subprocess,textwrap
import imageio_ffmpeg
P=Path(__file__).resolve().parents[2]
manifest=json.loads((P/'Tools/Isolated/CampaignVO.json').read_text(encoding='utf-8'))
catalog={c['id']:c for c in json.loads((P/'Tools/Cinematics/DialogueCatalog.en.json').read_text(encoding='utf-8'))['cues']}
def ids(page,a,b):return [f'P{page:02d}_{i:02d}' for i in range(a,b+1)]
GROUPS={
 'Opening':ids(3,1,4),'Intro':ids(3,5,13),
 'L01_Perfect':ids(4,1,4)+ids(5,3,4),'L01_FailBlocking':ids(4,5,6),'L01_FailClue':ids(5,1,2),
 'L01_Aftermath':ids(5,5,9),'L01_CrewTransition':ids(5,10,12),'Interlude01':ids(5,13,17),
 'KitchenApproach':ids(6,1,7),'L02_Perfect':ids(6,8,12)+ids(7,1,1),
 'L02_FailBlocking':ids(7,2,3),'L02_FailLight':ids(7,4,5),'L02_Aftermath':ids(7,6,12),
 'ServiceTransition':ids(7,13,17),'Interlude02':ids(8,1,6),'LastRoomApproach':ids(8,7,14),
 'L03_FailChair':ids(9,1,2),'L03_FailLight':ids(9,3,4),'L03_Perfect':ids(9,5,9),
 'L03_Aftermath':ids(10,1,6),'Interlude03':ids(10,7,11),
 'FinalPickup':ids(10,12,18)+ids(11,1,7),'Confession':ids(11,8,17)+ids(12,1,1),'Reveal':ids(12,2,4),
}
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
def align(lines,clip):
    actual=[w for s in clip['segments'] for w in s['words']]
    expected=[];boundaries=[]
    for line in lines:
        start=len(expected);expected.extend(norm(w) for w in line['text'].split());boundaries.append((start,len(expected)))
    matches={}
    for block in difflib.SequenceMatcher(None,expected,[norm(w['word']) for w in actual],autojunk=False).get_matching_blocks():
        for n in range(block.size):matches[block.a+n]=block.b+n
    cues=[];matched=0
    for line,(a,b) in zip(lines,boundaries):
        found=[actual[matches[n]] for n in range(a,b) if n in matches]
        if found:
            start=min(w['start'] for w in found);end=max(w['end'] for w in found);matched+=len(found)
        else:
            start=clip['duration']*a/max(1,len(expected));end=clip['duration']*b/max(1,len(expected))
        cues.append({'id':line['id'],'speaker':line['speaker'],'text':line['text'],'start':round(start,3),'end':round(end,3)})
    return cues,round(matched/max(1,len(expected)),3)

result={'clips':{},'missing_vo':['L01_Aftermath','L03_Aftermath'],'editorial_notes':[
 'The sofa failure recording contains a spoken CUT. Its take audio is trimmed at 7.6 s; the remaining CUT is a separate player-triggered cue.',
 'The supplied Aftermath recording belongs to Scene 2. Scene 1 and 3 aftermaths use canonical subtitles and no substitute/generated voice.',
 'ASR is used only for timing. Names and subtitle wording come from the team-review dialogue catalog. Intro contains an ASR name discrepancy requiring listening review.'
]}
for key,linesids in GROUPS.items():
    lines=[catalog[i] for i in linesids]
    sourcekey='Aftermath' if key=='L02_Aftermath' else key
    clip=manifest['clips'].get(sourcekey)
    if clip:
        cues,match=align(lines,clip);duration=7.6 if key=='L01_FailBlocking' else clip['duration']
        result['clips'][key]={'sound':clip['asset'],'audio_duration':duration,'cues':cues,'alignment_ratio':match,'source':clip['source'],'vo':True}
    else:
        t=0.;cues=[]
        for line in lines:
            duration=max(2.,len(line['text'].split())/2.7)
            cues.append({'id':line['id'],'speaker':line['speaker'],'text':line['text'],'start':round(t,3),'end':round(t+duration,3)});t+=duration+.35
        result['clips'][key]={'sound':None,'audio_duration':t,'cues':cues,'vo':False}
    # Extend caption holds into natural pauses, without overlapping the next speaker.
    for i,cue in enumerate(result['clips'][key]['cues']):
        limit=result['clips'][key]['cues'][i+1]['start']-.04 if i+1<len(lines) else result['clips'][key]['audio_duration']
        cue['end']=round(max(cue['end'],min(limit,cue['end']+.35)),3)
cut_source=next((P/'SourceArt/Isolated/IbraCampaign/VO').glob('S_VO_L01_FailBlocking.wav'))
cut_wav=cut_source.parent/'S_VO_CutSofa.wav'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-ss','7.72','-i',str(cut_source),'-c:a','pcm_s16le',str(cut_wav)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
result['cut_sofa']={'wav':str(cut_wav.relative_to(P)).replace('\\','/'),'asset':'/Game/Game/Isolated/IbraCampaign/Audio/S_VO_CutSofa'}
(P/'Tools/Isolated/CampaignNarrative.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:{'vo':v['vo'],'seconds':v['audio_duration'],'alignment':v.get('alignment_ratio')} for k,v in result['clips'].items()},indent=2))
