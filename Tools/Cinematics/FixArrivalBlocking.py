import unreal,json
P=unreal.Paths.project_dir();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary
actors={a.get_actor_label():a for a in S.get_all_level_actors()};bp=unreal.load_asset('/Game/Game/Blueprints/Flow/BP_ArrivalDirector')
for name in ['Scene1Sofa','Scene1Wardrobe']:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
a=actors['FLOW_Arrival_Tutorial_LivingRoom'];maya=actors['SET_Scene01_Maya_StandIn'];maya.set_actor_location(unreal.Vector(-190,-260,0),False,False)
for name,loc,yaw in [('NPC_Intro_CrewA_PropMaster',(130,-470,0),-90),('NPC_Intro_CrewB_SetDresser',(-225,-210,0),90),('NPC_Intro_CrewC_Lobby',(-1290,1270,0),-90)]:
 x=actors[name];x.set_actor_location(unreal.Vector(*loc),False,False);x.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
old=actors.get('PROP_Intro_CarriedCase')
if old:S.destroy_actor(old)
sofa=actors['PROP_House_Living_Sofa_ThreeSeat_01'];sofa.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE);sofa.set_actor_location(unreal.Vector(-350,-147,0),False,False)
sofa.attach_to_actor(actors['NPC_Intro_CrewB_SetDresser'],'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
wardrobe=actors.get('PROP_Scene01_Wardrobe') or S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(220,-470,0));wardrobe.set_actor_location(unreal.Vector(220,-470,0),False,False);wardrobe.set_actor_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0),False);wardrobe.set_actor_label('PROP_Scene01_Wardrobe');wardrobe.set_folder_path('Gameplay/Scene01/Props');c=wardrobe.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Game/Game/Art/Environment/House/Meshes/Props/SM_House_Cabinet_Tall'));c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_profile_name('BlockAll');wardrobe.attach_to_actor(actors['NPC_Intro_CrewA_PropMaster'],'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
a.set_editor_property('Scene1Sofa',sofa);a.set_editor_property('Scene1Wardrobe',wardrobe);a.set_editor_property('CrewCase',None)
E.save_loaded_asset(bp);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
