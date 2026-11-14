"""Editor-only authoring for Scene 01 (THE ARRIVAL) take content in SB_GrayBox.

Idempotent: re-running replaces the L01_* actors it owns and rebuilds the four
LS_L01_* sequences. Runtime logic lives in BP_FilmSceneManager; this script only
stages actors and keys sequences. Run with the level SB_GrayBox open.
"""
import unreal

FOLDER = 'Gameplay/Scene01/L01'
SEQ_DIR = '/Game/Game/Cinematics/L01'
FPS = 30

A = '/Game/Characters/Tripo/Anims/'
ANIM = {k: unreal.load_asset(A + v) for k, v in {
    'walk': 'A_Tripo_Walk', 'look': 'A_Tripo_LookAround', 'wait': 'A_Tripo_Wait', 'idle': 'A_Tripo_Idle'}.items()}

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def by_label(label):
    for a in subsys.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def spawn(cls, label, loc, yaw=0.0, pitch=0.0):
    """Reuse the labelled actor when it exists so references set on FilmSceneManager survive re-runs."""
    rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0)
    a = by_label(label)
    if a and a.get_class() == (cls if isinstance(cls, unreal.Class) else cls.static_class()):
        a.set_actor_location_and_rotation(unreal.Vector(*loc), rot, False, True)
        return a
    if a:
        subsys.destroy_actor(a)
    a = subsys.spawn_actor_from_class(cls, unreal.Vector(*loc), rot)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    return a


# ---------------------------------------------------------------- level actors
MAYA_START = (-90.0, 380.0, 0.0)   # just inside the north (hall) doorway, facing into the room
INSPECT = (-170.0, -160.0, 0.0)    # room centre inspection point, clear of the coffee table
WALL_YAW = -144.0                  # facing the odd wall at (-555, -440)

start = spawn(unreal.TargetPoint, 'L01_MayaStart', MAYA_START, yaw=-90)

maya_cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/Game/Blueprints/Characters/BP_Maya')
maya = spawn(maya_cls, 'MAYA_L01', MAYA_START, yaw=-90)
maya.set_actor_hidden_in_game(True)  # BP_Maya un-hides itself on the first ACTION
standins = [x for x in (by_label('MAYA_Scene01'), by_label('SET_Scene01_Maya_StandIn')) if x]
maya.set_editor_property('StandInsToHide', standins)

prop_cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/Game/Blueprints/Props/BP_InteractableProp')
M = '/Game/Game/Art/Environment/House/Meshes/Props/'


def make_prop(label, prop_id, mesh, loc, yaw, scale):
    p = spawn(prop_cls, label, loc, yaw=yaw)
    p.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    p.set_editor_property('PropID', prop_id)
    p.set_editor_property('SceneID', 'L01')
    comp = p.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(unreal.load_asset(M + mesh))
    return p


sofa = make_prop('L01_Prop_Sofa', 'Sofa', 'SM_House_Sofa_TwoSeat', (-140.0, 140.0, 0.0), 90.0, 1.1)
wardrobe = make_prop('L01_Prop_Wardrobe', 'Wardrobe', 'SM_House_Cabinet_Tall', (-490.0, -440.0, 0.0), 90.0, 1.0)

area_cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/Game/Blueprints/Gameplay/Testing/BP_PlacementArea')


def make_area(label, area_id, loc, radius):
    a = spawn(area_cls, label, loc)
    a.set_editor_property('AreaID', area_id)
    a.set_editor_property('Radius', radius)
    a.set_actor_hidden_in_game(True)  # production areas are invisible rules, not hints
    return a


make_area('L01_Area_Path_A', 'L01_Path', (-100.0, 290.0, 0.0), 100.0)
make_area('L01_Area_Path_B', 'L01_Path', (-135.0, 130.0, 0.0), 110.0)
make_area('L01_Area_Path_C', 'L01_Path', (-165.0, -20.0, 0.0), 110.0)
make_area('L01_Area_WallFront', 'L01_WallFront', (-470.0, -440.0, 0.0), 140.0)

cam_wide = spawn(unreal.CineCameraActor, 'CINE_L01_Wide', (470.0, -200.0, 180.0), yaw=164.0, pitch=-10.0)
cam_wall = spawn(unreal.CineCameraActor, 'CINE_L01_Wall', (-20.0, -20.0, 155.0), yaw=-142.0, pitch=-4.0)
for c in (cam_wide, cam_wall):
    cc = c.get_cine_camera_component()
    fb = cc.get_editor_property('filmback')
    fb.set_editor_property('sensor_width', 36.0)
    fb.set_editor_property('sensor_height', 15.06)  # 2.39:1, matches LS_TakePreview
    cc.set_editor_property('filmback', fb)
    cc.set_editor_property('current_focal_length', 24.0)
    focus = cc.get_editor_property('focus_settings')
    focus.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
    cc.set_editor_property('focus_settings', focus)


# ------------------------------------------------------------------ sequences
def sequence(name, frames):
    path = f'{SEQ_DIR}/{name}'
    seq = unreal.load_asset(path)
    if not seq:
        seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, SEQ_DIR, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    for b in list(seq.get_bindings()):
        b.remove()
    for t in list(seq.get_tracks()):
        seq.remove_track(t)
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_tick_resolution(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(frames)
    return seq


def keep(section):
    section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)


def maya_track(seq, frames, keys, anims):
    """keys: [(frame, (x, y, yaw))]; anims: [(start, end, anim_key)]"""
    b = seq.add_possessable(maya)
    t = b.add_track(unreal.MovieScene3DTransformTrack)
    s = t.add_section()
    s.set_range(0, frames)
    keep(s)
    ch = s.get_all_channels()
    for f, (x, y, yaw) in keys:
        for i, v in ((0, x), (1, y), (2, 0.0), (3, 0.0), (4, 0.0), (5, yaw), (6, 1.0), (7, 1.0), (8, 1.0)):
            ch[i].add_key(unreal.FrameNumber(f), v, interpolation=unreal.MovieSceneKeyInterpolation.AUTO)
    at = b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for row, (a0, a1, key) in enumerate(anims):
        sec = at.add_section()
        sec.set_range(a0, a1)
        sec.set_row_index(row % 2)
        keep(sec)
        p = sec.get_editor_property('params')
        p.set_editor_property('animation', ANIM[key])
        sec.set_editor_property('params', p)


def camera_cuts(seq, cuts):
    """cuts: [(start, end, camera_actor)]"""
    track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    ids = {}
    for a0, a1, cam in cuts:
        if cam not in ids:
            ids[cam] = seq.add_possessable(cam).get_id()
        s = track.add_section()
        s.set_range(a0, a1)
        keep(s)
        bid = unreal.MovieSceneObjectBindingID()
        bid.set_editor_property('guid', ids[cam])
        s.set_camera_binding_id(bid)


DOOR = (MAYA_START[0], MAYA_START[1], -90.0)
STEP_IN = (-105.0, 300.0, -100.0)
CENTER = (INSPECT[0], INSPECT[1], -100.0)

# Opening (7.5 s): Laras pauses in the doorway, then steps in. Ends before the sofa start spot.
seq = sequence('LS_L01_Opening', 225)
maya_track(seq, 225, [(0, DOOR), (180, DOOR), (225, STEP_IN)], [(0, 180, 'look'), (180, 225, 'walk')])
camera_cuts(seq, [(0, 225, cam_wide)])
unreal.EditorAssetLibrary.save_loaded_asset(seq)

# BLOCKED (5 s): one step, stops short, turns toward the director and waits.
seq = sequence('LS_L01_Blocked', 150)
maya_track(seq, 150, [(0, STEP_IN), (15, (-112.0, 284.0, -100.0)), (45, (-112.0, 284.0, -40.0))],
           [(0, 15, 'walk'), (15, 150, 'wait')])
camera_cuts(seq, [(0, 150, cam_wide)])
unreal.EditorAssetLibrary.save_loaded_asset(seq)

# MISSED_CLUE (6.5 s): reaches the centre but has nothing to react to.
seq = sequence('LS_L01_MissedClue', 195)
maya_track(seq, 195, [(0, STEP_IN), (120, CENTER)], [(0, 120, 'walk'), (120, 195, 'look')])
camera_cuts(seq, [(0, 195, cam_wide)])
unreal.EditorAssetLibrary.save_loaded_asset(seq)

# PERFECT (13 s): reaches the centre, turns to the odd wall and studies it.
seq = sequence('LS_L01_Perfect', 390)
maya_track(seq, 390, [(0, STEP_IN), (120, CENTER), (150, (INSPECT[0], INSPECT[1], WALL_YAW))],
           [(0, 120, 'walk'), (120, 150, 'wait'), (150, 390, 'look')])
camera_cuts(seq, [(0, 150, cam_wide), (150, 390, cam_wall)])
unreal.EditorAssetLibrary.save_loaded_asset(seq)

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('L01 staged:', [a.get_actor_label() for a in (start, maya, sofa, wardrobe, cam_wide, cam_wall)],
      'standins:', [s.get_actor_label() for s in standins])
