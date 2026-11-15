"""Use recorded full CUT lines where available; keep short shout fallback."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call,python
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Film/BP_FilmSceneManager'
wav='/Game/Game/Audio/VoiceOver/S_VO_GB_CUT_EARLY.S_VO_GB_CUT_EARLY'
code="""import unreal,json
p='/Game/Game/Data/Dialogue/DT_Dialogue';t=unreal.load_asset(p);rows=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(t))
for row in rows:
 if row['Name'] in ['L01_CUT_EARLY','L02_CUT_EARLY']:
  row['VoiceSound']=\"/Script/Engine.SoundWave'"""+wav+"""'\"
  row['Duration']=max(float(row['Duration']),unreal.load_asset('"""+wav+"""').get_editor_property('duration')+.15)
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(t,json.dumps(rows,ensure_ascii=False))
assert unreal.EditorAssetLibrary.save_loaded_asset(t,False)
"""
python('exec('+repr(code)+')')
s=call('read_blueprint_graph_summary',path=P,graphName='EventGraph');play=next(n for n in s['nodes'] if n['title']=='PlayCutAudio')
detail=call('read_blueprint_node_detail',path=P,graphName='EventGraph',nodeId=play['id'])
source=next(p for p in detail['pins'] if p['name']=='execute')['linkedTo'][0]
target=next(p for p in detail['pins'] if p['name']=='then')['linkedTo'][0]
call('remove_node',path=P,graphName='EventGraph',nodeId=play['id'])
g=Graph(P,'EventGraph')
selected='AC9C0B27.ReturnValue'
combined=None
for i,key in enumerate(['L01_CUT_BLOCKED','L01_CUT_EARLY','L02_CUT_EARLY']):
 c=g.fn('matched'+str(i),'KismetMathLibrary','EqualEqual_NameName',B=key);g.wire(selected,c+'.A')
 if combined is None:combined=c+'.ReturnValue'
 else:
  o=g.fn('or'+str(i),'KismetMathLibrary','BooleanOR');g.wire(combined,o+'.A');g.wire(c+'.ReturnValue',o+'.B');combined=o+'.ReturnValue'
yes,no=g.branch(combined,source['node']+'.'+source['pin'])
g.fn('shortShout','BP_FilmSceneManager_C','PlayCutAudio',no)
g.wire(yes,target['node']+'.'+target['pin']);g.wire('shortShout.then',target['node']+'.'+target['pin']);g.build()
r=call('compile_blueprint',path=P);assert r.get('success') and r.get('errorCount')==0,r
call('save_blueprint',path=P);print('CUT_VO_PATCHED',r)
