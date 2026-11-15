"""Patch UI presentation without changing cinematic or puzzle behavior."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
OUT=Path('Saved/UIRefresh');OUT.mkdir(exist_ok=True)
def function(path,name,inputs=None):
 try:s=call('read_blueprint_graph_summary',path=path,graphName=name)
 except RuntimeError:
  call('create_function',path=path,functionName=name,inputs=inputs or []);s=call('read_blueprint_graph_summary',path=path,graphName=name)
 entry=next(n['id'] for n in s['nodes'] if n['type']=='K2Node_FunctionEntry')
 return Graph(path,name,entry+'.then'),s

def visibility(g,name,previous,state,ref):
 g.fn(ref,'Widget','SetVisibility',previous,InVisibility=state);g.wire(g.get(name),ref+'.self');return ref+'.then'
P='/Game/Game/Blueprints/UI/WBP_DirectorNotes'
g,s=function(P,'SetReferenceImage',[{'name':'Texture','type':'object:Texture2D'}])
if len(s['nodes'])==1:
 entry=g.entry.split('.')[0];g.fn('applyClue','Image','SetBrushFromTexture',g.entry,bMatchSize='true');g.wire(g.get('ClueImage'),'applyClue.self');g.wire(entry+'.Texture','applyClue.Texture');previous='applyClue.then'
 for i,name in enumerate(['Todo1','Todo2','Todo3']):previous=visibility(g,name,previous,'Collapsed','hideChecklist'+str(i))
 g.build()
r=call('compile_blueprint',path=P);assert r.get('errorCount')==0,r;call('save_blueprint',path=P)
P='/Game/Game/Blueprints/Film/BP_FilmSceneManager';s=call('read_blueprint_graph_summary',path=P,graphName='RefreshDirectorNotes')
if not any(n['title']=='SetReferenceImage' for n in s['nodes']):
 apply=next(n for n in s['nodes'] if n['title']=='ApplyNotes');cast=next(n for n in s['nodes'] if n['title']=='Cast To WBP_DirectorNotes')
 g=Graph(P,'RefreshDirectorNotes');g.fn('storyboard','WBP_DirectorNotes_C','SetReferenceImage',apply['id']+'.then');g.wire(cast['id']+'.AsWBP Director Notes','storyboard.self')
 ref=g.get('ReferenceImage',owner='/Game/Game/Blueprints/Film/Data/PDA_SceneConfig.PDA_SceneConfig_C',target=g.get('CurrentConfig'));g.wire(ref,'storyboard.Texture');g.build()
r=call('compile_blueprint',path=P);assert r.get('errorCount')==0,r;call('save_blueprint',path=P)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from FixCinematicVisibility import apply as apply_cinematic_visibility
apply_cinematic_visibility()
print('NOTES_REFERENCE_AND_CINEMATIC_VISIBILITY_PATCHED')

# Legacy Canvas interaction prompt shares the same runtime font.
p='/Game/Game/Blueprints/UI/BP_InteractionHUD';s=call('read_blueprint_graph_summary',path=p,graphName='EventGraph');g=Graph(p,'EventGraph')
for n in s['nodes']:
 if n['title']=='Draw Text':g.value(n['id'],'Font','/Game/Game/UI/Fonts/F_UI.F_UI')
g.build();r=call('compile_blueprint',path=p);assert r.get('errorCount')==0,r;call('save_blueprint',path=p)
