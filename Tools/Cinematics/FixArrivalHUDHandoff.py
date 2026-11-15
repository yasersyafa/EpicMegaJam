"""Remove the tutorial HUD before the take HUD becomes the subtitle owner."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph

path='/Game/Game/Blueprints/Flow/BP_ArrivalDirector'
summary=call('read_blueprint_graph_summary',path=path,graphName='EventGraph')
if not any(n['title']=='Remove from Parent' and n['x']>3000 for n in summary['nodes']):
 graph=Graph(path,'EventGraph')
 graph.fn('removeArrivalHUD','Widget','RemoveFromParent','5C5D676E.then')
 graph.wire(graph.get('ArrivalHUD'),'removeArrivalHUD.self')
 graph.wire('removeArrivalHUD.then','AFA42B37.execute')
 graph.build()
 result=call('compile_blueprint',path=path)
 assert result.get('success') and result.get('errorCount')==0,result
 call('save_blueprint',path=path)
 print('ARRIVAL_HUD_HANDOFF',result)
