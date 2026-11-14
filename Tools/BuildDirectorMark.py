"""Author the director-mark gate and its manual FunctionalTest. Never runs tests."""
from pathlib import Path
from collections import defaultdict,deque
import hashlib
import json
from GameplayBridge import call, python
from BuildGameplaySystems import (
    Graph, MANAGER, HUD, build_configure_scene, build_refresh_director_mark,
    build_start_take, build_hud,
)


def function_graph(path, name, inputs=None, outputs=None):
    call('create_function', path=path, functionName=name, inputs=inputs or [], outputs=outputs or [])
    summary=call('read_blueprint_graph_summary', path=path, graphName=name)
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    graph=Graph(path,name,entry+'.then')
    graph.result=next((n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionResult'),None)
    return graph


def clear_function(path,name):
    summary=call('read_blueprint_graph_summary',path=path,graphName=name)
    for node in summary['nodes']:
        if node['type']!='K2Node_FunctionEntry':
            call('remove_node',path=path,graphName=name,nodeId=node['id'])
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    return Graph(path,name,entry+'.then')


def arrange_graph(path,name,comment):
    summary=call('read_blueprint_graph_summary',path=path,graphName=name)
    nodes=summary['nodes']
    for node in nodes:
        if node['type']=='EdGraphNode_Comment':
            call('remove_node',path=path,graphName=name,nodeId=node['id'])
    nodes=[n for n in nodes if n['type']!='EdGraphNode_Comment']
    outgoing=defaultdict(set)
    indegree={n['id']:0 for n in nodes}
    for node in nodes:
        for pin in node.get('connectedPins',[]):
            if pin['direction']=='out':
                for link in pin['linkedTo']:
                    target=link['node']
                    if target in indegree and target not in outgoing[node['id']]:
                        outgoing[node['id']].add(target)
                        indegree[target]+=1
    queue=deque(n for n in indegree if indegree[n]==0)
    rank=defaultdict(int)
    while queue:
        source=queue.popleft()
        for target in outgoing[source]:
            rank[target]=max(rank[target],rank[source]+1)
            indegree[target]-=1
            if indegree[target]==0:queue.append(target)
    rows=defaultdict(int)
    for node in nodes:
        column=rank[node['id']]
        row=rows[column]
        rows[column]+=1
        call('organize_graph',path=path,graphName=name,action='move_node',nodeId=node['id'],x=420*column,y=280*row)
    call('organize_graph',path=path,graphName=name,action='add_comment_box',text=comment,x=-80,y=-130,width=420*(max(rank.values(),default=0)+1)+350,height=280*max(rows.values(),default=1)+200)


def finish_authoring():
    from BuildDirectorMarkTests import TEST
    for name,comment in [
        ('RefreshDirectorMark','Distance check only: active scene mark, XY radius and separate height tolerance. Missing references fail closed. Called on Tick and immediately before ACTION.'),
        ('StartTake','ACTION requires Setup, the active director mark and empty hands. Rejection never increments TakeID/TakeCount or locks input. CUT remains a separate path.'),
        ('ConfigureScene','Each scene selects its own director mark and props. Moving to another scene mark does not authorize ACTION for this scene.')]:
        arrange_graph(MANAGER,name,comment)
    arrange_graph(HUD,'EventGraph','Standalone HUD. Show ACTION readiness only in Setup, on the active director mark, with no held prop. F6 runs the manual native FunctionalTest.')
    graphs=call('list_blueprint_graphs',path=TEST)['graphs']
    for graph in graphs:
        if graph['name']!='UserConstructionScript':
            arrange_graph(TEST,graph['name'],'Manual FunctionalTest: '+graph['name']+'. Test execution starts only when F6 or the Unreal test runner is used. No tests were run during authoring.')
    results={}
    for path in [MANAGER,HUD,TEST]:
        result=call('compile_blueprint',path=path)
        assert result['success'] and result['errorCount']==0 and result['warningCount']==0,result
        call('save_blueprint',path=path)
        results[path]=result
    print(python("import unreal; e=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); assert e.get_game_world() is None; s=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); a=s.get_all_level_actors(); m=next(x for x in a if x.get_actor_label()=='SYSTEM_GameplayTestManager'); assert all(m.get_editor_property('S'+str(i)+'DirectorMark') is not None for i in range(1,4)); t=next(x for x in a if x.get_actor_label()=='TEST_DirectorMark_Functional'); assert t.get_editor_property('Manager')==m; assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); unreal.log('DIRECTOR_MARK_SAVED - functional tests NOT RUN')"))
    protected=json.loads(Path('Saved/DirectorMarkProtectedHashes.json').read_text())
    changed=[name for name,digest in protected.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
    assert not changed,changed
    Path('Saved/DirectorMarkIsolation.json').write_text(json.dumps({'changed':changed,'protected_files':len(protected),'tests_run':False,'compiles':results},indent=2))
    print('DIRECTOR_MARK_AUTHORED_TESTS_NOT_RUN')


def author():
    protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
               for folder in ['Config','Content/Game/Blueprints','Content/Game/Cinematics','Content/Game/Levels']
               for p in Path(folder).rglob('*') if p.is_file() and 'Gameplay' not in p.parts
               and p.name!='L_GameplaySystems.umap'}
    Path('Saved/DirectorMarkProtectedHashes.json').write_text(json.dumps(protected,indent=2))
    print(python("import unreal; e=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); assert e.get_game_world() is None, 'Stop PIE first'; assert e.get_editor_world().get_path_name()=='/Game/Game/Levels/Tests/L_GameplaySystems.L_GameplaySystems'; assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(); assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()"))
    variables=[('ActiveDirectorMark','object:Actor','None'),('AtDirectorMark','bool','false'),
               ('DirectorMarkRadius','double','100'),('DirectorMarkHeightTolerance','double','120')]
    variables += [(f'S{s}DirectorMark','object:Actor','None') for s in range(1,4)]
    existing={v['name'] for v in call('list_variables',path=MANAGER)['variables']}
    assert not any(name in existing for name,_,_ in variables),'Director mark already authored.'
    for name,kind,default in variables:
        call('add_variable',path=MANAGER,variableName=name,type=kind,defaultValue=default,category='Director Mark')
    refresh=function_graph(MANAGER,'RefreshDirectorMark')
    build_refresh_director_mark(refresh)
    print(call('compile_blueprint',path=MANAGER))
    build_configure_scene(clear_function(MANAGER,'ConfigureScene'))
    build_start_take(clear_function(MANAGER,'StartTake'))
    # Patch Tick only, preserving input key flags and existing event wiring.
    summary=call('read_blueprint_graph_summary',path=MANAGER,graphName='EventGraph')
    tick=next(n for n in summary['nodes'] if n.get('title')=='Event Tick')
    pin=next(p for p in tick['connectedPins'] if p['pin']=='then')
    target=pin['linkedTo'][0]
    g=Graph(MANAGER,'EventGraph')
    ref=g.fn('refreshDirectorMark','BP_GameplayTestManager_C','RefreshDirectorMark',tick['id']+'.then')
    g.wire(ref+'.then',target['node']+'.'+target['pin']);g.build()
    summary=call('read_blueprint_graph_summary',path=HUD,graphName='EventGraph')
    for node in summary['nodes']:call('remove_node',path=HUD,graphName='EventGraph',nodeId=node['id'])
    build_hud()
    for path in [MANAGER,HUD]:
        result=call('compile_blueprint',path=path)
        assert result['success'] and result['errorCount']==0,result
        print('COMPILE',path,result)
        call('save_blueprint',path=path)
    print(python('"'+str(Path('Tools/StageDirectorMarks.py').resolve()).replace('\\','/')+'"'))
    from BuildDirectorMarkTests import author_tests
    author_tests()
    finish_authoring()


if __name__=='__main__':
    author()
