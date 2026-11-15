from Scene01Editor import *

def move_actor(g,var,p,location,rotation,seconds,ref):
    import re
    rotation=','.join(re.findall(r'=(\-?[0-9.]+)',rotation))
    actor=g.get(var);g.fn(ref+'root','Actor','K2_GetRootComponent');g.wire(actor,ref+'root.self')
    mesh=g.get('SkeletalMeshComponent',owner='SkeletalMeshActor',target=actor)
    g.fn(ref+'walk','SkeletalMeshComponent','PlayAnimation',p,NewAnimToPlay='/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd',bLooping='true');g.wire(mesh,ref+'walk.self')
    g.fn(ref,'KismetSystemLibrary','MoveComponentTo',None,TargetRelativeLocation=location,TargetRelativeRotation=rotation,OverTime=seconds,bEaseIn='true',bEaseOut='true',MoveAction='Move');g.wire(ref+'walk.then',ref+'.Move');g.wire(ref+'root.ReturnValue',ref+'.Component')
    g.fn(ref+'idle','SkeletalMeshComponent','PlayAnimation',ref+'.then',NewAnimToPlay='/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle',bLooping='true');g.wire(mesh,ref+'idle.self')
    return ref+'idle.then'

# The original widget only displays hints/notes; all spoken lines now go through VO.
g=graph(ARRIVAL,'InitializeArrival',clear=True)
g.fn('pc','GameplayStatics','GetPlayerController')
g.fn('create','WidgetBlueprintLibrary','Create',g.entry,WidgetType=obj(WIDGET)+'_C');g.wire('pc.ReturnValue','create.OwningPlayer')
g.node('cast','Cast',targetClass=obj(WIDGET)+'_C');g.wire('create.then','cast.execute');g.wire('create.ReturnValue','cast.Object')
p=g.set('SceneHUD',('cast.AsWBP Scene 01Objective',),'cast.then')
g.fn('show','UserWidget','AddToViewport',p,ZOrder='20');g.wire(g.get('SceneHUD'),'show.self')
g.fn('pawn','GameplayStatics','GetPlayerPawn');g.fn('pos','Actor','K2_GetActorLocation');g.wire('pawn.ReturnValue','pos.self')
p=g.set('StartLocation',('pos.ReturnValue',),'show.then');g.fn('rot','Controller','GetControlRotation');g.wire('pc.ReturnValue','rot.self');p=g.set('StartRotation',('rot.ReturnValue',),p);p=g.set('Stage',1,p)
invoke(g,'SetHint',p,g.get('SceneHUD'),obj(WIDGET)+'_C',Line='WASD - Walk toward the house.');g.build()
g=graph(ARRIVAL,'PollArrival',clear=True)
p=invoke(g,'AdvanceTutorial',g.entry)
yes,_=g.branch(g.compare(g.get('Stage'),'EqualEqual_IntInt',5),p)
g.fn('pawn','GameplayStatics','GetPlayerPawn');g.fn('pos','Actor','K2_GetActorLocation');g.wire('pawn.ReturnValue','pos.self')
g.fn('distance','KismetMathLibrary','Vector_Distance',V2='(X=-160,Y=220,Z=88)');g.wire('pos.ReturnValue','distance.V1')
near,_=g.branch(g.compare('distance.ReturnValue','LessEqual_DoubleDouble',85),yes)
p=g.set('Stage',6,near)
# StartConversation is a latent custom event created below.
g.build()

clear_events(ARRIVAL);compile_save(ARRIVAL);g=Graph(ARRIVAL,'EventGraph')
g.node('crew','CustomEvent',eventName='StartConversation')
p=invoke(g,'SeatDirector','crew.then');g.node('parallel','Sequence');g.wire(p,'parallel.execute')
for i,var,loc,rot,prop,secs in [(0,'CrewB','(X=-280,Y=-210,Z=0)','(Pitch=0,Yaw=90,Roll=0)','Scene1Sofa','4'),(1,'CrewA','(X=230,Y=-470,Z=0)','(Pitch=0,Yaw=-90,Roll=0)','Scene1Wardrobe','5')]:
    p=move_actor(g,var,'parallel.then_'+str(i),loc,rot,secs,'move'+var)
    g.fn('detach'+var,'Actor','K2_DetachFromActor',p,LocationRule='KeepWorld',RotationRule='KeepWorld',ScaleRule='KeepWorld');g.wire(g.get(prop),'detach'+var+'.self')
g.node('maya','CustomEvent',eventName='BeginMayaApproach')
p=move_actor(g,'Maya','maya.then','(X=-190,Y=80,Z=0)','(Pitch=0,Yaw=65,Roll=0)','3','approach');g.set('Stage',7,p)
g.node('finish','CustomEvent',eventName='FinishIntroduction')
p=move_actor(g,'Maya','finish.then','(X=-190,Y=-260,Z=0)','(Pitch=0,Yaw=180,Roll=0)','3','return')
p=invoke(g,'StandDirector',p);p=g.set('Stage',8,p)
invoke(g,'SetHint',p,g.get('SceneHUD'),obj(WIDGET)+'_C',Line='');g.build()
compile_save(ARRIVAL)
g=Graph(ARRIVAL,'PollArrival')
summary=call('read_blueprint_graph_summary',path=ARRIVAL,graphName='PollArrival')
last=next(n for n in summary['nodes'] if n['title']=='Set Stage')
invoke(g,'StartConversation',last['id']+'.then');g.build()
comment(ARRIVAL,'EventGraph','Isolated arrival blocking. Flow director owns dialogue timing and input routing. Crew placement and Maya approach/return retain the authored staging. No gameplay tests run.')
compile_save(ARRIVAL)
