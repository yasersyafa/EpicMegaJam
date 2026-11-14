"""Author isolated Blueprint gameplay. Run with the engine's bundled Python."""
from GameplayBridge import call, python
import hashlib
import json
from pathlib import Path

ROOT = '/Game/Game/Blueprints/Gameplay/Testing/'
MANAGER = ROOT + 'BP_GameplayTestManager'
PLAYER = ROOT + 'BP_GameplayPlayer'
HUD = ROOT + 'BP_TestHUD'
MODE = ROOT + 'BP_GameplayTestMode'
CLASS = 'BP_GameplayTestManager_C'
RECEIPTS = Path('Saved/GameplaySystemsBuild')
RECEIPTS.mkdir(exist_ok=True)


class Graph:
    def __init__(self, path, name, entry=None):
        self.path, self.name = path, name
        self.nodes, self.connections, self.defaults = [], [], []
        self.entry = entry

    def node(self, ref, kind, **values):
        self.nodes.append(dict(ref=ref, nodeType=kind, x=(len(self.nodes) % 8)*330,
                               y=(len(self.nodes)//8)*300, **values))
        return ref

    def wire(self, source, target):
        self.connections.append(dict(from_=source, to=target))
        self.connections[-1]['from'] = self.connections[-1].pop('from_')

    def value(self, node, pin, value):
        self.defaults.append(dict(node=node, pin=pin, value=str(value)))

    def get(self, name, ref=None, owner=None, target=None):
        ref = ref or 'get' + name + str(len(self.nodes))
        kwargs = dict(variableName=name)
        if owner:
            kwargs['ownerClass'] = owner
        self.node(ref, 'VariableGet', **kwargs)
        if target:
            self.wire(target, ref+'.self')
        return ref+'.'+name

    def set(self, name, value, previous, owner=None, target=None):
        ref = 'set' + name + str(len(self.nodes))
        kwargs = dict(variableName=name)
        if owner:
            kwargs['ownerClass'] = owner
        self.node(ref, 'VariableSet', **kwargs)
        self.wire(previous, ref+'.execute')
        if target:
            self.wire(target, ref+'.self')
        if isinstance(value, tuple):
            self.wire(value[0], ref+'.'+name)
        elif value != 'None':
            self.value(ref, name, value)
        return ref+'.then'

    def fn(self, ref, owner, function, previous=None, **defaults):
        self.node(ref, 'CallFunction', className=owner, functionName=function)
        if previous:
            self.wire(previous, ref+'.execute')
        for key, value in defaults.items():
            self.value(ref, key, value)
        return ref

    def invoke(self, name, previous):
        return self.fn('call'+name+str(len(self.nodes)), CLASS, name, previous)+'.then'

    def compare(self, left, function, right):
        ref='compare'+str(len(self.nodes))
        self.fn(ref,'KismetMathLibrary',function)
        self.wire(left,ref+'.A')
        if isinstance(right,tuple):
            self.wire(right[0],ref+'.B')
        else:
            self.value(ref,'B',right)
        return ref+'.ReturnValue'

    def branch(self, condition, previous):
        ref='branch'+str(len(self.nodes))
        self.node(ref,'Branch')
        self.wire(condition,ref+'.Condition')
        self.wire(previous,ref+'.execute')
        return ref+'.then',ref+'.else'

    def message(self, text, previous):
        return self.set('StatusText',text,previous)

    def build(self):
        payload=dict(path=self.path,graphName=self.name,nodes=self.nodes,
                     connections=self.connections,pinDefaults=self.defaults)
        result=call('build_graph',**payload)
        (RECEIPTS/(self.path.split('/')[-1]+'_'+self.name+'.json')).write_text(json.dumps(payload,indent=2))
        print('BUILT',self.name,len(self.nodes),flush=True)
        return result


def function(name, inputs=None):
    result=call('create_function',path=MANAGER,functionName=name,inputs=inputs or [])
    summary=call('read_blueprint_graph_summary',path=MANAGER,graphName=name)
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    return Graph(MANAGER,name,entry+'.then')


def start():
    # Record protected packages before any authoring, for a final isolation check.
    baseline={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ['Config','Content/Game/Blueprints','Content/Game/Cinematics','Content/Game/Levels']
              for p in Path(folder).rglob('*') if p.is_file() and 'Gameplay' not in p.parts
              and p.name!='L_GameplaySystems.umap'}
    (RECEIPTS/'protected_hashes.json').write_text(json.dumps(baseline,indent=2))
    print(python("import unreal; assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None; assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(); assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages(); assert not unreal.EditorAssetLibrary.does_asset_exist('"+MANAGER+"')"))
    for path,parent in [(PLAYER,'BP_PlayerCharacter_C'),(MANAGER,'Actor'),(HUD,'HUD'),(MODE,'GameModeBase')]:
        call('create_blueprint',packagePath=path,parentClass=parent)
    variables=[('SceneIndex','int','1'),('State','int','0'),('Outcome','int','0'),
               ('TakeID','int','0'),('TakeCount','int','0'),('CompletedCount','int','0'),
               ('Completed1','bool','false'),('Completed2','bool','false'),('Completed3','bool','false'),
               ('SimulatorEnabled','bool','true'),('SimulatorSeconds','double','2.0'),
               ('Deadline','double','0.0'),('Paused','bool','false'),('NotesVisible','bool','false'),
               ('StatusText','string','Arrange the props. F starts a take.'),('NotesText','string',''),
               ('Player','object:BP_GameplayPlayer_C','None'),('Controller','object:PlayerController','None'),
               ('ActiveProp1','object:BP_InteractableProp_C','None'),('ActiveProp2','object:BP_InteractableProp_C','None'),
               ('Intercom','object:Actor','None')]
    for scene in range(1,4):
        for prop in range(1,3):
            variables += [(f'S{scene}Prop{prop}','object:BP_InteractableProp_C','None'),
                          (f'S{scene}Start{prop}','object:Actor','None'),
                          (f'S{scene}Correct{prop}','name',f'S{scene}_P{prop}_B' if prop==1 else f'S{scene}_P{prop}_C')]
    for name,kind,default in variables:
        call('add_variable',path=MANAGER,variableName=name,type=kind,defaultValue=default,category='Gameplay Test')
    # Create all callable functions before building their callers.
    names=['ConfigureScene','EvaluatePuzzle','StartTake','CancelTake','RequestActionCut','CompleteScene',
           'AdvanceScene','RestartScene','ToggleNotes','TogglePause','InteractIntercom','SelectScene1','SelectScene2','SelectScene3']
    graphs={name:function(name) for name in names}
    graphs['NotifyTakeFinished']=function('NotifyTakeFinished',[dict(name='FinishedTakeID',type='int')])
    graphs['SetHeldProp']=function('SetHeldProp',[dict(name='Prop',type='object:BP_InteractableProp_C')])
    call('compile_blueprint',path=MANAGER)
    build_functions(graphs)
    g=graphs['SetHeldProp'];g.set('HeldProp',(g.entry.rsplit('.',1)[0]+'.Prop',),g.entry,owner='BP_GameplayPlayer_C',target=g.get('Player'));g.build()
    build_events()
    build_hud()
    for path in [PLAYER,MANAGER,HUD,MODE]:
        result=call('compile_blueprint',path=path)
        print('COMPILE',path,result,flush=True)
        assert result.get('success') and result.get('errorCount')==0, result
        call('save_blueprint',path=path)
    for prop,value in [('DefaultPawnClass',PLAYER+'.BP_GameplayPlayer_C'),('HUDClass',HUD+'.BP_TestHUD_C'),('PlayerControllerClass','/Script/Engine.PlayerController')]:
        call('set_class_default',path=MODE,property=prop,value=value)
    call('compile_blueprint',path=MODE);call('save_blueprint',path=MODE)


def build_functions(gs):
    g=gs['ConfigureScene'];previous=g.entry
    for scene in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',scene),previous)
        p=g.set('ActiveProp1',(g.get(f'S{scene}Prop1'),),yes)
        p=g.set('ActiveProp2',(g.get(f'S{scene}Prop2'),),p)
        objective={1:'SCENE 1 - ARRIVAL\nSofa: clear the walking route (slot B).\nWardrobe: expose the wall (slot C).',
                   2:'SCENE 2 - HOLLOW WALL\nCabinet: clear the inspection mark (slot B).\nLamp: light the sealed doorway (slot C).',
                   3:'SCENE 3 - LAST SCENE\nChair: match the staged reference (slot B).\nLamp: light the reveal (slot C).'}[scene]
        p=g.set('NotesText',objective, p)
        done=g.get('Completed'+str(scene))
        d,n=g.branch(done,p)
        g.message('Scene already complete. N continues to the next objective.',g.set('State',2,d))
        g.message('SETUP - arrange both props, then press F.',g.set('State',0,n))
        previous=no
    g.build()

    g=gs['EvaluatePuzzle'];previous=g.set('Outcome',0,g.entry)
    for scene in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',scene),previous)
        p1=g.get('ActiveProp1');p2=g.get('ActiveProp2')
        slot1=g.get('CurrentSlotID',owner='BP_InteractableProp_C',target=p1)
        slot2=g.get('CurrentSlotID',owner='BP_InteractableProp_C',target=p2)
        first,fail1=g.branch(g.compare(slot1,'EqualEqual_NameName',(g.get(f'S{scene}Correct1'),)),yes)
        second,fail2=g.branch(g.compare(slot2,'EqualEqual_NameName',(g.get(f'S{scene}Correct2'),)),first)
        g.set('Outcome',1,fail1);g.set('Outcome',2,fail2);g.set('Outcome',0,second)
        previous=no
    g.build()

    g=gs['StartTake'];allowed,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',0),g.entry)
    held=g.get('HeldProp',owner='BP_GameplayPlayer_C',target=g.get('Player'))
    valid=g.fn('heldValid','KismetSystemLibrary','IsValid');g.wire(held,valid+'.Object')
    reject,begin=g.branch(valid+'.ReturnValue',allowed)
    g.message('Place or cancel the held prop before ACTION.',reject)
    p=g.invoke('EvaluatePuzzle',begin)
    add=g.fn('nextID','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('TakeID'),add+'.A')
    p=g.set('TakeID',(add+'.ReturnValue',),p)
    add=g.fn('nextCount','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('TakeCount'),add+'.A')
    p=g.set('TakeCount',(add+'.ReturnValue',),p);p=g.set('State',1,p)
    pc=g.get('Controller');lock=g.fn('lock','Controller','SetIgnoreMoveInput',p,bNewMoveInput='true');g.wire(pc,'lock.self')
    movement=g.get('CharacterMovement',owner='Character',target=g.get('Player'))
    stop=g.fn('stop','MovementComponent','StopMovementImmediately','lock.then');g.wire(movement,'stop.self')
    now=g.fn('clock','KismetSystemLibrary','GetGameTimeInSeconds')
    end=g.fn('endTime','KismetMathLibrary','Add_DoubleDouble');g.wire(now+'.ReturnValue',end+'.A');g.wire(g.get('SimulatorSeconds'),end+'.B')
    p=g.set('Deadline',(end+'.ReturnValue',),'stop.then')
    perfect,failed=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',0),p)
    g.message('ACTION - both conditions met. Test simulator finishes this take.',perfect)
    path,visibility=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',1),failed)
    g.message('TAKE ACTIVE - blocking mismatch. Check first prop. Press F to CUT.',path)
    g.message('TAKE ACTIVE - composition/light mismatch. Check second prop. Press F to CUT.',visibility)
    g.build()

    g=gs['CancelTake'];p,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
    p=g.set('State',0,p)
    unlock=g.fn('unlock','Controller','ResetIgnoreMoveInput',p);g.wire(g.get('Controller'),'unlock.self')
    g.message('CUT - props preserved. Adjust the set, then F for RETAKE.','unlock.then');g.build()

    g=gs['RequestActionCut'];yes,no=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
    g.invoke('CancelTake',yes);g.invoke('StartTake',no);g.build()

    g=gs['NotifyTakeFinished'];yes,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
    yes,_=g.branch(g.compare(g.entry.rsplit('.',1)[0]+'.FinishedTakeID','EqualEqual_IntInt',(g.get('TakeID'),)),yes)
    yes,_=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',0),yes)
    g.invoke('CompleteScene',yes);g.build()

    g=gs['CompleteScene'];p,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
    p=g.set('State',2,p)
    unlock=g.fn('unlock','Controller','ResetIgnoreMoveInput',p);g.wire(g.get('Controller'),'unlock.self');previous='unlock.then'
    for scene in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',scene),previous)
        _,fresh=g.branch(g.get('Completed'+str(scene)),yes)
        p=g.set('Completed'+str(scene),'true',fresh)
        add=g.fn('increment'+str(scene),'KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('CompletedCount'),add+'.A')
        p=g.set('CompletedCount',(add+'.ReturnValue',),p)
        g.message('AUTO CUT - scene complete. N continues.' if scene<3 else 'AUTO CUT - CALL EVERYONE TO SET. N shows the intercom objective.',p)
        previous=no
    g.build()

    g=gs['AdvanceScene'];yes,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',2),g.entry)
    nextscene,final=g.branch(g.compare(g.get('SceneIndex'),'Less_IntInt',3),yes)
    add=g.fn('nextScene','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('SceneIndex'),add+'.A')
    p=g.set('SceneIndex',(add+'.ReturnValue',),nextscene);g.invoke('ConfigureScene',p)
    p=g.set('State',3,final);g.message('CALL EVERYONE TO SET - approach the intercom near the arena entrance and press E.',p)
    g.build()

    g=gs['RestartScene'];p=g.set('State',0,g.entry)
    unlock=g.fn('unlock','Controller','ResetIgnoreMoveInput',p);g.wire(g.get('Controller'),'unlock.self');p='unlock.then'
    # Clear selection before restoring prop transforms.
    p=g.set('HeldProp','None',p,owner='BP_GameplayPlayer_C',target=g.get('Player'))
    p=g.set('TargetSlot','None',p,owner='BP_GameplayPlayer_C',target=g.get('Player'))
    previous=p
    for scene in range(1,4):
        yes,no=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',scene),previous)
        completed,not_completed=g.branch(g.get('Completed'+str(scene)),yes)
        minus=g.fn('decrement'+str(scene),'KismetMathLibrary','Subtract_IntInt',B='1');g.wire(g.get('CompletedCount'),minus+'.A')
        cleared=g.set('CompletedCount',(minus+'.ReturnValue',),completed)
        cleared=g.set('Completed'+str(scene),'false',cleared)
        join=g.node('restore'+str(scene),'Sequence')
        g.wire(cleared,join+'.execute');g.wire(not_completed,join+'.execute')
        yes=join+'.then_0'
        for index in range(1,3):
            prop=g.get(f'S{scene}Prop{index}');marker=g.get(f'S{scene}Start{index}')
            loc=g.fn(f'location{scene}{index}','Actor','K2_GetActorLocation');g.wire(marker,loc+'.self')
            move=g.fn(f'reset{scene}{index}','Actor','K2_SetActorLocation',yes,bSweep='false',bTeleport='true');g.wire(prop,move+'.self');g.wire(loc+'.ReturnValue',move+'.NewLocation')
            yes=g.set('CurrentSlotID',f'S{scene}_P{index}_A',move+'.then',owner='BP_InteractableProp_C',target=prop)
        g.invoke('ConfigureScene',yes);previous=no
    g.build()

    g=gs['ToggleNotes'];neg=g.fn('flip','KismetMathLibrary','Not_PreBool');g.wire(g.get('NotesVisible'),'flip.A')
    g.set('NotesVisible',('flip.ReturnValue',),g.entry);g.build()

    g=gs['TogglePause'];neg=g.fn('flip','KismetMathLibrary','Not_PreBool');g.wire(g.get('Paused'),'flip.A')
    p=g.set('Paused',('flip.ReturnValue',),g.entry)
    pause=g.fn('pause','GameplayStatics','SetGamePaused',p);g.wire(g.get('Paused'),'pause.bPaused')
    g.build()

    g=gs['InteractIntercom'];p,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',3),g.entry)
    dist=g.fn('distance','Actor','GetDistanceTo');g.wire(g.get('Player'),'distance.self');g.wire(g.get('Intercom'),'distance.OtherActor')
    near,far=g.branch(g.compare('distance.ReturnValue','LessEqual_DoubleDouble',300),p)
    p=g.set('State',4,near);g.message('EVERYONE CALLED - systems test complete. 1/2/3 revisits scenes. Restart PIE for a fresh run.',p)
    g.message('Move within 3 metres of the INTERCOM, then press E.',far);g.build()

    for scene in range(1,4):
        g=gs['SelectScene'+str(scene)]
        taking,other=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),g.entry)
        p=g.invoke('CancelTake',taking)
        # Both routes converge into setting the selected scene.
        end=g.set('SceneIndex',scene,p)
        node=end.rsplit('.',1)[0];g.wire(other,node+'.execute')
        g.invoke('ConfigureScene',end);g.build()


def build_events():
    g=Graph(MANAGER,'EventGraph')
    begin=g.node('begin','Event',eventName='ReceiveBeginPlay')
    pc=g.fn('controller','GameplayStatics','GetPlayerController')
    p=g.set('Controller',('controller.ReturnValue',),'begin.then')
    enable=g.fn('enable','Actor','EnableInput',p);g.wire('controller.ReturnValue','enable.PlayerController')
    pawn=g.fn('pawn','GameplayStatics','GetPlayerCharacter')
    cast=g.node('cast','Cast',targetClass='BP_GameplayPlayer_C');g.wire('enable.then','cast.execute');g.wire('pawn.ReturnValue','cast.Object')
    p=g.set('Player',('cast.AsBP Gameplay Player',),'cast.then');g.invoke('ConfigureScene',p)
    for key,name in [('F','RequestActionCut'),('Tab','ToggleNotes'),('P','TogglePause'),('R','RestartScene'),('N','AdvanceScene'),('One','SelectScene1'),('Two','SelectScene2'),('Three','SelectScene3')]:
        event=g.node('key'+key,'InputKey',key=key)
        g.invoke(name,event+'.Pressed')
    event=g.node('interact','EnhancedInputAction',inputAction='/Game/Game/Input/IA_Interact')
    g.invoke('InteractIntercom',event+'.Started')
    tick=g.node('tick','Event',eventName='ReceiveTick')
    yes,_=g.branch(g.compare(g.get('State'),'EqualEqual_IntInt',1),'tick.then')
    yes,_=g.branch(g.get('SimulatorEnabled'),yes)
    yes,_=g.branch(g.compare(g.get('Outcome'),'EqualEqual_IntInt',0),yes)
    now=g.fn('now','KismetSystemLibrary','GetGameTimeInSeconds')
    yes,_=g.branch(g.compare('now.ReturnValue','GreaterEqual_DoubleDouble',(g.get('Deadline'),)),yes)
    notify=g.fn('notify',CLASS,'NotifyTakeFinished',yes);g.wire(g.get('TakeID'),'notify.FinishedTakeID')
    g.build()


def build_hud():
    g=Graph(HUD,'EventGraph')
    g.node('draw','Event',eventName='ReceiveDrawHUD')
    width=g.fn('width','KismetMathLibrary','Subtract_IntInt',B='40');g.wire('draw.SizeX','width.A')
    g.fn('background','HUD','DrawRect','draw.then',RectColor='(R=0,G=0,B=0,A=0.65)',ScreenX='20',ScreenY='42',ScreenH='120');g.wire('width.ReturnValue','background.ScreenW')
    find=g.fn('find','GameplayStatics','GetActorOfClass','background.then',ActorClass=MANAGER+'.BP_GameplayTestManager_C')
    g.node('cast','Cast',targetClass=CLASS);g.wire('find.then','cast.execute');g.wire('find.ReturnValue','cast.Object')
    status=g.get('StatusText',owner=CLASS,target='cast.AsBP Gameplay Test Manager')
    draw=g.fn('status','HUD','DrawText','cast.then',ScreenX='32',ScreenY='58',Scale='1.2',TextColor='(R=1,G=1,B=1,A=1)');g.wire(status,'status.Text')
    draw=g.fn('controls','HUD','DrawText','status.then',Text='WASD move | Mouse look | E pick/place | RMB cancel | F ACTION/CUT\nTab notes | N continue | R restart scene | 1/2/3 select scene | P pause/resume',ScreenX='32',ScreenY='105',Scale='1.0',TextColor='(R=0.8,G=0.9,B=1,A=1)')
    g.node('uiSequence','Sequence');g.wire('controls.then','uiSequence.execute')
    paused=g.get('Paused',owner=CLASS,target='cast.AsBP Gameplay Test Manager')
    yes,no=g.branch(paused,'uiSequence.then_0')
    g.fn('pauseText','HUD','DrawText',yes,Text='PAUSED - P resumes',ScreenX='32',ScreenY='170',Scale='1.5',TextColor='(R=1,G=0.8,B=0.2,A=1)')
    visible=g.get('NotesVisible',owner=CLASS,target='cast.AsBP Gameplay Test Manager')
    yes,_=g.branch(visible,no)
    notes=g.get('NotesText',owner=CLASS,target='cast.AsBP Gameplay Test Manager')
    g.fn('notesBackground','HUD','DrawRect',yes,RectColor='(R=0,G=0,B=0,A=0.7)',ScreenX='20',ScreenY='198',ScreenW='720',ScreenH='120')
    g.fn('notes','HUD','DrawText','notesBackground.then',ScreenX='32',ScreenY='210',Scale='1.2',TextColor='(R=1,G=0.9,B=0.5,A=1)');g.wire(notes,'notes.Text')
    centerx=g.fn('centerX','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeX','centerX.A')
    centery=g.fn('centerY','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeY','centerY.A')
    g.fn('crosshair','HUD','DrawText','uiSequence.then_1',Text='+',Scale='1.3',TextColor='(R=0,G=0,B=0,A=1)');g.wire('centerX.ReturnValue','crosshair.ScreenX');g.wire('centerY.ReturnValue','crosshair.ScreenY')
    player=g.get('Player',owner=CLASS,target='cast.AsBP Gameplay Test Manager')
    valid=g.fn('validPlayer','KismetSystemLibrary','IsValid');g.wire(player,'validPlayer.Object')
    yes,_=g.branch('validPlayer.ReturnValue','crosshair.then')
    held=g.get('HeldProp',owner='BP_GameplayPlayer_C',target=player)
    valid=g.fn('validHeld','KismetSystemLibrary','IsValid');g.wire(held,'validHeld.Object')
    holding,empty=g.branch('validHeld.ReturnValue',yes)
    target=g.get('TargetSlot',owner='BP_GameplayPlayer_C',target=player)
    valid=g.fn('validTarget','KismetSystemLibrary','IsValid');g.wire(target,'validTarget.Object')
    place,invalid=g.branch('validTarget.ReturnValue',holding)
    focus=g.get('FocusProp',owner='BP_GameplayPlayer_C',target=player)
    valid=g.fn('validFocus','KismetSystemLibrary','IsValid');g.wire(focus,'validFocus.Object')
    pickup,_=g.branch('validFocus.ReturnValue',empty)
    x=g.fn('promptX','KismetMathLibrary','Subtract_DoubleDouble',B='130');g.wire('centerX.ReturnValue','promptX.A')
    y=g.fn('promptY','KismetMathLibrary','Multiply_DoubleDouble',B='.63');g.wire('draw.SizeY','promptY.A')
    for ref,message,previous in [('place','[E] PLACE   [RMB] CANCEL',place),('invalid','NO VALID SLOT   [RMB] CANCEL',invalid),('pickup','[E] PICK UP',pickup)]:
        g.fn(ref,'HUD','DrawText',previous,Text=message,Scale='1.2',TextColor='(R=1,G=.7,B=.2,A=1)');g.wire('promptX.ReturnValue',ref+'.ScreenX');g.wire('promptY.ReturnValue',ref+'.ScreenY')
    g.build()


if __name__=='__main__':
    start()

