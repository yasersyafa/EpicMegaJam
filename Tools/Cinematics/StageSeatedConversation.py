import unreal
S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary
bp=unreal.load_asset('/Game/Game/Blueprints/Flow/BP_ArrivalDirector');unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'DirectorSeatCamera',True);unreal.BlueprintEditorLibrary.compile_blueprint(bp)
actors=S.get_all_level_actors();seat=next((a for a in actors if a.get_actor_label()=='CINE_Arrival_Director_Seated'),None)
if not seat:seat=S.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-350,155,125))
seat.set_actor_label('CINE_Arrival_Director_Seated');seat.set_folder_path('Gameplay/Arrival/Cameras');seat.set_actor_location(unreal.Vector(-350,155,125),False,False);seat.set_actor_rotation(unreal.Rotator(pitch=-3,yaw=-25,roll=0),False);seat.camera_component.set_field_of_view(75)
a=next(a for a in actors if a.get_actor_label()=='FLOW_Arrival_Tutorial_LivingRoom');a.set_editor_property('DirectorSeatCamera',seat)
E.save_loaded_asset(bp);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
