"""Editor-only authoring for Scene 01 (THE ARRIVAL) take content in SB_GrayBox.

Idempotent: re-running updates the L01_* actors it owns (reused by label) and
rebuilds the four LS_L01_* sequences. Runtime logic lives in BP_FilmSceneManager.
Run with SB_GrayBox open.
"""
import sys
import unreal

sys.path.append(unreal.Paths.project_dir() + 'Tools/Cinematics')
import importlib
import take_staging as ts
importlib.reload(ts)

FOLDER = 'Gameplay/Scene01/L01'
SEQ_DIR = '/Game/Game/Cinematics/L01'

MAYA_START = (-90.0, 380.0, 0.0)   # just inside the north (hall) doorway, facing into the room
INSPECT = (-170.0, -160.0, 0.0)    # room centre inspection point, clear of the coffee table
WALL_YAW = -144.0                  # facing the odd wall at (-555, -440)

start = ts.spawn(FOLDER, unreal.TargetPoint, 'L01_MayaStart', MAYA_START, yaw=-90)

maya = ts.take_maya() or ts.spawn(FOLDER, ts.bp_class('/Game/Game/Blueprints/Characters/BP_Maya'),
                                  'MAYA_Take', MAYA_START, yaw=-90)
maya.set_actor_label('MAYA_Take')
maya.set_actor_location_and_rotation(unreal.Vector(*MAYA_START), unreal.Rotator(0, -90, 0), False, True)
maya.set_actor_hidden_in_game(True)  # BP_Maya un-hides itself on the first ACTION
standins = [x for x in (ts.by_label('MAYA_Scene01'), ts.by_label('SET_Scene01_Maya_StandIn')) if x]
maya.set_editor_property('StandInsToHide', standins)

sofa = ts.prop(FOLDER, 'L01_Prop_Sofa', 'Sofa', 'L01', 'SM_House_Sofa_TwoSeat', (-140.0, 140.0, 0.0), 90.0, 1.1)
wardrobe = ts.prop(FOLDER, 'L01_Prop_Wardrobe', 'Wardrobe', 'L01', 'SM_House_Cabinet_Tall', (-490.0, -440.0, 0.0), 90.0)

ts.area(FOLDER, 'L01_Area_Path_A', 'L01_Path', (-100.0, 290.0, 0.0), 100.0)
ts.area(FOLDER, 'L01_Area_Path_B', 'L01_Path', (-135.0, 130.0, 0.0), 110.0)
ts.area(FOLDER, 'L01_Area_Path_C', 'L01_Path', (-165.0, -20.0, 0.0), 110.0)
ts.area(FOLDER, 'L01_Area_WallFront', 'L01_WallFront', (-470.0, -440.0, 0.0), 140.0)

mark = ts.director_mark(FOLDER, 'L01_DirectorMark', (240.0, -220.0))
# Dining -> kitchen doorway stays closed until L01 is complete (SceneLevelRefs[L01].GateActor).
gate = ts.gate_blocker(FOLDER, 'L01_Gate_KitchenDoor', (540.0, -695.0), (30.0, 250.0))

cam_wide = ts.camera(FOLDER, 'CINE_L01_Wide', (470.0, -200.0, 180.0), yaw=164.0, pitch=-10.0)
cam_wall = ts.camera(FOLDER, 'CINE_L01_Wall', (-20.0, -20.0, 155.0), yaw=-142.0, pitch=-4.0)

DOOR = (MAYA_START[0], MAYA_START[1], -90.0)
STEP_IN = (-105.0, 300.0, -100.0)
CENTER = (INSPECT[0], INSPECT[1], -100.0)

# Opening (7.5 s): Laras pauses in the doorway, then steps in. Ends before the sofa start spot.
seq = ts.sequence(SEQ_DIR, 'LS_L01_Opening', 225)
ts.maya_track(seq, maya, 225, [(0, DOOR), (180, DOOR), (225, STEP_IN)], [(0, 180, 'look'), (180, 225, 'walk')])
ts.camera_cuts(seq, [(0, 225, cam_wide)])
ts.save(seq)

# BLOCKED (5 s): one step, stops short, turns toward the director and waits.
seq = ts.sequence(SEQ_DIR, 'LS_L01_Blocked', 150)
ts.maya_track(seq, maya, 150, [(0, STEP_IN), (15, (-112.0, 284.0, -100.0)), (45, (-112.0, 284.0, -40.0))],
              [(0, 15, 'walk'), (15, 150, 'wait')])
ts.camera_cuts(seq, [(0, 150, cam_wide)])
ts.save(seq)

# MISSED_CLUE (6.5 s): reaches the centre but has nothing to react to.
seq = ts.sequence(SEQ_DIR, 'LS_L01_MissedClue', 195)
ts.maya_track(seq, maya, 195, [(0, STEP_IN), (120, CENTER)], [(0, 120, 'walk'), (120, 195, 'look')])
ts.camera_cuts(seq, [(0, 195, cam_wide)])
ts.save(seq)

# PERFECT (13 s): reaches the centre, turns to the odd wall and studies it.
seq = ts.sequence(SEQ_DIR, 'LS_L01_Perfect', 390)
ts.maya_track(seq, maya, 390, [(0, STEP_IN), (120, CENTER), (150, (INSPECT[0], INSPECT[1], WALL_YAW))],
              [(0, 120, 'walk'), (120, 150, 'wait'), (150, 390, 'look')])
ts.camera_cuts(seq, [(0, 150, cam_wide), (150, 390, cam_wall)])
ts.save(seq)

ts.save_level()
print('L01 staged. start', start.get_path_name(), '| mark', mark.get_path_name(), '| gate', gate.get_path_name(),
      '| maya', maya.get_path_name(), '| standins', [s.get_actor_label() for s in standins])
