"""Replace animation literals at the owning intro Blueprint, preserving timing and input flow."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
P='/Game/Game/Blueprints/Flow/BP_ArrivalDirector'
retarget=Path('Saved/CharacterPolish/crew_bone_tree.json')
if retarget.exists():
 payload=json.loads(retarget.read_text());call('set_asset_property',**payload);call('save_asset',path=payload['path'])
changes=[]
for graph in call('list_blueprint_graphs',path=P)['graphs']:
 name=graph['name'];summary=call('read_blueprint_graph_summary',path=P,graphName=name,withPinValues=True);nodes={n['id']:n for n in summary['nodes']}
 for n in nodes.values():
  if n['title']!='Play Animation':continue
  owners=set();queue=[n['id']];seen=set()
  while queue:
   key=queue.pop()
   if key in seen:continue
   seen.add(key);node=nodes[key]
   if node['title'] in ['Get Maya','Get CrewA','Get CrewB']:owners.add(node['title'])
   for pin in node.get('connectedPins',[]):
    if pin['direction']=='in' and pin['pin'] not in ['execute','exec']:
     queue.extend(x['node'] for x in pin['linkedTo'])
  assert len(owners)==1,(name,n,owners)
  old=n.get('values',{}).get('NewAnimToPlay','')
  walking='Walk' in old or 'walk' in old
  package='/Game/Game/Characters/Maya/Animations/A_Maya_' if 'Get Maya' in owners else '/Game/Game/Characters/Crew/Animations/A_Crew_'
  new=package+(('WalkWithScript' if walking else 'ReadScript') if 'Get Maya' in owners else ('Walk' if walking else 'Idle'))
  call('set_pin_default_value',path=P,graphName=name,nodeId=n['id'],pinName='NewAnimToPlay',value=new+'.'+new.rsplit('/',1)[-1])
  changes.append({'graph':name,'node':n['id'],'owner':next(iter(owners)),'animation':new})
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P)
Path('Saved/CharacterPolish/intro_animation_calls.json').write_text(json.dumps(changes,indent=2))
print('Intro animation calls patched:',len(changes),r)
