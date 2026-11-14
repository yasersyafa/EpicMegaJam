"""Scene 01 runtime orchestration in Blueprint. Never plays the game."""
from Scene01Editor import *

PHASES={0:'Opening',1:'Arrival',2:'Setup',3:'Taking',4:'Returning',5:'Aftermath',6:'Complete'}
def phase(g,n,p):return g.set('PhaseName',PHASES[n],g.set('Phase',n,p))
def step(g,n,p):return g.set('Step',n,p)
def call_arrival(g,name,p,**kw):return invoke(g,name,p,g.get('Arrival'),cls(ARRIVAL),**kw)
def play(g,line,p):return invoke(g,'PlayLine',p,g.get('Dialogue'),cls(DIALOGUE),InLineID=line)
def stop(g,p):return invoke(g,'StopDialogue',p,g.get('Dialogue'),cls(DIALOGUE))
def dialogue_done(g,p):return g.branch(g.get('Finished',owner=cls(DIALOGUE),target=g.get('Dialogue')),p)[0]
def widget(g):return g.get('SceneHUD',owner=cls(ARRIVAL),target=g.get('Arrival'))
def hint(g,text,p):return invoke(g,'SetHint',p,widget(g),obj(WIDGET)+'_C',Line=text)
def view(g,camera,p):
    ref=g.fn('view'+str(len(g.nodes)),'PlayerController','SetViewTargetWithBlend',p,BlendTime='.2');g.wire(g.get('Controller'),ref+'.self');g.wire(g.get(camera),ref+'.NewViewTarget');return ref+'.then'
def cinematic(g,on,p):
    ref=g.fn('cinematic'+str(len(g.nodes)),'PlayerController','SetCinematicMode',p,bInCinematicMode=str(on).lower(),bHidePlayer='true',bAffectsHUD='false',bAffectsMovement='true',bAffectsTurning='true');g.wire(g.get('Controller'),ref+'.self');return ref+'.then'
def restore_view(g,p):
    p=cinematic(g,False,p)
    for fn in ['ResetIgnoreMoveInput','ResetIgnoreLookInput']:
        ref=g.fn(fn+str(len(g.nodes)),'Controller',fn,p);g.wire(g.get('Controller'),ref+'.self');p=ref+'.then'
    return view(g,'Player',p)
def actor_location(g,var):
    ref=g.fn('location'+str(len(g.nodes)),'Actor','K2_GetActorLocation');g.wire(g.get(var),ref+'.self');return ref+'.ReturnValue'
def reset_maya(g,p):
    p=g.set('MayaMoving','false',p)
    ref=g.fn('resetMaya'+str(len(g.nodes)),'Actor','K2_SetActorLocation',p,bSweep='false',bTeleport='true');g.wire(g.get('Maya'),ref+'.self');g.wire(actor_location(g,'MayaStart'),ref+'.NewLocation');p=ref+'.then'
    ref=g.fn('markerRotation'+str(len(g.nodes)),'Actor','K2_GetActorRotation');g.wire(g.get('MayaStart'),ref+'.self')
    rot=g.fn('resetRotation'+str(len(g.nodes)),'Actor','K2_SetActorRotation',p,bTeleportPhysics='true');g.wire(g.get('Maya'),rot+'.self');g.wire(ref+'.ReturnValue',rot+'.NewRotation')
    return animation(g,False,rot+'.then')
def animation(g,walk,p):
    mesh=g.get('SkeletalMeshComponent',owner='SkeletalMeshActor',target=g.get('Maya'))
    ref=g.fn('animation'+str(len(g.nodes)),'SkeletalMeshComponent','PlayAnimation',p,NewAnimToPlay=('/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd' if walk else '/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle'),bLooping='true');g.wire(mesh,ref+'.self');return ref+'.then'
def move_to(g,target,p):
    p=g.set('MayaTarget',(g.get(target),),p);p=g.set('MayaMoving','true',p);return animation(g,True,p)
def stopped(g,p):return g.branch(g.get('MayaMoving'),p)[1]

items=[('Phase','int','0'),('PhaseName','name','Opening'),('Step','int','0'),('Outcome','int','1'),('TakeID','int','0'),('ActiveTakeID','int','0'),('TakeCount','int','0'),('Deadline','double','0'),('TickDelta','double','0'),('Paused','bool','false'),('ShowTitle','bool','false'),('Completed','bool','false'),('CrewDoneCount','int','0'),('AtDirectorMark','bool','false'),('DirectorMarkRadius','double','100'),('DirectorMarkHeightTolerance','double','120'),('MayaMoving','bool','false'),('MayaSpeed','double','90'),('SavedControlRotation','rotator','0,0,0'),('StatusText','string',''),('Controller','object:PlayerController','None'),('Player','object:'+cls(PLAYER),'None'),('Arrival','object:'+cls(ARRIVAL),'None'),('Dialogue','object:'+cls(DIALOGUE),'None'),('Maya','object:SkeletalMeshActor','None'),('CrewA','object:SkeletalMeshActor','None'),('CrewB','object:SkeletalMeshActor','None'),('OpeningStandIn','object:Actor','None'),('OpeningSequence','object:LevelSequence',obj(SEQUENCE)),('SequencePlayer','object:LevelSequencePlayer','None'),('Sofa','object:BP_InteractableProp_C','None'),('Wardrobe','object:BP_InteractableProp_C','None'),('SofaArea','object:BP_PlacementArea_C','None'),('WardrobeArea','object:BP_PlacementArea_C','None')]
items += [(name,'object:Actor','None') for name in ['DirectorMark','MayaStart','MayaTarget','FailureMark','WalkMark','AisleMark','InspectMark','WideCamera','MediumCamera','DetailCamera']]
addvars(FLOW,items)
addvars(FLOW,[('FailureShown','bool','false')])
functions=['InitializeScene','PollScene','FinishOpening','PollOpening','PollArrival','EnterSetup','RefreshDirectorMark','EvaluatePuzzle','StartTake','CancelTake','RequestActionCut','TickMaya','PollTake','CompleteTake','PollAftermath','HandleInteract','HandleNotes','TogglePause','RestorePlayer','RestartScene']
for name in functions:graph(FLOW,name,clear=True)
graph(FLOW,'NotifyTakeFinished',[dict(name='FinishedTakeID',type='int')],clear=True)

# Create latent transition events before callers are authored.
clear_events(FLOW);compile_save(FLOW)
g=Graph(FLOW,'EventGraph');g.node('transition','CustomEvent',eventName='RunCrewTransition');g.node('parallel','Sequence');g.wire('transition.then','parallel.execute')
def latent_move(g,var,p,loc,ref):
    actor=g.get(var);mesh=g.get('SkeletalMeshComponent',owner='SkeletalMeshActor',target=actor)
    g.fn(ref+'walk','SkeletalMeshComponent','PlayAnimation',p,NewAnimToPlay='/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.MF_Unarmed_Walk_Fwd',bLooping='true');g.wire(mesh,ref+'walk.self')
    g.fn(ref+'root','Actor','K2_GetRootComponent');g.wire(actor,ref+'root.self')
    g.fn(ref,'KismetSystemLibrary','MoveComponentTo',TargetRelativeLocation=loc,TargetRelativeRotation='0,90,0',OverTime='3',bEaseIn='true',bEaseOut='true',MoveAction='Move');g.wire(ref+'walk.then',ref+'.Move');g.wire(ref+'root.ReturnValue',ref+'.Component')
    return ref+'.then'
for i,(var,delay,points) in enumerate([
 ('Maya','0',['-190,-260,0','-190,270,0','-90,400,0','-90,710,0']),
 ('CrewB','2',['-190,-210,0','-190,240,0','-150,400,0','-150,650,0']),
 ('CrewA','4',['-190,-350,0','-190,150,0','-90,400,0','-90,590,0'])]):
    if i>1:
        # Sequence defaults have two outputs; attach a nested sequence for Crew B/A.
        if i==2:p='crewSplit.then_1'
    elif i==1:
        g.node('crewSplit','Sequence');g.wire('parallel.then_1','crewSplit.execute');p='crewSplit.then_0'
    else:p='parallel.then_0'
    g.fn('delay'+var,'KismetSystemLibrary','Delay',p,Duration=delay);p='delay'+var+'.then'
    for index,loc in enumerate(points):p=latent_move(g,var,p,loc,'transition'+var+str(index))
    mesh=g.get('SkeletalMeshComponent',owner='SkeletalMeshActor',target=g.get(var));g.fn('idle'+var,'SkeletalMeshComponent','PlayAnimation',p,NewAnimToPlay='/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle',bLooping='true');g.wire(mesh,'idle'+var+'.self')
    g.fn('count'+var,'KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('CrewDoneCount'),'count'+var+'.A');g.set('CrewDoneCount',('count'+var+'.ReturnValue',),'idle'+var+'.then')
g.node('complete','CustomEvent',eventName='OnScene01Completed')
g.build();compile_save(FLOW)

g=graph(FLOW,'InitializeScene',clear=True)
g.fn('pc','GameplayStatics','GetPlayerController');p=g.set('Controller',('pc.ReturnValue',),g.entry)
g.fn('enable','Actor','EnableInput',p);g.wire('pc.ReturnValue','enable.PlayerController')
g.fn('pawn','GameplayStatics','GetPlayerPawn');g.node('cast','Cast',targetClass=cls(PLAYER));g.wire('enable.then','cast.execute');g.wire('pawn.ReturnValue','cast.Object');p=g.set('Player',('cast.AsBP Scene 01Player',),'cast.then')
p=call_arrival(g,'InitializeArrival',p)
caption=g.get('DialogueCaption',owner=obj(WIDGET)+'_C',target=widget(g));p=g.set('Caption',(caption,),p,owner=cls(DIALOGUE),target=g.get('Dialogue'))
p=hint(g,'',p);p=cinematic(g,True,p)
movement=g.get('CharacterMovement',owner='Character',target=g.get('Player'));g.fn('stop','MovementComponent','StopMovementImmediately',p);g.wire(movement,'stop.self')
g.fn('createSequence','LevelSequencePlayer','CreateLevelSequencePlayer','stop.then');g.wire(g.get('OpeningSequence'),'createSequence.LevelSequence')
p=g.set('SequencePlayer',('createSequence.ReturnValue',),'createSequence.then');yes,no=valid(g,g.get('SequencePlayer'),p)
g.fn('play','MovieSceneSequencePlayer','Play',yes);g.wire(g.get('SequencePlayer'),'play.self');deadline(g,'play.then',2.05);invoke(g,'FinishOpening',no);g.build()

g=graph(FLOW,'FinishOpening',clear=True)
yes,_=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',0),g.entry);p=phase(g,1,yes);p=step(g,0,p);p=g.set('ShowTitle','false',p);p=stop(g,p)
yes,no=valid(g,g.get('SequencePlayer'),p);g.fn('stopSeq','MovieSceneSequencePlayer','Stop',yes);g.wire(g.get('SequencePlayer'),'stopSeq.self');g.node('join','Sequence');g.wire('stopSeq.then','join.execute');g.wire(no,'join.execute')
p=restore_view(g,'join.then_0');yes,no=valid(g,g.get('OpeningStandIn'),p);g.fn('destroy','Actor','K2_DestroyActor',yes);g.wire(g.get('OpeningStandIn'),'destroy.self');g.node('join2','Sequence');g.wire('destroy.then','join2.execute');g.wire(no,'join2.execute')
g.fn('showMaya','Actor','SetActorHiddenInGame','join2.then_0',bNewHidden='false');g.wire(g.get('Maya'),'showMaya.self');hint(g,'WASD - Walk toward the house.','showMaya.then');g.build()

g=graph(FLOW,'PollOpening',clear=True)
previous=g.entry
for s in range(4):
    yes,previous=g.branch(g.compare(g.get('Step'),'EqualEqual_IntInt',s),previous)
    if s==0:
        p=expired(g,yes);p=step(g,1,p);g.fn('pauseSequence','MovieSceneSequencePlayer','Pause',p);g.wire(g.get('SequencePlayer'),'pauseSequence.self');play(g,'Opening_01','pauseSequence.then')
    elif s==1:
        p=dialogue_done(g,yes);p=step(g,2,p);p=deadline(g,p,2.8);g.fn('resumeSequence','MovieSceneSequencePlayer','Play',p);g.wire(g.get('SequencePlayer'),'resumeSequence.self')
    elif s==2:
        p=expired(g,yes);p=g.set('ShowTitle','true',p);step(g,3,p)
    else:
        g.fn('playing','MovieSceneSequencePlayer','IsPlaying');g.wire(g.get('SequencePlayer'),'playing.self');_,done=g.branch('playing.ReturnValue',yes);invoke(g,'FinishOpening',done)
g.build()

g=graph(FLOW,'PollArrival',clear=True)
p=call_arrival(g,'PollArrival',g.entry);previous=p
for s in range(5):
    yes,previous=g.branch(g.compare(g.get('Step'),'EqualEqual_IntInt',s),previous)
    stagevar=g.get('Stage',owner=cls(ARRIVAL),target=g.get('Arrival'))
    if s==0:
        yes,_=g.branch(g.compare(stagevar,'EqualEqual_IntInt',6),yes);p=step(g,1,yes);play(g,'Intro_Crew_01',p)
    elif s==1:
        p=dialogue_done(g,yes);p=step(g,2,p);call_arrival(g,'BeginMayaApproach',p)
    elif s==2:
        yes,_=g.branch(g.compare(stagevar,'EqualEqual_IntInt',7),yes);p=step(g,3,yes);play(g,'Intro_Maya_01',p)
    elif s==3:
        p=dialogue_done(g,yes);p=step(g,4,p);call_arrival(g,'FinishIntroduction',p)
    else:
        yes,_=g.branch(g.compare(stagevar,'EqualEqual_IntInt',8),yes);invoke(g,'EnterSetup',yes)
g.build()

g=graph(FLOW,'EnterSetup',clear=True)
p=phase(g,2,g.entry);p=step(g,0,p);p=reset_maya(g,p);p=hint(g,'Prepare the set. Return to the director mark when ready.',p)
p=invoke(g,'SetDirectorNotes',p,widget(g),obj(WIDGET)+'_C',Notes="DIRECTOR'S NOTES\nScene 01 - The Arrival\nLaras returns to her childhood home after years away.\nShe enters the living room and notices something unfamiliar.\n\nGive Maya a clear route through the room.\nKeep the unusual wall detail readable.\n\nE - pick up / place | RMB - cancel\nF at director mark - ACTION | F during take - CUT\nTab - close notes")
g.set('StatusText','Arrange the sofa and wardrobe. F: ACTION at the director mark.',p);g.build()

g=graph(FLOW,'RefreshDirectorMark',clear=True)
p=g.set('AtDirectorMark','false',g.entry);p,_=valid(g,g.get('Player'),p);p,_=valid(g,g.get('DirectorMark'),p)
g.fn('distance','KismetMathLibrary','Vector_Distance2D');g.wire(actor_location(g,'Player'),'distance.V1');g.wire(actor_location(g,'DirectorMark'),'distance.V2')
yes,_=g.branch(g.compare('distance.ReturnValue','LessEqual_DoubleDouble',(g.get('DirectorMarkRadius'),)),p)
g.fn('delta','KismetMathLibrary','Subtract_VectorVector');g.wire(actor_location(g,'Player'),'delta.A');g.wire(actor_location(g,'DirectorMark'),'delta.B');g.fn('split','KismetMathLibrary','BreakVector');g.wire('delta.ReturnValue','split.InVec');g.fn('height','KismetMathLibrary','Abs');g.wire('split.Z','height.A')
g.set('AtDirectorMark',(g.compare('height.ReturnValue','LessEqual_DoubleDouble',(g.get('DirectorMarkHeightTolerance'),)),),yes);g.build()

g=graph(FLOW,'EvaluatePuzzle',clear=True);p=g.set('Outcome',1,g.entry)
for index,(area,prop) in enumerate([('SofaArea','Sofa'),('WardrobeArea','Wardrobe')]):
    p,_=valid(g,g.get(area),p)
    ref=g.fn('contains'+str(index),'BP_PlacementArea_C','ContainsProp',p);g.wire(g.get(area),ref+'.self');g.wire(g.get(prop),ref+'.Prop');p,_=g.branch(ref+'.Inside',ref+'.then');p=g.set('Outcome',2 if index==0 else 0,p)
g.build()

g=graph(FLOW,'StartTake',clear=True)
p,_=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',2),g.entry);p=invoke(g,'RefreshDirectorMark',p)
yes,no=g.branch(g.get('AtDirectorMark'),p);g.set('StatusText','Return to the director mark before ACTION.',no)
held=g.get('HeldProp',owner=cls(PLAYER),target=g.get('Player'));holding,p=valid(g,held,yes);g.set('StatusText','Place or cancel the held prop before ACTION.',holding)
p=stop(g,p);p=invoke(g,'EvaluatePuzzle',p)
g.fn('nextID','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('TakeID'),'nextID.A');p=g.set('TakeID',('nextID.ReturnValue',),p);p=g.set('ActiveTakeID',(g.get('TakeID'),),p)
g.fn('nextCount','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('TakeCount'),'nextCount.A');p=g.set('TakeCount',('nextCount.ReturnValue',),p)
g.fn('rotation','Controller','GetControlRotation');g.wire(g.get('Controller'),'rotation.self');p=g.set('SavedControlRotation',('rotation.ReturnValue',),p)
p=phase(g,3,p);p=step(g,0,p);p=g.set('FailureShown','false',p)
# Close both visual Notes and the physical clipboard before a take.
open_notes,closed=g.branch(g.get('bNotesOpen',owner=obj(WIDGET)+'_C',target=widget(g)),p);open_notes=invoke(g,'ToggleNotes',open_notes,widget(g),obj(WIDGET)+'_C');g.node('notesJoin','Sequence');g.wire(open_notes,'notesJoin.execute');g.wire(closed,'notesJoin.execute');p=g.set('bNotesUp','false','notesJoin.then_0',owner=cls(PLAYER),target=g.get('Player'))
p=reset_maya(g,p);p=cinematic(g,True,p)
movement=g.get('CharacterMovement',owner='Character',target=g.get('Player'));g.fn('stopPlayer','MovementComponent','StopMovementImmediately',p);g.wire(movement,'stopPlayer.self');p=view(g,'WideCamera','stopPlayer.then');play(g,'Take_Entry_01',p);g.build()

g=graph(FLOW,'RestorePlayer',clear=True)
p=restore_view(g,g.entry)
g.fn('rotation','Controller','SetControlRotation',p);g.wire(g.get('Controller'),'rotation.self');g.wire(g.get('SavedControlRotation'),'rotation.NewRotation');g.build()

g=graph(FLOW,'CancelTake',clear=True)
p,_=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',3),g.entry);p=phase(g,4,p);p=stop(g,p);p=reset_maya(g,p);p=invoke(g,'RestorePlayer',p)
g.fn('invalidate','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('TakeID'),'invalidate.A');p=g.set('TakeID',('invalidate.ReturnValue',),p)
failed,early=g.branch(g.get('FailureShown'),p);play(g,'Cut_Early_01',early)
sofa,wardrobe=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',1),failed);play(g,'Cut_Sofa_01',sofa);play(g,'Cut_Wardrobe_01',wardrobe);g.build()

g=graph(FLOW,'RequestActionCut',clear=True)
taking,other=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',3),g.entry);invoke(g,'CancelTake',taking);invoke(g,'StartTake',other);g.build()

g=graph(FLOW,'TickMaya',clear=True)
p,_=g.branch(g.get('MayaMoving'),g.entry)
g.fn('interp','KismetMathLibrary','VInterpTo_Constant');g.wire(actor_location(g,'Maya'),'interp.Current');g.wire(actor_location(g,'MayaTarget'),'interp.Target');g.wire(g.get('TickDelta'),'interp.DeltaTime');g.wire(g.get('MayaSpeed'),'interp.InterpSpeed')
g.fn('move','Actor','K2_SetActorLocation',p,bSweep='false',bTeleport='true');g.wire(g.get('Maya'),'move.self');g.wire('interp.ReturnValue','move.NewLocation')
g.fn('look','KismetMathLibrary','FindLookAtRotation');g.wire(actor_location(g,'Maya'),'look.Start');g.wire(actor_location(g,'MayaTarget'),'look.Target');g.fn('splitLook','KismetMathLibrary','BreakRotator');g.wire('look.ReturnValue','splitLook.InRot');g.fn('yaw','KismetMathLibrary','MakeRotator');g.wire('splitLook.Yaw','yaw.Yaw')
g.fn('face','Actor','K2_SetActorRotation','move.then',bTeleportPhysics='true');g.wire(g.get('Maya'),'face.self');g.wire('yaw.ReturnValue','face.NewRotation')
g.fn('distance','KismetMathLibrary','Vector_Distance');g.wire(actor_location(g,'Maya'),'distance.V1');g.wire(actor_location(g,'MayaTarget'),'distance.V2');yes,_=g.branch(g.compare('distance.ReturnValue','LessEqual_DoubleDouble',5),'face.then');p=g.set('MayaMoving','false',yes)
g.fn('arriveRotation','Actor','K2_GetActorRotation');g.wire(g.get('MayaTarget'),'arriveRotation.self');g.fn('arriveFace','Actor','K2_SetActorRotation',p,bTeleportPhysics='true');g.wire(g.get('Maya'),'arriveFace.self');g.wire('arriveRotation.ReturnValue','arriveFace.NewRotation');animation(g,False,'arriveFace.then');g.build()

g=graph(FLOW,'PollTake',clear=True);previous=g.entry
for s in range(9):
    yes,previous=g.branch(g.compare(g.get('Step'),'EqualEqual_IntInt',s),previous)
    if s==0:
        p=dialogue_done(g,yes);sofa,clear=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',1),p)
        p=step(g,6,sofa);move_to(g,'FailureMark',p)
        p=step(g,1,clear);p=view(g,'MediumCamera',p);p=move_to(g,'WalkMark',p);play(g,'Take_Walk_01',p)
    elif s==1:
        p=dialogue_done(g,yes);p=stopped(g,p);p=step(g,2,p);move_to(g,'AisleMark',p)
    elif s==2:
        p=stopped(g,yes);p=step(g,3,p);move_to(g,'InspectMark',p)
    elif s==3:
        p=stopped(g,yes);p=view(g,'DetailCamera',p);bad,good=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',2),p)
        p=g.set('FailureShown','true',bad);p=step(g,8,p);play(g,'Fail_Wardrobe_01',p)
        p=step(g,4,good);play(g,'Take_Clue_01',p)
    elif s==4:
        p=dialogue_done(g,yes);p=step(g,5,p);play(g,'Take_Perfect_01',p)
    elif s==5:
        p=dialogue_done(g,yes);ref=g.fn('finished',cls(FLOW),'NotifyTakeFinished',p);g.wire(g.get('ActiveTakeID'),'finished.FinishedTakeID')
    elif s==6:
        p=stopped(g,yes);p=g.set('FailureShown','true',p);p=step(g,8,p);play(g,'Fail_Sofa_01',p)
    # Step 8 deliberately holds indefinitely, even after feedback VO ends.
g.build()

g=graph(FLOW,'NotifyTakeFinished',clear=True)
p,_=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',3),g.entry)
p,_=g.branch(g.compare(g.entry.rsplit('.',1)[0]+'.FinishedTakeID','EqualEqual_IntInt',(g.get('TakeID'),)),p)
p,_=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',0),p);invoke(g,'CompleteTake',p);g.build()
g=graph(FLOW,'CompleteTake',clear=True)
p=phase(g,5,g.entry);p=step(g,0,p);p=stop(g,p);p=reset_maya(g,p);p=invoke(g,'RestorePlayer',p);play(g,'Aftermath_01',p);g.build()
g=graph(FLOW,'PollAftermath',clear=True)
first,second=g.branch(g.compare(g.get('Step'),'EqualEqual_IntInt',0),g.entry)
p=dialogue_done(g,first);p=step(g,1,p);p=g.set('CrewDoneCount',0,p);p=invoke(g,'RunCrewTransition',p);play(g,'Transition_01',p)
p=dialogue_done(g,second);p,_=g.branch(g.compare(g.get('CrewDoneCount'),'GreaterEqual_IntInt',3),p)
p=phase(g,6,p);p=g.set('Completed','true',p);p=hint(g,'',p);p=invoke(g,'SetDirectorNotes',p,widget(g),obj(WIDGET)+'_C',Notes='Scene 01 complete.\nThe crew is preparing the next set.\nScene 02 is not included in this integration level.');invoke(g,'OnScene01Completed',p);g.build()

g=graph(FLOW,'HandleInteract',clear=True)
setup,other=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',2),g.entry);invoke(g,'TryFreeInteract',setup,g.get('Player'),cls(PLAYER))
arrival,_=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',1),other);call_arrival(g,'HandleDoor',arrival);g.build()
g=graph(FLOW,'HandleNotes',clear=True)
opening,yes=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',0),g.entry);taking,yes=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',3),yes)
yes=call_arrival(g,'HandleNotes',yes);g.set('bNotesUp',(g.get('bNotesOpen',owner=obj(WIDGET)+'_C',target=widget(g)),),yes,owner=cls(PLAYER),target=g.get('Player'));g.build()
g=graph(FLOW,'TogglePause',clear=True)
g.fn('flip','KismetMathLibrary','Not_PreBool');g.wire(g.get('Paused'),'flip.A');p=g.set('Paused',('flip.ReturnValue',),g.entry)
ref=g.fn('audioPause',cls(DIALOGUE),'SetDialoguePaused',p);g.wire(g.get('Dialogue'),'audioPause.self');g.wire(g.get('Paused'),'audioPause.InPaused');g.fn('pause','GameplayStatics','SetGamePaused','audioPause.then');g.wire(g.get('Paused'),'pause.bPaused');g.build()

g=graph(FLOW,'RestartScene',clear=True)
# Reserved API for later explicit restart UI. It resets the level by name, never
# bound to a debug key in this scene. Reload also cleans all actors/VO.
g.fn('reload','GameplayStatics','OpenLevel',g.entry,LevelName=LEVEL,bAbsolute='true');g.build()

g=graph(FLOW,'PollScene',clear=True)
p=invoke(g,'TickMaya',g.entry);previous=p
for n,fn in [(0,'PollOpening'),(1,'PollArrival'),(2,'RefreshDirectorMark'),(3,'PollTake'),(4,None),(5,'PollAftermath')]:
    yes,previous=g.branch(g.compare(g.get('Phase'),'EqualEqual_IntInt',n),previous)
    if fn:invoke(g,fn,yes)
    else:invoke(g,'EnterSetup',dialogue_done(g,yes))
g.build()

# Add normal lifecycle/input events without replacing latent transition events.
g=Graph(FLOW,'EventGraph');g.node('begin','Event',eventName='ReceiveBeginPlay');invoke(g,'InitializeScene','begin.then')
g.node('tick','Event',eventName='ReceiveTick');p=g.set('TickDelta',('tick.DeltaSeconds',),'tick.then');invoke(g,'PollScene',p)
g.node('cut','EnhancedInputAction',inputAction='/Game/Game/Input/IA_ActionCut');invoke(g,'RequestActionCut','cut.Started')
g.node('skip','InputKey',key='SpaceBar');invoke(g,'FinishOpening','skip.Pressed')
g.node('pauseKey','InputKey',key='P');invoke(g,'TogglePause','pauseKey.Pressed')
g.node('end','Event',eventName='ReceiveEndPlay');stop(g,'end.then');g.build()
for name in ['PollScene','StartTake','CancelTake','PollTake','PollAftermath']:
    comment(FLOW,name,'Scene 01 phase owner. Opening -> Arrival -> Setup -> Taking -> Returning/Aftermath -> Complete. Failure takes wait for manual CUT; perfect completion is guarded by TakeID. Authoring only; PIE/tests NOT run.')
compile_save(FLOW)
