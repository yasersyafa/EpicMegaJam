from Scene01Editor import *
from Scene01DialogueData import rows
import sys

for path,parent in ([] if '--resume' in sys.argv else [(FLOW,'Actor'),(DIALOGUE,'Actor'),(HUD,'HUD'),(MODE,'GameModeBase')]):
    call('create_blueprint',packagePath=path,parentClass=parent)

fields=[dict(name=n,type=t) for n,t in [('LineID','name'),('Speaker','string'),('Subtitle','string'),('Sound','object:SoundBase'),('FallbackSeconds','double'),('NextLine','name'),('Spatial','bool'),('Group','name')]]
if '--resume' not in sys.argv:
    print(call('create_struct',packagePath=STRUCT,fields=fields))
    print(call('create_data_table',packagePath=TABLE,rowStruct=STRUCT))
    for row in rows():call('add_data_table_row',path=TABLE,rowName=row['LineID'],values=row)
for path in [TABLE,STRUCT]:call('save_asset',path=path)
(OUT/'dialogue_manifest.json').write_text(json.dumps(rows(),indent=2))

# Dedicated caption widget has the same functions/layout, no legacy timed dialogue.
clear_events(WIDGET)
compile_save(WIDGET)
# All incoming calls in the cloned arrival now target the isolated widget class.
addvars(ARRIVAL,[('SceneHUD','object:'+obj(WIDGET)+'_C','None')])
for name in ['AdvanceTutorial','HandleDoor','HandleNotes']:
    s=call('read_blueprint_graph_summary',path=ARRIVAL,graphName=name)
    g=Graph(ARRIVAL,name)
    replacements={}
    for n in s['nodes']:
        if n['title']=='Get ArrivalHUD':
            ref='isolated'+n['id'];g.node(ref,'VariableGet',variableName='SceneHUD');replacements[n['id']]=ref
            continue
        if n['title'] not in ['SetHint','ToggleNotes']:continue
        ref='isolated'+n['id'];g.fn(ref,obj(WIDGET)+'_C',n['title'])
        d=call('read_blueprint_node_detail',path=ARRIVAL,graphName=name,nodeId=n['id'])
        for p in d['pins']:
            if p['direction']=='in' and not p.get('linkedTo') and p.get('defaultValue') not in [None,''] and p['name']!='self':g.value(ref,p['name'],p['defaultValue'])
        replacements[n['id']]=ref
    def endpoint(node,pin):return replacements.get(node[:8],node)+'.'+('SceneHUD' if node[:8] in replacements and pin=='ArrivalHUD' else pin)
    edges=set()
    for n in s['nodes']:
        for p in n.get('connectedPins',[]):
            if p['direction']=='out':
                for link in p['linkedTo']:
                    if n['id'] in replacements or link['node'] in replacements:edges.add((endpoint(n['id'],p['pin']),endpoint(link['node'],link['pin'])))
    for a,b in edges:g.wire(a,b)
    g.build()
    for n in replacements:call('remove_node',path=ARRIVAL,graphName=name,nodeId=n)

# Keep only the original controller's inherited mapping context configuration.
# Mapping contexts are defaults on the existing controller's parent (check below).
clear_events(CONTROLLER)
compile_save(CONTROLLER)
print(call('read_class_defaults',path=CONTROLLER))

# Retarget the copied animation to the copied player contract.
animation=ROOT+'ABP_Scene01Player'
for graphinfo in call('list_blueprint_graphs',path=animation)['graphs']:
    name=graphinfo['name']
    if name!='EventGraph':continue
    s=call('read_blueprint_graph_summary',path=animation,graphName=name);g=Graph(animation,name);replacements={};details={}
    for n in s['nodes']:
        if n['type'] not in ['K2Node_DynamicCast','K2Node_VariableGet','K2Node_VariableSet']:continue
        d=call('read_blueprint_node_detail',path=animation,graphName=name,nodeId=n['id'])
        old=n['type']=='K2Node_DynamicCast' and 'FreePlacementPlayerBase' in n['title']
        target=next((p for p in d['pins'] if p['name']=='self'),{})
        if not old and target.get('subCategory')!='BP_FreePlacementPlayerBase_C':continue
        ref='scene'+n['id']
        if old:g.node(ref,'Cast',targetClass=cls(PLAYER))
        else:
            variable=next(p['name'] for p in d['pins'] if p['name'] not in ['self','execute','then','Output_Get'])
            g.node(ref,'VariableGet' if n['type']=='K2Node_VariableGet' else 'VariableSet',variableName=variable,ownerClass=cls(PLAYER))
        replacements[n['id']]=(ref,old);details[n['id']]=d
    def ep(node,pin):
        if node[:8] not in replacements:return node+'.'+pin
        ref,cast=replacements[node[:8]]
        return ref+'.'+('AsBP Scene 01Player' if cast and pin.startswith('As') else pin)
    edges=set()
    for node,d in details.items():
        for p in d['pins']:
            for l in p.get('linkedTo',[]):
                edges.add((ep(l['node'],l['pin']),ep(node,p['name'])) if p['direction']=='in' else (ep(node,p['name']),ep(l['node'],l['pin'])))
    for a,b in edges:g.wire(a,b)
    g.build()
    for node in replacements:call('remove_node',path=animation,graphName=name,nodeId=node)
compile_save(animation)
for n in call('read_blueprint_graph_summary',path=PLAYER,graphName='EventGraph')['nodes']:
    if n['title']=='Set Anim Instance Class':call('set_pin_default_value',path=PLAYER,graphName='EventGraph',nodeId=n['id'],pinName='NewClass',value=obj(animation)+'_C')
compile_save(PLAYER)
print('ASSETS_READY_NO_RUNTIME_TESTS')
