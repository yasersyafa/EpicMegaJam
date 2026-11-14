from Scene01Editor import *

# Route interactions from the existing Enhanced Input events through the phase
# owner, so E cannot both open a tutorial door and pick up a prop.
for title,fn in [('EnhancedInputAction IA_Interact','HandleInteract'),('EnhancedInputAction IA_Notes','HandleNotes')]:
    s=call('read_blueprint_graph_summary',path=PLAYER,graphName='EventGraph')
    event=next(n for n in s['nodes'] if n['title']==title)
    g=Graph(PLAYER,'EventGraph')
    g.fn('flow','GameplayStatics','GetActorOfClass',event['id']+'.Started',ActorClass=obj(FLOW)+'_C')
    g.node('castFlow','Cast',targetClass=cls(FLOW));g.wire('flow.then','castFlow.execute');g.wire('flow.ReturnValue','castFlow.Object')
    invoke(g,fn,'castFlow.then','castFlow.AsBP Scene 01Flow Director',cls(FLOW));g.build()
compile_save(PLAYER)

clear_events(HUD)
g=Graph(HUD,'EventGraph');g.node('draw','Event',eventName='ReceiveDrawHUD')
g.fn('find','GameplayStatics','GetActorOfClass','draw.then',ActorClass=obj(FLOW)+'_C')
g.node('cast','Cast',targetClass=cls(FLOW));g.wire('find.then','cast.execute');g.wire('find.ReturnValue','cast.Object');flow='cast.AsBP Scene 01Flow Director'
def flowvar(n):return g.get(n,owner=cls(FLOW),target=flow)
g.fn('cx','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeX','cx.A')
g.fn('cy','KismetMathLibrary','Multiply_DoubleDouble',B='.5');g.wire('draw.SizeY','cy.A')
g.node('sections','Sequence');g.wire('cast.then','sections.execute')
title,no=g.branch(flowvar('ShowTitle'),'sections.then_0')
g.fn('titleX','KismetMathLibrary','Subtract_DoubleDouble',B='180');g.wire('cx.ReturnValue','titleX.A')
g.fn('title','HUD','DrawText',title,Text='CUT! CUT! CUT!',Scale='3',TextColor='(R=1,G=1,B=1,A=1)');g.wire('titleX.ReturnValue','title.ScreenX');g.wire('cy.ReturnValue','title.ScreenY')
paused,unp=g.branch(flowvar('Paused'),no);g.fn('paused','HUD','DrawText',paused,Text='PAUSED - P to resume',ScreenX='32',ScreenY='40',Scale='1.2',TextColor='(R=1,G=1,B=1,A=1)')
setup,other=g.branch(g.compare(flowvar('Phase'),'EqualEqual_IntInt',2),'sections.then_1')
g.fn('cross','HUD','DrawText',setup,Text='+',Scale='1.2',TextColor='(R=1,G=1,B=1,A=1)');g.wire('cx.ReturnValue','cross.ScreenX');g.wire('cy.ReturnValue','cross.ScreenY')
g.node('setupSections','Sequence');g.wire('cross.then','setupSections.execute')
player=flowvar('Player');p,_=valid(g,player,'setupSections.then_0');held=g.get('HeldProp',owner=cls(PLAYER),target=player)
holding,empty=valid(g,held,p);place,invalid=g.branch(g.get('CanPlaceFreely',owner=cls(PLAYER),target=player),holding)
pickup,_=valid(g,g.get('FocusProp',owner=cls(PLAYER),target=player),empty)
g.fn('promptX','KismetMathLibrary','Subtract_DoubleDouble',B='150');g.wire('cx.ReturnValue','promptX.A');g.fn('promptY','KismetMathLibrary','Multiply_DoubleDouble',B='.62');g.wire('draw.SizeY','promptY.A')
for ref,text,p in [('place','[E] PLACE   [RMB] CANCEL',place),('invalid','BLOCKED / NO FLAT SURFACE   [RMB] CANCEL',invalid),('pick','[E] PICK UP',pickup)]:
    g.fn(ref,'HUD','DrawText',p,Text=text,Scale='1.1',TextColor='(R=1,G=.85,B=.4,A=1)');g.wire('promptX.ReturnValue',ref+'.ScreenX');g.wire('promptY.ReturnValue',ref+'.ScreenY')
# A small contextual action hint replaces the test arena's debug dashboard.
g.fn('status','HUD','DrawText','setupSections.then_1',ScreenX='32',ScreenY='40',Scale='1',TextColor='(R=1,G=1,B=1,A=1)');g.wire(flowvar('StatusText'),'status.Text')
ready,far=g.branch(flowvar('AtDirectorMark'),'status.then')
g.fn('ready','HUD','DrawText',ready,Text='[F] ACTION   [Tab] Notes',ScreenX='32',ScreenY='65',Scale='1.1',TextColor='(R=1,G=.85,B=.4,A=1)')
taking,_=g.branch(g.compare(flowvar('Phase'),'EqualEqual_IntInt',3),other)
g.fn('cut','HUD','DrawText',taking,Text='[F] CUT',ScreenX='32',ScreenY='40',Scale='1.1',TextColor='(R=1,G=1,B=1,A=1)')
g.build();compile_save(HUD)
for prop,value in [('DefaultPawnClass',obj(PLAYER)+'_C'),('HUDClass',obj(HUD)+'_C'),('PlayerControllerClass',obj(CONTROLLER)+'_C')]:call('set_class_default',path=MODE,property=prop,value=value)
compile_save(MODE)
print(call('list_components',path='/Game/Game/Blueprints/Props/BP_InteractableProp'))
print(call('list_variables',path='/Game/Game/Blueprints/Props/BP_InteractableProp'))
