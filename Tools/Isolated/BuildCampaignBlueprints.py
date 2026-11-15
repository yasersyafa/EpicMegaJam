"""Author the standalone voiced campaign director and HUD through the local editor bridge.

Only writes /Game/Game/Isolated/IbraCampaign. Runtime is Blueprint + Sequencer.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import BuildGameplaySystems as B
from GameplayBridge import call,python
from BuildFreePlacement import build_evaluate_puzzle

ROOT='/Game/Game/Isolated/IbraCampaign'
MANAGER=ROOT+'/Blueprints/BP_CampaignDirector'
HUD=ROOT+'/Blueprints/BP_CampaignHUD'
MODE=ROOT+'/Blueprints/BP_CampaignMode'
PLAYER=ROOT+'/Blueprints/BP_CampaignPlayer'
CLASS='BP_CampaignDirector_C'
B.MANAGER=MANAGER;B.CLASS=CLASS;B.RECEIPTS=Path('Saved/QA/CampaignGraphs');B.RECEIPTS.mkdir(parents=True,exist_ok=True)
G=B.Graph
CLIPS=['Opening','Intro','L01_Perfect','L01_FailBlocking','L01_FailClue','L01_Aftermath','L01_CrewTransition','Interlude01','KitchenApproach',
       'L02_Perfect','L02_FailBlocking','L02_FailLight','L02_Aftermath','ServiceTransition','Interlude02','LastRoomApproach',
       'L03_Perfect','L03_FailChair','L03_FailLight','L03_Aftermath','Interlude03','FinalPickup','BlackEllipsis','Confession','Reveal']
FUNCTIONS=['ConfigureScene','EvaluatePuzzle','RefreshDirectorMark','StartTake','CancelTake','RequestActionCut','ResetMaya','ReleasePlayer','LockPlayer',
           'StopClip','PlayClip','OnClipFinished','PlaySceneTake','StartCampaign','ResetAllProps','ResetScene','ToggleNotes','TogglePause','Interact','StopCutVoice','CompleteActiveScene','StartCredits','ReturnToMenu','SuppressLegacyNotes']

def invoke(g,name,p,**inputs):
    ref=g.fn(name+str(len(g.nodes)),CLASS,name,p)
    for pin,value in inputs.items():
        if isinstance(value,tuple):g.wire(value[0],ref+'.'+pin)
        else:g.value(ref,pin,value)
    return ref+'.then'

def method(g,owner,name,target,p=None,**args):
    n=g.fn(name+str(len(g.nodes)),owner,name,p,**args);g.wire(target,n+'.self');return n

def location(g,actor):return method(g,'Actor','K2_GetActorLocation',actor)+'.ReturnValue'
def valid(g,obj,p):
    n=g.fn('valid'+str(len(g.nodes)),'KismetSystemLibrary','IsValid');g.wire(obj,n+'.Object');return g.branch(n+'.ReturnValue',p)
def transform(g,obj):return method(g,'Actor','GetTransform',obj)+'.ReturnValue'
def move(g,obj,marker,p):
    n=method(g,'Actor','K2_SetActorTransform',obj,p,bSweep='false',bTeleport='true');g.wire(transform(g,marker),n+'.NewTransform');return n+'.then'
def clock(g):return g.fn('clock'+str(len(g.nodes)),'KismetSystemLibrary','GetGameTimeInSeconds')+'.ReturnValue'
def add(g,a,b):
    n=g.fn('add'+str(len(g.nodes)),'KismetMathLibrary','Add_DoubleDouble');g.wire(a,n+'.A');g.value(n,'B',b);return n+'.ReturnValue'
def inc(g,name,p):
    n=g.fn('inc'+str(len(g.nodes)),'KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get(name),n+'.A');return g.set(name,(n+'.ReturnValue',),p)
def state(g,value,p):return g.set('State',value,p)
def play(g,key,step,p):return invoke(g,'PlayClip',p,Sequence=(g.get('Clip_'+key),),NextStep=step)
def function(name,inputs=None):
    existing={x['name'] for x in call('list_blueprint_graphs',path=MANAGER)['graphs']}
    if name not in existing:call('create_function',path=MANAGER,functionName=name,inputs=inputs or [])
    summary=call('read_blueprint_graph_summary',path=MANAGER,graphName=name)
    for n in summary['nodes']:
        if n['type'] not in ['K2Node_FunctionEntry','K2Node_FunctionResult']:call('remove_node',path=MANAGER,graphName=name,nodeId=n['id'])
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    return G(MANAGER,name,entry+'.then')

def author():
    for path,parent in [(MANAGER,'Actor'),(HUD,'HUD'),(MODE,'GameModeBase'),(PLAYER,'BP_GameplayPlayer_C')]:
        disk=Path('Content')/Path(path.removeprefix('/Game/')).with_suffix('.uasset')
        if not disk.exists():call('create_blueprint',packagePath=path,parentClass=parent)
    variables=[('SceneIndex','int','1'),('State','int','7'),('Outcome','int','0'),('TakeID','int','0'),('TakeCount','int','0'),('CompletedCount','int','0'),
      ('Completed1','bool','false'),('Completed2','bool','false'),('Completed3','bool','false'),('WaitingForCut','bool','false'),('NeedPoll','bool','false'),
      ('PendingStep','int','-1'),('ConsumedStep','int','-1'),('PollAfter','double','0'),('CreditStart','double','0'),('CreditsY','double','700'),('Paused','bool','false'),('NotesVisible','bool','false'),
      ('CutCaptionUntil','double','0'),
      ('AtDirectorMark','bool','false'),('DirectorMarkRadius','double','110'),('DirectorMarkHeightTolerance','double','120'),
      ('Player','object:BP_GameplayPlayer_C','None'),('Controller','object:PlayerController','None'),('Maya','object:Actor','None'),('ActiveMayaStart','object:Actor','None'),
      ('MayaMesh','object:SkeletalMeshComponent','None'),('MayaIdle','object:AnimationAsset','None'),
      ('Crew1','object:Actor','None'),('Crew2','object:Actor','None'),('Crew3','object:Actor','None'),
      ('ActiveDirectorMark','object:Actor','None'),('ActiveProp1','object:BP_InteractableProp_C','None'),('ActiveProp2','object:BP_InteractableProp_C','None'),
      ('ActiveArea1','object:BP_PlacementArea_C','None'),('ActiveArea2','object:BP_PlacementArea_C','None'),
      ('SequencePlayer','object:LevelSequencePlayer','None'),('SequenceActor','object:Actor','None'),('PlaybackSettings','struct:/Script/MovieScene.MovieSceneSequencePlaybackSettings',''),
      ('CutSound','object:SoundBase','None'),('CutSofaSound','object:SoundBase','None'),('CutVoice','object:AudioComponent','None'),('Intercom','object:Actor','None'),
      ('Gate1','object:Actor','None'),('Gate2','object:Actor','None'),
      ('SubtitleText','string',''),('StatusText','string',''),('ObjectiveText','string',''),('NotesText','string',''),
      ('CreditsText','string','THE HOUSE THAT REMEMBERS\nAn Unreleased Film\n\nDirected by Surya Adikara\nStarring Maya\n\nCUT! CUT! CUT!\nCreated by the CUT! CUT! CUT! team\n\nNot everything belongs in the final cut.\n\nThank you for playing.')]
    for i in range(1,4):
        for name in ['Spawn','MayaStart','DirectorMark']:variables.append((f'S{i}{name}','object:Actor','None'))
        for j in [1,2]:variables += [(f'S{i}Prop{j}','object:BP_InteractableProp_C','None'),(f'S{i}Start{j}','object:Actor','None'),(f'S{i}Area{j}','object:BP_PlacementArea_C','None')]
    variables += [('Clip_'+k,'object:LevelSequence','None') for k in CLIPS]
    existing={v['name'] for v in call('list_variables',path=MANAGER)['variables']}
    for n,t,d in variables:
        if n not in existing:call('add_variable',path=MANAGER,variableName=n,type=t,defaultValue=d,category='Campaign')
    Path('Saved/QA/CampaignVariables.json').write_text(json.dumps(call('list_variables',path=MANAGER)['variables'],indent=2))
    gs={n:function(n,[{'name':'Sequence','type':'object:LevelSequence'},{'name':'NextStep','type':'int'}] if n=='PlayClip' else None) for n in FUNCTIONS}
    result=call('compile_blueprint',path=MANAGER);assert result['errorCount']==0,result
    B.build_refresh_director_mark(gs['RefreshDirectorMark']);build_evaluate_puzzle(gs['EvaluatePuzzle'])

    g=gs['StopClip'];p=g.set('NeedPoll','false',g.entry);p=g.set('PendingStep',-1,p)
    yes,no=valid(g,g.get('SequencePlayer'),p)
    stop=method(g,'MovieSceneSequencePlayer','Stop',g.get('SequencePlayer'),yes)
    yes2,no2=valid(g,g.get('SequenceActor'),stop+'.then')
    destroy=method(g,'Actor','K2_DestroyActor',g.get('SequenceActor'),yes2)
    clear=g.set('SequencePlayer','None',destroy+'.then');node=clear.rsplit('.',1)[0]
    for route in [no,no2]:g.wire(route,node+'.execute')
    g.set('SequenceActor','None',clear);g.build()

    g=gs['StopCutVoice'];yes,no=valid(g,g.get('CutVoice'),g.entry);method(g,'AudioComponent','Stop',g.get('CutVoice'),yes);g.build()
    g=gs['SuppressLegacyNotes'];yes,no=valid(g,g.get('Player'),g.entry)
    p=g.set('bNotesUp','false',yes,owner='BP_FreePlacementPlayerBase_C',target=g.get('Player'))
    paper=g.get('NotesPaper',owner='BP_FreePlacementPlayerBase_C',target=g.get('Player'))
    method(g,'SceneComponent','SetVisibility',paper,p,bNewVisibility='false');g.build()
    g=gs['LockPlayer'];p=method(g,'BP_FreePlacementPlayerBase_C','CancelFreePlacement',g.get('Player'),g.entry)+'.then'
    for methodname,kw in [('ResetIgnoreMoveInput',{}),('ResetIgnoreLookInput',{}),('SetIgnoreMoveInput',{'bNewMoveInput':'true'}),('SetIgnoreLookInput',{'bNewLookInput':'true'})]:
        p=method(g,'Controller',methodname,g.get('Controller'),p,**kw)+'.then'
    cm=g.get('CharacterMovement',owner='Character',target=g.get('Player'));p=method(g,'MovementComponent','StopMovementImmediately',cm,p)+'.then'
    method(g,'Actor','SetActorHiddenInGame',g.get('Player'),p,bNewHidden='true');g.build()
    g=gs['ReleasePlayer'];p=invoke(g,'StopClip',g.entry)
    for methodname in ['ResetIgnoreMoveInput','ResetIgnoreLookInput']:p=method(g,'Controller',methodname,g.get('Controller'),p)+'.then'
    p=method(g,'Actor','SetActorHiddenInGame',g.get('Player'),p,bNewHidden='false')+'.then'
    n=method(g,'PlayerController','SetViewTargetWithBlend',g.get('Controller'),p,BlendTime='.25');g.wire(g.get('Player'),n+'.NewViewTarget')
    p=g.set('SubtitleText','',n+'.then')
    for crew in ['Crew1','Crew2','Crew3']:p=method(g,'Actor','SetActorHiddenInGame',g.get(crew),p,bNewHidden='false')+'.then'
    g.build()

    g=gs['PlayClip'];p=invoke(g,'StopClip',g.entry);p=invoke(g,'StopCutVoice',p);p=invoke(g,'LockPlayer',p)
    p=g.set('SubtitleText','',p);p=g.set('CutCaptionUntil',0,p)
    entry=g.entry.rsplit('.',1)[0]
    p=g.set('PendingStep',(entry+'.NextStep',),p)
    n=g.fn('create','LevelSequencePlayer','CreateLevelSequencePlayer',p)
    g.wire(entry+'.Sequence','create.LevelSequence');g.wire(g.get('PlaybackSettings'),'create.Settings')
    p=g.set('SequencePlayer',('create.ReturnValue',),'create.then');p=g.set('SequenceActor',('create.OutActor',),p)
    p=g.set('PollAfter',(add(g,clock(g),.15),),p);p=g.set('NeedPoll','true',p)
    method(g,'MovieSceneSequencePlayer','Play',g.get('SequencePlayer'),p);g.build()

    g=gs['ResetMaya'];yes,no=valid(g,g.get('Maya'),g.entry);yes,no=valid(g,g.get('ActiveMayaStart'),yes)
    p=move(g,g.get('Maya'),g.get('ActiveMayaStart'),yes)
    p=method(g,'Actor','SetActorHiddenInGame',g.get('Maya'),p,bNewHidden='false')+'.then'
    n=method(g,'SkeletalMeshComponent','PlayAnimation',g.get('MayaMesh'),p,bLooping='true');g.wire(g.get('MayaIdle'),n+'.NewAnimToPlay');g.build()
    g=gs['ResetAllProps'];p=g.entry
    for i in range(1,4):
        for j in [1,2]:p=move(g,g.get(f'S{i}Prop{j}'),g.get(f'S{i}Start{j}'),p)
    g.build()
    g=gs['ConfigureScene'];p=invoke(g,'ReleasePlayer',g.entry)
    p=g.set('NotesVisible','false',p);p=g.set('WaitingForCut','false',p)
    for i in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',i),p)
        q=yes
        for name in ['Prop1','Prop2','Area1','Area2','DirectorMark','MayaStart']:
            q=g.set('Active'+name,(g.get(f'S{i}'+name),),q)
        q=move(g,g.get('Player'),g.get(f'S{i}Spawn'),q)
        rot=method(g,'Actor','K2_GetActorRotation',g.get(f'S{i}Spawn'))
        n=method(g,'Controller','SetControlRotation',g.get('Controller'),q);g.wire(rot+'.ReturnValue',n+'.NewRotation');q=n+'.then'
        q=invoke(g,'ResetMaya',q);q=state(g,0,q)
        title={1:'SCENE 01 / THE ARRIVAL',2:'SCENE 02 / THE HOLLOW WALL',3:'SCENE 03 / THE LAST SCENE'}[i]
        notes={1:'Give Maya a clear route through the living room.\nKeep the patched wall readable.\nMove the sofa and wardrobe freely.',2:'Keep the inspection position clear.\nBring the sealed doorway out of shadow.\nMove the cabinet and standing lamp.',3:'Match the reference photograph on the table.\nReconstruct the chair and light positions.\nThe lamp should light the chair from the left.'}[i]
        q=g.set('ObjectiveText',title+' — Arrange the set.',q);q=g.set('NotesText',title+'\n\n'+notes,q)
        q=g.set('StatusText','',q);invoke(g,'RefreshDirectorMark',q);p=no
    g.build()

    g=gs['PlaySceneTake'];p=g.entry
    for i,fail1,fail2,step in [(1,'L01_FailBlocking','L01_FailClue',2),(2,'L02_FailBlocking','L02_FailLight',7),(3,'L03_FailChair','L03_FailLight',12)]:
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',i),p)
        success,fail=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',0),yes)
        play(g,f'L0{i}_Perfect',step,success)
        one,two=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',1),fail)
        play(g,fail1,99,one);play(g,fail2,99,two);p=no
    g.build()
    g=gs['StartTake'];yes,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',0),g.entry)
    p=invoke(g,'RefreshDirectorMark',yes)
    yes,no=g.branch(g.get('AtDirectorMark'),p);g.set('StatusText','Return to the director mark to call ACTION.',no)
    holding,empty=valid(g,g.get('HeldProp',owner='BP_GameplayPlayer_C',target=g.get('Player')),yes)
    g.set('StatusText','Place or cancel the prop before calling ACTION.',holding)
    p=invoke(g,'EvaluatePuzzle',empty);p=inc(g,'TakeID',p);p=inc(g,'TakeCount',p);p=state(g,1,p)
    p=g.set('NotesVisible','false',p);p=g.set('WaitingForCut','false',p);p=invoke(g,'ResetMaya',p);invoke(g,'PlaySceneTake',p);g.build()
    g=gs['CancelTake'];yes,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
    p=inc(g,'TakeID',yes);p=invoke(g,'ReleasePlayer',p);p=invoke(g,'ResetMaya',p);p=state(g,0,p)
    p=g.set('WaitingForCut','false',p);p=g.set('StatusText','CUT. Adjust the set and try again.',p)
    sceneone,other=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',1),p)
    sofa,generic=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',1),sceneone)
    for ref,sound,route in [('sofaVoice','CutSofaSound',sofa),('genericVoice','CutSound',generic)]:
        route=g.set('SubtitleText',"SURYA: CUT! Let's open up that walkway. We'll go again." if sound=='CutSofaSound' else 'SURYA: CUT! Hold on, I need to tidy up the scene.',route)
        route=g.set('CutCaptionUntil',(add(g,clock(g),3.5),),route)
        n=g.fn(ref,'GameplayStatics','SpawnSound2D',route,VolumeMultiplier='1.0');g.wire(g.get(sound),ref+'.Sound')
        g.set('CutVoice',(ref+'.ReturnValue',),ref+'.then')
    generic_start=next(c['to'] for c in g.connections if c['from']==generic)
    g.wire(other,generic_start);g.build()
    g=gs['ResetScene'];yes,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',0),g.entry)
    p=method(g,'BP_FreePlacementPlayerBase_C','CancelFreePlacement',g.get('Player'),yes)+'.then'
    for i in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',i),p)
        q=yes
        for j in [1,2]:q=move(g,g.get(f'S{i}Prop{j}'),g.get(f'S{i}Start{j}'),q)
        g.set('StatusText','Set restored to its starting arrangement.',q);p=no
    g.build()
    g=gs['CompleteActiveScene'];p=g.entry
    for i in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',i),p)
        done,fresh=g.branch(g.get('Completed'+str(i)),yes)
        q=g.set('Completed'+str(i),'true',fresh);inc(g,'CompletedCount',q);p=no
    g.build()

    g=gs['StartCampaign'];p=invoke(g,'StopClip',g.entry);p=invoke(g,'StopCutVoice',p)
    p=method(g,'BP_FreePlacementPlayerBase_C','CancelFreePlacement',g.get('Player'),p)+'.then'
    p=invoke(g,'ResetAllProps',p)
    for n,v in [('SceneIndex',1),('CompletedCount',0),('Completed1','false'),('Completed2','false'),('Completed3','false'),('TakeCount',0),('WaitingForCut','false'),('NotesVisible','false')]:p=g.set(n,v,p)
    for gate in ['Gate1','Gate2']:p=method(g,'Actor','SetActorEnableCollision',g.get(gate),p,bNewActorEnableCollision='true')+'.then'
    p=state(g,5,p);play(g,'Opening',0,p);g.build()
    g=gs['ReturnToMenu'];p=invoke(g,'StopClip',g.entry);p=state(g,7,p);p=g.set('SubtitleText','',p);invoke(g,'LockPlayer',p);g.build()
    g=gs['StartCredits'];p=invoke(g,'StopClip',g.entry);p=state(g,6,p);p=g.set('CreditStart',(clock(g),),p);g.set('SubtitleText','',p);g.build()

    g=gs['OnClipFinished'];p=g.set('ConsumedStep',(g.get('PendingStep'),),g.entry);p=g.set('PendingStep',-1,p)
    routes={0:('Intro',1),2:('L01_Aftermath',3),3:('L01_CrewTransition',4),4:('Interlude01',5),5:('KitchenApproach',6),
            7:('L02_Aftermath',8),8:('ServiceTransition',9),9:('Interlude02',10),10:('LastRoomApproach',11),
            12:('L03_Aftermath',13),13:('Interlude03',14),15:('BlackEllipsis',16),16:('Confession',17),17:('Reveal',18)}
    for step in sorted(set(routes)|{1,6,11,14,18,99}):
        yes,no=g.branch(g.compare(g.get('ConsumedStep'),'EqualEqual_IntInt',step),p)
        if step==99:
            q=g.set('WaitingForCut','true',yes);g.set('StatusText','[F] CUT',q)
        elif step in [1,6,11]:
            scene={1:1,6:2,11:3}[step];q=g.set('SceneIndex',scene,yes);invoke(g,'ConfigureScene',q)
        elif step==14:
            q=invoke(g,'ReleasePlayer',yes);q=state(g,3,q);g.set('ObjectiveText','CALL EVERYONE TO SET — Use the production intercom.',q)
        elif step==18:invoke(g,'StartCredits',yes)
        else:
            q=yes
            if step in [2,7,12]:q=invoke(g,'CompleteActiveScene',q)
            if step in [3,8]:q=method(g,'Actor','SetActorEnableCollision',g.get('Gate1' if step==3 else 'Gate2'),q,bNewActorEnableCollision='false')+'.then'
            q=state(g,5,q);play(g,*routes[step],q)
        p=no
    g.build()
    g=gs['RequestActionCut'];menu,other=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',7),g.entry)
    invoke(g,'StartCampaign',menu);taking,other=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),other)
    invoke(g,'CancelTake',taking);invoke(g,'StartTake',other);g.build()
    g=gs['Interact'];menu,other=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',7),g.entry);invoke(g,'StartCampaign',menu)
    ready,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',3),other)
    holding,ready=valid(g,g.get('HeldProp',owner='BP_GameplayPlayer_C',target=g.get('Player')),ready)
    g.set('StatusText','Place or cancel the prop before using the intercom.',holding)
    distance=method(g,'Actor','GetDistanceTo',g.get('Player'));g.wire(g.get('Intercom'),distance+'.OtherActor')
    near,far=g.branch(g.compare(distance+'.ReturnValue','LessEqual_DoubleDouble',300),ready)
    q=state(g,5,near);play(g,'FinalPickup',15,q);g.set('StatusText','Approach the production intercom.',far);g.build()
    g=gs['ToggleNotes'];ready,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',0),g.entry)
    n=g.fn('flip','KismetMathLibrary','Not_PreBool');g.wire(g.get('NotesVisible'),'flip.A');g.set('NotesVisible',('flip.ReturnValue',),ready);g.build()
    g=gs['TogglePause'];n=g.fn('flip','KismetMathLibrary','Not_PreBool');g.wire(g.get('Paused'),'flip.A')
    p=g.set('Paused',('flip.ReturnValue',),g.entry);n=g.fn('pause','GameplayStatics','SetGamePaused',p);g.wire(g.get('Paused'),'pause.bPaused')
    g.node('pauseMedia','Sequence');g.wire('pause.then','pauseMedia.execute')
    active,no=g.branch(g.get('NeedPoll'),'pauseMedia.then_0');active,no=valid(g,g.get('SequencePlayer'),active)
    paused,resume=g.branch(g.get('Paused'),active)
    method(g,'MovieSceneSequencePlayer','Pause',g.get('SequencePlayer'),paused);method(g,'MovieSceneSequencePlayer','Play',g.get('SequencePlayer'),resume)
    voice,no=valid(g,g.get('CutVoice'),'pauseMedia.then_1');n=method(g,'AudioComponent','SetPaused',g.get('CutVoice'),voice);g.wire(g.get('Paused'),n+'.bPause');g.build()
    build_events();build_hud()
    for bp in [MANAGER,HUD,MODE,PLAYER]:
        result=call('compile_blueprint',path=bp);assert result['errorCount']==0,result;call('save_blueprint',path=bp)
        Path('Saved/QA/CampaignGraphs/'+bp.split('/')[-1]+'_compile.json').write_text(json.dumps(result,indent=2))
    print('CAMPAIGN_BLUEPRINTS_AUTHORED',flush=True)

def build_events():
    summary=call('read_blueprint_graph_summary',path=MANAGER,graphName='EventGraph')
    for node in summary['nodes']:call('remove_node',path=MANAGER,graphName='EventGraph',nodeId=node['id'])
    g=G(MANAGER,'EventGraph');g.node('begin','Event',eventName='ReceiveBeginPlay')
    pc=g.fn('pc','GameplayStatics','GetPlayerController');p=g.set('Controller',('pc.ReturnValue',),'begin.then')
    n=g.fn('enable','Actor','EnableInput',p);g.wire('pc.ReturnValue','enable.PlayerController')
    pawn=g.fn('pawn','GameplayStatics','GetPlayerCharacter');g.node('cast','Cast',targetClass='BP_GameplayPlayer_C')
    g.wire('enable.then','cast.execute');g.wire('pawn.ReturnValue','cast.Object')
    p=g.set('Player',('cast.AsBP Gameplay Player',),'cast.then');invoke(g,'ReturnToMenu',p)
    for key,fn in [('F','RequestActionCut'),('E','Interact'),('Tab','ToggleNotes'),('R','ResetScene'),('P','TogglePause'),('Escape','TogglePause')]:
        g.node('key'+key,'InputKey',key=key);invoke(g,fn,'key'+key+'.Pressed')
    g.node('tick','Event',eventName='ReceiveTick');p=invoke(g,'SuppressLegacyNotes','tick.then');p=invoke(g,'RefreshDirectorMark',p)
    g.node('branches','Sequence');g.wire(p,'branches.execute')
    yes,no=g.branch(g.get('NeedPoll'),'branches.then_0')
    yes,no=g.branch(g.compare(clock(g),'GreaterEqual_DoubleDouble',(g.get('PollAfter'),)),yes)
    yes,no=valid(g,g.get('SequencePlayer'),yes)
    playing=method(g,'MovieSceneSequencePlayer','IsPlaying',g.get('SequencePlayer'))
    yes,stopped=g.branch(playing+'.ReturnValue',yes)
    p=g.set('NeedPoll','false',stopped);invoke(g,'OnClipFinished',p)
    g.node('extraTick','Sequence');g.wire('branches.then_1','extraTick.execute')
    credit,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',6),'extraTick.then_0')
    now=clock(g);age=g.fn('age','KismetMathLibrary','Subtract_DoubleDouble');g.wire(now,'age.A');g.wire(g.get('CreditStart'),'age.B')
    rate=g.fn('rate','KismetMathLibrary','Multiply_DoubleDouble',B='24');g.wire('age.ReturnValue','rate.A')
    y=g.fn('creditY','KismetMathLibrary','Subtract_DoubleDouble',A='680');g.wire('rate.ReturnValue','creditY.B')
    p=g.set('CreditsY',('creditY.ReturnValue',),credit)
    done,no=g.branch(g.compare('age.ReturnValue','GreaterEqual_DoubleDouble',30),p);invoke(g,'ReturnToMenu',done)
    # Clear the standalone player-triggered CUT caption after its voice line.
    setup,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',0),'extraTick.then_1')
    due,no=g.branch(g.compare(g.get('CutCaptionUntil'),'Greater_DoubleDouble',0),setup)
    due,no=g.branch(g.compare(clock(g),'GreaterEqual_DoubleDouble',(g.get('CutCaptionUntil'),)),due)
    p=g.set('SubtitleText','',due);g.set('CutCaptionUntil',0,p);g.build()

def build_hud():
    summary=call('read_blueprint_graph_summary',path=HUD,graphName='EventGraph')
    for node in summary['nodes']:call('remove_node',path=HUD,graphName='EventGraph',nodeId=node['id'])
    g=G(HUD,'EventGraph');g.node('draw','Event',eventName='ReceiveDrawHUD')
    n=g.fn('find','GameplayStatics','GetActorOfClass','draw.then',ActorClass=MANAGER+'.'+CLASS)
    g.node('cast','Cast',targetClass=CLASS);g.wire('find.then','cast.execute');g.wire('find.ReturnValue','cast.Object')
    target='cast.AsBP Campaign Director'
    def get(n):return g.get(n,owner=CLASS,target=target)
    def draw(ref,p,text=None,value=None,x=38,y=40,scale=1.1,color='(R=1,G=.97,B=.90,A=1)'):
        n=g.fn(ref,'HUD','DrawText',p,ScreenX=x,ScreenY=y,Scale=scale,TextColor=color)
        if value:g.wire(value,n+'.Text')
        else:g.value(n,'Text',text or '')
        return n+'.then'
    def rect(ref,p,x,y,w,h,alpha=.8):
        n=g.fn(ref,'HUD','DrawRect',p,RectColor=f'(R=0,G=0,B=0,A={alpha})',ScreenX=x,ScreenY=y,ScreenW=w,ScreenH=h);return n+'.then'
    menu,other=g.branch(g.compare(get('State'),'EqualEqual_IntInt',7),'cast.then')
    p=rect('menuBlack',menu,0,0,4000,4000,1);p=draw('title',p,'CUT! CUT! CUT!',x=90,y=180,scale=3)
    p=draw('menuStart',p,'[F] START\n\nA film about what stays outside the frame.',x=95,y=300,scale=1.25)
    credits,other=g.branch(g.compare(get('State'),'EqualEqual_IntInt',6),other)
    p=rect('creditsBlack',credits,0,0,4000,4000,1)
    n=g.fn('credits','HUD','DrawText',p,ScreenX='150',Scale='1.6',TextColor='(R=1,G=.97,B=.9,A=1)');g.wire(get('CreditsText'),'credits.Text');g.wire(get('CreditsY'),'credits.ScreenY')
    setup,other2=g.branch(g.compare(get('State'),'EqualEqual_IntInt',0),other)
    p=draw('objective',setup,value=get('ObjectiveText'),x=35,y=32,scale=1.15)
    p=draw('controls',p,'E INTERACT  /  RMB CANCEL  /  F ACTION  /  TAB NOTES',x=35,y=64,scale=.8)
    p=draw('status',p,value=get('StatusText'),x=35,y=91,scale=.9)
    x=g.fn('cx','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeX','cx.A')
    y=g.fn('cy','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeY','cy.A')
    n=g.fn('cross','HUD','DrawText',p,Text='+',Scale='1.0',TextColor='(R=1,G=1,B=1,A=.8)');g.wire('cx.ReturnValue','cross.ScreenX');g.wire('cy.ReturnValue','cross.ScreenY')
    notes,no=g.branch(get('NotesVisible'),'cross.then');p=rect('notesBox',notes,25,130,850,260)
    draw('notesText',p,value=get('NotesText'),x=45,y=150,scale=1.2)
    final,other3=g.branch(g.compare(get('State'),'EqualEqual_IntInt',3),other2);draw('finalObjective',final,value=get('ObjectiveText'),x=35,y=40)
    taking,cinematic=g.branch(g.compare(get('State'),'EqualEqual_IntInt',1),other3)
    draw('cutPrompt',taking,'[F] CUT',x=35,y=40,scale=.9)
    # Caption rendering is independent of cinematic state and survives camera cuts.
    g.node('captionSequence','Sequence');g.wire('draw.then','captionSequence.execute')
    # Use a second HUD draw route to keep captions visible in both take and narrative clips.
    # It must start after the manager cast; sequence shares that validated target.
    g.node('afterCast','Sequence');g.wire('cast.then','afterCast.execute')
    # Route only the caption branch here; state UI remains on the original cast output.
    bottom=g.fn('bottom','KismetMathLibrary','Subtract_DoubleDouble',B='100');g.wire('draw.SizeY','bottom.A')
    width=g.fn('captionWidth','KismetMathLibrary','Subtract_DoubleDouble',B='60');g.wire('draw.SizeX','captionWidth.A')
    # Avoid a black caption strip while no text is being spoken.
    length=g.fn('length','KismetStringLibrary','Len');g.wire(get('SubtitleText'),'length.S')
    g.node('captionAndPause','Sequence');g.wire('afterCast.then_0','captionAndPause.execute')
    spoken,no=g.branch(g.compare('length.ReturnValue','Greater_IntInt',0),'captionAndPause.then_0')
    box=g.fn('captionBox','HUD','DrawRect',spoken,RectColor='(R=0,G=0,B=0,A=.8)',ScreenX='25',ScreenH='78');g.wire('bottom.ReturnValue','captionBox.ScreenY');g.wire('captionWidth.ReturnValue','captionBox.ScreenW')
    yy=g.fn('captionY','KismetMathLibrary','Add_DoubleDouble',B='14');g.wire('bottom.ReturnValue','captionY.A')
    n=g.fn('caption','HUD','DrawText','captionBox.then',ScreenX='43',Scale='1.25',TextColor='(R=1,G=1,B=1,A=1)');g.wire(get('SubtitleText'),'caption.Text');g.wire('captionY.ReturnValue','caption.ScreenY')
    # Rewire exec fan-out via a Sequence; build_graph rejects multiple exec links.
    g.connections=[c for c in g.connections if not (c['from']=='cast.then' and c['to']!='afterCast.execute') and not c['to']=='captionSequence.execute']
    first_branch=next(n['ref'] for n in g.nodes if n['nodeType']=='Branch')
    g.wire('afterCast.then_1',first_branch+'.execute')
    paused,no=g.branch(get('Paused'),'captionAndPause.then_1')
    p=rect('pauseShade',paused,200,230,600,140,.9);draw('pauseLabel',p,'PAUSED\n[P] RESUME',x=240,y=270,scale=1.5)
    g.build()

if __name__=='__main__':author()
