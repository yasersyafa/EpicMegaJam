"""Read-only asset/VO binding audit for the final campaign."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());ROOT='/Game/Game/Isolated/IbraCampaign'
data=json.loads((P/'Tools/Isolated/CampaignNarrative.json').read_text(encoding='utf-8'))
report={'checks':[],'errors':[]}
def check(name,ok):report['checks'].append({'name':name,'passed':bool(ok)})
try:
    for key,record in data['clips'].items():
        seq=unreal.load_asset(ROOT+'/Cinematics/LS_'+key);check(key+' sequence exists',isinstance(seq,unreal.LevelSequence))
        sections=[sec for tr in seq.get_tracks() if isinstance(tr,unreal.MovieSceneAudioTrack) for sec in tr.get_sections()]
        if record['vo']:
            check(key+' matching supplied VO bound',len(sections)==1 and sections[0].get_sound().get_path_name().split('.')[0]==record['sound'])
            sound=sections[0].get_sound();check(key+' sound has duration and is not looping',sound.get_editor_property('duration')>0 and not sound.get_editor_property('looping'))
            check(key+' audio range follows its recording/trim',abs((sections[0].get_end_frame()-sections[0].get_start_frame())/30-record['audio_duration'])<.05)
        else:check(key+' explicit silent fallback',not sections)
    check('black ellipsis sequence exists',isinstance(unreal.load_asset(ROOT+'/Cinematics/LS_BlackEllipsis'),unreal.LevelSequence))
    report['passed']=all(x['passed'] for x in report['checks'])
except Exception:report['errors'].append(traceback.format_exc());report['passed']=False
(P/'Saved/QA/CampaignAssetAudit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
