import unreal
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert editor.get_game_world() is None
assert editor.get_editor_world().get_name()=='L_GameplaySystems'
tools=unreal.AssetToolsHelpers.get_asset_tools()
library=unreal.MaterialEditingLibrary


def material(name,color):
    path='/Game/Game/Materials/GameplayTesting/'+name
    result=unreal.load_asset(path)
    if not result:
        result=tools.create_asset(name,'/Game/Game/Materials/GameplayTesting',unreal.Material,unreal.MaterialFactoryNew())
        node=library.create_material_expression(result,unreal.MaterialExpressionConstant3Vector,-300,0)
        node.set_editor_property('constant',unreal.LinearColor(*color,1))
        library.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
        rough=library.create_material_expression(result,unreal.MaterialExpressionConstant,-300,200)
        rough.set_editor_property('r',.85)
        library.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
        library.recompile_material(result)
        unreal.EditorAssetLibrary.save_asset(path)
    return result


floor=material('M_TestFloor',(.08,.11,.14))
prop=material('M_TestProp',(.38,.28,.17))
pad=material('M_TestPad',(.18,.23,.28))
marker=material('M_TestSlotTarget',(.02,.6,.8))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors=actors.get_all_level_actors()
existing={a.get_actor_label() for a in all_actors}
for actor in all_actors:
    name=actor.get_actor_label()
    mesh=actor.get_component_by_class(unreal.StaticMeshComponent)
    if name=='TEST_Floor':mesh.set_material(0,floor)
    if name.endswith('_Pad'):mesh.set_material(0,pad)
    if actor.get_class().get_name()=='BP_InteractableProp_C':mesh.set_material(0,prop)
    if isinstance(actor,unreal.TextRenderActor):actor.text_render.set_text_render_color(unreal.Color(235,245,255,255))
    if actor.get_class().get_name()=='BP_PropSlot_C' and name+'_Target' not in existing:
        target=actors.spawn_actor_from_class(unreal.StaticMeshActor,actor.get_actor_location())
        target.set_actor_label(name+'_Target')
        target.set_folder_path('SlotTargets')
        target.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere'))
        target.set_actor_scale3d(unreal.Vector(.18,.18,.18))
        target.static_mesh_component.set_material(0,marker)
        target.static_mesh_component.set_collision_profile_name('NoCollision')
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.log('GAMEPLAY_SLOT_TARGETS_VISIBLE')
