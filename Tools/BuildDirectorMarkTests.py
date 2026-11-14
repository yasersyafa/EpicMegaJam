"""Create a native Unreal FunctionalTest Blueprint. Authoring does not run it."""
from GameplayBridge import call,python
from BuildGameplaySystems import Graph,MANAGER,CLASS
from BuildDirectorMark import function_graph

TEST='/Game/Game/Blueprints/Gameplay/Testing/BP_DirectorMarkFunctionalTest'
TEST_CLASS='BP_DirectorMarkFunctionalTest_C'


def manager_value(graph,name):
    return graph.get(name,owner=CLASS,target=graph.get('Manager'))


def set_manager(graph,name,value,previous):
    return graph.set(name,value,previous,owner=CLASS,target=graph.get('Manager'))


def manager_call(graph,name,previous,**defaults):
    ref=graph.fn('manager'+name+str(len(graph.nodes)),CLASS,name,previous,**defaults)
    graph.wire(graph.get('Manager'),ref+'.self')
    return ref


def test_call(graph,name,previous):
    return graph.fn('test'+name+str(len(graph.nodes)),TEST_CLASS,name,previous)


def actor_location(graph,actor):
    ref=graph.fn('location'+str(len(graph.nodes)),'Actor','K2_GetActorLocation')
    graph.wire(actor,ref+'.self')
    return ref+'.ReturnValue'


def move_player(graph,location,previous):
    ref=graph.fn('movePlayer'+str(len(graph.nodes)),'Actor','K2_SetActorLocation',previous,bSweep='false',bTeleport='true')
    graph.wire(graph.get('Player'),ref+'.self')
    graph.wire(location,ref+'.NewLocation')
    return ref+'.then'


def record(graph,condition,message,previous):
    ref=graph.fn('assert'+str(len(graph.nodes)),'FunctionalTest','AssertTrue',previous,Message=message)
    graph.wire(condition,ref+'.Condition')
    combined=graph.fn('combine'+str(len(graph.nodes)),'KismetMathLibrary','BooleanAND')
    graph.wire(graph.get('CasePassed'),combined+'.A')
    graph.wire(ref+'.ReturnValue',combined+'.B')
    return graph.set('CasePassed',(combined+'.ReturnValue',),ref+'.then')


def make_offset(graph,x_delta=None,z_delta=None):
    defaults={'Y':'0'}
    if x_delta is None:defaults['X']='0'
    if z_delta is None:defaults['Z']='88'
    ref=graph.fn('offset'+str(len(graph.nodes)),'KismetMathLibrary','MakeVector',**defaults)
    if x_delta is not None:
        add=graph.fn('offsetX'+str(len(graph.nodes)),'KismetMathLibrary','Add_DoubleDouble',B=str(x_delta))
        graph.wire(manager_value(graph,'DirectorMarkRadius'),add+'.A')
        graph.wire(add+'.ReturnValue',ref+'.X')
    if z_delta is not None:
        add=graph.fn('offsetZ'+str(len(graph.nodes)),'KismetMathLibrary','Add_DoubleDouble',B=str(z_delta))
        graph.wire(manager_value(graph,'DirectorMarkHeightTolerance'),add+'.A')
        graph.wire(add+'.ReturnValue',ref+'.Z')
    return ref+'.ReturnValue'


def build_case(name,scene,accepted,x_delta=None,z_delta=None,wrong_scene=False,missing=False,holding=False):
    graph=function_graph(TEST,name,outputs=[dict(name='Passed',type='bool')])
    previous=graph.set('CasePassed','true',graph.entry)
    previous=manager_call(graph,'SelectScene'+str(scene),previous)+'.then'
    previous=graph.set('CaseMark',(manager_value(graph,'ActiveDirectorMark'),),previous)
    previous=graph.set('CaseTakeID',(manager_value(graph,'TakeID'),),previous)
    previous=graph.set('CaseTakeCount',(manager_value(graph,'TakeCount'),),previous)
    for index in [1,2]:
        prop=manager_value(graph,'ActiveProp'+str(index))
        previous=graph.set('CasePosition'+str(index),(actor_location(graph,prop),),previous)
        slot=graph.get('CurrentSlotID',owner='BP_InteractableProp_C',target=prop)
        previous=graph.set('CaseSlot'+str(index),(slot,),previous)
    mark=manager_value(graph,'S2DirectorMark') if wrong_scene else graph.get('CaseMark')
    location=actor_location(graph,mark)
    offset=make_offset(graph,x_delta,z_delta)
    destination=graph.fn('destination','KismetMathLibrary','Add_VectorVector')
    graph.wire(location,destination+'.A');graph.wire(offset,destination+'.B')
    previous=move_player(graph,destination+'.ReturnValue',previous)
    if missing:
        previous=set_manager(graph,'ActiveDirectorMark','None',previous)
    if holding:
        selected=manager_call(graph,'SetHeldProp',previous)
        graph.wire(manager_value(graph,'ActiveProp1'),selected+'.Prop')
        previous=selected+'.then'
    previous=manager_call(graph,'RequestActionCut',previous)+'.then'
    condition=graph.compare(manager_value(graph,'State'),'EqualEqual_IntInt',1 if accepted else 0)
    previous=record(graph,condition,name+' accepts or rejects ACTION correctly',previous)
    for value in ['TakeID','TakeCount']:
        expected=graph.get('Case'+value)
        if accepted:
            add=graph.fn('expected'+value,'KismetMathLibrary','Add_IntInt',B='1')
            graph.wire(expected,add+'.A');expected=add+'.ReturnValue'
        condition=graph.compare(manager_value(graph,value),'EqualEqual_IntInt',(expected,))
        previous=record(graph,condition,name+' updates '+value+' only on accepted ACTION',previous)
    locked=graph.fn('locked','Controller','IsMoveInputIgnored')
    graph.wire(graph.get('Controller'),'locked.self')
    if accepted:
        condition=locked+'.ReturnValue'
    else:
        neg=graph.fn('notLocked','KismetMathLibrary','Not_PreBool');graph.wire(locked+'.ReturnValue',neg+'.A')
        condition=neg+'.ReturnValue'
    previous=record(graph,condition,name+' movement lock matches the result',previous)
    if accepted:
        # Simulate displacement after ACTION. CUT must remain available off the mark.
        delta=make_offset(graph,x_delta=500)
        destination=graph.fn('outsideAfterAction','KismetMathLibrary','Add_VectorVector')
        graph.wire(actor_location(graph,graph.get('CaseMark')),destination+'.A')
        graph.wire(delta,destination+'.B')
        previous=move_player(graph,destination+'.ReturnValue',previous)
        previous=manager_call(graph,'RequestActionCut',previous)+'.then'
    else:
        previous=manager_call(graph,'CancelTake',previous)+'.then'
    if holding:
        previous=manager_call(graph,'SetHeldProp',previous)+'.then'
    previous=set_manager(graph,'ActiveDirectorMark',(graph.get('CaseMark'),),previous)
    previous=record(graph,graph.compare(manager_value(graph,'State'),'EqualEqual_IntInt',0),name+' finishes in Setup',previous)
    check=graph.fn('unlocked','Controller','IsMoveInputIgnored');graph.wire(graph.get('Controller'),'unlocked.self')
    neg=graph.fn('movementRestored','KismetMathLibrary','Not_PreBool');graph.wire(check+'.ReturnValue',neg+'.A')
    previous=record(graph,neg+'.ReturnValue',name+' restores movement after CUT',previous)
    for index in [1,2]:
        prop=manager_value(graph,'ActiveProp'+str(index))
        distance=graph.fn('propDistance'+str(index),'KismetMathLibrary','Vector_Distance')
        graph.wire(actor_location(graph,prop),distance+'.V1')
        graph.wire(graph.get('CasePosition'+str(index)),distance+'.V2')
        previous=record(graph,graph.compare(distance+'.ReturnValue','LessEqual_DoubleDouble',.1),name+' preserves prop '+str(index)+' position',previous)
        slot=graph.get('CurrentSlotID',owner='BP_InteractableProp_C',target=prop)
        previous=record(graph,graph.compare(slot,'EqualEqual_NameName',(graph.get('CaseSlot'+str(index)),)),name+' preserves prop '+str(index)+' slot',previous)
    graph.wire(previous,graph.result+'.execute')
    graph.wire(graph.get('CasePassed'),graph.result+'.Passed')
    graph.build()


def author_tests():
    call('create_blueprint',packagePath=TEST,parentClass='FunctionalTest')
    variables=[('Manager','object:BP_GameplayTestManager_C','None'),('Player','object:BP_GameplayPlayer_C','None'),
               ('Controller','object:PlayerController','None'),('SnapshotTaken','bool','false'),('CasePassed','bool','false'),
               ('OriginalSceneIndex','int','1'),('OriginalTakeID','int','0'),('OriginalTakeCount','int','0'),
               ('OriginalSimulatorEnabled','bool','true'),('OriginalPlayerLocation','vector','(X=0,Y=0,Z=0)'),
               ('OriginalPlayerRotation','rotator','(Pitch=0,Yaw=0,Roll=0)'),('OriginalControlRotation','rotator','(Pitch=0,Yaw=0,Roll=0)'),
               ('CaseMark','object:Actor','None'),('CaseTakeID','int','0'),('CaseTakeCount','int','0'),
               ('CasePosition1','vector','(X=0,Y=0,Z=0)'),('CasePosition2','vector','(X=0,Y=0,Z=0)'),
               ('CaseSlot1','name','None'),('CaseSlot2','name','None')]
    for name,kind,default in variables:
        call('add_variable',path=TEST,variableName=name,type=kind,defaultValue=default,category='Director Mark Tests')
    restore=function_graph(TEST,'RestoreSnapshot')
    previous,_=restore.branch(restore.get('SnapshotTaken'),restore.entry)
    previous=manager_call(restore,'CancelTake',previous)+'.then'
    for name in ['SceneIndex','TakeID','TakeCount','SimulatorEnabled']:
        previous=set_manager(restore,name,(restore.get('Original'+name),),previous)
    previous=manager_call(restore,'ConfigureScene',previous)+'.then'
    move=restore.fn('restorePlayer','Actor','K2_SetActorLocationAndRotation',previous,bSweep='false',bTeleport='true')
    restore.wire(restore.get('Player'),'restorePlayer.self')
    restore.wire(restore.get('OriginalPlayerLocation'),'restorePlayer.NewLocation')
    restore.wire(restore.get('OriginalPlayerRotation'),'restorePlayer.NewRotation')
    view=restore.fn('restoreView','Controller','SetControlRotation','restorePlayer.then')
    restore.wire(restore.get('Controller'),'restoreView.self')
    restore.wire(restore.get('OriginalControlRotation'),'restoreView.NewRotation')
    previous=manager_call(restore,'RefreshDirectorMark','restoreView.then')+'.then'
    restore.set('SnapshotTaken','false',previous);restore.build()

    cases=[('OutsideActiveMark',1,False,dict(x_delta=25)),
           ('InsideActiveMark',1,True,{}),
           ('ExactRadiusBoundary',1,True,dict(x_delta=0)),
           ('OneCentimetreOutside',1,False,dict(x_delta=1)),
           ('AboveMarkTolerance',1,False,dict(z_delta=1)),
           ('WrongSceneMark',1,False,dict(wrong_scene=True)),
           ('MissingMarkReference',1,False,dict(missing=True)),
           ('HeldPropOnMark',1,False,dict(holding=True)),
           ('SceneTwoMark',2,True,{}),
           ('SceneThreeMark',3,True,{})]
    for name,scene,accepted,options in cases:
        build_case(name,scene,accepted,**options)
    call('compile_blueprint',path=TEST)

    graph=Graph(TEST,'EventGraph')
    graph.node('begin','Event',eventName='ReceiveBeginPlay')
    pc=graph.fn('localController','GameplayStatics','GetPlayerController')
    graph.fn('enableInput','Actor','EnableInput','begin.then')
    graph.wire('localController.ReturnValue','enableInput.PlayerController')
    graph.node('runKey','InputKey',key='F6')
    graph.fn('manualRun','FunctionalTestingManager','RunAllFunctionalTests','runKey.Pressed',bNewLog='true',bRunLooped='false')
    graph.node('testFinished','Event',eventName='ReceiveTestFinished')
    test_call(graph,'RestoreSnapshot','testFinished.then')
    graph.node('testStart','Event',eventName='ReceiveStartTest')
    previous=graph.set('SnapshotTaken','false','testStart.then')
    failures=[]
    for name,target in [('managerValid',graph.get('Manager'))]:
        valid=graph.fn(name,'KismetSystemLibrary','IsValid');graph.wire(target,valid+'.Object')
        previous,failed=graph.branch(valid+'.ReturnValue',previous);failures.append(failed)
    previous=graph.set('Player',(manager_value(graph,'Player'),),previous)
    previous=graph.set('Controller',(manager_value(graph,'Controller'),),previous)
    for name,target in [('playerValid',graph.get('Player')),('controllerValid',graph.get('Controller'))]+[(f'mark{s}Valid',manager_value(graph,f'S{s}DirectorMark')) for s in range(1,4)]:
        valid=graph.fn(name,'KismetSystemLibrary','IsValid');graph.wire(target,valid+'.Object')
        previous,failed=graph.branch(valid+'.ReturnValue',previous);failures.append(failed)
    previous,failed=graph.branch(graph.compare(manager_value(graph,'State'),'EqualEqual_IntInt',0),previous);failures.append(failed)
    previous,failed=graph.branch(graph.compare(manager_value(graph,'CompletedCount'),'EqualEqual_IntInt',0),previous);failures.append(failed)
    held=graph.get('HeldProp',owner='BP_GameplayPlayer_C',target=graph.get('Player'))
    valid=graph.fn('heldValid','KismetSystemLibrary','IsValid');graph.wire(held,'heldValid.Object')
    failed,previous=graph.branch('heldValid.ReturnValue',previous);failures.append(failed)
    for name in ['SceneIndex','TakeID','TakeCount','SimulatorEnabled']:
        previous=graph.set('Original'+name,(manager_value(graph,name),),previous)
    previous=graph.set('OriginalPlayerLocation',(actor_location(graph,graph.get('Player')),),previous)
    rotation=graph.fn('playerRotation','Actor','K2_GetActorRotation');graph.wire(graph.get('Player'),'playerRotation.self')
    previous=graph.set('OriginalPlayerRotation',('playerRotation.ReturnValue',),previous)
    rotation=graph.fn('controlRotation','Controller','GetControlRotation');graph.wire(graph.get('Controller'),'controlRotation.self')
    previous=graph.set('OriginalControlRotation',('controlRotation.ReturnValue',),previous)
    previous=graph.set('SnapshotTaken','true',previous)
    previous=set_manager(graph,'SimulatorEnabled','false',previous)
    for name,_,_,_ in cases:
        invocation=test_call(graph,name,previous)
        previous,failed=graph.branch(invocation+'.Passed',invocation+'.then')
        graph.fn('fail'+name,'FunctionalTest','FinishTest',failed,TestResult='Failed',Message='Director mark case failed: '+name)
    graph.fn('success','FunctionalTest','FinishTest',previous,TestResult='Succeeded',Message='Director mark functional cases passed. CUT remains available outside the mark.')
    graph.fn('fixtureFailed','FunctionalTest','FinishTest',failures[0],TestResult='Failed',Message='Start from a fresh PIE session in Setup, with no held prop and all three director marks assigned.')
    for source in failures[1:]:graph.wire(source,'fixtureFailed.execute')
    graph.build()
    result=call('compile_blueprint',path=TEST)
    assert result['success'] and result['errorCount']==0,result
    print('COMPILE_FUNCTIONAL_TEST_ONLY',result)
    call('save_blueprint',path=TEST)
    print(python("import unreal; p='"+TEST+"'; b=unreal.load_asset(p); unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(b,'Manager',True); unreal.BlueprintEditorLibrary.compile_blueprint(b); unreal.EditorAssetLibrary.save_asset(p); s=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); a=s.get_all_level_actors(); m=next(x for x in a if x.get_actor_label()=='SYSTEM_GameplayTestManager'); t=s.spawn_actor_from_class(b.generated_class(),unreal.Vector(-200,-2500,0)); t.set_actor_label('TEST_DirectorMark_Functional'); t.set_folder_path('Tests/Manual'); t.set_editor_property('Manager',m); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); unreal.log('FUNCTIONAL_TEST_AUTHORED - press F6 in a fresh PIE session to run manually')"))
