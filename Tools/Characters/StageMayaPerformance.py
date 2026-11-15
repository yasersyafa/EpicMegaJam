"""Stage Maya's compatible performances, path-facing and stride-matched locomotion."""
import math
import unreal

P = '/Game/Game/Characters/Maya/'
FPS = 30
# Original Tripo walk travels 267.17555 cm in 2.33333 seconds before in-place conversion.
REFERENCE_WALK_SPEED_CM_S = 114.50380614732079
mesh = unreal.load_asset(P + 'SK_Maya')
names = ['Idle', 'Walk', 'LookAround', 'LookAtDirector', 'Hesitate', 'Inspect',
         'Surprised', 'Waiting', 'TurnLeft', 'TurnRight', 'Confession']
anims = {name: unreal.load_asset(P + 'Animations/A_Maya_' + name) for name in names}
assert mesh and all(anims.values())
assert all(a.get_editor_property('skeleton') == mesh.get_editor_property('skeleton') for a in anims.values())


def key_time(key):
    time = key.get_time()
    return time.frame_number.value + time.sub_frame


def sample(channel, frame):
    keys = sorted((key_time(k), k.get_value()) for k in channel.get_keys())
    if not keys:
        return channel.get_default()
    if frame <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if frame <= f1:
            return v0 + (v1 - v0) * (frame - f0) / (f1 - f0)
    return keys[-1][1]


def transform_section(binding):
    track = next(t for t in binding.get_tracks() if isinstance(t, unreal.MovieScene3DTransformTrack))
    return track.get_sections()[0]


def travel_distance(binding, start, end):
    channels = transform_section(binding).get_all_channels()
    frames = sorted({start, end} | {key_time(k) for c in channels[:2] for k in c.get_keys()
                                  if start < key_time(k) < end})
    points = [(sample(channels[0], f), sample(channels[1], f)) for f in frames]
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def stage_kitchen_path(binding):
    """Cross the door before rounding the corner; keep speed and facing continuous."""
    points = [(710.0, 970.0), (705.0, 470.0), (705.0, 360.0)]
    start, control, end = points[-1], (705.0, 320.0), (745.0, 315.0)
    for i in range(1, 7):
        t = i / 6
        points.append(tuple((1-t)**2 * start[j] + 2*(1-t)*t * control[j] + t*t*end[j]
                            for j in range(2)))
    points.append((1100.0, 270.0))
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + math.dist(a, b))
    total = cumulative[-1]
    frames = [round(d / total * 230) for d in cumulative]
    headings = []
    for i, point in enumerate(points):
        if i == 0:
            direction = (points[1][0]-point[0], points[1][1]-point[1])
        elif i == len(points)-1:
            direction = (point[0]-points[i-1][0], point[1]-points[i-1][1])
        else:
            before = (point[0]-points[i-1][0], point[1]-points[i-1][1])
            after = (points[i+1][0]-point[0], points[i+1][1]-point[1])
            direction = (before[0]/math.hypot(*before)+after[0]/math.hypot(*after),
                         before[1]/math.hypot(*before)+after[1]/math.hypot(*after))
        headings.append(math.degrees(math.atan2(direction[1], direction[0]))-90)
    section = transform_section(binding)
    channels = section.get_all_channels()
    for channel in channels[:6]:
        for key in list(channel.get_keys()):
            channel.remove_key(key)
    for frame, point, yaw in zip(frames, points, headings):
        for index, value in [(0,point[0]), (1,point[1]), (2,0), (3,0), (4,0), (5,yaw)]:
            channels[index].add_key(unreal.FrameNumber(frame), value,
                                    interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    for index, value in [(0,1100.0), (1,270.0), (2,0), (3,0), (4,0), (5,0)]:
        channels[index].add_key(unreal.FrameNumber(255), value,
                                interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    # Match the authored pivot's smooth heading curve; animation does not rotate the actor.
    for key in channels[5].get_keys():
        if round(key_time(key)) in [230, 255]:
            key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_CUBIC)
            key.set_tangent_mode(unreal.RichCurveTangentMode.RCTM_USER)
            key.set_arrive_tangent(0)
            key.set_leave_tangent(0)
    print('KITCHEN_PATH', round(total, 3), 'cm', list(zip(frames, points)))


BP = '/Game/Game/Blueprints/Characters/BP_Maya'
bp = unreal.load_asset(BP)
cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class(BP))
material = mesh.get_editor_property('materials')[0].get_editor_property('material_interface')
assert material
cdo.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
cdo.skeletal_mesh_component.set_material(0, material)
cdo.set_editor_property('IdleAnim', anims['Idle'])
cdo.set_editor_property('WaitingAnim', anims['Waiting'])
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
maya = next(a for a in actors if a.get_actor_label() == 'MAYA_Take')
component = maya.get_component_by_class(unreal.SkeletalMeshComponent)
component.set_skeletal_mesh_asset(mesh)
component.set_material(0, material)
component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
component.set_animation(anims['Idle'])
component.set_update_animation_in_editor(True)
maya.set_editor_property('IdleAnim', anims['Idle'])
maya.set_editor_property('MeshYawOffset', -90.0)
maya.set_actor_hidden_in_game(True)

clips = {
    'Interlude01': [(0,615,'Confession')],
    'L01_Opening': [(0,180,'LookAround'), (180,225,'Walk')],
    'L01_Blocked': [(0,15,'Walk'), (15,65,'Hesitate'), (65,125,'LookAtDirector'), (125,150,'Waiting')],
    'L01_MissedClue': [(0,120,'Walk'), (120,170,'LookAround'), (170,195,'Hesitate')],
    'L01_Perfect': [(0,120,'Walk'), (120,150,'TurnLeft'), (150,390,'Inspect')],
    'L02_Opening': [(0,90,'LookAround'), (90,195,'Walk')],
    'L02_Obstructed': [(0,12,'Walk'), (12,70,'Hesitate'), (70,120,'LookAtDirector'), (120,150,'Waiting')],
    'L02_Dark': [(0,230,'Walk'), (230,255,'TurnRight'), (255,315,'Inspect'), (315,345,'Hesitate')],
    'L02_Perfect': [(0,230,'Walk'), (230,255,'TurnRight'), (255,465,'Inspect'), (465,525,'Surprised')],
}
for name, parts in clips.items():
    folder = 'Interludes' if name == 'Interlude01' else name[:3]
    seq = unreal.load_asset('/Game/Game/Cinematics/' + folder + '/LS_' + name)
    binding = next(b for b in seq.get_bindings()
                   if any(isinstance(t, unreal.MovieSceneSkeletalAnimationTrack) for t in b.get_tracks()))
    if name in ['L02_Dark', 'L02_Perfect']:
        stage_kitchen_path(binding)
    for track in list(binding.get_tracks()):
        if isinstance(track, unreal.MovieSceneSkeletalAnimationTrack):
            binding.remove_track(track)
    track = binding.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for i, (start, end, kind) in enumerate(parts):
        section = track.add_section()
        pivot = kind.startswith('Turn')
        a0 = start if i == 0 or pivot else max(0, start-4)
        a1 = end if i == len(parts)-1 or pivot else min(seq.get_playback_end(), end+4)
        section.set_range(a0, a1)
        section.set_row_index(i % 2)
        section.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
        params = section.get_editor_property('params')
        params.set_editor_property('animation', anims[kind])
        params.set_editor_property('skip_anim_notifiers', True)
        params.set_editor_property('force_custom_mode', True)
        speed = None
        if kind == 'Walk':
            speed = travel_distance(binding, start, end) / ((end-start)/FPS)
            playback = speed / REFERENCE_WALK_SPEED_CM_S
        elif kind not in ['Waiting', 'Confession'] and not pivot:
            playback = anims[kind].get_play_length() / ((end-start)/FPS)
        else:
            playback = 1.0
        rate = params.get_editor_property('play_rate')
        rate.set_fixed_play_rate(playback)
        params.set_editor_property('play_rate', rate)
        section.set_editor_property('params', params)
        weight = section.get_all_channels()[0]
        if i:
            weight.add_key(unreal.FrameNumber(a0), 0.0, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            weight.add_key(unreal.FrameNumber(start+4), 1.0, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        if i != len(parts)-1:
            weight.add_key(unreal.FrameNumber(end-4), 1.0, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
            weight.add_key(unreal.FrameNumber(a1), 0.0, interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
        if speed is not None:
            print('STRIDE_MATCH', name, round(speed,3), 'cm/s', round(playback,4))
    for transform in [t for t in binding.get_tracks() if isinstance(t, unreal.MovieScene3DTransformTrack)]:
        for section in transform.get_sections():
            for channel in section.get_all_channels()[:3]:
                for key in channel.get_keys():
                    key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
            if name == 'Interlude01':
                for key in section.get_all_channels()[5].get_keys():
                    key.set_value(0.0)
    unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('MAYA_STAGING_COMPLETE')
