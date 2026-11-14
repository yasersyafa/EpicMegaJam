import unreal,os,json
P=unreal.Paths.project_dir();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary
bp=unreal.load_asset('/Game/Game/Blueprints/Cinematics/BP_OpeningDirector')
for name in ('OpeningSequence','OpeningStandIn','Scene1StandIn'):unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
S.clear_actor_selection_set()
for a in list(S.get_all_level_actors()):
 if a.get_actor_label().startswith(('FLOW_Opening','SET_Scene01_Maya_')):S.destroy_actor(a)
actors=S.get_all_level_actors();opening=next(a for a in actors if a.get_actor_label()=='CINE_Opening_Maya_StandIn')
# Separate previs stand-in in the playable set; the opening performance remains bound to its original actor.
may=S.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(-385,-170,0));may.set_actor_label('SET_Scene01_Maya_StandIn');may.set_folder_path('Gameplay/Scene01/Characters');may.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False)
c=may.skeletal_mesh_component;c.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'));c.set_collision_profile_name('NoCollision');c.override_animation_data(unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'));may.set_actor_hidden_in_game(True)
bp=unreal.load_asset('/Game/Game/Blueprints/Cinematics/BP_OpeningDirector');cls=bp.generated_class();actor=S.spawn_actor_from_class(cls,unreal.Vector(0,0,0));actor.set_actor_label('FLOW_Opening_ToScene01');actor.set_folder_path('Gameplay/Flow')
for name,value in [('OpeningSequence',unreal.load_asset('/Game/Game/Cinematics/Opening/LS_Opening_Maya')),('OpeningStandIn',opening),('Scene1StandIn',may)]:actor.set_editor_property(name,value)
# Reuse the existing player/game mode and HUD. No Python runs at game startup.
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,'/Game/Game/Blueprints/Player/BP_GrayBoxGameMode.BP_GrayBoxGameMode_C'))
for p in ['/Game/Game/Blueprints/Cinematics/BP_OpeningDirector','/Game/Game/UI/Cinematics/WBP_OpeningOverlay','/Game/Game/UI/Scene01/WBP_Scene01Objective']:E.save_asset(p,only_if_is_dirty=False)
saved=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
with open(os.path.join(P,'Saved/OpeningFlowReport.json'),'w') as f:json.dump({'saved':saved,'director':actor.get_path_name(),'sequence_seconds':30,'temporary_maya':'Quinn mannequin','voice_over':False,'gameplay_runtime':'Blueprint + LevelSequence'},f,indent=2)
unreal.log('OPENING_FLOW_STAGED '+str(saved))
