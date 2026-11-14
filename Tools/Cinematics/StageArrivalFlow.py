import unreal,json,os
P=unreal.Paths.project_dir();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary
path='/Game/Game/Blueprints/Flow/BP_ArrivalDirector';bp=unreal.load_asset(path)
for n in ['OpeningDirector','DoorHinge','Maya','CrewA','CrewB','CrewCase']:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,n,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
for a in list(S.get_all_level_actors()):
 if a.get_actor_label().startswith(('FLOW_Arrival','NPC_Intro_','PROP_Intro_','DOOR_Entrance_')):S.destroy_actor(a)
actors=S.get_all_level_actors();opening=next(a for a in actors if a.get_actor_label()=='FLOW_Opening_ToScene01');maya=next(a for a in actors if a.get_actor_label()=='SET_Scene01_Maya_StandIn');maya.set_actor_location(unreal.Vector(-340,-170,0),False,False);maya.set_actor_hidden_in_game(True)
idle=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle');manny=unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple');cube=unreal.load_asset('/Engine/BasicShapes/Cube')
def npc(label,loc,yaw):
 a=S.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(*loc));a.set_actor_label(label);a.set_folder_path('Gameplay/Arrival/Characters');a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False);c=a.skeletal_mesh_component;c.set_skeletal_mesh_asset(manny);c.set_collision_profile_name('NoCollision');c.override_animation_data(idle,is_looping=True,is_playing=True);return a
crewA=npc('NPC_Intro_CrewA_PropMaster',(-420,190,0),-90);crewB=npc('NPC_Intro_CrewB_SetDresser',(330,140,0),180);crewC=npc('NPC_Intro_CrewC_Lobby',(-1390,1220,0),-90)
def mesh(label,loc,scale,material=None):
 a=S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label(label);a.set_folder_path('Gameplay/Arrival/Props');a.set_actor_scale3d(unreal.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(cube);c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_profile_name('NoCollision')
 if material:c.set_material(0,material)
 return a
# A proper hinge root; the leaf is offset from its pivot and swings into the lobby.
hinge=S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-1143,1580,0));hinge.set_actor_label('DOOR_Entrance_Hinge');hinge.set_folder_path('Gameplay/Arrival/Door');hinge.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE);hinge.static_mesh_component.set_collision_profile_name('NoCollision')
wood=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Remaster/MI_House_Timber_AgedIvory')
leaf=mesh('DOOR_Entrance_Leaf',(-1045,1580,117),(1.96,.08,2.34),wood);leaf.static_mesh_component.set_collision_profile_name('BlockAll');leaf.attach_to_actor(hinge,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
# Reuse the existing optimized equipment-case mesh, carried by the crew stand-in.
case=mesh('PROP_Intro_CarriedCase',(330,170,80),(.7,.7,.7));assets=E.list_assets('/Game/Game/Art/Environment/House/Meshes/Props',recursive=True,include_folder=False);casepath=next(p for p in assets if 'FlightCase_Black' in p);case.static_mesh_component.set_static_mesh(unreal.load_asset(casepath));case.attach_to_actor(crewB,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
paper=mesh('PROP_Intro_Maya_Script',(0,0,0),(.23,.035,.31));paper.static_mesh_component.set_material(0,unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Paper'));paper.attach_to_component(maya.skeletal_mesh_component,'hand_r',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False);paper.set_actor_relative_location(unreal.Vector(5,0,0),False,False)
for i in range(4):
 line=mesh('PROP_Intro_ScriptLine_'+str(i),(0,0,0),(.13,.004,.006),wood);line.attach_to_actor(paper,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False);line.set_actor_relative_location(unreal.Vector(0,-.52,-.27+i*.15),False,False)
# Player begins on the garden walk, outside the closed entrance.
starts=[a for a in S.get_all_level_actors() if isinstance(a,unreal.PlayerStart)]
if not starts:starts=[S.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(-1045,2280,100))]
for a in starts:a.set_actor_location(unreal.Vector(-1045,2280,100),False,False);a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0),False);a.set_actor_label('START_Director_Arrival')
a=S.spawn_actor_from_class(bp.generated_class(),unreal.Vector(0,0,0));a.set_actor_label('FLOW_Arrival_Tutorial_LivingRoom');a.set_folder_path('Gameplay/Flow')
for n,v in [('OpeningDirector',opening),('DoorHinge',hinge),('Maya',maya),('CrewA',crewA),('CrewB',crewB),('CrewCase',case)]:a.set_editor_property(n,v)
for p in [path,'/Game/Game/Blueprints/Cinematics/BP_OpeningDirector','/Game/Game/UI/Scene01/WBP_Scene01Objective']:E.save_asset(p,False)
saved=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();json.dump({'saved':saved,'exterior_actors':sum(x.get_actor_label().startswith('EXT_House_') for x in S.get_all_level_actors()),'crew_count':3,'start':[-1045,2280,100]},open(P+'Saved/ArrivalStageReport.json','w'),indent=2)

# Current arrival blocking replaces the original case prototype.
exec(open(P+'Tools/Cinematics/FixArrivalBlocking.py').read())
