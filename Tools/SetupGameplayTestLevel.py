"""Build a standalone native-actor test map. Never edits Blueprint assets."""
import json
import os
import unreal

PATH = '/Game/Game/Levels/Tests/L_GameplaySystems'
assets = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert editor.get_game_world() is None, 'Stop PIE before building the test map.'
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages(), 'Save your open map first.'
assert not assets.does_asset_exist(PATH), 'Test map already exists. Refusing to overwrite.'
assert levels.new_level(PATH), 'Could not create test map.'
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
count = 0


def spawn(cls, name, location, folder):
    global count
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(*location))
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path(folder)
    count += 1
    return actor


def block(name, location, size, folder, collision=True):
    actor = spawn(unreal.StaticMeshActor, name, location, folder)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(*(v / 100 for v in size)))
    actor.static_mesh_component.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    return actor


def text(name, message, location, folder, size=25):
    actor = spawn(unreal.TextRenderActor, name, location, folder)
    actor.set_actor_rotation(unreal.Rotator(pitch=0, yaw=180, roll=0), False)
    actor.text_render.set_text(message)
    actor.text_render.set_world_size(size)
    actor.text_render.set_text_render_color(unreal.Color(230, 240, 255, 255))
    return actor


world = editor.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', unreal.GameModeBase)
block('TEST_Floor', (900, 0, -20), (2600, 5400, 40), '00_Arena')
for name, pos, size in [
    ('North', (2220, 0, 100), (40, 5400, 240)),
    ('South', (-420, 0, 100), (40, 5400, 240)),
    ('East', (900, 2720, 100), (2600, 40, 240)),
    ('West', (900, -2720, 100), (2600, 40, 240)),
]:
    block('TEST_Boundary_' + name, pos, size, '00_Arena')
start = spawn(unreal.PlayerStart, 'TEST_PlayerStart', (-100, 0, 100), '00_Arena')
start.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
sun = spawn(unreal.DirectionalLight, 'TEST_Sun', (0, 0, 1200), '00_Arena/Lighting')
sun.set_actor_rotation(unreal.Rotator(-55, -35, 0), False)
sun.light_component.set_editor_property('intensity', 4.0)
sky = spawn(unreal.SkyLight, 'TEST_SkyLight', (0, 0, 1000), '00_Arena/Lighting')
sky.light_component.set_editor_property('intensity', 1.0)
text('TEST_Instructions', 'GAMEPLAY SYSTEMS LAB\nNative placeholders. Add your Blueprints here.\nScene 01 left | Scene 02 center | Scene 03 right', (1850, -600, 280), '00_Arena', 35)

scenes = [
    ('01', -1750, 'ARRIVAL', [('Sofa', (220, 100, 80)), ('Wardrobe', (80, 140, 210))]),
    ('02', 0, 'HOLLOW WALL', [('Cabinet', (100, 130, 100)), ('Lamp', (45, 45, 180))]),
    ('03', 1750, 'LAST SCENE', [('Chair', (60, 60, 90)), ('Lamp', (45, 45, 180))]),
]
for number, y, title, props in scenes:
    folder = 'Scene' + number
    text('S' + number + '_Title', 'SCENE ' + number + ' - ' + title, (1600, y - 550, 250), folder, 32)
    spawn(unreal.TargetPoint, 'S' + number + '_PerformerStart', (350, y, 0), folder + '/Markers')
    spawn(unreal.TargetPoint, 'S' + number + '_InspectTarget', (1450, y, 0), folder + '/Markers')
    for index, (prop, dimensions) in enumerate(props):
        row = y - 360 + index * 700
        for slot, x in [('A', 600), ('B', 1100), ('C', 1600)]:
            label = 'S' + number + '_' + prop + '_Slot_' + slot
            block(label + '_Pad', (x, row, 1), (270, 230, 2), folder + '/SlotGuides', False)
            spawn(unreal.TargetPoint, label, (x, row, dimensions[2] / 2), folder + '/Markers')
            text(label + '_Label', prop.upper() + ' / ' + slot, (x + 130, row - 100, 25), folder + '/Labels', 20)
        block('S' + number + '_' + prop + '_Placeholder', (600, row, dimensions[2] / 2 + 2), dimensions, folder + '/Placeholders')
    block('S' + number + '_ClueWall', (1850, y, 110), (30, 330, 220), folder + '/Environment')
    light = spawn(unreal.PointLight, 'S' + number + '_WorkLight', (900, y, 650), folder + '/Lighting')
    light.point_light_component.set_editor_property('intensity', 12000.0)
    light.point_light_component.set_editor_property('attenuation_radius', 1800.0)

spawn(unreal.TargetPoint, 'FINAL_IntercomAnchor', (100, 2350, 120), 'Finale/Markers')
text('FINAL_IntercomLabel', 'INTERCOM TEST ANCHOR', (180, 2200, 160), 'Finale', 22)
editor.set_level_viewport_camera_info(unreal.Vector(-250, -800, 1600), unreal.Rotator(-35, 20, 0))
assert levels.save_current_level(), 'Could not save test map.'
report = {'map': PATH, 'native_actor_count': count, 'blueprint_assets_changed': 0,
          'game_mode': 'Engine GameModeBase; temporary free-flight DefaultPawn',
          'slots': 'A/B/C are neutral markers. Define puzzle correctness in your Blueprint.',
          'scene_centers_y_cm': [-1750, 0, 1750]}
with open(os.path.join(unreal.Paths.project_saved_dir(), 'GameplayTestLevelSetup.json'), 'w') as stream:
    json.dump(report, stream, indent=2)
unreal.log('GAMEPLAY_TEST_LEVEL_READY ' + json.dumps(report))
