"""Shared editor-only helpers for staging take scenes (BuildL0xTakes.py) in SB_GrayBox.

Actors are reused by label so references stored on FilmSceneManager survive re-runs.
"""
import unreal

FPS = 30
_A = '/Game/Characters/Tripo/Anims/'
ANIM = {k: unreal.load_asset(_A + v) for k, v in {
    'walk': 'A_Tripo_Walk', 'look': 'A_Tripo_LookAround', 'wait': 'A_Tripo_Wait',
    'idle': 'A_Tripo_Idle', 'agree': 'A_Tripo_Agree'}.items()}
PROP_MESHES = '/Game/Game/Art/Environment/House/Meshes/Props/'

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def by_label(label):
    for a in subsys.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def spawn(folder, cls, label, loc, yaw=0.0, pitch=0.0):
    rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0)
    a = by_label(label)
    if a and a.get_class() == (cls if isinstance(cls, unreal.Class) else cls.static_class()):
        a.set_actor_location_and_rotation(unreal.Vector(*loc), rot, False, True)
        return a
    if a:
        subsys.destroy_actor(a)
    a = subsys.spawn_actor_from_class(cls, unreal.Vector(*loc), rot)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


def bp_class(path):
    return unreal.EditorAssetLibrary.load_blueprint_class(path)


def take_maya():
    """The single BP_Maya that performs every take (FilmSceneManager.Maya)."""
    m = by_label('MAYA_Take') or by_label('MAYA_L01')
    if m:
        m.set_actor_label('MAYA_Take')
    return m


def prop(folder, label, prop_id, scene_id, mesh, loc, yaw, scale=1.0,
         cls_path='/Game/Game/Blueprints/Props/BP_InteractableProp'):
    p = spawn(folder, bp_class(cls_path), label, loc, yaw=yaw)
    p.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    p.set_editor_property('PropID', prop_id)
    p.set_editor_property('SceneID', scene_id)
    p.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(unreal.load_asset(PROP_MESHES + mesh))
    return p


def area(folder, label, area_id, loc, radius):
    a = spawn(folder, bp_class('/Game/Game/Blueprints/Gameplay/Testing/BP_PlacementArea'), label, loc)
    a.set_editor_property('AreaID', area_id)
    a.set_editor_property('Radius', radius)
    a.set_actor_hidden_in_game(True)  # production areas are invisible rules, not hints
    return a


def director_mark(folder, label, loc):
    m = spawn(folder, unreal.StaticMeshActor, label, (loc[0], loc[1], 1.0))
    c = m.static_mesh_component
    c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'))
    c.set_material(0, unreal.load_asset('/Game/Game/Materials/GameplayTesting/M_DirectorMark'))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    m.set_actor_scale3d(unreal.Vector(2.0, 2.0, 0.02))
    m.tags = [unreal.Name('mcp.placement.ok')]
    return m


def gate_blocker(folder, label, loc, size_xy):
    """Invisible BlockAll wall in a doorway; FilmSceneManager.OpenSceneGate hides it and drops collision."""
    g = spawn(folder, unreal.StaticMeshActor, label, (loc[0], loc[1], 140.0))
    c = g.static_mesh_component
    c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    c.set_collision_profile_name('BlockAll')
    g.set_actor_scale3d(unreal.Vector(size_xy[0] / 100.0, size_xy[1] / 100.0, 2.8))
    g.set_actor_hidden_in_game(True)
    g.tags = [unreal.Name('mcp.placement.ok')]
    return g


def camera(folder, label, loc, yaw, pitch, focal=24.0):
    c = spawn(folder, unreal.CineCameraActor, label, loc, yaw=yaw, pitch=pitch)
    cc = c.get_cine_camera_component()
    fb = cc.get_editor_property('filmback')
    fb.set_editor_property('sensor_width', 36.0)
    fb.set_editor_property('sensor_height', 15.06)  # 2.39:1, matches LS_TakePreview
    cc.set_editor_property('filmback', fb)
    cc.set_editor_property('current_focal_length', focal)
    focus = cc.get_editor_property('focus_settings')
    focus.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
    cc.set_editor_property('focus_settings', focus)
    return c


def sequence(seq_dir, name, frames):
    path = f'{seq_dir}/{name}'
    seq = unreal.load_asset(path)
    if not seq:
        seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, seq_dir, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    for b in list(seq.get_bindings()):
        b.remove()
    for t in list(seq.get_tracks()):
        seq.remove_track(t)
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_tick_resolution(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(frames)
    return seq


def _keep(section):
    # Keep State: Maya and the camera hold the last frame while the take waits for CUT.
    section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)


def maya_track(seq, maya, frames, keys, anims):
    """keys: [(frame, (x, y, yaw))]; anims: [(start, end, anim_key)]"""
    b = seq.add_possessable(maya)
    s = b.add_track(unreal.MovieScene3DTransformTrack).add_section()
    s.set_range(0, frames)
    _keep(s)
    ch = s.get_all_channels()
    for f, (x, y, yaw) in keys:
        for i, v in ((0, x), (1, y), (2, 0.0), (3, 0.0), (4, 0.0), (5, yaw), (6, 1.0), (7, 1.0), (8, 1.0)):
            ch[i].add_key(unreal.FrameNumber(f), v, interpolation=unreal.MovieSceneKeyInterpolation.AUTO)
    at = b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for row, (a0, a1, key) in enumerate(anims):
        sec = at.add_section()
        sec.set_range(a0, a1)
        sec.set_row_index(row % 2)
        _keep(sec)
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
        _keep(s)
        bid = unreal.MovieSceneObjectBindingID()
        bid.set_editor_property('guid', ids[cam])
        s.set_camera_binding_id(bid)


def save(seq):
    unreal.EditorAssetLibrary.save_loaded_asset(seq)


def save_level():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
