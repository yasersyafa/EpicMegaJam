"""Wire the final intercom and confession into the main FilmSceneManager."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph

P='/Game/Game/Blueprints/Film/BP_FilmSceneManager';C='BP_FilmSceneManager_C'
variables={v['name'] for v in call('list_variables',path=P)['variables']}
for name,typ,default in [
 ('FinalIntercom','object:Actor','None'),('bFinalObjectiveActive','bool','false'),('bFinalStarted','bool','false'),
 ('FinalPickupSequence','object:LevelSequence','/Game/Game/Cinematics/Finale/LS_FinalPickup.LS_FinalPickup'),
 ('FinalConfessionSequence','object:LevelSequence','/Game/Game/Cinematics/Finale/LS_FinalConfession.LS_FinalConfession'),
 ('FinalRevealSequence','object:LevelSequence','/Game/Game/Cinematics/Finale/LS_FinalReveal.LS_FinalReveal')]:
 if name not in variables:call('add_variable',path=P,variableName=name,type=typ,defaultValue=default,category='Finale')

graphs={g['name'] for g in call('list_blueprint_graphs',path=P)['graphs']}
if 'StartFinalSequence' not in graphs:
 call('create_function',path=P,functionName='StartFinalSequence',inputs=[dict(name='Sequence',type='object:LevelSequence')])
s=call('read_blueprint_graph_summary',path=P,graphName='StartFinalSequence')
if len(s['nodes'])<=2:
 entry=next(n['id'] for n in s['nodes'] if n['type']=='K2Node_FunctionEntry')
 g=Graph(P,'StartFinalSequence',entry+'.then')
 create=g.fn('create','LevelSequencePlayer','CreateLevelSequencePlayer',g.entry)
 g.wire(entry+'.Sequence',create+'.LevelSequence')
 play=g.fn('play','MovieSceneSequencePlayer','Play',create+'.then')
 g.wire(create+'.ReturnValue',play+'.self')
 g.build()

events=['StartFinalObjective','BeginFinalPickup','BeginFinalConfession','BeginFinalReveal']
existing={n['title']:n['id'] for n in call('read_blueprint_graph_summary',path=P,graphName='EventGraph')['nodes']}
missing=[name for name in events if name not in existing]
if missing:
 e=Graph(P,'EventGraph')
 for name in missing:e.node('event'+name,'CustomEvent',eventName=name)
 e.build()
 call('compile_blueprint',path=P)
 existing={n['title']:n['id'] for n in call('read_blueprint_graph_summary',path=P,graphName='EventGraph')['nodes']}
def event(g,ref,name):return existing[name]+'.then'
def invoke(g,name,p):return g.fn('call'+name+str(len(g.nodes)),C,name,p)+'.then'
def line(g,p,key,seconds):
 n=g.fn('line'+str(len(g.nodes)),C,'PlayLine',p,ID='FINAL_'+key)
 d=g.fn('wait'+str(len(g.nodes)),'KismetSystemLibrary','Delay',n+'.then',Duration=str(seconds))
 return d+'.then'
def sequence(g,p,var):
 n=g.fn('seq'+str(len(g.nodes)),C,'StartFinalSequence',p)
 g.wire(g.get(var),n+'.Sequence')
 return n+'.then'

s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph')
if not any(n['title']=='Get bFinalObjectiveActive' for n in s['nodes']):
 g=Graph(P,'EventGraph')
 p=event(g,'objective','StartFinalObjective')
 p=g.set('bFinalObjectiveActive','true',p)
 hud=g.get('HUD');note=g.fn('note','WBP_GameHUD_C','SetObjective',p,Objective='FINAL PICKUP  /  CALL EVERYONE TO SET. Approach the intercom and press E.')
 g.wire(hud,note+'.self')
 pc=g.fn('pc','GameplayStatics','GetPlayerController')
 enable=g.fn('enable','Actor','EnableInput',note+'.then');g.wire(pc+'.ReturnValue',enable+'.PlayerController')

 g.node('interact','InputKey',key='E')
 active,other=g.branch(g.get('bFinalObjectiveActive'),'interact.Pressed')
 not_started=g.fn('notStarted','KismetMathLibrary','Not_PreBool');g.wire(g.get('bFinalStarted'),not_started+'.A')
 ready,_=g.branch(not_started+'.ReturnValue',active)
 pawn=g.fn('pawn','GameplayStatics','GetPlayerPawn')
 pos=g.fn('pawnPos','Actor','K2_GetActorLocation');g.wire(pawn+'.ReturnValue',pos+'.self')
 intercom=g.get('FinalIntercom')
 ipos=g.fn('intercomPos','Actor','K2_GetActorLocation');g.wire(intercom,ipos+'.self')
 dist=g.fn('distance','KismetMathLibrary','Vector_Distance')
 g.wire(pos+'.ReturnValue',dist+'.V1');g.wire(ipos+'.ReturnValue',dist+'.V2')
 near=g.fn('near','KismetMathLibrary','LessEqual_DoubleDouble',B='250')
 g.wire(dist+'.ReturnValue',near+'.A')
 near_exec,_=g.branch(near+'.ReturnValue',ready)
 invoke(g,'BeginFinalPickup',near_exec)

 p=event(g,'pickup','BeginFinalPickup')
 p=g.set('bFinalStarted','true',p)
 p=g.set('bFinalObjectiveActive','false',p)
 pc2=g.fn('pc2','GameplayStatics','GetPlayerController')
 lock=g.fn('lock','Controller','SetIgnoreMoveInput',p,bNewMoveInput='true');g.wire(pc2+'.ReturnValue',lock+'.self')
 look=g.fn('look','Controller','SetIgnoreLookInput',lock+'.then',bNewLookInput='true');g.wire(pc2+'.ReturnValue',look+'.self')
 p=sequence(g,look+'.then','FinalPickupSequence')
 pickup=[3.8,2.5,2.8,3.3,2.5,2.5,5.2,2.5,2.5,3.2,2.5,2.8,2.5,3.0]
 for i,seconds in enumerate(pickup,1):p=line(g,p,'PICKUP_%02d'%i,seconds)
 fade=g.fn('fadeBlack','PlayerCameraManager','StartCameraFade',p,FromAlpha='0',ToAlpha='1',Duration='0.5',Color='(R=0,G=0,B=0,A=1)',bShouldFadeAudio='true',bHoldWhenFinished='true')
 cm=g.fn('cameraManager','GameplayStatics','GetPlayerCameraManager');g.wire(cm+'.ReturnValue',fade+'.self')
 wait=g.fn('blackPause','KismetSystemLibrary','Delay',fade+'.then',Duration='1.5')
 invoke(g,'BeginFinalConfession',wait+'.then')

 p=event(g,'confession','BeginFinalConfession')
 p=sequence(g,p,'FinalConfessionSequence')
 clear=g.fn('fadeUp','PlayerCameraManager','StartCameraFade',p,FromAlpha='1',ToAlpha='0',Duration='0.7',Color='(R=0,G=0,B=0,A=1)',bShouldFadeAudio='false',bHoldWhenFinished='false')
 g.wire(cm+'.ReturnValue',clear+'.self');p=clear+'.then'
 confession=[3.5,3.5,3.2,4.5,3.0,4.4,3.1,4.2,3.8,3.8,4.5]
 for i,seconds in enumerate(confession,1):p=line(g,p,'CONFESSION_%02d'%i,seconds)
 invoke(g,'BeginFinalReveal',p)

 p=event(g,'reveal','BeginFinalReveal')
 p=sequence(g,p,'FinalRevealSequence')
 for i,seconds in enumerate([3.4,5.0,5.0],1):p=line(g,p,'REVEAL_%02d'%i,seconds)
 finalfade=g.fn('finalFade','PlayerCameraManager','StartCameraFade',p,FromAlpha='0',ToAlpha='1',Duration='0.8',Color='(R=0,G=0,B=0,A=1)',bShouldFadeAudio='true',bHoldWhenFinished='true')
 g.wire(cm+'.ReturnValue',finalfade+'.self')
 invoke(g,'EndOfDemo',finalfade+'.then')
 g.build()

s=call('read_blueprint_graph_summary',path=P,graphName='AdvanceScene')
if not any(n['title']=='StartFinalObjective' for n in s['nodes']):
 g=Graph(P,'AdvanceScene')
 invoke(g,'StartFinalObjective','95820DE0.then')
 g.build()

print(call('compile_blueprint',path=P))
print(call('save_blueprint',path=P))
