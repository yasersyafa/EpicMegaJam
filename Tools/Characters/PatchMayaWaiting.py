"""Give BP_Maya a looping waiting pose without changing take ownership."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Characters/BP_Maya'
variables=call('list_variables',path=P)['variables']
if not any(v['name']=='WaitingAnim' for v in variables):
 call('add_variable',path=P,variableName='WaitingAnim',type='object:AnimSequenceBase',category='Maya',defaultValue='/Game/Game/Characters/Maya/Animations/A_Maya_Waiting.A_Maya_Waiting')
summary=call('read_blueprint_graph_summary',path=P,graphName='SetMayaState')
# Append only once; preserve the original PERFORMING -> ReplaceStandIns branch.
if not any(n['title']=='Play Animation' for n in summary['nodes']):
 entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
 branch=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_IfThenElse')
 g=Graph(P,'SetMayaState')
 yes,_=g.branch(g.compare(entry+'.NewState','EqualEqual_ByteByte',4),branch+'.else')
 g.fn('playWaiting','SkeletalMeshComponent','PlayAnimation',yes,bLooping='true')
 g.wire(g.get('SkeletalMeshComponent'),'playWaiting.self')
 g.wire(g.get('WaitingAnim'),'playWaiting.NewAnimToPlay')
 g.build()
r=call('compile_blueprint',path=P)
assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P)
print(json.dumps(r))
