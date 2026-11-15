"""Editor-only authoring for the Blueprint take preview. Run through Unreal Python."""
import unreal

tools = unreal.AssetToolsHelpers.get_asset_tools()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
path = '/Game/Game/Cinematics/LS_TakePreview'
sequence = unreal.load_asset(path)
if sequence is None:
    sequence = tools.create_asset('LS_TakePreview', '/Game/Game/Cinematics', unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
if len(sequence.get_bindings()) < 2:
    for binding in sequence.get_bindings():
        binding.remove()
    for track in sequence.get_tracks():
        sequence.remove_track(track)
    sequence.set_display_rate(unreal.FrameRate(30, 1))
    sequence.set_playback_start(0)
    sequence.set_playback_end(240)
    cuts = next((t for t in sequence.get_tracks() if isinstance(t, unreal.MovieSceneCameraCutTrack)), None) or sequence.add_track(unreal.MovieSceneCameraCutTrack)
    shots = [((-300, 350, 170), (0, -100, 90), 24, 0, 120),
             ((160, -230, 120), (-30, -60, 55), 50, 120, 240)]
    for i, (position, target, lens, start, end) in enumerate(shots):
        location = unreal.Vector(*position)
        rotation = unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(*target))
        camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == 'Cine_TakePreview_%02d' % (i + 1)), None) or actors.spawn_actor_from_class(unreal.CineCameraActor, location, rotation)
        camera.set_actor_label('Cine_TakePreview_%02d' % (i + 1))
        component = camera.get_cine_camera_component()
        component.set_editor_property('filmback', unreal.CameraFilmbackSettings(sensor_width=36.0, sensor_height=36.0/2.39))
        component.set_editor_property('constrain_aspect_ratio', True)
        component.set_editor_property('current_focal_length', lens)
        focus = component.get_editor_property('focus_settings')
        focus.set_editor_property('focus_method', unreal.CameraFocusMethod.DISABLE)
        component.set_editor_property('focus_settings', focus)
        binding = sequence.add_possessable(camera)
        section = cuts.add_section()
        section.set_range(start, end)
        camera_id = unreal.MovieSceneObjectBindingID()
        camera_id.set_editor_property('guid', binding.get_id())
        section.set_camera_binding_id(camera_id)
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)

action = unreal.load_asset('/Game/Game/Input/IA_ActionCut')
if action is None:
    action = tools.create_asset('IA_ActionCut', '/Game/Game/Input', unreal.InputAction, unreal.InputAction_Factory())
    action.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    unreal.EditorAssetLibrary.save_loaded_asset(action)
context = unreal.load_asset('/Game/Game/Input/IMC_Director')
if not any(m.action == action for m in context.get_editor_property('mappings')):
    key = unreal.Key()
    key.set_editor_property('key_name', 'F')
    context.map_key(action, key)
    unreal.EditorAssetLibrary.save_loaded_asset(context, False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('Take preview and ACTION/CUT input authored.')




