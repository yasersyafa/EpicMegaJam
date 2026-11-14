"""Create reusable mannequin performances. Run in the Unreal Editor before RemasterPerformances."""
import math
import unreal

EDITOR = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MATH = unreal.MathLibrary
POSE = unreal.AnimPoseExtensions
V = unreal.Vector
LOCAL = unreal.AnimPoseSpaces.LOCAL
WORLD = unreal.AnimPoseSpaces.WORLD
FOLDER = '/Game/Game/Cinematics/Animations'
IDLE = unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle')
OPTIONS = unreal.AnimPoseEvaluationOptions()


def local_turn(local, world, joint, child, parent, destination, parent_rotation=None):
    original = world[child].translation - world[joint].translation
    delta = MATH.quat_find_between_vectors(original, V(*destination))
    desired = delta * world[joint].rotation
    parent_q = parent_rotation if parent_rotation is not None else world[parent].rotation
    local[joint].rotation = MATH.quat_inversed(parent_q) * desired
    return desired


def pose_for(base, action, phase):
    names = POSE.get_bone_names(base)
    local = {str(n): POSE.get_bone_pose(base, n, LOCAL) for n in names}
    world = {str(n): POSE.get_bone_pose(base, n, WORLD) for n in names}
    breath = math.sin(phase * math.tau)
    if action == 'Sit':
        pelvis = local['pelvis'].translation
        local['pelvis'].translation = V(pelvis.x, pelvis.y, pelvis.z - 35)
        for side, sign in [('l', 1), ('r', -1)]:
            thigh, calf, foot = [name + '_' + side for name in ('thigh', 'calf', 'foot')]
            thigh_q = local_turn(local, world, thigh, calf, 'pelvis', (3*sign, 42, -7))
            shin_q = local_turn(local, world, calf, foot, thigh, (0, 3, -42), thigh_q)
            local[foot].rotation = MATH.quat_inversed(shin_q) * world[foot].rotation
            upper, lower, hand = [name + '_' + side for name in ('upperarm', 'lowerarm', 'hand')]
            arm_q = local_turn(local, world, upper, lower, 'clavicle_'+side, (3*sign, 5, -26))
            local_turn(local, world, lower, hand, upper, (-8*sign, 22, -12+breath), arm_q)
    else:
        # Lead with the eyes/head when the drawing, a seam, or a distant sound catches Maya.
        target = (-.30, 1, -.51 + .04*breath) if action == 'Study' else (.30, 1, .16 + .025*breath)
        turn = MATH.quat_find_between_vectors(V(0,1,0), V(*target))
        parent = world['spine_05'].rotation
        local['neck_01'].rotation = MATH.quat_inversed(parent) * turn * world['neck_01'].rotation
        if action == 'Study':
            arm = local_turn(local, world, 'upperarm_r', 'lowerarm_r', 'clavicle_r', (-4, 10, -24))
            local_turn(local, world, 'lowerarm_r', 'hand_r', 'upperarm_r', (9, 20, 16), arm)
    return local


def sample_poses(action, frames, rate):
    samples = []
    idle_pose = POSE.get_anim_pose_at_frame(IDLE, 0, OPTIONS)
    for i in range(frames+1):
        phase = i / frames
        # A breathing loop starts and ends on the same pose. Stand-up finishes in stock idle.
        base = POSE.get_anim_pose_at_time(IDLE, (1 - math.cos(phase*math.tau))*.7, OPTIONS)
        sample = pose_for(base, 'Sit' if action == 'Rise' else action, phase)
        if action == 'Rise':
            ease = phase*phase*(3 - 2*phase)
            for name, value in sample.items():
                standing = POSE.get_bone_pose(idle_pose, name, LOCAL)
                value.translation = value.translation*(1-ease) + standing.translation*ease
                value.rotation = MATH.quat_slerp(value.rotation, standing.rotation, ease)
        samples.append(sample)
    return samples


def create(name, action, frames, rate):
    path = FOLDER+'/'+name
    asset = EDITOR.load_asset(path) if EDITOR.does_asset_exist(path) else None
    if not asset:
        factory = unreal.AnimSequenceFactory()
        factory.target_skeleton = IDLE.get_editor_property('skeleton')
        asset = TOOLS.create_asset(name, FOLDER, unreal.AnimSequence, factory)
    samples = sample_poses(action, frames, rate)
    controller = asset.get_editor_property('controller')
    controller.open_bracket('Author mannequin '+action)
    try:
        controller.remove_all_bone_tracks(False)
        controller.set_frame_rate(unreal.FrameRate(rate, 1))
        controller.set_number_of_frames(unreal.FrameNumber(frames))
        for bone in samples[0]:
            controller.add_bone_curve(bone, False)
            values = [s[bone] for s in samples]
            assert controller.set_bone_track_keys(bone, [v.translation for v in values],
                       [v.rotation for v in values], [v.scale3d for v in values], False), bone
    finally:
        controller.close_bracket()
    assert EDITOR.save_loaded_asset(asset), path
    return asset


if __name__ in ('__main__','builtins'):
    for settings in [('A_Maya_Chair_Idle', 'Sit', 40, 10), ('A_Maya_Chair_Rise', 'Rise', 30, 30),
                     ('A_Maya_StudyPage', 'Study', 36, 10), ('A_Maya_Listen', 'Listen', 36, 10)]:
        create(*settings)
    unreal.log('PERFORMANCE_POSES_READY')
