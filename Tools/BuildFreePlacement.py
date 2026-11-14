"""Author free placement and radius goals in the isolated test map. No tests run."""
import hashlib
import json
from pathlib import Path
from GameplayBridge import call,python
from BuildGameplaySystems import Graph,MANAGER,PLAYER,HUD,CLASS,build_configure_scene,build_hud
from BuildDirectorMark import function_graph,clear_function,arrange_graph

ROOT='/Game/Game/Blueprints/Gameplay/Testing/'
BASE=ROOT+'BP_FreePlacementPlayerBase'
BASE_CLASS='BP_FreePlacementPlayerBase_C'
AREA=ROOT+'BP_PlacementArea'
AREA_CLASS='BP_PlacementArea_C'
ANIMATION=ROOT+'ABP_FreePlacementPlayer'


def local_call(g,name,previous):
    return g.fn('call'+name+str(len(g.nodes)),BASE_CLASS,name,previous)


def location(g,target):
    ref=g.fn('location'+str(len(g.nodes)),'Actor','K2_GetActorLocation')
    g.wire(target,ref+'.self')
    return ref+'.ReturnValue'


def bounds(g,target,ref='bounds'):
    g.fn(ref,'Actor','GetActorBounds',bOnlyCollidingComponents='true')
    g.wire(target,ref+'.self')
    return ref


def vector_z(g,source,ref):
    g.fn(ref,'KismetMathLibrary','BreakVector');g.wire(source,ref+'.InVec')
    return ref+'.Z'


def vector_add(g,a,b,ref):
    g.fn(ref,'KismetMathLibrary','Add_VectorVector');g.wire(a,ref+'.A');g.wire(b,ref+'.B')
    return ref+'.ReturnValue'


def valid(g,target,previous,ref):
    g.fn(ref,'KismetSystemLibrary','IsValid');g.wire(target,ref+'.Object')
    return g.branch(ref+'.ReturnValue',previous)


def finish_function(g,previous,result=None):
    g.wire(previous,g.result+'.execute')
    if result:g.wire(result,g.result+'.'+g.output_name)


def build_contains_prop(g):
    g.output_name='Inside'
    previous=g.set('LastContainsResult','false',g.entry)
    prop=g.entry.rsplit('.',1)[0]+'.Prop'
    failures=[]
    for ref,target in [('validProp',prop),('validAllowedProp',g.get('AllowedProp'))]:
        previous,no=valid(g,target,previous,ref);failures.append(no)
    same=g.fn('sameProp','KismetMathLibrary','EqualEqual_ObjectObject');g.wire(prop,'sameProp.A');g.wire(g.get('AllowedProp'),'sameProp.B')
    previous,no=g.branch('sameProp.ReturnValue',previous);failures.append(no)
    box=bounds(g,prop)
    center=location(g,g.node('self','Self')+'.self')
    distance=g.fn('distance','KismetMathLibrary','Vector_Distance2D');g.wire(box+'.Origin','distance.V1');g.wire(center,'distance.V2')
    horizontal=g.compare('distance.ReturnValue','LessEqual_DoubleDouble',(g.get('Radius'),))
    previous=g.set('LastContainsResult',(horizontal,),previous)
    finish_function(g,previous,g.get('LastContainsResult'))
    for no in failures:g.wire(no,g.result+'.execute')
    g.build()


def author_area():
    call('create_blueprint',packagePath=AREA,parentClass='Actor')
    for name,kind,default in [('AllowedProp','object:BP_InteractableProp_C','None'),('Radius','double','125'),('LastContainsResult','bool','false'),('PreviewMesh','object:SceneComponent','None')]:
        call('add_variable',path=AREA,variableName=name,type=kind,defaultValue=default,category='Placement Area')
    build_contains_prop(function_graph(AREA,'ContainsProp',inputs=[dict(name='Prop',type='object:BP_InteractableProp_C')],outputs=[dict(name='Inside',type='bool')]))
    visual=function_graph(AREA,'UpdateAreaVisual')
    previous,_=valid(visual,visual.get('PreviewMesh'),visual.entry,'previewValid')
    diameter=visual.fn('scale','KismetMathLibrary','Divide_DoubleDouble',B='50');visual.wire(visual.get('Radius'),'scale.A')
    size=visual.fn('size','KismetMathLibrary','MakeVector',Z='.004');visual.wire('scale.ReturnValue','size.X');visual.wire('scale.ReturnValue','size.Y')
    visual.fn('resize','SceneComponent','SetWorldScale3D',previous);visual.wire(visual.get('PreviewMesh'),'resize.self');visual.wire('size.ReturnValue','resize.NewScale')
    visual.build();compile_save(AREA)
    summary=call('read_blueprint_graph_summary',path=AREA,graphName='UserConstructionScript')
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    construction=Graph(AREA,'UserConstructionScript')
    construction.fn('updateAreaPreview',AREA_CLASS,'UpdateAreaVisual',entry+'.then');construction.build()
    compile_save(AREA)


def compile_save(path):
    result=call('compile_blueprint',path=path)
    assert result['success'] and result['errorCount']==0,result
    print('COMPILE',path,result,flush=True)
    call('save_blueprint',path=path)
    return result


def author_player():
    print(python("import unreal; assert unreal.EditorAssetLibrary.duplicate_asset('/Game/Game/Blueprints/Player/BP_PlayerCharacter','"+BASE+"')"))
    for name,kind,default in [
        ('CanPlaceFreely','bool','false'),('PlacementPoint','vector','(X=0,Y=0,Z=0)'),
        ('FreeSurfacePoint','vector','(X=0,Y=0,Z=0)'),('PlacementDistance','double','600'),
        ('MinimumSurfaceNormalZ','double','0.85'),('TraceIgnoreActors','object:Actor[]',''),
        ('PlacementObjectTypes','enum:EObjectTypeQuery[]','(ObjectTypeQuery1,ObjectTypeQuery2,ObjectTypeQuery3,ObjectTypeQuery4,ObjectTypeQuery5,ObjectTypeQuery6)')]:
        params=dict(path=BASE,variableName=name,type=kind,category='Free Placement')
        if default:params['defaultValue']=default
        call('add_variable',**params)
    gs={name:function_graph(BASE,name) for name in ['RefreshFreePlacement','TryFreeInteract','CancelFreePlacement']}
    gs['ValidateFreePlacement']=function_graph(BASE,'ValidateFreePlacement',inputs=[dict(name='Location',type='vector'),dict(name='SurfaceNormal',type='vector'),dict(name='HasSurface',type='bool')],outputs=[dict(name='CanPlace',type='bool')])
    compile_save(BASE)
    build_validation(gs['ValidateFreePlacement'])
    build_cancel(gs['CancelFreePlacement'])
    build_refresh(gs['RefreshFreePlacement'])
    build_interact(gs['TryFreeInteract'])
    summary=call('read_blueprint_graph_summary',path=BASE,graphName='EventGraph')
    g=Graph(BASE,'EventGraph')
    for title,name,pin in [('UpdateInteraction','RefreshFreePlacement','then'),('EnhancedInputAction IA_Interact','TryFreeInteract','Started'),('EnhancedInputAction IA_Cancel','CancelFreePlacement','Started')]:
        node=next(n for n in summary['nodes'] if n.get('title')==title)
        local_call(g,name,node['id']+'.'+pin)
    g.build()
    prune_dead_interaction_nodes()
    compile_save(BASE)
    author_animation()
    print(python("import unreal; b=unreal.load_asset('"+PLAYER+"'); unreal.BlueprintEditorLibrary.reparent_blueprint(b,unreal.load_asset('"+BASE+"').generated_class()); unreal.BlueprintEditorLibrary.compile_blueprint(b); unreal.EditorAssetLibrary.save_asset(b.get_path_name())"))
    compile_save(PLAYER)
    retarget_player_members()


def author_animation():
    # The production animation reads reach/Notes variables through a cast to the
    # production player. Keep the same locomotion and retarget only that contract
    # in an isolated animation copy.
    print(python("import unreal; assert unreal.EditorAssetLibrary.duplicate_asset('/Game/Characters/Surya/Anims/ABP_Unarmed_Surya','"+ANIMATION+"')"))
    summary=call('read_blueprint_graph_summary',path=ANIMATION,graphName='EventGraph')
    replacements={}
    details={}
    g=Graph(ANIMATION,'EventGraph')
    for node in summary['nodes']:
        if node['type'] not in ['K2Node_DynamicCast','K2Node_VariableGet','K2Node_VariableSet']:continue
        detail=call('read_blueprint_node_detail',path=ANIMATION,graphName='EventGraph',nodeId=node['id'])
        old_cast=node['type']=='K2Node_DynamicCast' and 'BP_PlayerCharacter' in node.get('title','')
        target=next((p for p in detail['pins'] if p['name']=='self'),{})
        if not old_cast and target.get('subCategory')!='BP_PlayerCharacter_C':continue
        ref='isolated'+node['id']
        if old_cast:g.node(ref,'Cast',targetClass=BASE_CLASS)
        else:
            variable=next(p['name'] for p in detail['pins'] if p['name'] not in ['self','execute','then','Output_Get'])
            g.node(ref,'VariableGet' if node['type']=='K2Node_VariableGet' else 'VariableSet',variableName=variable,ownerClass=BASE_CLASS)
        replacements[node['id']]=(ref,old_cast)
        details[node['id']]=detail
    def endpoint(node_id,pin):
        item=replacements.get(node_id[:8])
        if item:
            ref,is_cast=item
            if is_cast and pin.startswith('As'):pin='AsBP Free Placement Player Base'
            return ref+'.'+pin
        return node_id+'.'+pin
    connections=set()
    for node_id,detail in details.items():
        for pin in detail['pins']:
            for link in pin.get('linkedTo',[]):
                here=endpoint(node_id,pin['name']);other=endpoint(link['node'],link['pin'])
                connections.add((other,here) if pin['direction']=='in' else (here,other))
    for source,target in sorted(connections):g.wire(source,target)
    g.build()
    for node_id in replacements:call('remove_node',path=ANIMATION,graphName='EventGraph',nodeId=node_id)
    compile_save(ANIMATION)
    summary=call('read_blueprint_graph_summary',path=BASE,graphName='EventGraph')
    begin=next(n for n in summary['nodes'] if n.get('title')=='Event BeginPlay')
    link=next(p for p in begin['connectedPins'] if p['pin']=='then')['linkedTo'][0]
    g=Graph(BASE,'EventGraph')
    g.fn('isolatedAnimation','SkeletalMeshComponent','SetAnimInstanceClass',begin['id']+'.then',NewClass=ANIMATION+'.ABP_FreePlacementPlayer_C')
    g.wire(g.get('Mesh'),'isolatedAnimation.self')
    g.wire('isolatedAnimation.then',link['node']+'.'+link['pin'])
    g.build();compile_save(BASE)


def retarget_player_members():
    # Reparenting preserves the player class but inherited variable nodes retain
    # their declaring class. Recreate those nodes with the isolated base owner.
    for path in [MANAGER,ROOT+'BP_DirectorMarkFunctionalTest']:
        for graph in call('list_blueprint_graphs',path=path)['graphs']:
            name=graph['name']
            summary=call('read_blueprint_graph_summary',path=path,graphName=name)
            for node in summary['nodes']:
                if node['type'] not in ['K2Node_VariableGet','K2Node_VariableSet']:continue
                detail=call('read_blueprint_node_detail',path=path,graphName=name,nodeId=node['id'])
                target=next((p for p in detail['pins'] if p['name']=='self'),{})
                if target.get('subCategory')!='BP_PlayerCharacter_C':continue
                variable=next(p['name'] for p in detail['pins'] if p['name'] not in ['self','execute','then','Output_Get'])
                g=Graph(path,name)
                g.node('isolatedMember','VariableGet' if node['type']=='K2Node_VariableGet' else 'VariableSet',variableName=variable,ownerClass=BASE_CLASS)
                for pin in detail['pins']:
                    for link in pin.get('linkedTo',[]):
                        if pin['direction']=='in':g.wire(link['node']+'.'+link['pin'],'isolatedMember.'+pin['name'])
                        else:g.wire('isolatedMember.'+pin['name'],link['node']+'.'+link['pin'])
                g.build()
                call('remove_node',path=path,graphName=name,nodeId=node['id'])
        compile_save(path)


def build_validation(g):
    entry=g.entry.rsplit('.',1)[0]
    previous=g.set('CanPlaceFreely','false',g.entry)
    previous=g.set('PlacementPoint',(entry+'.Location',),previous)
    failures=[]
    previous,no=valid(g,g.get('HeldProp'),previous,'heldValid');failures.append(no)
    previous,no=g.branch(entry+'.HasSurface',previous);failures.append(no)
    normal_z=vector_z(g,entry+'.SurfaceNormal','surfaceNormal')
    previous,no=g.branch(g.compare(normal_z,'GreaterEqual_DoubleDouble',(g.get('MinimumSurfaceNormalZ'),)),previous);failures.append(no)
    box=bounds(g,g.get('HeldProp'))
    offset=g.fn('boundsOffset','KismetMathLibrary','Subtract_VectorVector');g.wire(box+'.Origin','boundsOffset.A');g.wire(location(g,g.get('HeldProp')),'boundsOffset.B')
    box_center=vector_add(g,entry+'.Location','boundsOffset.ReturnValue','candidateCenter')
    inset=g.fn('inset','KismetMathLibrary','Subtract_VectorVector',B='(X=1,Y=1,Z=1)');g.wire(box+'.BoxExtent','inset.A')
    split=g.fn('halfSize','KismetMathLibrary','BreakVector');g.wire('inset.ReturnValue','halfSize.InVec')
    for axis in ['X','Y','Z']:
        previous,no=g.branch(g.compare('halfSize.'+axis,'Greater_DoubleDouble',0),previous);failures.append(no)
    overlap=g.fn('overlap','KismetSystemLibrary','BoxOverlapActors',previous)
    g.wire(box_center,'overlap.BoxPos');g.wire('inset.ReturnValue','overlap.BoxExtent')
    g.wire(g.get('PlacementObjectTypes'),'overlap.ObjectTypes');g.wire(g.get('TraceIgnoreActors'),'overlap.ActorsToIgnore')
    clear=g.fn('clear','KismetMathLibrary','Not_PreBool');g.wire('overlap.ReturnValue','clear.A')
    previous=g.set('CanPlaceFreely',('clear.ReturnValue',),'overlap.then')
    g.output_name='CanPlace';finish_function(g,previous,g.get('CanPlaceFreely'))
    for no in failures:g.wire(no,g.result+'.execute')
    g.build()


def build_cancel(g):
    previous=g.entry
    for name in ['HeldProp','TargetSlot','FocusProp']:
        previous=g.set(name,'None',previous)
    previous=g.set('CanPlaceFreely','false',previous)
    hide=g.fn('hideGhost','SceneComponent','SetVisibility',previous,bNewVisibility='false');g.wire(g.get('Ghost'),'hideGhost.self')
    g.build()


def trace(g,previous,distance,ref):
    camera=g.get('FirstPersonCamera')
    start=g.fn(ref+'Start','SceneComponent','K2_GetComponentLocation');g.wire(camera,start+'.self')
    controller=g.fn(ref+'Controller','Pawn','GetController')
    rotation=g.fn(ref+'Rotation','Controller','GetControlRotation');g.wire(controller+'.ReturnValue',rotation+'.self')
    forward=g.fn(ref+'Forward','KismetMathLibrary','GetForwardVector');g.wire(rotation+'.ReturnValue',forward+'.InRot')
    length=g.fn(ref+'Length','KismetMathLibrary','Multiply_VectorFloat');g.wire(forward+'.ReturnValue',length+'.A');g.wire(distance,length+'.B')
    end=vector_add(g,start+'.ReturnValue',length+'.ReturnValue',ref+'End')
    node=g.fn(ref,'KismetSystemLibrary','LineTraceSingle',previous,TraceChannel='TraceTypeQuery1',bTraceComplex='false',bIgnoreSelf='true',DrawDebugType='None')
    g.wire(start+'.ReturnValue',node+'.Start');g.wire(end,node+'.End');g.wire(g.get('TraceIgnoreActors'),node+'.ActorsToIgnore')
    hit=g.fn(ref+'Hit','GameplayStatics','BreakHitResult');g.wire(node+'.OutHit',hit+'.Hit')
    return node,hit,end


def build_refresh(g):
    previous=g.set('CanPlaceFreely','false',g.entry)
    previous=g.set('FocusProp','None',previous)
    hide=g.fn('hide','SceneComponent','SetVisibility',previous,bNewVisibility='false');g.wire(g.get('Ghost'),'hide.self')
    controller=g.fn('controller','Pawn','GetController')
    ignored=g.fn('ignored','Controller','IsMoveInputIgnored');g.wire('controller.ReturnValue','ignored.self')
    _,previous=g.branch('ignored.ReturnValue','hide.then')
    clear=g.fn('clearIgnore','KismetArrayLibrary','Array_Clear',previous);g.wire(g.get('TraceIgnoreActors'),'clearIgnore.TargetArray')
    holding,empty=valid(g,g.get('HeldProp'),'clearIgnore.then','holding')
    pickup,pickup_hit,_=trace(g,empty,g.get('InteractDistance'),'focusTrace')
    hit,_=g.branch(pickup+'.ReturnValue',pickup+'.then')
    g.node('focusCast','Cast',targetClass='BP_InteractableProp_C');g.wire(hit,'focusCast.execute');g.wire(pickup_hit+'.HitActor','focusCast.Object')
    previous=g.set('FocusProp',('focusCast.AsBP Interactable Prop',),'focusCast.then')
    g.set('FocusHitPoint',(pickup_hit+'.ImpactPoint',),previous)
    add=g.fn('ignoreHeld','KismetArrayLibrary','Array_Add',holding);g.wire(g.get('TraceIgnoreActors'),'ignoreHeld.TargetArray');g.wire(g.get('HeldProp'),'ignoreHeld.NewItem')
    placing,place_hit,end=trace(g,'ignoreHeld.then',g.get('PlacementDistance'),'placeTrace')
    previous=g.set('FreeSurfacePoint',(end,),placing+'.then')
    yes,no=g.branch(placing+'.ReturnValue',previous)
    surface=g.set('FreeSurfacePoint',(place_hit+'.ImpactPoint',),yes)
    box=bounds(g,g.get('HeldProp'))
    origin_z=vector_z(g,box+'.Origin','heldOrigin');extent_z=vector_z(g,box+'.BoxExtent','heldExtent')
    bottom=g.fn('bottom','KismetMathLibrary','Subtract_DoubleDouble');g.wire(origin_z,'bottom.A');g.wire(extent_z,'bottom.B')
    offset=g.fn('pivotOffset','KismetMathLibrary','Subtract_DoubleDouble');g.wire(vector_z(g,location(g,g.get('HeldProp')),'heldPivot'),'pivotOffset.A');g.wire('bottom.ReturnValue','pivotOffset.B')
    gap=g.fn('surfaceGap','KismetMathLibrary','Add_DoubleDouble',B='.5');g.wire('pivotOffset.ReturnValue','surfaceGap.A')
    lift=g.fn('lift','KismetMathLibrary','MakeVector',X='0',Y='0');g.wire('surfaceGap.ReturnValue','lift.Z')
    destination=vector_add(g,g.get('FreeSurfacePoint'),'lift.ReturnValue','destination')
    validate=local_call(g,'ValidateFreePlacement',surface)
    g.wire(no,validate+'.execute');g.wire(destination,validate+'.Location');g.wire(place_hit+'.ImpactNormal',validate+'.SurfaceNormal');g.wire(placing+'.ReturnValue',validate+'.HasSurface')
    rotation=g.fn('heldRotation','Actor','K2_GetActorRotation');g.wire(g.get('HeldProp'),'heldRotation.self')
    move=g.fn('movePreview','SceneComponent','K2_SetWorldLocationAndRotation',validate+'.then',bSweep='false',bTeleport='true')
    g.wire(g.get('Ghost'),'movePreview.self');g.wire(g.get('PlacementPoint'),'movePreview.NewLocation');g.wire('heldRotation.ReturnValue','movePreview.NewRotation')
    show=g.fn('show','SceneComponent','SetVisibility','movePreview.then',bNewVisibility='true');g.wire(g.get('Ghost'),'show.self')
    yes,no=g.branch(g.get('CanPlaceFreely'),'show.then')
    for ref,color,previous in [('green','(X=.05,Y=1,Z=.2)',yes),('red','(X=1,Y=.05,Z=.03)',no)]:
        g.fn(ref,'MeshComponent','SetVectorParameterValueOnMaterials',previous,ParameterName='PlacementColor',ParameterValue=color);g.wire(g.get('Ghost'),ref+'.self')
    g.build()


def build_interact(g):
    controller=g.fn('controller','Pawn','GetController')
    ignored=g.fn('ignored','Controller','IsMoveInputIgnored');g.wire('controller.ReturnValue','ignored.self')
    _,previous=g.branch('ignored.ReturnValue',g.entry)
    previous=local_call(g,'RefreshFreePlacement',previous)+'.then'
    holding,empty=valid(g,g.get('HeldProp'),previous,'heldValid')
    commit,_=g.branch(g.get('CanPlaceFreely'),holding)
    rotation=g.fn('heldRotation','Actor','K2_GetActorRotation');g.wire(g.get('HeldProp'),'heldRotation.self')
    move=g.fn('commit','Actor','K2_SetActorLocationAndRotation',commit,bSweep='false',bTeleport='true')
    g.wire(g.get('HeldProp'),'commit.self');g.wire(g.get('PlacementPoint'),'commit.NewLocation');g.wire('heldRotation.ReturnValue','commit.NewRotation')
    previous=g.set('CurrentSlotID','None','commit.then',owner='BP_InteractableProp_C',target=g.get('HeldProp'))
    local_call(g,'CancelFreePlacement',previous)
    pickup,_=valid(g,g.get('FocusProp'),empty,'focusValid')
    previous=g.set('HeldProp',(g.get('FocusProp'),),pickup)
    mesh=g.get('Mesh',owner='BP_InteractableProp_C',target=g.get('HeldProp'))
    asset=g.get('StaticMesh',owner='StaticMeshComponent',target=mesh)
    g.fn('previewMesh','StaticMeshComponent','SetStaticMesh',previous);g.wire(g.get('Ghost'),'previewMesh.self');g.wire(asset,'previewMesh.NewMesh')
    scale=g.fn('heldScale','Actor','GetActorScale3D');g.wire(g.get('HeldProp'),'heldScale.self')
    g.fn('previewScale','SceneComponent','SetWorldScale3D','previewMesh.then');g.wire(g.get('Ghost'),'previewScale.self');g.wire('heldScale.ReturnValue','previewScale.NewScale')
    now=g.fn('time','KismetSystemLibrary','GetGameTimeInSeconds')
    reach=g.fn('reachEnd','KismetMathLibrary','Add_DoubleDouble',B='.18');g.wire('time.ReturnValue','reachEnd.A')
    previous=g.set('ReachUntil',('reachEnd.ReturnValue',),'previewScale.then')
    reach_point=g.fn('reachPoint','KismetMathLibrary','Add_VectorVector',B='(X=0,Y=0,Z=35)');g.wire(g.get('FocusHitPoint'),'reachPoint.A')
    previous=g.set('ReachTarget',('reachPoint.ReturnValue',),previous)
    local_call(g,'RefreshFreePlacement',previous)
    g.build()


def prune_dead_interaction_nodes():
    summary=call('read_blueprint_graph_summary',path=BASE,graphName='EventGraph')
    index={n['id']:n for n in summary['nodes']}
    keep={n['id'] for n in summary['nodes'] if n['type'] in ['K2Node_Event','K2Node_CustomEvent','K2Node_EnhancedInputAction']}
    queue=list(keep)
    while queue:
        source=queue.pop()
        for pin in index[source].get('connectedPins',[]):
            if pin['direction']=='out' and (pin['pin'].startswith('then') or pin['pin'] in ['execute','Started','Triggered','Completed','Canceled','Ongoing','else','CastFailed','LoopBody']):
                for link in pin['linkedTo']:
                    if link['node'] not in keep:keep.add(link['node']);queue.append(link['node'])
    queue=list(keep)
    while queue:
        target=queue.pop()
        for pin in index[target].get('connectedPins',[]):
            if pin['direction']=='in':
                for link in pin['linkedTo']:
                    if link['node'] not in keep:keep.add(link['node']);queue.append(link['node'])
    for node in summary['nodes']:
        if node['id'] not in keep:call('remove_node',path=BASE,graphName='EventGraph',nodeId=node['id'])


def build_evaluate_puzzle(g):
    previous=g.set('Outcome',1,g.entry)
    valid1,missing1=valid(g,g.get('ActiveArea1'),previous,'areaOneValid')
    one=g.fn('insideOne',AREA_CLASS,'ContainsProp',valid1);g.wire(g.get('ActiveArea1'),'insideOne.self');g.wire(g.get('ActiveProp1'),'insideOne.Prop')
    inside1,_=g.branch('insideOne.Inside','insideOne.then')
    previous=g.set('Outcome',2,inside1)
    valid2,_=valid(g,g.get('ActiveArea2'),previous,'areaTwoValid')
    two=g.fn('insideTwo',AREA_CLASS,'ContainsProp',valid2);g.wire(g.get('ActiveArea2'),'insideTwo.self');g.wire(g.get('ActiveProp2'),'insideTwo.Prop')
    both,_=g.branch('insideTwo.Inside','insideTwo.then')
    g.set('Outcome',0,both)
    g.build()


def build_restart_free_placement(g):
    previous=g.set('State',0,g.entry)
    g.fn('unlock','Controller','ResetIgnoreMoveInput',previous);g.wire(g.get('Controller'),'unlock.self')
    g.fn('cancelSelection',BASE_CLASS,'CancelFreePlacement','unlock.then');g.wire(g.get('Player'),'cancelSelection.self')
    previous='cancelSelection.then'
    for scene in range(1,4):
        selected,next_scene=g.branch(g.compare(g.get('SceneIndex'),'EqualEqual_IntInt',scene),previous)
        completed,fresh=g.branch(g.get('Completed'+str(scene)),selected)
        decrement=g.fn('decrement'+str(scene),'KismetMathLibrary','Subtract_IntInt',B='1');g.wire(g.get('CompletedCount'),decrement+'.A')
        cleared=g.set('CompletedCount',(decrement+'.ReturnValue',),completed)
        cleared=g.set('Completed'+str(scene),'false',cleared)
        join=g.node('reset'+str(scene),'Sequence');g.wire(cleared,join+'.execute');g.wire(fresh,join+'.execute')
        restore=join+'.then_0'
        for index in [1,2]:
            prop=g.get(f'S{scene}Prop{index}');start=g.get(f'S{scene}Start{index}')
            rotation=g.fn(f'rotation{scene}{index}','Actor','K2_GetActorRotation');g.wire(start,rotation+'.self')
            move=g.fn(f'restore{scene}{index}','Actor','K2_SetActorLocationAndRotation',restore,bSweep='false',bTeleport='true')
            g.wire(prop,move+'.self');g.wire(location(g,start),move+'.NewLocation');g.wire(rotation+'.ReturnValue',move+'.NewRotation')
            restore=g.set('CurrentSlotID','None',move+'.then',owner='BP_InteractableProp_C',target=prop)
        g.invoke('ConfigureScene',restore)
        previous=next_scene
    g.build()


def author_manager():
    existing={v['name'] for v in call('list_variables',path=MANAGER)['variables']}
    for name in ['ActiveArea1','ActiveArea2']+[f'S{s}Area{p}' for s in range(1,4) for p in [1,2]]:
        if name not in existing:call('add_variable',path=MANAGER,variableName=name,type='object:'+AREA_CLASS,category='Placement Areas')
    build_evaluate_puzzle(clear_function(MANAGER,'EvaluatePuzzle'))
    build_configure_scene(clear_function(MANAGER,'ConfigureScene'))
    build_restart_free_placement(clear_function(MANAGER,'RestartScene'))
    for scene in range(1,4):
        for index in [1,2]:
            name=f'S{scene}Correct{index}'
            if name in existing:call('remove_variable',path=MANAGER,variableName=name)
    compile_save(MANAGER)


def author():
    protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['Config','Content/Game/Blueprints','Content/Game/Cinematics','Content/Game/Levels'] for p in Path(folder).rglob('*') if p.is_file() and 'Gameplay' not in p.parts and p.name!='L_GameplaySystems.umap'}
    Path('Saved/FreePlacementProtectedHashes.json').write_text(json.dumps(protected,indent=2))
    print(python("import unreal; e=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); assert e.get_game_world() is None; assert e.get_editor_world().get_path_name()=='/Game/Game/Levels/Tests/L_GameplaySystems.L_GameplaySystems'; assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(); assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages(); assert not unreal.EditorAssetLibrary.does_asset_exist('"+BASE+"')"))
    author_area();author_player();author_manager()
    summary=call('read_blueprint_graph_summary',path=HUD,graphName='EventGraph')
    for node in summary['nodes']:call('remove_node',path=HUD,graphName='EventGraph',nodeId=node['id'])
    build_hud();compile_save(HUD)
    print(python('"'+str(Path('Tools/StageFreePlacement.py').resolve()).replace('\\','/')+'"'))
    from BuildFreePlacementTests import author_tests
    author_tests()
    finish_authoring()


def finish_authoring():
    from BuildFreePlacementTests import TEST
    for path,names in [(BASE,['RefreshFreePlacement','TryFreeInteract','CancelFreePlacement','ValidateFreePlacement']),(AREA,['ContainsProp']),(MANAGER,['EvaluatePuzzle','ConfigureScene']),(HUD,['EventGraph'])]:
        for name in names:
            arrange_graph(path,name,'Free placement: '+name+'. Placement validity is geometric. Puzzle completion is a separate radius check. No gameplay tests were run during authoring.')
    for graph in call('list_blueprint_graphs',path=TEST)['graphs']:
        if graph['name']!='UserConstructionScript':arrange_graph(TEST,graph['name'],'Manual free-placement FunctionalTest. Run with F6 in a fresh PIE session. Authored only; not executed by the agent.')
    compiles={}
    for path in [BASE,PLAYER,ANIMATION,AREA,MANAGER,HUD,ROOT+'BP_DirectorMarkFunctionalTest',TEST]:compiles[path]=compile_save(path)
    print(python("import unreal; assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None; assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); unreal.log('FREE_PLACEMENT_SAVED - tests NOT RUN')"))
    protected=json.loads(Path('Saved/FreePlacementProtectedHashes.json').read_text())
    changed=[name for name,digest in protected.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
    assert not changed,changed
    Path('Saved/FreePlacementAuthoring.json').write_text(json.dumps(dict(tests_run=False,protected_files=len(protected),changed=changed,compiles=compiles),indent=2))


if __name__=='__main__':author()
