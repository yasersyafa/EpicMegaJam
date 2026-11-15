"""Audio device can be absent in tests; never call Play on a null component."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
for path,graph,var in [('/Game/Game/Blueprints/Film/BP_FilmSceneManager','EventGraph','DialogueAudio'),('/Game/Game/UI/Scene01/WBP_Scene01Objective','PlayIntroVoice','IntroVoiceAudio')]:
 s=call('read_blueprint_graph_summary',path=path,graphName=graph)
 n=next(n for n in s['nodes'] if n['title']=='Play' and any(x['pin']==var for p in n['connectedPins'] for x in p['linkedTo']))
 d=call('read_blueprint_node_detail',path=path,graphName=graph,nodeId=n['id'])
 source=next(p for p in d['pins'] if p['name']=='execute')['linkedTo'][0]
 call('remove_node',path=path,graphName=graph,nodeId=n['id'])
 g=Graph(path,graph);g.fn('validAudio','KismetSystemLibrary','IsValid');g.wire(g.get(var),'validAudio.Object')
 yes,_=g.branch('validAudio.ReturnValue',source['node']+'.'+source['pin'])
 g.fn('playAudio','AudioComponent','Play',yes,StartTime='0');g.wire(g.get(var),'playAudio.self');g.build()
 r=call('compile_blueprint',path=path);assert r.get('success') and r.get('errorCount')==0,r
 call('save_blueprint',path=path);print('GUARDED',path,r)
