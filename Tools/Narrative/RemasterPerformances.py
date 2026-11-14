"""Apply the dialogue blocking pass after FinalizeNarrativeStaging. Editor only."""
from pathlib import Path
import json
import math
import random
import struct
import wave
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
EDITOR = unreal.EditorAssetLibrary
SUBSYSTEM = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ACTORS = {a.get_actor_label(): a for a in SUBSYSTEM.get_all_level_actors()}
REPORT = json.loads((ROOT/'Tools/Narrative/BuildReport.json').read_text())
SEQUENCES = {s['index']: unreal.load_asset(s['path']) for s in REPORT['sequences']}
MAYA, A, B, C = ['SET_Scene01_Maya_StandIn','NPC_Intro_CrewA_PropMaster',
                 'NPC_Intro_CrewB_SetDresser','NPC_Intro_CrewC_Lobby']
PAGES = [n for n in ACTORS if n.startswith(('PROP_Intro_Maya_Script','PROP_Intro_ScriptLine_'))]
V = unreal.Vector
KEEP = unreal.MovieSceneCompletionMode.KEEP_STATE
RESTORE = unreal.MovieSceneCompletionMode.RESTORE_STATE
TRANSFORM = unreal.MovieScene3DTransformTrack
ANIMATION = unreal.MovieSceneSkeletalAnimationTrack
VISIBILITY = unreal.MovieSceneVisibilityTrack
CLIPS = {n: unreal.load_asset('/Game/Game/Cinematics/Animations/A_Maya_'+n)
         for n in ('Chair_Idle','Chair_Rise','Listen','StudyPage')}
CLIPS['Idle'] = unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle')
CLIPS['Walk'] = unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd')
changed = set()


def binding(seq, label):
    return next((b for b in seq.get_bindings() if b.get_name() == label), None) or seq.add_possessable(ACTORS[label])


def strip(bound, classes):
    for track in list(bound.get_tracks()):
        if isinstance(track, classes):
            bound.remove_track(track)


def frame(seconds):
    return round(seconds * 30)


def pose(seq, label, keys, acting):
    bound = binding(seq, label)
    strip(bound, (TRANSFORM, ANIMATION))
    move = bound.add_track(TRANSFORM).add_section()
    end = seq.get_playback_end()
    move.set_range(0, end)
    move.set_completion_mode(KEEP)
    channels = move.get_all_channels()
    for seconds, x, y, yaw in keys:
        for channel, value in zip(channels, (x, y, 0, 0, 0, yaw, 1, 1, 1)):
            channel.add_key(unreal.FrameNumber(frame(seconds)), float(value),
                            interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    track = bound.add_track(ANIMATION)
    for i, (start, clip) in enumerate(acting):
        section = track.add_section()
        section.set_range(frame(start), frame(acting[i+1][0]) if i+1 < len(acting) else end)
        section.set_completion_mode(KEEP)
        params = section.params
        params.animation = CLIPS[clip]
        section.params = params
    changed.add(seq)


def visibility(seq, label, keys):
    bound = binding(seq, label)
    strip(bound, VISIBILITY)
    track = bound.add_track(VISIBILITY)
    track.set_property_name_and_path('bHidden','bHidden')
    section = track.add_section()
    section.set_range(0, seq.get_playback_end())
    section.set_completion_mode(RESTORE)
    channel = section.get_all_channels()[0]
    channel.set_default(keys[0][1])
    for t, show in keys:
        channel.add_key(unreal.FrameNumber(frame(t)), show)
    changed.add(seq)


def cut(seq, shots):
    for track in list(seq.get_tracks()):
        if isinstance(track, unreal.MovieSceneCameraCutTrack):
            seq.remove_track(track)
    track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    for i, (start, who) in enumerate(shots):
        section = track.add_section()
        section.set_range(frame(start), frame(shots[i+1][0]) if i+1 < len(shots) else seq.get_playback_end())
        camera_id = unreal.MovieSceneObjectBindingID()
        camera_id.set_editor_property('guid',binding(seq,who).get_id())
        section.set_camera_binding_id(camera_id)
    changed.add(seq)


def frame_camera(seq, who, position, subject):
    # Local to this shot. Restore the camera afterwards because other sequences reuse it.
    bound = binding(seq, who)
    strip(bound, TRANSFORM)
    section = bound.add_track(TRANSFORM).add_section()
    section.set_range(0,seq.get_playback_end())
    section.set_completion_mode(RESTORE)
    rot = unreal.MathLibrary.find_look_at_rotation(V(*position),V(*subject))
    for ch,value in zip(section.get_all_channels(), [*position,rot.roll,rot.pitch,rot.yaw,1,1,1]):
        ch.set_default(value)


def spatial_sound(name, kind):
    path = '/Game/Game/Audio/Cinematics/'+name
    if EDITOR.does_asset_exist(path):
        return unreal.load_asset(path)
    rng, rate = random.Random(4711), 22050
    length = .27 if kind == 'radio' else 1.67
    pcm, low = bytearray(), 0
    for sample in range(int(rate*length)):
        t = sample/rate
        white = rng.uniform(-1,1)
        low += .11*(white-low)
        if kind == 'radio':
            value = .31*low*math.exp(-t*21) + .11*math.sin(2*math.pi*890*t)*math.exp(-t*76)
        else:
            value = 0
            for index, when in enumerate((.04,.59,1.14)):
                u=t-when
                if 0 < u < .32:
                    value += (math.sin(2*math.pi*(98-6*index)*u)*.095*math.exp(-u*32)
                              + low*.25*math.exp(-u*15)) * min(u/.012,1)
        pcm.extend(struct.pack('<h',int(32767*max(-1,min(1,value)))))
    source = ROOT/'SourceArt/Audio/Cinematics'/(name+'.wav')
    source.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(source),'wb') as wav:
        wav.setparams((1,2,rate,0,'NONE','not compressed'))
        wav.writeframes(pcm)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = '/Game/Game/Audio/Cinematics'
    task.destination_name, task.automated, task.save = name, True, True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(path)


def add_foley(seq):
    title = 'Pickup | Intercom and hall'
    for track in list(seq.get_tracks()):
        if isinstance(track, unreal.MovieSceneAudioTrack) and str(track.get_display_name()) == title:
            seq.remove_track(track)
    track = seq.add_track(unreal.MovieSceneAudioTrack)
    track.set_display_name(title)
    radio = spatial_sound('S_Production_IntercomLatch','radio')
    boots = spatial_sound('S_Production_HallFootsteps','boots')
    for at, sound, length in [(4.82,radio,.26),(7.57,radio,.26),(15.2,boots,1.66),(22.4,boots,1.66)]:
        section = track.add_section()
        section.set_sound(sound)
        section.set_range(frame(at),frame(at+length))


def remaster():
    # S1: door crossing, small hesitation, then the patch catches her eye.
    q = SEQUENCES[0]
    pose(q,MAYA,[(0,-90,360,148),(2,-90,360,148),(3.8,-190,200,180),(7.8,-190,-258,180),
         (8.3,-190,-260,-112+360),(11.9,170,-400,248),(12.5,170,-400,202),(19,170,-400,202)],
         [(0,'Idle'),(2,'Walk'),(11.9,'Listen')])
    frame_camera(q,'NAR_Cam_S1_Entry',(118,325,151),(-150,140,128))
    frame_camera(q,'NAR_Cam_S1_Walk',(-128,-501,155),(-70,-300,130))
    frame_camera(q,'NAR_Cam_S1_Wall',(-20,-329,148),(215,-511,138))
    cut(q,[(0,'NAR_Cam_S1_Entry'),(5.4,'NAR_Cam_S1_Walk'),(10.6,'NAR_Cam_S1_Wall')])
    # S2 crew has already crossed during the recording. A single lamp clears the corner.
    q = SEQUENCES[6]
    pose(q,B,[(0,708,-695,-90),(1.5,708,-695,-90),(4.5,1040,-695,-90),(7.6,1300,-500,-54),
               (10,1300,-500,69)],[(0,'Idle'),(1.5,'Walk'),(7.6,'Idle')])
    pose(q,C,[(0,900,-350,-151),(5,900,-350,-151),(7,900,-350,-124)],[(0,'Listen'),(7,'Idle')])
    pose(q,MAYA,[(0,1050,-500,-120),(8,1050,-500,-120),(11,1050,-500,8),(17,1050,-500,8)],
         [(0,'Idle'),(8.7,'StudyPage'),(18.6,'Listen')])
    visibility(q,'NAR_Carry_EquipmentTrolley',[(0,False)])
    q=SEQUENCES[7]
    pose(q,MAYA,[(0,1050,-500,0),(3.2,1050,-500,0),(7.6,1050,50,0),(9.3,1120,220,-22),
                 (10.2,1120,220,-11),(15.5,1120,220,-11),(16.4,1120,220,7)],
         [(0,'StudyPage'),(3.2,'Walk'),(9.3,'Listen')])
    frame_camera(q,'NAR_Cam_S2_Tracking',(1180,-331,151),(1050,-500,129))
    frame_camera(q,'NAR_Cam_S2_OverShoulder',(1042,35,153),(1140,302,136))
    cut(q,[(0,'NAR_Cam_S2_Tracking'),(5,'NAR_Cam_S2_OverShoulder'),(12,'NAR_Cam_S2_Seam'),
           (15.35,'NAR_Cam_S2_OverShoulder')])
    # Read the reference on set; a single approach ends at the table. Turn towards the physical chair.
    q=SEQUENCES[13]
    pose(q,MAYA,[(0,1000,1040,-90),(3,1000,1040,-90),(4.3,1080,1040,-90),(4.8,1080,1040,-173),
                 (7.3,1100,850,-173),(8,1100,850,-180),(15,1100,850,-180),(16.2,1100,850,-45)],
         [(0,'Idle'),(3,'Walk'),(7.3,'StudyPage'),(15,'Listen')])
    q=SEQUENCES[14]
    pose(q,MAYA,[(0,1000,1040,-90),(1.15,1080,1040,-90),(1.7,1080,1040,-173),(4.2,1100,850,-173),
                 (5,1100,850,-180),(8.2,1100,850,-180),(9.4,1100,850,-45),(13.5,1100,850,-45)],
         [(0,'Walk'),(4.2,'StudyPage'),(8.2,'Listen')])
    frame_camera(q,'NAR_Cam_S3_Reaction',(992,950,149),(1170,910,114))
    cut(q,[(0,'NAR_Cam_S3_Entry'),(4.9,'NAR_Cam_S3_Photo'),(8.8,'NAR_Cam_S3_Reaction')])
    # Preserve Maya's mark from the take into the conversation; the pages leave her hand on permission.
    q=SEQUENCES[17]
    pose(q,MAYA,[(0,1100,850,-45),(3,1100,850,-45),(5,1100,850,-62),(10,1100,850,-62),(12,1100,850,-44)],
         [(0,'Idle'),(4.1,'StudyPage'),(9.2,'Idle')])
    frame_camera(q,'NAR_Cam_S3_Reaction',(1248,1030,151),(1100,850,137))
    for name in PAGES:
        visibility(q,name,[(0,True),(10.2,False)])
    # Recording and pickup share a physical chair at the recording mark and grounded +Y-facing legs.
    q=SEQUENCES[19]
    pose(q,MAYA,[(0,1230,1220,0)],[(0,'Chair_Idle')])
    visibility(q,'NAR_Master_RecordingChair',[(0,True)])
    visibility(q,'NAR_Prop_Scene03_Chair',[(0,False)])
    for name in PAGES+['NAR_Prop_Maya_Floorplan','NAR_Carry_LightingStand','NAR_Carry_ProductionCase']:
        visibility(q,name,[(0,False)])
    # Crew A's case remains visible during entry. Lower it out of sight on the doorway cut.
    visibility(q,'NAR_Carry_ProductionCase',[(0,True),(24.9,False)])
    radio,door,group,medium = 'NAR_Cam_S2_Seam','NAR_Cam_S1_Walk','NAR_Cam_FinalPickup_Wide','NAR_Cam_S2_Conversation'
    frame_camera(q,radio,(972,1216,144),(907,1190,139))
    frame_camera(q,door,(1265,1072,145),(885,1054,129))
    frame_camera(q,group,(1122,1455,150),(1217,1190,108))
    frame_camera(q,medium,(1299,1371,135),(1230,1223,115))
    cut(q,[(0,radio),(7.65,group),(13.9,door),(25.55,group),(32.6,medium),(51.8,group),
           (55.2,'CINE_Opening_Camera_Closeup')])
    add_foley(q)
    for i in (0,1,2,4,7,8,9,14,15,16):
        for name in PAGES:
            visibility(SEQUENCES[i],name,[(0,False)])
    for i in (6,10):
        for name in PAGES:
            visibility(SEQUENCES[i],name,[(0,False)])
    opening = unreal.load_asset('/Game/Game/Cinematics/Opening/LS_Opening_Maya')
    visibility(opening,'NAR_Master_RecordingChair',[(0,True)])
    for sq in [opening,*(SEQUENCES[i] for i in (5,12,18,20,22))]:
        for bound in sq.get_bindings():
            for track in bound.get_tracks():
                if not isinstance(track,ANIMATION):
                    continue
                for section in track.get_sections():
                    params = section.params
                    current = params.animation.get_name() if params.animation else ''
                    target = {'A_Maya_Record_Seated':'Chair_Idle','A_Maya_Record_Stand':'Chair_Rise'}.get(current)
                    if target:
                        params.animation = CLIPS[target]
                        section.params = params
                        changed.add(sq)
    for sq in changed:
        assert EDITOR.save_loaded_asset(sq,False), sq.get_path_name()
    unreal.log('PERFORMANCE_REMASTER_READY '+str(len(changed)))


if __name__ in ('__main__','builtins'):
    remaster()
