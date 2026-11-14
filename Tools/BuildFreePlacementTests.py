"""Author manual native FunctionalTests for radius goals and free placement."""
from GameplayBridge import call,python
from BuildGameplaySystems import Graph,MANAGER,CLASS
from BuildDirectorMark import function_graph
from BuildDirectorMarkTests import record,manager_value,set_manager,manager_call,actor_location,move_player
from BuildFreePlacement import ROOT,BASE_CLASS,AREA_CLASS,bounds,vector_z,vector_add,compile_save

TEST=ROOT+'BP_FreePlacementFunctionalTest'
TEST_CLASS='BP_FreePlacementFunctionalTest_C'
AREA_CASES=[('AreaCenter','center'),('AreaOffsetInside','offset'),('AreaRadiusBoundary','boundary'),('AreaOutside','outside'),('WrongProp','wrong'),('MissingProp','missing')]


def test_call(g,name,previous):
    return g.fn('test'+name+str(len(g.nodes)),TEST_CLASS,name,previous)


def player_call(g,name,previous,**defaults):
    ref=g.fn('player'+name+str(len(g.nodes)),BASE_CLASS,name,previous,**defaults)
    g.wire(g.get('Player'),ref+'.self')
    return ref


def put_on_floor(g,prop,ground,previous):
    box=bounds(g,prop,'bounds'+str(len(g.nodes)))
    offset=g.fn('offset'+str(len(g.nodes)),'KismetMathLibrary','Subtract_VectorVector')
    g.wire(actor_location(g,prop),offset+'.A');g.wire(box+'.Origin',offset+'.B')
    height=g.fn('height'+str(len(g.nodes)),'KismetMathLibrary','Add_DoubleDouble',B='.5')
    g.wire(vector_z(g,box+'.BoxExtent','extent'+str(len(g.nodes))),height+'.A')
    lift=g.fn('lift'+str(len(g.nodes)),'KismetMathLibrary','MakeVector',X='0',Y='0');g.wire(height+'.ReturnValue',lift+'.Z')
    delta=vector_add(g,offset+'.ReturnValue',lift+'.ReturnValue','delta'+str(len(g.nodes)))
    destination=vector_add(g,ground,delta,'destination'+str(len(g.nodes)))
    move=g.fn('moveProp'+str(len(g.nodes)),'Actor','K2_SetActorLocation',previous,bSweep='false',bTeleport='true')
    g.wire(prop,move+'.self');g.wire(destination,move+'.NewLocation')
    return move+'.then'


def inside(g,area,prop,previous):
    ref=g.fn('contains'+str(len(g.nodes)),AREA_CLASS,'ContainsProp',previous)
    g.wire(area,ref+'.self')
    if prop:g.wire(prop,ref+'.Prop')
    return ref


def expected(g,condition,wanted):
    if wanted:return condition
    neg=g.fn('not'+str(len(g.nodes)),'KismetMathLibrary','Not_PreBool');g.wire(condition,neg+'.A')
    return neg+'.ReturnValue'


def end_case(g,previous):
    g.wire(previous,g.result+'.execute');g.wire(g.get('CasePassed'),g.result+'.Passed');g.build()


def area_case(name,kind):
    g=function_graph(TEST,name,outputs=[dict(name='Passed',type='bool')])
    previous=g.set('CasePassed','true',g.entry)
    area=manager_value(g,'S1Area1');prop=manager_value(g,'S1Prop1')
    center=actor_location(g,area)
    offset=g.fn('testOffset','KismetMathLibrary','MakeVector',Y='0')
    if kind in ['boundary','offset','outside']:
        add=g.fn('radiusOffset','KismetMathLibrary','Add_DoubleDouble',B=str({'boundary':0,'offset':-25,'outside':1}[kind]))
        g.wire(g.get('Radius',owner=AREA_CLASS,target=area),'radiusOffset.A');g.wire('radiusOffset.ReturnValue','testOffset.X')
    else:g.value('testOffset','X','0')
    g.value('testOffset','Z','0')
    ground=vector_add(g,center,'testOffset.ReturnValue','testGround')
    previous=put_on_floor(g,prop,ground,previous)
    tested_prop=manager_value(g,'S1Prop2') if kind=='wrong' else (None if kind=='missing' else prop)
    result=inside(g,area,tested_prop,previous)
    passed=expected(g,result+'.Inside',kind in ['center','boundary','offset'])
    previous=record(g,passed,name+' radius validation',result+'.then')
    end_case(g,previous)


def build_all_areas():
    g=function_graph(TEST,'AllSceneAreas',outputs=[dict(name='Passed',type='bool')])
    previous=g.set('CasePassed','true',g.entry)
    for scene in range(1,4):
        for index in [1,2]:
            area=manager_value(g,f'S{scene}Area{index}');prop=manager_value(g,f'S{scene}Prop{index}')
            previous=put_on_floor(g,prop,actor_location(g,area),previous)
            result=inside(g,area,prop,previous)
            previous=record(g,result+'.Inside',f'Scene {scene} prop {index} recognizes its own area',result+'.then')
    end_case(g,previous)


def build_puzzle_outcomes():
    g=function_graph(TEST,'PuzzleUsesRadius',outputs=[dict(name='Passed',type='bool')])
    previous=g.set('CasePassed','true',g.entry)
    previous=manager_call(g,'SelectScene1',previous)+'.then'
    for index in [1,2]:
        prop=manager_value(g,f'S1Prop{index}');area=manager_value(g,f'S1Area{index}')
        previous=put_on_floor(g,prop,actor_location(g,area),previous)
        previous=g.set('CurrentSlotID','UNRELATED_TEST_ID',previous,owner='BP_InteractableProp_C',target=prop)
    previous=manager_call(g,'EvaluatePuzzle',previous)+'.then'
    previous=record(g,g.compare(manager_value(g,'Outcome'),'EqualEqual_IntInt',0),'Both areas pass regardless of legacy slot metadata',previous)
    for index,outcome in [(1,1),(2,2)]:
        area=manager_value(g,f'S1Area{index}');prop=manager_value(g,f'S1Prop{index}')
        radius=g.fn('outside'+str(index),'KismetMathLibrary','Add_DoubleDouble',B='20');g.wire(g.get('Radius',owner=AREA_CLASS,target=area),radius+'.A')
        offset=g.fn('offset'+str(index),'KismetMathLibrary','MakeVector',Y='0',Z='0');g.wire(radius+'.ReturnValue',offset+'.X')
        point=vector_add(g,actor_location(g,area),offset+'.ReturnValue','outsidePoint'+str(index))
        previous=put_on_floor(g,prop,point,previous)
        previous=manager_call(g,'EvaluatePuzzle',previous)+'.then'
        previous=record(g,g.compare(manager_value(g,'Outcome'),'EqualEqual_IntInt',outcome),'Outside prop '+str(index)+' selects the correct failure branch',previous)
        previous=put_on_floor(g,prop,actor_location(g,area),previous)
    end_case(g,previous)


def aim_at(g,target,previous):
    camera=g.get('FirstPersonCamera',owner=BASE_CLASS,target=g.get('Player'))
    start=g.fn('camera'+str(len(g.nodes)),'SceneComponent','K2_GetComponentLocation');g.wire(camera,start+'.self')
    rotation=g.fn('lookAt'+str(len(g.nodes)),'KismetMathLibrary','FindLookAtRotation');g.wire(start+'.ReturnValue',rotation+'.Start');g.wire(target,rotation+'.Target')
    set_rotation=g.fn('aim'+str(len(g.nodes)),'Controller','SetControlRotation',previous);g.wire(g.get('Controller'),set_rotation+'.self');g.wire(rotation+'.ReturnValue',set_rotation+'.NewRotation')
    return set_rotation+'.then'


def validate(g,point,previous,normal='(X=0,Y=0,Z=1)',has_surface='true'):
    ref=player_call(g,'ValidateFreePlacement',previous,SurfaceNormal=normal,HasSurface=has_surface)
    g.wire(point,ref+'.Location')
    return ref


def build_placement_flow(graph=None):
    g=graph or function_graph(TEST,'FreePlacementFlow',outputs=[dict(name='Passed',type='bool')])
    previous=g.set('CasePassed','true',g.entry)
    previous=manager_call(g,'SelectScene1',previous)+'.then'
    prop=manager_value(g,'S1Prop1')
    position=g.fn('propPosition','KismetMathLibrary','BreakVector');g.wire(actor_location(g,prop),'propPosition.InVec')
    nearby_x=g.fn('nearbyX','KismetMathLibrary','Subtract_DoubleDouble',B='300');g.wire('propPosition.X','nearbyX.A')
    nearby=g.fn('nearby','KismetMathLibrary','MakeVector',Z='88');g.wire('nearbyX.ReturnValue','nearby.X');g.wire('propPosition.Y','nearby.Y')
    previous=move_player(g,'nearby.ReturnValue',previous)
    box=bounds(g,prop)
    previous=aim_at(g,box+'.Origin',previous)
    previous=player_call(g,'TryFreeInteract',previous)+'.then'
    held=g.get('HeldProp',owner=BASE_CLASS,target=g.get('Player'))
    same=g.fn('pickedUp','KismetMathLibrary','EqualEqual_ObjectObject');g.wire(held,'pickedUp.A');g.wire(prop,'pickedUp.B')
    previous=record(g,'pickedUp.ReturnValue','Normal interact handler picks up the prop',previous)
    spot=g.fn('playerSpot','KismetMathLibrary','MakeVector',X='-300',Y='-2300',Z='88')
    ground=g.fn('freeGround','KismetMathLibrary','MakeVector',X='-80',Y='-2300',Z='0')
    previous=move_player(g,'playerSpot.ReturnValue',previous)
    previous=aim_at(g,'freeGround.ReturnValue',previous)
    previous=player_call(g,'RefreshFreePlacement',previous)+'.then'
    previous=record(g,g.get('CanPlaceFreely',owner=BASE_CLASS,target=g.get('Player')),'Clear floor outside all solution areas allows placement',previous)
    previous=player_call(g,'TryFreeInteract',previous)+'.then'
    valid=g.fn('stillHeld','KismetSystemLibrary','IsValid');g.wire(held,'stillHeld.Object')
    previous=record(g,expected(g,'stillHeld.ReturnValue',False),'Free placement commits and releases selection',previous)
    previous=g.set('CommittedPosition',(actor_location(g,prop),),previous)
    result=inside(g,manager_value(g,'S1Area1'),prop,previous)
    previous=record(g,expected(g,result+'.Inside',False),'Committed placement may be outside the puzzle solution',result+'.then')
    select=manager_call(g,'SetHeldProp',previous);g.wire(prop,select+'.Prop')
    previous=player_call(g,'RefreshFreePlacement',select+'.then')+'.then'
    wardrobe=manager_value(g,'S1Prop2')
    result=validate(g,actor_location(g,wardrobe),previous)
    previous=record(g,expected(g,result+'.CanPlace',False),'Overlapping furniture rejects placement',result+'.then')
    open_spot=g.fn('openPlayerSpot','KismetMathLibrary','MakeVector',X='200',Y='-2300',Z='88')
    previous=move_player(g,'openPlayerSpot.ReturnValue',previous)
    result=validate(g,actor_location(g,g.get('Player')),previous)
    previous=record(g,expected(g,result+'.CanPlace',False),'Placement cannot overlap the player capsule',result+'.then')
    for label,normal,has_surface in [('Steep surface','(X=1,Y=0,Z=0)','true'),('Missing surface','(X=0,Y=0,Z=1)','false')]:
        result=validate(g,g.get('CommittedPosition'),previous,normal,has_surface)
        previous=record(g,expected(g,result+'.CanPlace',False),label+' rejects placement',result+'.then')
    # An upward ray has no nearby surface in the open test arena.
    upward=g.fn('upwardRotation','KismetMathLibrary','MakeRotator',Pitch='60',Yaw='0',Roll='0')
    look=g.fn('lookUp','Controller','SetControlRotation',previous);g.wire(g.get('Controller'),'lookUp.self');g.wire(upward+'.ReturnValue','lookUp.NewRotation')
    previous=player_call(g,'TryFreeInteract','lookUp.then')+'.then'
    previous=record(g,'pickedUp.ReturnValue','Invalid interact retains the selected prop',previous)
    previous=player_call(g,'CancelFreePlacement',previous)+'.then'
    previous=record(g,expected(g,'stillHeld.ReturnValue',False),'Cancel clears selection',previous)
    distance=g.fn('cancelDistance','KismetMathLibrary','Vector_Distance');g.wire(actor_location(g,prop),'cancelDistance.V1');g.wire(g.get('CommittedPosition'),'cancelDistance.V2')
    previous=record(g,g.compare('cancelDistance.ReturnValue','LessEqual_DoubleDouble',.1),'Invalid placement and cancel preserve the last committed position',previous)
    mark=actor_location(g,manager_value(g,'ActiveDirectorMark'))
    lift=g.fn('markHeight','KismetMathLibrary','Add_VectorVector',B='(X=0,Y=0,Z=88)');g.wire(mark,'markHeight.A')
    previous=move_player(g,'markHeight.ReturnValue',previous)
    previous=manager_call(g,'RequestActionCut',previous)+'.then'
    previous=record(g,g.compare(manager_value(g,'State'),'EqualEqual_IntInt',1),'ACTION still requires and accepts the director mark',previous)
    previous=manager_call(g,'RequestActionCut',previous)+'.then'
    previous=record(g,g.compare(manager_value(g,'State'),'EqualEqual_IntInt',0),'Manual CUT returns to Setup',previous)
    previous=record(g,g.compare('cancelDistance.ReturnValue','LessEqual_DoubleDouble',.1),'CUT preserves freely placed prop position',previous)
    end_case(g,previous)


def build_restore():
    g=function_graph(TEST,'RestoreSnapshot')
    previous,_=g.branch(g.get('SnapshotTaken'),g.entry)
    previous=manager_call(g,'CancelTake',previous)+'.then'
    previous=player_call(g,'CancelFreePlacement',previous)+'.then'
    for scene in range(1,4):
        for index in [1,2]:
            prop=manager_value(g,f'S{scene}Prop{index}')
            ref=g.fn(f'restore{scene}{index}','Actor','K2_SetActorLocationAndRotation',previous,bSweep='false',bTeleport='true')
            g.wire(prop,ref+'.self');g.wire(g.get(f'OriginalS{scene}P{index}Location'),ref+'.NewLocation');g.wire(g.get(f'OriginalS{scene}P{index}Rotation'),ref+'.NewRotation')
            previous=g.set('CurrentSlotID',(g.get(f'OriginalS{scene}P{index}LegacyID'),),ref+'.then',owner='BP_InteractableProp_C',target=prop)
    for name in ['SceneIndex','TakeID','TakeCount','SimulatorEnabled','Outcome']:
        previous=set_manager(g,name,(g.get('Original'+name),),previous)
    previous=manager_call(g,'ConfigureScene',previous)+'.then'
    ref=g.fn('restorePlayer','Actor','K2_SetActorLocationAndRotation',previous,bSweep='false',bTeleport='true')
    g.wire(g.get('Player'),'restorePlayer.self');g.wire(g.get('OriginalPlayerLocation'),'restorePlayer.NewLocation');g.wire(g.get('OriginalPlayerRotation'),'restorePlayer.NewRotation')
    ref=g.fn('restoreControl','Controller','SetControlRotation','restorePlayer.then');g.wire(g.get('Controller'),'restoreControl.self');g.wire(g.get('OriginalControlRotation'),'restoreControl.NewRotation')
    previous=manager_call(g,'RefreshDirectorMark','restoreControl.then')+'.then'
    g.set('SnapshotTaken','false',previous);g.build()


def author_tests():
    call('create_blueprint',packagePath=TEST,parentClass='FunctionalTest')
    variables=[('Manager','object:BP_GameplayTestManager_C','None'),('Player','object:BP_GameplayPlayer_C','None'),('Controller','object:PlayerController','None'),
               ('SnapshotTaken','bool','false'),('CasePassed','bool','false'),('CommittedPosition','vector','(X=0,Y=0,Z=0)'),
               ('OriginalSceneIndex','int','1'),('OriginalTakeID','int','0'),('OriginalTakeCount','int','0'),('OriginalOutcome','int','0'),('OriginalSimulatorEnabled','bool','true'),
               ('OriginalPlayerLocation','vector','(X=0,Y=0,Z=0)'),('OriginalPlayerRotation','rotator','(Pitch=0,Yaw=0,Roll=0)'),('OriginalControlRotation','rotator','(Pitch=0,Yaw=0,Roll=0)')]
    for scene in range(1,4):
        for index in [1,2]:
            variables += [(f'OriginalS{scene}P{index}Location','vector','(X=0,Y=0,Z=0)'),(f'OriginalS{scene}P{index}Rotation','rotator','(Pitch=0,Yaw=0,Roll=0)'),(f'OriginalS{scene}P{index}LegacyID','name','None')]
    for name,kind,default in variables:call('add_variable',path=TEST,variableName=name,type=kind,defaultValue=default,category='Free Placement Tests')
    build_restore()
    for name,kind in AREA_CASES:area_case(name,kind)
    build_all_areas();build_puzzle_outcomes();build_placement_flow()
    compile_save(TEST)
    build_test_events()


def build_test_events():
    g=Graph(TEST,'EventGraph')
    g.node('finished','Event',eventName='ReceiveTestFinished');test_call(g,'RestoreSnapshot','finished.then')
    g.node('start','Event',eventName='ReceiveStartTest')
    previous=g.set('SnapshotTaken','false','start.then')
    failures=[]
    targets=[('manager',g.get('Manager'))]
    for ref,target in targets:
        node=g.fn(ref+'Valid','KismetSystemLibrary','IsValid');g.wire(target,node+'.Object')
        previous,no=g.branch(node+'.ReturnValue',previous);failures.append(no)
    for name in ['Player','Controller']:previous=g.set(name,(manager_value(g,name),),previous)
    targets=[('player',g.get('Player')),('controller',g.get('Controller'))]+[(f'area{s}{p}',manager_value(g,f'S{s}Area{p}')) for s in range(1,4) for p in [1,2]]
    for ref,target in targets:
        node=g.fn(ref+'Valid','KismetSystemLibrary','IsValid');g.wire(target,node+'.Object')
        previous,no=g.branch(node+'.ReturnValue',previous);failures.append(no)
    for name in ['State','CompletedCount']:
        previous,no=g.branch(g.compare(manager_value(g,name),'EqualEqual_IntInt',0),previous);failures.append(no)
    held=g.get('HeldProp',owner=BASE_CLASS,target=g.get('Player'))
    node=g.fn('heldValid','KismetSystemLibrary','IsValid');g.wire(held,'heldValid.Object')
    no,previous=g.branch('heldValid.ReturnValue',previous);failures.append(no)
    for name in ['SceneIndex','TakeID','TakeCount','SimulatorEnabled','Outcome']:previous=g.set('Original'+name,(manager_value(g,name),),previous)
    previous=g.set('OriginalPlayerLocation',(actor_location(g,g.get('Player')),),previous)
    rot=g.fn('playerRotation','Actor','K2_GetActorRotation');g.wire(g.get('Player'),'playerRotation.self')
    previous=g.set('OriginalPlayerRotation',('playerRotation.ReturnValue',),previous)
    rot=g.fn('controlRotation','Controller','GetControlRotation');g.wire(g.get('Controller'),'controlRotation.self')
    previous=g.set('OriginalControlRotation',('controlRotation.ReturnValue',),previous)
    for scene in range(1,4):
        for index in [1,2]:
            prop=manager_value(g,f'S{scene}Prop{index}')
            previous=g.set(f'OriginalS{scene}P{index}Location',(actor_location(g,prop),),previous)
            rot=g.fn(f'rotation{scene}{index}','Actor','K2_GetActorRotation');g.wire(prop,rot+'.self')
            previous=g.set(f'OriginalS{scene}P{index}Rotation',(rot+'.ReturnValue',),previous)
            previous=g.set(f'OriginalS{scene}P{index}LegacyID',(g.get('CurrentSlotID',owner='BP_InteractableProp_C',target=prop),),previous)
    previous=g.set('SnapshotTaken','true',previous)
    previous=set_manager(g,'SimulatorEnabled','false',previous)
    for name in [name for name,_ in AREA_CASES]+['AllSceneAreas','PuzzleUsesRadius','FreePlacementFlow']:
        node=test_call(g,name,previous)
        previous,no=g.branch(node+'.Passed',node+'.then')
        g.fn('fail'+name,'FunctionalTest','FinishTest',no,TestResult='Failed',Message='Free placement case failed: '+name)
    g.fn('success','FunctionalTest','FinishTest',previous,TestResult='Succeeded',Message='Free placement and radius-area functional cases passed.')
    g.fn('fixtureFailed','FunctionalTest','FinishTest',failures[0],TestResult='Failed',Message='Start a fresh PIE session in Setup, with empty hands and all six solution areas assigned.')
    for no in failures[1:]:g.wire(no,'fixtureFailed.execute')
    g.build();compile_save(TEST)
    print(python("import unreal; b=unreal.load_asset('"+TEST+"'); unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(b,'Manager',True); unreal.BlueprintEditorLibrary.compile_blueprint(b); unreal.EditorAssetLibrary.save_asset(b.get_path_name()); s=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); m=next(a for a in s.get_all_level_actors() if a.get_actor_label()=='SYSTEM_GameplayTestManager'); t=s.spawn_actor_from_class(b.generated_class(),unreal.Vector(-200,-2200,0)); t.set_actor_label('TEST_FreePlacement_Functional'); t.set_folder_path('Tests/Manual'); t.set_editor_property('Manager',m); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); unreal.log('FREE_PLACEMENT_TEST_AUTHORED - run manually with F6; not executed')"))
