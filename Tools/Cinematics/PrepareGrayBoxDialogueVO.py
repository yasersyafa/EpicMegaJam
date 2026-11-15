"""Extract only exact spoken lines used by the production graybox dialogue."""
import json,re,wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
N=json.loads((ROOT/'Tools/Isolated/CampaignNarrative.json').read_text())['clips']
V=json.loads((ROOT/'Tools/Isolated/CampaignVO.json').read_text())['clips']
D=json.loads((ROOT/'Saved/GrayBoxAudio/AvailabilityAudit/DT_Dialogue.json').read_text(encoding='utf-8-sig'))
OUT=ROOT/'SourceArt/Audio/GrayBoxDialogue';OUT.mkdir(parents=True,exist_ok=True)
GROUPS=['Intro','L01_CrewTransition','KitchenApproach','L02_Aftermath','ServiceTransition','L01_FailBlocking','L01_FailClue','L02_FailBlocking','L02_FailLight']
def norm(s):
 s=re.sub(r'^NSLOCTEXT\([^,]+,[^,]+,\s*"(.*)"\)$',r'\1',s).replace("\\'","'")
 return re.sub(r'[^a-z0-9]+','',s.lower())
rows={norm(x['SubtitleText']):x['Name'] for x in D}
report={'clips':[],'unmatched':[]}
for group in GROUPS:
 source=ROOT/V['Aftermath' if group=='L02_Aftermath' else group]['wav']
 with wave.open(str(source),'rb') as inp:
  params=inp.getparams();rate=inp.getframerate();frames=inp.readframes(inp.getnframes());width=inp.getsampwidth()*inp.getnchannels()
  for index,cue in enumerate(N[group]['cues']):
   key=rows.get(norm(cue['text']))
   if group=='Intro':key='INTRO_'+str(index+1).zfill(2)
   if not key or key.startswith(('L01_MAYA','L02_MAYA')):
    report['unmatched'].append({'group':group,'cue':index,'text':cue['text']});continue
   start=max(0,round((cue['start']-.025)*rate));end=min(len(frames)//width,round((cue['end']+.075)*rate))
   name='S_VO_GB_'+key;dest=OUT/(name+'.wav')
   with wave.open(str(dest),'wb') as wav:wav.setparams(params);wav.writeframes(frames[start*width:end*width])
   report['clips'].append({'id':key,'source':group,'cue':index,'asset':'/Game/Game/Audio/VoiceOver/'+name,'wav':str(dest),'duration':(end-start)/rate,'text':cue['text']})
# Full manual CUT and sofa-specific CUT are already independently trimmed to their spoken text.
for key,group in [('CUT_EARLY','ManualCut'),('L01_CUT_BLOCKED','CutSofa')]:
 source=ROOT/(V[group]['wav'] if group in V else 'SourceArt/Isolated/IbraCampaign/VO/S_VO_CutSofa.wav');name='S_VO_GB_'+key;dest=OUT/(name+'.wav')
 dest.write_bytes(source.read_bytes())
 with wave.open(str(dest),'rb') as wav:duration=wav.getnframes()/wav.getframerate()
 report['clips'].append({'id':key,'source':group,'cue':0,'asset':'/Game/Game/Audio/VoiceOver/'+name,'wav':str(dest),'duration':duration,'text':key})
assert len(report['clips'])==37,len(report['clips'])
assert not [x for x in report['unmatched'] if x['group'] not in ('L01_FailBlocking','L01_FailClue','L02_FailBlocking','L02_FailLight')]
(ROOT/'Saved/GrayBoxAudio/PreparedDialogue.json').write_text(json.dumps(report,indent=2))
print('PREPARED',len(report['clips']))
