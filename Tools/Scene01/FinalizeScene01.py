"""Final editor authoring adjustments and static reference inventory only."""
import unreal,json
P=unreal.Paths.project_dir();E=unreal.EditorAssetLibrary;S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name()=='/Game/Game/Levels/Tests/L_Scene01.L_Scene01'
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
labels={a.get_actor_label():a for a in S.get_all_level_actors()};flow=labels['SYSTEM_Scene01Flow'];dialogue=labels['SYSTEM_Scene01Dialogue']
for label in ['PROP_House_Living_Table_Side_01','PROP_House_Living_Lamp_Desk_02']:
 if label in labels:S.destroy_actor(labels[label])
labels['MARK_Scene01_MayaStart'].set_actor_location(unreal.Vector(-400,-440,0),False,False)
for label,loc in [('MARK_Scene01_Director',(180,300,0)),('SET_Scene01_DirectorMark',(180,300,1)),('SET_Scene01_DirectorMarkLabel',(150,325,3))]:labels[label].set_actor_location(unreal.Vector(*loc),False,False)
bp=unreal.load_asset('/Game/Game/Blueprints/Scene01/BP_Scene01FlowDirector')
unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'FailureMark',True);unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
labels={a.get_actor_label():a for a in S.get_all_level_actors()};flow=labels['SYSTEM_Scene01Flow']
failure=next((a for a in S.get_all_level_actors() if a.get_actor_label()=='MARK_Scene01_FailureMark'),None)
if not failure:
 failure=S.spawn_actor_from_class(unreal.TargetPoint,unreal.Vector(-400,-385,0));failure.set_actor_label('MARK_Scene01_FailureMark');failure.set_folder_path('Scene01/Markers');failure.set_actor_rotation(unreal.Rotator(pitch=0,yaw=90,roll=0),False)
flow.set_editor_property('FailureMark',failure)
root='/Game/Game/Audio/Scene01';path=root+'/SA_Scene01Dialogue'
attenuation=unreal.load_asset(path) if E.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset('SA_Scene01Dialogue',root,unreal.SoundAttenuation,unreal.SoundAttenuationFactory())
assert attenuation
settings=attenuation.get_editor_property('attenuation')
settings.set_editor_property('attenuate',True);settings.set_editor_property('spatialize',True)
settings.set_editor_property('attenuation_shape',unreal.AttenuationShape.SPHERE)
settings.set_editor_property('attenuation_shape_extents',unreal.Vector(600,0,0));settings.set_editor_property('falloff_distance',1800.)
attenuation.set_editor_property('attenuation',settings);E.save_loaded_asset(attenuation)
bp=unreal.load_asset('/Game/Game/Blueprints/Scene01/BP_Scene01DialoguePlayer')
unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'Attenuation',True);unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
dialogue=next(a for a in S.get_all_level_actors() if a.get_actor_label()=='SYSTEM_Scene01Dialogue');dialogue.set_editor_property('Attenuation',attenuation)
# P must continue to receive input while globally paused. Compilation/reinstancing
# preserves these editor flags, explicitly set again after final graph changes.
for i in range(150):
 node=unreal.find_object(None,'/Game/Game/Blueprints/Scene01/BP_Scene01FlowDirector.BP_Scene01FlowDirector:EventGraph.K2Node_InputKey_'+str(i))
 if node:
  key=str(node.get_editor_property('InputKey').get_editor_property('KeyName'));node.set_editor_property('bConsumeInput',False);node.set_editor_property('bExecuteWhenPaused',key=='P')
E.save_asset('/Game/Game/Blueprints/Scene01/BP_Scene01FlowDirector',False)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

actors=S.get_all_level_actors();labels={a.get_actor_label():a for a in actors};flow=labels['SYSTEM_Scene01Flow']
refs={name:flow.get_editor_property(name).get_path_name() if flow.get_editor_property(name) else None for name in ['Arrival','Dialogue','Maya','CrewA','CrewB','OpeningStandIn','Sofa','Wardrobe','SofaArea','WardrobeArea','DirectorMark','MayaStart','FailureMark','WalkMark','AisleMark','InspectMark','WideCamera','MediumCamera','DetailCamera']}
table=unreal.load_asset('/Game/Game/Audio/Scene01/DT_Scene01Dialogue')
json.dump({'map':world.get_path_name(),'references':refs,'game_mode':world.get_world_settings().get_editor_property('default_game_mode').get_path_name(),'row_names':[str(n) for n in unreal.DataTableFunctionLibrary.get_data_table_row_names(table)],'speaker_column':list(unreal.DataTableFunctionLibrary.get_data_table_column_as_string(table,'Speaker')),'sound_column':list(unreal.DataTableFunctionLibrary.get_data_table_column_as_string(table,'Sound')),'actors':len(actors),'tests_run':False,'pie_run':False,'packaging_run':False},open(P+'Saved/Scene01Build/static_inventory.json','w'),indent=2)
unreal.log('SCENE01_FINALIZED_NO_TESTS')
