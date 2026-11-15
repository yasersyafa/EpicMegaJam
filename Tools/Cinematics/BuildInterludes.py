"""Editor-only authoring for the story beats between takes in SB_GrayBox.

- Interlude 01 "Out of Frame" (after L01 success): Maya close-up monologue on the set of Ibra's
  opening close-up (CINE_Opening_KeyLight), with its own camera. FilmSceneManager plays
  DA_SceneConfig_L01.InterludeSequence + InterludeDialogueIDs from FinishPostTake (TakePhase 3).
- Transition 07 "A Different Kind of Scene" (dining -> kitchen, before L02): crew B carries a
  floor lamp, crew C pushes a flight case, Maya reads her script by the dining table. A
  BP_DialogueTrigger at the kitchen doorway plays DA_SceneConfig_L02.TransitionDialogueIDs once.

Idempotent like BuildL01Takes.py. Run after BuildL01Takes.py and BuildL02Takes.py.
"""
import sys
import unreal

sys.path.append(unreal.Paths.project_dir() + 'Tools/Cinematics')
import importlib
import take_staging as ts
importlib.reload(ts)

FOLDER = 'Gameplay/Interludes'
SEQ_DIR = '/Game/Game/Cinematics/Interludes'
CREW_ANIM = unreal.load_asset('/Game/Characters/Tripo/Anims/A_Tripo_Crew_Idle')

maya = ts.take_maya()
assert maya, 'Run BuildL01Takes.py first: it creates MAYA_Take'

# Ibra's opening Maya stand-ins sit on the close-up mark; hide them once takes start.
hide = list(maya.get_editor_property('StandInsToHide'))
for label in ('MAYA_Opening', 'CINE_Opening_Maya_StandIn'):
    a = ts.by_label(label)
    if a and a not in hide:
        hide.append(a)
maya.set_editor_property('StandInsToHide', hide)

# --- Interlude 01: close-up monologue (5 lines, 19 s of subtitles) ---------------------------
# Same spot and key light as Ibra's opening close-up, but our own camera: his sits too close for
# a standing Maya. Yaw 0 faces the camera (the Tripo mesh is offset, as on Ibra's stand-in).
MARK = (1230.0, 1230.0, 0.0)
closeup = ts.camera(FOLDER, 'CINE_IL01_Closeup', (1230.0, 1520.0, 150.0), yaw=-90.0, pitch=-4.0, focal=35.0)

seq = ts.sequence(SEQ_DIR, 'LS_Interlude01', 615)
ts.maya_track(seq, maya, 615, [(0, MARK), (615, MARK)],
              [(0, 238, 'idle'), (238, 320, 'look'), (320, 456, 'agree'), (456, 615, 'idle')])
ts.camera_cuts(seq, [(0, 615, closeup)])
ts.save(seq)


# --- Transition 07: dining room staging --------------------------------------------------------
def crew(label, mesh, loc, yaw):
    c = ts.spawn(FOLDER, unreal.SkeletalMeshActor, label, loc, yaw=yaw)
    sk = c.skeletal_mesh_component
    sk.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Tripo/Crew/' + mesh))
    sk.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    ad = sk.get_editor_property('animation_data')
    ad.set_editor_property('anim_to_play', CREW_ANIM)
    ad.set_editor_property('saved_looping', True)
    ad.set_editor_property('saved_playing', True)
    sk.set_editor_property('animation_data', ad)
    sk.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return c


def set_dressing(label, mesh, loc, yaw):
    p = ts.spawn(FOLDER, unreal.StaticMeshActor, label, loc, yaw=yaw)
    p.static_mesh_component.set_static_mesh(unreal.load_asset(ts.PROP_MESHES + mesh))
    return p


crew('TR02_Crew_B', 'SKM_Crew_B', (300.0, -880.0, 0.0), -60.0)
set_dressing('TR02_Prop_FloorLamp', 'SM_House_Lamp_Floor', (345.0, -935.0, 0.0), 0.0)
crew('TR02_Crew_C', 'SKM_Crew_Utility', (440.0, -1010.0, 0.0), 150.0)
set_dressing('TR02_Prop_FlightCase', 'SM_House_FlightCase_Black', (380.0, -1050.0, 0.0), 60.0)

# Maya waits for L02 reading her script by the dining table (L02 SETUP / after every CUT).
# LS_L02_* key her from the corridor start on frame 0, so the take itself is unchanged.
ts.spawn('Gameplay/Scene02/L02', unreal.TargetPoint, 'L02_MayaStart', (160.0, -980.0, 0.0), yaw=180.0)

trigger = ts.spawn(FOLDER, ts.bp_class('/Game/Game/Blueprints/Film/BP_DialogueTrigger'),
                   'TR02_DialogueTrigger', (420.0, -695.0, 100.0))
trigger.set_editor_property('SceneID', 'L02')

# --- Scene config data ------------------------------------------------------------------------
l01 = unreal.load_asset('/Game/Game/Data/Scenes/DA_SceneConfig_L01')
l01.set_editor_property('InterludeSequence', unreal.load_asset(SEQ_DIR + '/LS_Interlude01'))
l01.set_editor_property('InterludeDialogueIDs', [f'IL01_MAYA_0{i}' for i in range(1, 6)])
unreal.EditorAssetLibrary.save_loaded_asset(l01)

l02 = unreal.load_asset('/Game/Game/Data/Scenes/DA_SceneConfig_L02')
l02.set_editor_property('TransitionDialogueIDs', [f'TR02_0{i}' for i in range(1, 8)])
unreal.EditorAssetLibrary.save_loaded_asset(l02)

ts.save_level()
print('Interludes staged. trigger', trigger.get_path_name())
