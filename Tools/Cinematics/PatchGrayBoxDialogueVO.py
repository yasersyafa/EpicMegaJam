"""Make production dialogue playback cancellable and bind intro VO to each subtitle."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameplayBridge import call
from BuildGameplaySystems import Graph
P='/Game/Game/Blueprints/Film/BP_FilmSceneManager';W='/Game/Game/UI/Scene01/WBP_Scene01Objective'
OUT=Path('Saved/GrayBoxAudio');OUT.mkdir(exist_ok=True)
clips={c['id']:c for c in json.loads((OUT/'PreparedDialogue.json').read_text())['clips']}
for path in [P,W]:
 src=Path('Content')/(path.removeprefix('/Game/')+'.uasset');dest=OUT/'Backup'/('BeforeDialogueVO_'+src.name)
 if not dest.exists():shutil.copy2(src,dest)
def summary(path,graph):return call('read_blueprint_graph_summary',path=path,graphName=graph)
def detail(path,graph,id):return call('read_blueprint_node_detail',path=path,graphName=graph,nodeId=id)
def links(d,pin):return next(p for p in d['pins'] if p['name']==pin).get('linkedTo',[])
def function(path,name,inputs=None):
 try:s=summary(path,name)
 except RuntimeError:
  call('create_function',path=path,functionName=name,inputs=inputs or []);s=summary(path,name)
 assert len(s['nodes'])==1,(name,len(s['nodes']))
 return next(n['id'] for n in s['nodes'] if n['type']=='K2Node_FunctionEntry')
def addvar(path,name,typ):
 if not any(v['name']==name for v in call('list_variables',path=path)['variables']):call('add_variable',path=path,variableName=name,type=typ,category='Voice Over',defaultValue='None')
def compile(path):
 r=call('compile_blueprint',path=path);assert r.get('success') and r.get('errorCount')==0,r
 call('save_blueprint',path=path);print('VO_COMPILED',path,r,flush=True)

# FilmSceneManager: the existing table lookup owns subtitle timing; retain the
# AudioComponent so StopDialogue can actually stop a line on CUT/reset.
addvar(P,'DialogueAudio','object:AudioComponent')
entry=function(P,'StopDialogueAudio');g=Graph(P,'StopDialogueAudio',entry+'.then')
g.fn('valid','KismetSystemLibrary','IsValid');g.wire(g.get('DialogueAudio'),'valid.Object')
yes,no=g.branch('valid.ReturnValue',g.entry)
g.fn('stop','AudioComponent','Stop',yes);g.wire(g.get('DialogueAudio'),'stop.self')
g.set('DialogueAudio','None','stop.then');g.set('DialogueAudio','None',no);g.build()
s=summary(P,'StopDialogue');entry=next(n for n in s['nodes'] if n['type']=='K2Node_FunctionEntry')
next_link=links(detail(P,'StopDialogue',entry['id']),'then')[0]
g=Graph(P,'StopDialogue');g.fn('stopVoice','BP_FilmSceneManager_C','StopDialogueAudio',entry['id']+'.then');g.wire('stopVoice.then',next_link['node']+'.'+next_link['pin']);g.build()
s=summary(P,'EventGraph');old=next(n for n in s['nodes'] if n['title']=='Play Sound 2D')
cast=next(n for n in s['nodes'] if n['title']=='Cast To SoundBase' and any(x['node']==old['id'] for p in n['connectedPins'] for x in p['linkedTo']))
call('remove_node',path=P,graphName='EventGraph',nodeId=old['id'])
g=Graph(P,'EventGraph');g.fn('newVoice','GameplayStatics','CreateSound2D',cast['id']+'.then',bAutoDestroy='false');g.wire(cast['id']+'.AsSound Base','newVoice.Sound')
p=g.set('DialogueAudio',('newVoice.ReturnValue',),'newVoice.then')
g.fn('playVoice','AudioComponent','Play',p,StartTime='0');g.wire(g.get('DialogueAudio'),'playVoice.self');g.build()
# Stop any earlier line before the next one begins, even when a row lacks VO.
s=summary(P,'EventGraph');root=next(n for n in s['nodes'] if n['title']=='PlayNextDialogue' and n['type']=='K2Node_CustomEvent')
link=links(detail(P,'EventGraph',root['id']),'then')[0]
g=Graph(P,'EventGraph');g.fn('stopPreviousVoice','BP_FilmSceneManager_C','StopDialogueAudio',root['id']+'.then');g.wire('stopPreviousVoice.then',link['node']+'.'+link['pin']);g.build()
compile(P)

# Intro subtitles are authored as nine SetText nodes in WBP_Scene01Objective.
# Insert playback immediately after each caption change; leave delays and
# tutorial pacing intact unless a recorded line needs longer to finish.
addvar(W,'IntroVoiceAudio','object:AudioComponent')
entry=function(W,'StopIntroVoice');g=Graph(W,'StopIntroVoice',entry+'.then')
g.fn('valid','KismetSystemLibrary','IsValid');g.wire(g.get('IntroVoiceAudio'),'valid.Object')
yes,no=g.branch('valid.ReturnValue',g.entry)
g.fn('stop','AudioComponent','Stop',yes);g.wire(g.get('IntroVoiceAudio'),'stop.self')
g.set('IntroVoiceAudio','None','stop.then');g.set('IntroVoiceAudio','None',no);g.build()
entry=function(W,'PlayIntroVoice',[{'name':'Sound','type':'object:SoundBase'}]);g=Graph(W,'PlayIntroVoice',entry+'.then')
g.fn('stopPrevious','WBP_Scene01Objective_C','StopIntroVoice',g.entry)
g.fn('newVoice','GameplayStatics','CreateSound2D','stopPrevious.then',bAutoDestroy='false')
g.wire(entry+'.Sound','newVoice.Sound');p=g.set('IntroVoiceAudio',('newVoice.ReturnValue',),'newVoice.then')
g.fn('playVoice','AudioComponent','Play',p,StartTime='0');g.wire(g.get('IntroVoiceAudio'),'playVoice.self');g.build()
intro_nodes=['9FE28F92','FA0D9B39','FEDF3A10','2C55638E','311513D8','99E880CF','72E6A810','E98B5235','04EFF9CC']
delays=['CAAA209B','71A406F5','D280E09D','CF9CFC0A','4F3329E6','E4F79997','2C974460','EFB77C4A','1BB30B03']
for i,node in enumerate(intro_nodes,1):
 d=detail(W,'EventGraph',node);link=links(d,'then')[0];clip=clips['INTRO_'+str(i).zfill(2)]
 g=Graph(W,'EventGraph');ref='introVoice'+str(i)
 g.fn(ref,'WBP_Scene01Objective_C','PlayIntroVoice',d['id']+'.then',Sound=clip['asset']+'.'+clip['asset'].split('/')[-1]);g.wire(ref+'.then',link['node']+'.'+link['pin']);g.build()
 # The next line must not cut off a longer recording.
 if link['node'][:8] in delays:
  dd=detail(W,'EventGraph',link['node'])
  old=float(next(p for p in dd['pins'] if p['name']=='Duration')['defaultValue'])
  if clip['duration']+.15>old:call('set_pin_default_value',path=W,graphName='EventGraph',nodeId=dd['id'],pinName='Duration',value=str(round(clip['duration']+.15,3)))
s=summary(W,'EventGraph');end=next((n for n in s['nodes'] if n['title']=='Event Destruct'),None)
if not end:
 g=Graph(W,'EventGraph');g.node('destruct','Event',eventName='Destruct');g.fn('stopVoiceOnDestruct','WBP_Scene01Objective_C','StopIntroVoice','destruct.then');g.build()
compile(W)
