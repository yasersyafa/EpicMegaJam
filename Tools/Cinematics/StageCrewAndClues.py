"""Editor-only staging for per-scene crew spots, wall clues and director-mark labels in SB_GrayBox.

Idempotent: actors are reused by label. Run with SB_GrayBox open.
- Crew: one TargetPoint per role per scene (CrewSpot_<Scene>_<Role>). Each BP_CrewMember gets
  SceneSpots[SceneID] -> spot; BP_FilmSceneManager.StageCrew moves them in ConfigureScene (PRD 5.5).
- Clues: L01 patched doorway on the odd west wall, L02 sealed-door outline on the hollow wall.
- Director's Notes text per scene (DA_SceneConfig_L0x.DirectorNotesText).
"""
import math
import sys
import unreal

sys.path.append(unreal.Paths.project_dir() + 'Tools/Cinematics')
import importlib
import take_staging as ts
importlib.reload(ts)

CUBE = unreal.load_asset('/Engine/BasicShapes/Cube')
MI = '/Game/Game/Art/Environment/House/Materials/Instances/'
MAT_PATCH = unreal.load_asset(MI + 'Remaster/MI_House_Plaster_Olive')
MAT_FRAME = unreal.load_asset(MI + 'Props/MI_House_Prop_Oak')
MAT_SEAM = unreal.load_asset(MI + 'Props/MI_House_Prop_Ink')

# ---------------------------------------------------------------- crew spots
# Out of every take camera's frame, off Maya's path and the prop areas.
FOCUS = {'L01': (-170.0, -160.0), 'L02': (1000.0, 250.0)}
SPOTS = {
    'L01': {'Camera': (465.0, -60.0), 'Boom': (330.0, 300.0), 'Gaffer': (420.0, -520.0), 'Script': (330.0, -330.0)},
    # Kitchen counters run along x 1453..1524: every spot stays west of x 1410. The mark -> lamp walk
    # (1250,-300) -> (1150,-800) is kept clear, so the interact trace to the lamp is never blocked.
    'L02': {'Camera': (1400.0, -640.0), 'Boom': (1410.0, -260.0), 'Gaffer': (1350.0, -900.0), 'Script': (1300.0, -640.0)},
}
CREW_Z = 90.0


def yaw_to(src, dst):
    return math.degrees(math.atan2(dst[1] - src[1], dst[0] - src[0]))


spot_actors = {}
for scene, roles in SPOTS.items():
    for role, xy in roles.items():
        label = 'CrewSpot_%s_%s' % (scene, role)
        a = ts.spawn('Gameplay/Crew/Spots', unreal.TargetPoint, label, (xy[0], xy[1], CREW_Z), yaw=yaw_to(xy, FOCUS[scene]))
        spot_actors[(scene, role)] = a

for role in ('Camera', 'Boom', 'Gaffer', 'Script'):
    crew = ts.by_label('Crew_' + role)
    if not crew:
        print('missing crew', role)
        continue
    crew.set_editor_property('SceneSpots', {unreal.Name(s): spot_actors[(s, role)] for s in SPOTS})
    first = spot_actors[('L01', role)]
    crew.set_actor_location_and_rotation(first.get_actor_location(), first.get_actor_rotation(), False, True)

# ---------------------------------------------------------------- clue meshes


def slab(folder, label, center, size, mat, yaw=0.0):
    """A box from the engine 100 cm cube: size is (x, y, z) in cm. No collision, no shadow clutter."""
    a = ts.spawn(folder, unreal.StaticMeshActor, label, center, yaw=yaw)
    c = a.static_mesh_component
    c.set_static_mesh(CUBE)
    c.set_material(0, mat)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    a.tags = [unreal.Name('mcp.placement.ok')]
    return a


# L01: a doorway that was plastered over. A newer, differently coloured patch breaks the panelling,
# and the old frame still shows around it. West wall inner face x = -547, Maya looks at y ~ -440.
F1 = 'Gameplay/Scene01/L01/Clue'
# y = -490: still behind the start wardrobe (y -568..-312) but clear of the three-seat sofa back (ends y -343)
# in the CINE_L01_Wall shot.
WX, WY, W, H = -547.0, -490.0, 100.0, 215.0
slab(F1, 'L01_Clue_Patch', (WX + 9.0, WY, H / 2), (4.0, W, H), MAT_PATCH)
slab(F1, 'L01_Clue_JambN', (WX + 11.0, WY - W / 2 - 5.0, H / 2), (6.0, 10.0, H), MAT_FRAME)
slab(F1, 'L01_Clue_JambS', (WX + 11.0, WY + W / 2 + 5.0, H / 2), (6.0, 10.0, H), MAT_FRAME)
slab(F1, 'L01_Clue_Lintel', (WX + 11.0, WY, H + 5.0), (6.0, W + 20.0, 10.0), MAT_FRAME)
slab(F1, 'L01_Clue_Crack', (WX + 11.5, WY + 18.0, 120.0), (1.0, 1.5, 70.0), MAT_SEAM)

# L02: the outline of a sealed door in the hollow wall (kitchen face y = 387), only readable when lit.
F2 = 'Gameplay/Scene02/L02/Clue'
DX, DY, DW, DH = 1100.0, 385.0, 95.0, 210.0
slab(F2, 'L02_Clue_SeamW', (DX - DW / 2, DY, (DH - 1.5) / 2), (3.0, 3.0, DH - 1.5), MAT_SEAM)
slab(F2, 'L02_Clue_SeamE', (DX + DW / 2, DY, (DH - 1.5) / 2), (3.0, 3.0, DH - 1.5), MAT_SEAM)
slab(F2, 'L02_Clue_SeamTop', (DX, DY, DH), (DW + 3.0, 3.0, 3.0), MAT_SEAM)
slab(F2, 'L02_Clue_HingeUp', (DX - DW / 2 + 4.0, DY - 0.5, 175.0), (4.0, 2.0, 12.0), MAT_SEAM)
slab(F2, 'L02_Clue_HingeLow', (DX - DW / 2 + 4.0, DY - 0.5, 35.0), (4.0, 2.0, 12.0), MAT_SEAM)
slab(F2, 'L02_Clue_Keyhole', (DX + DW / 2 - 10.0, DY - 0.5, 100.0), (2.0, 2.0, 6.0), MAT_SEAM)

# ---------------------------------------------------------------- director-mark labels
for scene in ('L01', 'L02'):
    mark = ts.by_label('%s_DirectorMark' % scene)
    if not mark:
        continue
    loc = mark.get_actor_location()
    label = ts.spawn('Gameplay/Scene0%s/%s' % (scene[-1], scene), unreal.TextRenderActor,
                     '%s_DirectorMarkLabel' % scene, (loc.x - 120.0, loc.y, 2.0), yaw=0.0, pitch=90.0)
    t = label.text_render
    t.set_text("DIRECTOR'S MARK")
    t.set_text_render_color(unreal.Color(255, 140, 30, 255))
    t.set_editor_property('world_size', 16.0)
    t.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
    t.set_editor_property('vertical_alignment', unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    t.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    label.set_actor_rotation(unreal.Rotator(pitch=90.0, yaw=0.0, roll=0.0), False)
    label.tags = [unreal.Name('mcp.placement.ok')]

# ---------------------------------------------------------------- Director's Notes text
# "Movable:" names the props the player can pick up (QA M7: movable vs decoration).
NOTES = {
    'L01': "Laras (played by Maya) walks in from the hall door and notices the strange wall.\n\n"
           "[ ]  Clear her path from the hall door\n[ ]  Keep the strange wall in view\n\n"
           "Movable: the sofa by the door, the tall wardrobe",
    'L02': "Laras walks down the service corridor to the kitchen wall and finds a sealed door.\n\n"
           "[ ]  Keep the corridor clear\n[ ]  Keep the old doorway uncovered\n[ ]  Light it with the standing lamp\n\n"
           "Movable: the small cabinet, the standing lamp",
}
# QA M8: Scene 2 objective says where to go.
OBJECTIVES = {
    'L02': 'SCENE 2 - THE HOLLOW WALL: go to the kitchen. Let Laras reach the old doorway and light it. [F] ACTION',
}
for scene, text in NOTES.items():
    da = unreal.load_asset('/Game/Game/Data/Scenes/DA_SceneConfig_%s' % scene)
    da.set_editor_property('DirectorNotesText', text)
    if scene in OBJECTIVES:
        da.set_editor_property('ObjectiveText', OBJECTIVES[scene])
    unreal.EditorAssetLibrary.save_loaded_asset(da)

# ---------------------------------------------------------------- L01 BLOCKED camera (QA M5)
# Same camera as BuildL01Takes.py; only the camera cut of LS_L01_Blocked is swapped, Maya's track stays.
cam_blocked = ts.camera('Gameplay/Scene01/L01', 'CINE_L01_Blocked', (-60.0, 540.0, 175.0), yaw=-105.0, pitch=-14.0)
blocked = unreal.load_asset('/Game/Game/Cinematics/L01/LS_L01_Blocked')
for t in list(blocked.get_tracks()):
    if isinstance(t, unreal.MovieSceneCameraCutTrack):
        blocked.remove_track(t)
for b in list(blocked.get_bindings()):
    if str(b.get_display_name()) == 'CINE_L01_Blocked':
        b.remove()  # re-run safe: camera_cuts adds the binding again
ts.camera_cuts(blocked, [(0, blocked.get_playback_end(), cam_blocked)])
ts.save(blocked)

ts.save_level()
print('crew spots', len(spot_actors), '| clues + labels staged | notes updated')
