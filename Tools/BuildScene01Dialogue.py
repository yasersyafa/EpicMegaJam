"""Build cancellable, data-driven Blueprint VO. Authoring/compile only."""
from Scene01Editor import *

def column(g,name,p,var=None):
    ref='read'+name+str(len(g.nodes));g.fn(ref,cls(DIALOGUE),'ReadColumn',p,Column=name)
    if var:return g.set(var,(ref+'.Value',),ref+'.then')
    return ref+'.then',ref+'.Value'

addvars(DIALOGUE,[('DialogueTable','object:DataTable',obj(TABLE)),('LineID','name','None'),('NextLine','name','None'),('SessionID','int','0'),('CompletedSessionID','int','0'),('Active','bool','false'),('Finished','bool','false'),('Paused','bool','false'),('Deadline','double','0'),('FallbackSeconds','double','3'),('Speaker','string',''),('Subtitle','string',''),('SoundExport','string',''),('Spatial','bool','false'),('ColumnValue','string',''),('Audio','object:AudioComponent','None'),('Caption','object:TextBlock','None'),('Maya','object:Actor','None'),('CrewA','object:Actor','None'),('CrewB','object:Actor','None'),('SpeakerActor','object:Actor','None'),('Volume','double','1')])
addvars(DIALOGUE,[('Attenuation','object:SoundAttenuation','None')])
for name,inputs,outputs in [
 ('ReadColumn',[dict(name='Column',type='name')],[dict(name='Value',type='string')]),
 ('PlayLine',[dict(name='InLineID',type='name')],[]),('StopDialogue',[],[]),('PollDialogue',[],[]),('FinishLine',[],[]),
 ('SetDialoguePaused',[dict(name='InPaused',type='bool')],[]),('OnDialogueFinished',[dict(name='FinishedSessionID',type='int')],[])]:
    graph(DIALOGUE,name,inputs,outputs)

g=graph(DIALOGUE,'ReadColumn',clear=True)
p=g.set('ColumnValue','',g.entry)
g.fn('names','DataTableFunctionLibrary','GetDataTableRowNames',p);g.wire(g.get('DialogueTable'),'names.Table')
g.fn('find','KismetArrayLibrary','Array_Find');g.wire('names.OutRowNames','find.TargetArray');g.wire(g.get('LineID'),'find.ItemToFind')
g.fn('column','DataTableFunctionLibrary','GetDataTableColumnAsString','names.then');g.wire(g.get('DialogueTable'),'column.DataTable');g.wire(g.entry.rsplit('.',1)[0]+'.Column','column.PropertyName')
g.node('each','Macro',macroName='ForEachLoop');g.wire('column.then','each.Exec');g.wire('column.ReturnValue','each.Array')
same=g.compare('each.Array Index','EqualEqual_IntInt',('find.ReturnValue',))
yes,_=g.branch(same,'each.LoopBody');g.set('ColumnValue',('each.Array Element',),yes)
finish(g,'each.Completed',Value=g.get('ColumnValue'));g.build()

g=graph(DIALOGUE,'StopDialogue',clear=True)
p=g.set('Active','false',g.entry);p=g.set('Finished','false',p);p=g.set('NextLine','None',p)
g.fn('inc','KismetMathLibrary','Add_IntInt',B='1');g.wire(g.get('SessionID'),'inc.A');p=g.set('SessionID',('inc.ReturnValue',),p)
yes,no=valid(g,g.get('Audio'),p)
g.fn('stop','AudioComponent','Stop',yes);g.wire(g.get('Audio'),'stop.self')
g.fn('destroy','ActorComponent','K2_DestroyComponent','stop.then');g.wire(g.get('Audio'),'destroy.self')
join=g.node('join','Sequence');g.wire('destroy.then','join.execute');g.wire(no,'join.execute')
p=g.set('Audio','None','join.then_0');yes,_=valid(g,g.get('Caption'),p)
g.fn('clear','TextBlock','SetText',yes,InText='');g.wire(g.get('Caption'),'clear.self');g.build()

g=graph(DIALOGUE,'PlayLine',clear=True)
p=invoke(g,'StopDialogue',g.entry)
p=g.set('LineID',(g.entry.rsplit('.',1)[0]+'.InLineID',),p)
p=g.set('Finished','false',p)
for name in ['Speaker','Subtitle','SoundExport']:
    p=column(g,'Sound' if name=='SoundExport' else name,p,name)
p,value=column(g,'FallbackSeconds',p)
g.fn('seconds','KismetStringLibrary','Conv_StringToDouble');g.wire(value,'seconds.InString')
g.fn('minimum','KismetMathLibrary','FMax',B='.25');g.wire('seconds.ReturnValue','minimum.A');p=g.set('FallbackSeconds',('minimum.ReturnValue',),p)
p,value=column(g,'NextLine',p);g.fn('nextName','KismetStringLibrary','Conv_StringToName');g.wire(value,'nextName.InString');p=g.set('NextLine',('nextName.ReturnValue',),p)
p,value=column(g,'Spatial',p);g.fn('isSpatial','KismetStringLibrary','EqualEqual_StrStr',B='True');g.wire(value,'isSpatial.A');p=g.set('Spatial',('isSpatial.ReturnValue',),p)
p=g.set('Active','true',p)
g.fn('expiry','KismetMathLibrary','Add_DoubleDouble');g.wire(clock(g),'expiry.A');g.wire(g.get('FallbackSeconds'),'expiry.B');p=g.set('Deadline',('expiry.ReturnValue',),p)
yes,no=valid(g,g.get('Caption'),p)
g.fn('label','KismetStringLibrary','Concat_StrStr',B='\n');g.wire(g.get('Speaker'),'label.A')
g.fn('captionText','KismetStringLibrary','Concat_StrStr');g.wire('label.ReturnValue','captionText.A');g.wire(g.get('Subtitle'),'captionText.B')
g.fn('text','KismetTextLibrary','Conv_StringToText');g.wire('captionText.ReturnValue','text.InString')
g.fn('show','TextBlock','SetText',yes);g.wire(g.get('Caption'),'show.self');g.wire('text.ReturnValue','show.InText')
g.node('join','Sequence');g.wire('show.then','join.execute');g.wire(no,'join.execute')
# Object references export as SoundWave'/Game/..Asset.Asset'. Empty references
# keep the subtitle fallback. Resolve only the quoted object path, then cast.
g.fn('splitType','KismetStringLibrary','Split',InStr="'");g.wire(g.get('SoundExport'),'splitType.SourceString')
g.fn('splitPath','KismetStringLibrary','Split',InStr="'");g.wire('splitType.RightS','splitPath.SourceString')
has,_=g.branch('splitType.ReturnValue','join.then_0')
g.fn('softPath','KismetSystemLibrary','MakeSoftObjectPath');g.wire('splitPath.LeftS','softPath.PathString')
g.fn('soft','KismetSystemLibrary','Conv_SoftObjPathToSoftObjRef');g.wire('softPath.ReturnValue','soft.SoftObjectPath')
g.fn('load','KismetSystemLibrary','LoadAsset_Blocking',has);g.wire('soft.ReturnValue','load.Asset')
g.node('sound','Cast',targetClass='SoundBase');g.wire('load.then','sound.execute');g.wire('load.ReturnValue','sound.Object')
p=g.set('SpeakerActor',(g.get('Maya'),),'sound.then')
g.fn('isCrewA','KismetStringLibrary','EqualEqual_StrStr',B='CREW A');g.wire(g.get('Speaker'),'isCrewA.A')
yes,no=g.branch('isCrewA.ReturnValue',p);yes=g.set('SpeakerActor',(g.get('CrewA'),),yes)
g.node('actorJoin','Sequence');g.wire(yes,'actorJoin.execute');g.wire(no,'actorJoin.execute')
g.fn('isCrewB','KismetStringLibrary','EqualEqual_StrStr',B='CREW B');g.wire(g.get('Speaker'),'isCrewB.A')
yes,no=g.branch('isCrewB.ReturnValue','actorJoin.then_0');yes=g.set('SpeakerActor',(g.get('CrewB'),),yes)
g.node('actorJoinB','Sequence');g.wire(yes,'actorJoinB.execute');g.wire(no,'actorJoinB.execute')
spatial,flat=g.branch(g.get('Spatial'),'actorJoinB.then_0');spatial,missing=valid(g,g.get('SpeakerActor'),spatial)
g.fn('root','Actor','K2_GetRootComponent');g.wire(g.get('SpeakerActor'),'root.self')
g.fn('attached','GameplayStatics','SpawnSoundAttached',spatial,bAutoDestroy='false',bStopWhenAttachedToDestroyed='true',Location='(X=0,Y=0,Z=150)');g.wire('sound.AsSound Base','attached.Sound');g.wire('root.ReturnValue','attached.AttachToComponent');g.wire(g.get('Volume'),'attached.VolumeMultiplier');g.wire(g.get('Attenuation'),'attached.AttenuationSettings')
attached=g.set('Audio',('attached.ReturnValue',),'attached.then')
g.fn('flat','GameplayStatics','CreateSound2D',flat,bAutoDestroy='false');g.wire(missing,'flat.execute');g.wire('sound.AsSound Base','flat.Sound');g.wire(g.get('Volume'),'flat.VolumeMultiplier')
p=g.set('Audio',('flat.ReturnValue',),'flat.then');g.fn('play','AudioComponent','Play',p,StartTime='0');g.wire(g.get('Audio'),'play.self')
g.build()

g=graph(DIALOGUE,'PollDialogue',clear=True)
yes,_=g.branch(g.get('Active'),g.entry);_,yes=g.branch(g.get('Paused'),yes)
audio,no=valid(g,g.get('Audio'),yes)
g.fn('playing','AudioComponent','IsPlaying');g.wire(g.get('Audio'),'playing.self');_,done=g.branch('playing.ReturnValue',audio)
invoke(g,'FinishLine',done);invoke(g,'FinishLine',expired(g,no));g.build()

g=graph(DIALOGUE,'FinishLine',clear=True)
active,_=g.branch(g.get('Active'),g.entry)
g.fn('hasNext','KismetMathLibrary','NotEqual_NameName',B='None');g.wire(g.get('NextLine'),'hasNext.A')
nextline,done=g.branch('hasNext.ReturnValue',active)
# Capture the next ID before StopDialogue clears it inside PlayLine.
nextline=g.set('LineID',(g.get('NextLine'),),nextline)
ref=g.fn('next','BP_Scene01DialoguePlayer_C','PlayLine',nextline);g.wire(g.get('LineID'),'next.InLineID')
p=g.set('Active','false',done);p=g.set('Finished','true',p);p=g.set('CompletedSessionID',(g.get('SessionID'),),p)
yes,no=valid(g,g.get('Caption'),p);g.fn('clear','TextBlock','SetText',yes,InText='');g.wire(g.get('Caption'),'clear.self')
g.node('join','Sequence');g.wire('clear.then','join.execute');g.wire(no,'join.execute')
ref=g.fn('notify',cls(DIALOGUE),'OnDialogueFinished','join.then_0');g.wire(g.get('CompletedSessionID'),'notify.FinishedSessionID');g.build()

g=graph(DIALOGUE,'SetDialoguePaused',clear=True)
p=g.set('Paused',(g.entry.rsplit('.',1)[0]+'.InPaused',),g.entry);yes,_=valid(g,g.get('Audio'),p)
g.fn('pause','AudioComponent','SetPaused',yes);g.wire(g.get('Audio'),'pause.self');g.wire(g.get('Paused'),'pause.bPause');g.build()
clear_events(DIALOGUE);g=Graph(DIALOGUE,'EventGraph');g.node('tick','Event',eventName='ReceiveTick');invoke(g,'PollDialogue','tick.then');g.node('end','Event',eventName='ReceiveEndPlay');invoke(g,'StopDialogue','end.then');g.build()
for name in ['ReadColumn','PlayLine','StopDialogue','PollDialogue','FinishLine']:comment(DIALOGUE,name,'Scene 01 VO: synchronous row lookup, cancellable audio polling; no latent dialogue callbacks. Audio completion drives lines; missing VO uses fallback. No runtime tests executed.')
compile_save(DIALOGUE)
