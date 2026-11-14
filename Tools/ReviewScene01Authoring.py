"""Static authoring review only: compile, references and package isolation.

Does not invoke runtime Blueprint functions, PIE, functional/unit tests, input,
viewport previews, or packaging.
"""
from Scene01Editor import *
import hashlib

def prune_unreachable_player_nodes():
    name='EventGraph';s=call('read_blueprint_graph_summary',path=PLAYER,graphName=name)
    index={n['id']:n for n in s['nodes']}
    keep={n['id'] for n in s['nodes'] if n['type'] in ['K2Node_Event','K2Node_CustomEvent','K2Node_EnhancedInputAction']}
    queue=list(keep)
    while queue:
        for p in index[queue.pop()].get('connectedPins',[]):
            if p['direction']=='out' and (p['pin'].startswith('then') or p['pin'] in ['Started','Triggered','Completed','Canceled','Ongoing','else','CastFailed','LoopBody']):
                for link in p['linkedTo']:
                    if link['node'] not in keep:keep.add(link['node']);queue.append(link['node'])
    queue=list(keep)
    while queue:
        for p in index[queue.pop()].get('connectedPins',[]):
            if p['direction']=='in':
                for link in p['linkedTo']:
                    if link['node'] not in keep:keep.add(link['node']);queue.append(link['node'])
    for n in s['nodes']:
        if n['id'] not in keep:call('remove_node',path=PLAYER,graphName=name,nodeId=n['id'])

prune_unreachable_player_nodes()
for variable in ['OpeningDirector','ArrivalHUD','CrewCase','bNotesOpen']:
    if variable in {v['name'] for v in call('list_variables',path=ARRIVAL)['variables']}:call('remove_variable',path=ARRIVAL,variableName=variable)
if 'FilmSceneManager' in {v['name'] for v in call('list_variables',path=CONTROLLER)['variables']}:call('remove_variable',path=CONTROLLER,variableName='FilmSceneManager')

results={}
for path in [WIDGET,PLAYER,ROOT+'ABP_Scene01Player',CONTROLLER,ARRIVAL,DIALOGUE,FLOW,HUD,MODE]:results[path]=compile_save(path)
inventory=json.loads((OUT/'static_inventory.json').read_text())
missing=[k for k,v in inventory['references'].items() if not v]
assert not missing,missing
assert all('/Game/Game/Levels/Tests/L_Scene01.' in v for v in inventory['references'].values())
assert inventory['game_mode']==obj(MODE)+'_C'
assert len(inventory['row_names'])==len(set(inventory['row_names']))
assert all(v=='None' for v in inventory['sound_column'])

# Check graph links structurally; never execute these functions.
for path,name in [(FLOW,'StartTake'),(FLOW,'PollTake'),(FLOW,'CancelTake'),(FLOW,'NotifyTakeFinished'),(DIALOGUE,'PlayLine'),(DIALOGUE,'PollDialogue')]:
    s=call('read_blueprint_graph_summary',path=path,graphName=name)
    (OUT/(cls(path)+'_'+name+'_final.json')).write_text(json.dumps(s,indent=2))
print(edit("import unreal; assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None; assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()"))
protected=json.loads((OUT/'protected_hashes.json').read_text())
changed=[p for p,digest in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest]
assert not changed,changed
report=dict(tests_run=False,pie_run=False,packaging_run=False,protected_packages=len(protected),changed_source_packages=changed,dialogue_rows=len(inventory['row_names']),compiles=results)
(OUT/'authoring_report.json').write_text(json.dumps(report,indent=2))
Path('Docs/Scene01_AuthoringReport.json').write_text(json.dumps(report,indent=2))
print('STATIC_AUTHORING_REVIEW_COMPLETE',len(protected),'source packages unchanged;',len(inventory['row_names']),'dialogue rows. NO runtime tests.')
