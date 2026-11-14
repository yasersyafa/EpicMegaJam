"""Place three native director marks in the isolated gameplay map."""
import unreal

editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert editor.get_game_world() is None
assert editor.get_editor_world().get_path_name()=='/Game/Game/Levels/Tests/L_GameplaySystems.L_GameplaySystems'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets=unreal.EditorAssetLibrary
root='/Game/Game/Blueprints/Gameplay/Testing/'
blueprint=unreal.load_asset(root+'BP_GameplayTestManager')
for name in ['DirectorMarkRadius','DirectorMarkHeightTolerance']+[f'S{s}DirectorMark' for s in range(1,4)]:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(blueprint,name,True)
unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
assets.save_asset(blueprint.get_path_name())
manager=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='SYSTEM_GameplayTestManager')
by_name={a.get_actor_label():a for a in actors.get_all_level_actors()}
material_path='/Game/Game/Materials/GameplayTesting/M_DirectorMark'
if assets.does_asset_exist(material_path):
    material=unreal.load_asset(material_path)
else:
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DirectorMark','/Game/Game/Materials/GameplayTesting',unreal.Material,unreal.MaterialFactoryNew())
    color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,0)
    color.set_editor_property('constant',unreal.LinearColor(.55,.22,.015,1))
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    assets.save_asset(material_path)


def spawn(cls,name,location):
    actor=by_name.get(name)
    if actor is None:
        actor=actors.spawn_actor_from_class(cls,unreal.Vector(*location))
        actor.set_actor_label(name)
        actor.set_folder_path('DirectorMarks')
    return actor


for scene,y in [(1,-1750),(2,0),(3,1750)]:
    mark=spawn(unreal.TargetPoint,f'S{scene:02d}_DirectorMark',(200,y,0))
    mark.get_editor_property('root_component').set_mobility(unreal.ComponentMobility.MOVABLE)
    manager.set_editor_property(f'S{scene}DirectorMark',mark)
    pad=spawn(unreal.StaticMeshActor,f'S{scene:02d}_DirectorMark_Pad',(200,y,1))
    pad.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    pad.set_actor_scale3d(unreal.Vector(2,2,.02))
    pad.static_mesh_component.set_collision_profile_name('NoCollision')
    pad.static_mesh_component.set_material(0,material)
    pad.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    pad.attach_to_actor(mark,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
    label=spawn(unreal.TextRenderActor,f'S{scene:02d}_DirectorMark_Label',(280,y-100,70))
    label.set_actor_location(mark.get_actor_location()+unreal.Vector(80,-100,70),False,False)
    label.set_actor_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False)
    label.text_render.set_text(f'DIRECTOR MARK\nSCENE {scene:02d}')
    label.text_render.set_world_size(18)
    label.text_render.set_text_render_color(unreal.Color(255,235,170,255))
    label.text_render.set_mobility(unreal.ComponentMobility.MOVABLE)
    label.attach_to_actor(mark,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('DIRECTOR_MARKS_STAGED - no PIE or functional tests started')
