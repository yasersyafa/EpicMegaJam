"""Keep intro extras and the four-role take cast from appearing simultaneously."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Film/BP_FilmSceneManager'
s=call('read_blueprint_graph_summary',path=P,graphName='StageCrew')
if not any(n['title']=='Set Actor Hidden In Game' for n in s['nodes']):
 move=next(n['id'] for n in s['nodes'] if n['title']=='MoveToSceneSpot')
 loop=next(n['id'] for n in s['nodes'] if n['title']=='For Each Loop')
 g=Graph(P,'StageCrew');g.fn('hideBeforeIntro','KismetMathLibrary','Not_PreBool');g.wire(g.get('bIntroDone'),'hideBeforeIntro.A')
 g.fn('crewVisibility','Actor','SetActorHiddenInGame',move+'.then');g.wire(loop+'.Array Element','crewVisibility.self');g.wire('hideBeforeIntro.ReturnValue','crewVisibility.bNewHidden')
 for n in g.nodes:n['x']+=1400;n['y']+=100
 g.build()
s=call('read_blueprint_graph_summary',path=P,graphName='OnIntroFinished')
if not any(n['title']=='StageCrew' for n in s['nodes']):
 objective=next(n['id'] for n in s['nodes'] if n['title']=='ApplyObjective')
 g=Graph(P,'OnIntroFinished');g.fn('showTakeCrew','BP_FilmSceneManager_C','StageCrew',objective+'.then');g.nodes[0].update(x=1300,y=-14);g.build()
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P);print('CREW_VISIBILITY_PATCHED',r)
P='/Game/Game/Blueprints/Flow/BP_ArrivalDirector'
s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph');nodes={n['id']:n for n in s['nodes']}
root=next(n for n in nodes.values() if n['title']=='StartConversation')
link=next(p for p in root['connectedPins'] if p['pin']=='then')['linkedTo'];assert len(link)==1
if nodes[link[0]['node']]['title']!='Set Actor Hidden In Game':
 g=Graph(P,'EventGraph');g.fn('showIntroSpeakerA','Actor','SetActorHiddenInGame',root['id']+'.then',bNewHidden='false');g.wire(g.get('CrewA'),'showIntroSpeakerA.self')
 g.fn('showIntroSpeakerB','Actor','SetActorHiddenInGame','showIntroSpeakerA.then',bNewHidden='false');g.wire(g.get('CrewB'),'showIntroSpeakerB.self')
 g.wire('showIntroSpeakerB.then',link[0]['node']+'.'+link[0]['pin'])
 for i,n in enumerate(g.nodes):n.update(x=root['x']+350+(i%2)*350,y=root['y']+120+(i//2)*180)
 g.build()
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r;call('save_blueprint',path=P)
print('INTRO_SPEAKERS_VISIBILITY_PATCHED',r)
