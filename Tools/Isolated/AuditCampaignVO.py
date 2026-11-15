"""Read-only audit of source integrity and normalized WAV formats/peaks."""
import json,wave,hashlib,array
from pathlib import Path
P=Path(__file__).resolve().parents[2]
manifest=json.loads((P/'Tools/Isolated/CampaignVO.json').read_text(encoding='utf-8'))
report={'sources':[],'wav_files':[],'errors':[]}
for name,clip in manifest['clips'].items():
    source=Path(manifest['source_folder'])/clip['source']
    same=source.exists() and hashlib.sha256(source.read_bytes()).hexdigest()==clip['sha256']
    report['sources'].append({'id':name,'unchanged':same})
    if not same:report['errors'].append('Source changed or missing: '+clip['source'])
for path in sorted((P/'SourceArt/Isolated/IbraCampaign/VO').glob('*.wav')):
    with wave.open(str(path)) as f:
        rate,channels,width,frames=f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes()
        samples=array.array('h',f.readframes(frames));peak=max((abs(v) for v in samples),default=0)
    ok=rate==48000 and channels==1 and width==2 and frames>0 and peak<32767
    report['wav_files'].append({'name':path.name,'rate':rate,'channels':channels,'seconds':round(frames/rate,3),'peak_dbfs':round(20*__import__('math').log10(max(peak,1)/32768),2),'passed':ok})
    if not ok:report['errors'].append('Invalid format/clipping: '+path.name)
report['passed']=not report['errors'] and len(report['sources'])==23 and len(report['wav_files'])==24
(P/'Saved/QA/CampaignAudioAudit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'original_sources':len(report['sources']),'normalized_wavs':len(report['wav_files']),'errors':report['errors']}))
