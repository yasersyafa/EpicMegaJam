"""Show the CUT control as soon as a failed take reaches the hold frame."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph

path='/Game/Game/Blueprints/Film/BP_FilmSceneManager'
summary=call('read_blueprint_graph_summary',path=path,graphName='EventGraph')
if not any(n['title']=='SetCutHintVisible' and n.get('y')==0 for n in summary['nodes']):
 graph=Graph(path,'EventGraph')
 graph.fn('showFailureCut','WBP_GameHUD_C','SetCutHintVisible','B4D4E00D.then',bVisible='true')
 graph.wire(graph.get('HUD'),'showFailureCut.self')
 graph.wire('showFailureCut.then','FF4B7D25.execute')
 graph.build()
 result=call('compile_blueprint',path=path)
 assert result.get('success') and result.get('errorCount')==0,result
 call('save_blueprint',path=path)
 print('FAILURE_CUT_READY',result)
