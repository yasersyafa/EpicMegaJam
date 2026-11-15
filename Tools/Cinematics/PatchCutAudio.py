"""Own the CUT shout in FilmSceneManager; SequencePlayer owns cutscene VO."""
import sys,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Film/BP_FilmSceneManager';C='BP_FilmSceneManager_C';OUT=Path('Saved/GrayBoxAudio');OUT.mkdir(exist_ok=True)
asset=Path('Content/Game/Blueprints/Film/BP_FilmSceneManager.uasset');backup=OUT/'BP_FilmSceneManager_before_audio.uasset'
if not backup.exists():shutil.copy2(asset,backup)
variables=call('list_variables',path=P)['variables']
for name,typ,default in [('CutAudio','object:AudioComponent','None'),('CutShout','object:SoundBase','/Game/Game/Audio/Cinematics/S_Director_Cut.S_Director_Cut')]:
 if not any(v['name']==name for v in variables):call('add_variable',path=P,variableName=name,type=typ,category='Audio',defaultValue=default)
for name in ['StopCutAudio','PlayCutAudio']:
 # Existing function detection is an explicit query, not a destructive rebuild.
 try:s=call('read_blueprint_graph_summary',path=P,graphName=name)
 except RuntimeError:
  call('create_function',path=P,functionName=name,inputs=[]);s=call('read_blueprint_graph_summary',path=P,graphName=name)
 if len(s['nodes'])>1:continue
 entry=next(n['id'] for n in s['nodes'] if n['type']=='K2Node_FunctionEntry')
 g=Graph(P,name)
 if name=='StopCutAudio':
  g.fn('validCut','KismetSystemLibrary','IsValid');g.wire(g.get('CutAudio'),'validCut.Object');yes,no=g.branch('validCut.ReturnValue',entry+'.then')
  g.fn('stopCut','AudioComponent','Stop',yes);g.wire(g.get('CutAudio'),'stopCut.self');g.set('CutAudio','None','stopCut.then');g.set('CutAudio','None',no)
 else:
  g.fn('stopPrevious',C,'StopCutAudio',entry+'.then')
  g.fn('spawnCut','GameplayStatics','SpawnSound2D','stopPrevious.then',VolumeMultiplier='1.0',PitchMultiplier='1.0',StartTime='0.0',bPersistAcrossLevelTransition='false',bAutoDestroy='true');g.wire(g.get('CutShout'),'spawnCut.Sound');g.set('CutAudio',('spawnCut.ReturnValue',),'spawnCut.then')
 g.build()
# ResetTake already calls StopDialogue before SequencePlayer.Stop. Starting a take also calls StopDialogue.
s=call('read_blueprint_graph_summary',path=P,graphName='StopDialogue')
if not any(n['title']=='StopCutAudio' for n in s['nodes']):
 root=next(n for n in s['nodes'] if n['type']=='K2Node_FunctionEntry');link=next(p for p in root['connectedPins'] if p['pin']=='then')['linkedTo'][0]
 g=Graph(P,'StopDialogue');g.fn('clearCutOnReset',C,'StopCutAudio',root['id']+'.then');g.wire('clearCutOnReset.then',link['node']+'.'+link['pin']);g.build()
s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph')
if not any(n['title']=='PlayCutAudio' for n in s['nodes']):
 nodes={n['id']:n for n in s['nodes']};root=next(n for n in nodes.values() if n['title']=='ManualCut' and n['type']=='K2Node_CustomEvent')
 todo=[root['id']];seen=set();reset=None
 while todo:
  i=todo.pop(0)
  if i in seen:continue
  seen.add(i);n=nodes[i]
  if n['title']=='ResetTake':reset=n;break
  for p in n.get('connectedPins',[]):
   if p['direction']=='out' and p['pin']=='then':todo += [x['node'] for x in p['linkedTo']]
 assert reset
 link=next(p for p in reset['connectedPins'] if p['pin']=='then')['linkedTo'][0]
 g=Graph(P,'EventGraph');g.fn('cutAfterSequenceStops',C,'PlayCutAudio',reset['id']+'.then');g.wire('cutAfterSequenceStops.then',link['node']+'.'+link['pin']);g.build()
s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph')
end=next((n for n in s['nodes'] if n['title']=='Event EndPlay'),None)
if not end:
 g=Graph(P,'EventGraph');g.node('audioEndPlay','Event',eventName='ReceiveEndPlay');g.fn('stopCutAtEndPlay',C,'StopCutAudio','audioEndPlay.then');g.build()
else:
 # Existing EndPlay must already own cleanup; append without discarding its chain.
 detail=call('read_blueprint_node_detail',path=P,graphName='EventGraph',nodeId=end['id'])
 links=next(p for p in detail['pins'] if p['name']=='then').get('linkedTo',[])
 if not any(n['title']=='StopCutAudio' for n in s['nodes']):
  g=Graph(P,'EventGraph');g.fn('stopCutAtEndPlay',C,'StopCutAudio',end['id']+'.then')
  for link in links:g.wire('stopCutAtEndPlay.then',link['node']+'.'+link['pin'])
  g.build()
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P);(OUT/'compile.json').write_text(json.dumps(r,indent=2));print('CUT_AUDIO_PATCHED',r)
