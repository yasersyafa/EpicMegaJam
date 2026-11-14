"""Shared background-only authoring helpers. No PIE/input/window automation."""
import json
from pathlib import Path
from GameplayBridge import call, python
from BuildGameplaySystems import Graph

ROOT='/Game/Game/Blueprints/Scene01/'
FLOW=ROOT+'BP_Scene01FlowDirector'
DIALOGUE=ROOT+'BP_Scene01DialoguePlayer'
ARRIVAL=ROOT+'BP_Scene01ArrivalDirector'
PLAYER=ROOT+'BP_Scene01Player'
HUD=ROOT+'BP_Scene01HUD'
MODE=ROOT+'BP_Scene01GameMode'
CONTROLLER=ROOT+'BP_Scene01Controller'
WIDGET='/Game/Game/UI/Scene01/Integration/WBP_Scene01Objective'
TABLE='/Game/Game/Audio/Scene01/DT_Scene01Dialogue'
STRUCT='/Game/Game/Audio/Scene01/ST_Scene01DialogueLine'
LEVEL='/Game/Game/Levels/Tests/L_Scene01'
SEQUENCE='/Game/Game/Cinematics/Scene01/LS_Scene01Opening'
OUT=Path('Saved/Scene01Build')
OUT.mkdir(exist_ok=True)

def cls(path):return path.rsplit('/',1)[-1]+'_C'
def obj(path):return path+'.'+path.rsplit('/',1)[-1]
def edit(code):
    # One exec expression captures all Python statements in the editor bridge.
    wrapper="import unreal,json,traceback\ntry:\n exec("+repr(code)+")\n json.dump({'ok':True},open(unreal.Paths.project_dir()+'Saved/Scene01Build/LastPythonResult.json','w'))\nexcept Exception:\n json.dump({'ok':False,'error':traceback.format_exc()},open(unreal.Paths.project_dir()+'Saved/Scene01Build/LastPythonResult.json','w'))\n"
    result=python('exec('+repr(wrapper)+')')
    report=json.loads((OUT/'LastPythonResult.json').read_text())
    assert report['ok'],report
    return result
def stage(name):return edit("exec(open(unreal.Paths.project_dir()+'Tools/Scene01/'+%r,encoding='utf-8').read())"%name)
def graph(path,name,inputs=None,outputs=None,clear=False):
    graphs={g['name'] for g in call('list_blueprint_graphs',path=path)['graphs']}
    if name not in graphs:call('create_function',path=path,functionName=name,inputs=inputs or [],outputs=outputs or [])
    summary=call('read_blueprint_graph_summary',path=path,graphName=name)
    if clear:
        for n in summary['nodes']:
            if n['type'] not in ['K2Node_FunctionEntry','K2Node_FunctionResult']:call('remove_node',path=path,graphName=name,nodeId=n['id'])
    entry=next(n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionEntry')
    g=Graph(path,name,entry+'.then')
    g.result=next((n['id'] for n in summary['nodes'] if n['type']=='K2Node_FunctionResult'),None)
    return g
def clear_events(path):
    for n in call('read_blueprint_graph_summary',path=path,graphName='EventGraph')['nodes']:call('remove_node',path=path,graphName='EventGraph',nodeId=n['id'])
def addvars(path,items):
    have={v['name'] for v in call('list_variables',path=path)['variables']}
    for name,kind,default in items:
        if name not in have:
            p=dict(path=path,variableName=name,type=kind,category='Scene 01')
            if default is not None:p['defaultValue']=str(default)
            call('add_variable',**p)
def compile_save(path):
    r=call('compile_blueprint',path=path)
    print('COMPILE',path,r,flush=True)
    (OUT/(path.rsplit('/',1)[-1]+'_compile.json')).write_text(json.dumps(r,indent=2))
    assert r.get('success') and r.get('errorCount')==0,r
    call('save_blueprint',path=path)
    return r
def invoke(g,name,p,target=None,owner=None,**values):
    ref='call'+name+str(len(g.nodes))
    g.fn(ref,owner or cls(g.path),name,p,**values)
    if target:g.wire(target,ref+'.self')
    return ref+'.then'
def valid(g,value,p):
    ref='valid'+str(len(g.nodes));g.fn(ref,'KismetSystemLibrary','IsValid');g.wire(value,ref+'.Object')
    return g.branch(ref+'.ReturnValue',p)
def clock(g):return g.fn('clock'+str(len(g.nodes)),'KismetSystemLibrary','GetGameTimeInSeconds')+'.ReturnValue'
def deadline(g,p,seconds,var='Deadline'):
    ref='deadline'+str(len(g.nodes));g.fn(ref,'KismetMathLibrary','Add_DoubleDouble',B=str(seconds));g.wire(clock(g),ref+'.A')
    return g.set(var,(ref+'.ReturnValue',),p)
def expired(g,p,var='Deadline'):return g.branch(g.compare(clock(g),'GreaterEqual_DoubleDouble',(g.get(var),)),p)[0]
def finish(g,p,**outputs):
    g.wire(p,g.result+'.execute')
    for name,value in outputs.items():g.wire(value,g.result+'.'+name)
def comment(path,name,text):
    call('organize_graph',path=path,graphName=name,action='add_comment_box',text=text,x=-80,y=-150,width=1700,height=150)
