"""Replace snap guides with radius solution areas in L_GameplaySystems only."""
import unreal

ROOT='/Game/Game/Blueprints/Gameplay/Testing/'
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert editor.get_game_world() is None
assert editor.get_editor_world().get_path_name()=='/Game/Game/Levels/Tests/L_GameplaySystems.L_GameplaySystems'
subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=subsystem.get_all_level_actors()
labels={a.get_actor_label():a for a in actors}
manager=labels['SYSTEM_GameplayTestManager']
manager_blueprint=unreal.load_asset(ROOT+'BP_GameplayTestManager')
area_blueprint=unreal.load_asset(ROOT+'BP_PlacementArea')
for scene in range(1,4):
    for index in [1,2]:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(manager_blueprint,f'S{scene}Area{index}',True)
for name in ['AllowedProp','Radius','PreviewMesh']:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(area_blueprint,name,True)
for blueprint in [manager_blueprint,area_blueprint]:
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_asset(blueprint.get_path_name())
# Reinstance-safe actor lookup after compilation.
actors=subsystem.get_all_level_actors()
labels={a.get_actor_label():a for a in actors}
manager=labels['SYSTEM_GameplayTestManager']
for actor in actors:
    label=actor.get_actor_label()
    if actor.get_class().get_name()=='BP_PropSlot_C' or '_Slot_' in label or label.endswith('_Target'):
        actor.set_actor_enable_collision(False)
        actor.set_actor_hidden_in_game(True)
        actor.set_folder_path('LegacySnapGuides/Disabled')

material_path='/Game/Game/Materials/GameplayTesting/M_PlacementArea'
if unreal.EditorAssetLibrary.does_asset_exist(material_path):
    material=unreal.load_asset(material_path)
else:
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PlacementArea','/Game/Game/Materials/GameplayTesting',unreal.Material,unreal.MaterialFactoryNew())
    color=unreal.MaterialEditingLibrary.create_material_expression(material,unreal.MaterialExpressionConstant3Vector,-300,0)
    color.set_editor_property('constant',unreal.LinearColor(.015,.2,.45,1))
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material_path)

for scene,names in [(1,['Sofa','Wardrobe']),(2,['Cabinet','Lamp']),(3,['Chair','Lamp'])]:
    for index,name in enumerate(names,1):
        slot='B' if index==1 else 'C'
        old=labels[f'S{scene:02d}_{name}_Slot_{slot}'].get_actor_location()
        center=unreal.Vector(old.x,old.y,0)
        area=subsystem.spawn_actor_from_class(area_blueprint.generated_class(),center)
        area.set_actor_label(f'S{scene:02d}_{name}_SolutionArea')
        area.set_folder_path(f'Scene{scene:02d}/SolutionAreas')
        area.get_editor_property('root_component').set_mobility(unreal.ComponentMobility.MOVABLE)
        area.set_editor_property('AllowedProp',manager.get_editor_property(f'S{scene}Prop{index}'))
        manager.get_editor_property(f'S{scene}Prop{index}').set_editor_property('CurrentSlotID',unreal.Name('None'))
        area.set_editor_property('Radius',125.0)
        manager.set_editor_property(f'S{scene}Area{index}',area)
        pad=subsystem.spawn_actor_from_class(unreal.StaticMeshActor,center+unreal.Vector(0,0,.2))
        pad.set_actor_label(f'S{scene:02d}_{name}_AreaPreview')
        pad.set_folder_path(f'Scene{scene:02d}/SolutionAreas')
        pad.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
        pad.static_mesh_component.set_material(0,material)
        pad.static_mesh_component.set_collision_profile_name('NoCollision')
        pad.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        pad.set_actor_scale3d(unreal.Vector(2.5,2.5,.004))
        pad.attach_to_actor(area,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
        area.set_editor_property('PreviewMesh',pad.static_mesh_component)
        label=subsystem.spawn_actor_from_class(unreal.TextRenderActor,center+unreal.Vector(80,-125,75))
        label.set_actor_label(f'S{scene:02d}_{name}_AreaLabel')
        label.set_folder_path(f'Scene{scene:02d}/SolutionAreas')
        label.set_actor_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False)
        label.text_render.set_text(name.upper()+' TARGET AREA')
        label.text_render.set_world_size(18)
        label.text_render.set_text_render_color(unreal.Color(170,220,255,255))
        label.text_render.set_mobility(unreal.ComponentMobility.MOVABLE)
        label.attach_to_actor(area,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)

labels['TEST_Instructions'].text_render.set_text('FREE PLACEMENT LAB\nE place freely | Blue areas are puzzle solutions\nF ACTION at director mark | F6 manual functional tests')
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('FREE_PLACEMENT_AREAS_STAGED - no tests executed')
