"""Stage the hidden-room reconstruction puzzle in the existing graybox map."""
import sys
import unreal
sys.path.append(unreal.Paths.project_dir() + 'Tools/Cinematics')
import take_staging as ts

F='Gameplay/Scene03/L03'; Q='/Game/Game/Cinematics/L03'
maya=ts.take_maya();assert maya
for label in ['PROP_House_HiddenRoom_Chair_Dining_12','PROP_House_HiddenRoom_Chair_Dining_13']:
 a=ts.by_label(label)
 if a:a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)

start=ts.spawn(F,unreal.TargetPoint,'L03_MayaStart',(970,1060,0),yaw=0)
chair=ts.prop(F,'L03_Prop_WoodenChair','WoodenChair','L03','SM_House_Chair_Dining',(1430,750,0),0)
lamp=ts.prop(F,'L03_Prop_StandingLamp','StandingLamp','L03','SM_House_Lamp_Floor',(1490,1300,0),0,
             cls_path='/Game/Game/Blueprints/Props/BP_StandingLampProp')
ts.area(F,'L03_Area_ChairReference','L03_ChairReference',(1270,900,0),95)
ts.area(F,'L03_Area_LampReference','L03_LampReference',(1430,1110,0),95)
mark=ts.director_mark(F,'L03_DirectorMark',(1050,1290))
label=ts.spawn(F,unreal.TextRenderActor,'L03_DirectorMarkLabel',(1050,1290,3),pitch=90)
label.text_render.set_text("DIRECTOR'S MARK")
label.text_render.set_editor_property('world_size',19.)
label.text_render.set_text_render_color(unreal.Color(r=255,g=190,b=55,a=255))
label.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

photo=ts.spawn(F,unreal.TextRenderActor,'L03_ReferencePhoto',(1210,1000,103),pitch=90)
photo.text_render.set_text('EVELYN  /  ORIGINAL SET\nCHAIR LEFT   +   LAMP RIGHT')
photo.text_render.set_editor_property('world_size',12.)
photo.text_render.set_text_render_color(unreal.Color(r=45,g=30,b=20,a=255))
photo.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
paper=ts.spawn(F,unreal.StaticMeshActor,'L03_ReferencePaper',(1210,1000,98))
paper.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
paper.static_mesh_component.set_material(0,unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Paper'))
paper.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
paper.set_actor_scale3d(unreal.Vector(1.8,1.2,.015))

wide=ts.camera(F,'CINE_L03_Wide',(1490,665,175),yaw=145,pitch=-8)
detail=ts.camera(F,'CINE_L03_Reference',(1350,810,160),yaw=135,pitch=-25,focal=45)
reaction=ts.camera(F,'CINE_L03_Reaction',(1390,1000,165),yaw=180,pitch=-7,focal=45)
def make(name,frames,keys,animations,cuts):
 seq=ts.sequence(Q,name,frames);ts.maya_track(seq,maya,frames,keys,animations)
 ts.camera_cuts(seq,[(a,b,c) for a,b,c in cuts]);ts.save(seq)

make('LS_L03_Opening',150,[(0,(970,1060,0)),(150,(1080,1030,0))],
     [(0,55,'look'),(55,150,'walk')],[(0,150,wide)])
make('LS_L03_ChairWrong',270,[(0,(1080,1030,0)),(180,(1190,1010,0)),(270,(1190,1010,20))],
     [(0,180,'walk'),(180,270,'hesitate')],[(0,150,wide),(150,270,detail)])
make('LS_L03_LampWrong',270,[(0,(1080,1030,0)),(180,(1190,1010,0)),(270,(1190,1010,20))],
     [(0,180,'walk'),(180,270,'inspect')],[(0,150,wide),(150,270,detail)])
make('LS_L03_Perfect',450,[(0,(1080,1030,0)),(180,(1190,1010,0)),(450,(1190,1010,20))],
     [(0,180,'walk'),(180,320,'inspect'),(320,450,'surprised')],
     [(0,180,wide),(180,320,detail),(320,450,reaction)])
ts.save_level()
print('L03_STAGED',start.get_path_name(),mark.get_path_name())
