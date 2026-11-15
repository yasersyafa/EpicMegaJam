"""Stop intro voice when the arrival director hands control to the scene manager."""
import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Flow/BP_ArrivalDirector';src=Path('Content/Game/Blueprints/Flow/BP_ArrivalDirector.uasset');backup=Path('Saved/GrayBoxAudio/Backup/BeforeDialogueVO_'+src.name)
if not backup.exists():shutil.copy2(src,backup)
s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph')
finish=next(n for n in s['nodes'] if n['title']=='FinishIntroduction' and n['type']=='K2Node_CustomEvent')
link=next(p for p in finish['connectedPins'] if p['pin']=='then')['linkedTo'][0]
g=Graph(P,'EventGraph')
hud=g.get('ArrivalHUD');g.fn('validHUD','KismetSystemLibrary','IsValid');g.wire(hud,'validHUD.Object')
yes,no=g.branch('validHUD.ReturnValue',finish['id']+'.then')
g.fn('stopIntroVoice','WBP_Scene01Objective_C','StopIntroVoice',yes);g.wire(hud,'stopIntroVoice.self')
g.wire('stopIntroVoice.then',link['node']+'.'+link['pin']);g.wire(no,link['node']+'.'+link['pin']);g.build()
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P);print('ARRIVAL_VO_HANDOFF',r)
