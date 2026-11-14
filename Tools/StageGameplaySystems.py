"""Editor-only staging for the standalone gameplay test level."""
import unreal
import json
import os

PATH='/Game/Game/Levels/Tests/L_GameplaySystems'
ROOT='/Game/Game/Blueprints/Gameplay/Testing/'
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets=unreal.EditorAssetLibrary
assert editor.get_game_world() is None
assert editor.get_editor_world().get_path_name()==PATH+'.L_GameplaySystems'
all_actors=actors.get_all_level_actors()
by_name={a.get_actor_label():a for a in all_actors}
assert 'SYSTEM_GameplayTestManager' not in by_name, 'Already staged.'

# Set editable node flags directly on this new asset only. Legacy E must not
# consume the character's Enhanced Input event. P must work while paused.
bp=unreal.load_asset(ROOT+'BP_GameplayTestManager')
input_nodes=[]
for i in range(150):
    node=unreal.find_object(None,ROOT+'BP_GameplayTestManager.BP_GameplayTestManager:EventGraph.K2Node_InputKey_'+str(i))
    if node:
        node.set_editor_property('bConsumeInput',False)
        node.set_editor_property('bExecuteWhenPaused',str(node.get_editor_property('InputKey').get_editor_property('KeyName'))=='P')
        input_nodes.append(node.get_path_name())
assert len(input_nodes)==8, str(input_nodes)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
for name in ['Intercom','SimulatorEnabled','SimulatorSeconds','DirectorMarkRadius','DirectorMarkHeightTolerance']+[f'S{s}DirectorMark' for s in range(1,4)]+[f'S{s}{kind}{p}' for s in range(1,4) for p in range(1,3) for kind in ['Prop','Start','Correct']]:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assets.save_asset(ROOT+'BP_GameplayTestManager')

mode=unreal.load_asset(ROOT+'BP_GameplayTestMode')
editor.get_editor_world().get_world_settings().set_editor_property('default_game_mode',mode.generated_class())

def spawn(cls,label,location,folder):
    actor=actors.spawn_actor_from_class(cls,location)
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    return actor

manager=spawn(bp.generated_class(),'SYSTEM_GameplayTestManager',unreal.Vector(0,0,0),'Systems')
prop_class=unreal.load_class(None,'/Game/Game/Blueprints/Props/BP_InteractableProp.BP_InteractableProp_C')
slot_class=unreal.load_class(None,'/Game/Game/Blueprints/Props/BP_PropSlot.BP_PropSlot_C')
cube=unreal.load_asset('/Engine/BasicShapes/Cube')
records=[]
for scene,props in [(1,['Sofa','Wardrobe']),(2,['Cabinet','Lamp']),(3,['Chair','Lamp'])]:
    for index,name in enumerate(props,1):
        prefix=f'S{scene:02d}_{name}'
        placeholder=by_name[prefix+'_Placeholder']
        location=placeholder.get_actor_location()
        scale=placeholder.get_actor_scale3d()
        actors.destroy_actor(placeholder)
        prop=spawn(prop_class,prefix+'_Interactable',location,f'Scene{scene:02d}/Gameplay')
        prop.set_actor_scale3d(scale)
        mesh=next(c for c in prop.get_components_by_class(unreal.StaticMeshComponent) if c.get_name()=='Mesh')
        mesh.set_static_mesh(cube)
        mesh.set_relative_location(unreal.Vector(0,0,0),False,False)
        mesh.set_collision_profile_name('BlockAllDynamic')
        mesh.set_editor_property('generate_overlap_events',True)
        prop.set_editor_property('PropID',unreal.Name(f'S{scene}_P{index}'))
        prop.set_editor_property('CurrentSlotID',unreal.Name(f'S{scene}_P{index}_A'))
        manager.set_editor_property(f'S{scene}Prop{index}',prop)
        manager.set_editor_property(f'S{scene}Start{index}',by_name[prefix+'_Slot_A'])
        for slot in ['A','B','C']:
            marker=by_name[prefix+'_Slot_'+slot]
            target=spawn(slot_class,prefix+'_Snap_'+slot,marker.get_actor_location(),f'Scene{scene:02d}/Gameplay/Slots')
            target.set_editor_property('SlotID',unreal.Name(f'S{scene}_P{index}_{slot}'))
            target.set_editor_property('AllowedPropID',unreal.Name(f'S{scene}_P{index}'))
            box=target.get_component_by_class(unreal.BoxComponent)
            # Keep slots usable as trace targets while excluding neighbours from occupancy.
            box.set_box_extent(unreal.Vector(12,12,12),True)
            box.set_collision_profile_name('OverlapAllDynamic')
            box.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY,unreal.CollisionResponseType.ECR_BLOCK)
            box.set_editor_property('generate_overlap_events',True)
            records.append({'scene':scene,'prop':name,'slot':slot,'actor':target.get_actor_label()})

anchor=by_name['FINAL_IntercomAnchor']
manager.set_editor_property('Intercom',anchor)
intercom=spawn(unreal.StaticMeshActor,'FINAL_IntercomHousing',anchor.get_actor_location(),'Finale')
intercom.static_mesh_component.set_static_mesh(cube)
intercom.set_actor_scale3d(unreal.Vector(.25,.4,.5))
intercom.static_mesh_component.set_collision_profile_name('BlockAll')

# Bright working view, same requested orientation for every label.
for actor in actors.get_all_level_actors():
    if isinstance(actor,unreal.TextRenderActor):
        actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False)
by_name['TEST_PlayerStart'].set_actor_location(unreal.Vector(300,-1750,110),False,False)
by_name['TEST_PlayerStart'].set_actor_rotation(unreal.Rotator(0,0,0),False)
assert levels.save_current_level()
result={'map':PATH,'slots':records,'input_nodes_configured':len(input_nodes),'saved':True}
with open(os.path.join(unreal.Paths.project_saved_dir(),'GameplaySystemsStaging.json'),'w') as f:json.dump(result,f,indent=2)
unreal.log('GAMEPLAY_SYSTEMS_STAGED '+str(len(records))+' slots')
with open(os.path.join(unreal.Paths.project_dir(),'Tools','StageDirectorMarks.py'),encoding='utf-8-sig') as stage:
    exec(compile(stage.read(),stage.name,'exec'))
