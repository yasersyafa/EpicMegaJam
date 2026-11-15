"""Editor-only authoring for Scene 02 (THE HOLLOW WALL) take content in SB_GrayBox.

Corridor = the Service passage (x 540..880). Maya walks from its north end, through the
service door (705, 400) into the kitchen, and stops at the hollow wall GB_Wall_KitchenServiceE
(y = 400, kitchen side), which hides the secret room. Idempotent like BuildL01Takes.py.
"""
import sys
import unreal

sys.path.append(unreal.Paths.project_dir() + 'Tools/Cinematics')
import importlib
import take_staging as ts
importlib.reload(ts)

FOLDER = 'Gameplay/Scene02/L02'
SEQ_DIR = '/Game/Game/Cinematics/L02'

START = (710.0, 1300.0, -90.0)
OPEN_END = (710.0, 970.0, -90.0)     # opening ends before the cabinet start spot
DOORWAY = (705.0, 470.0, -90.0)
INSPECT_XY = (1100.0, 270.0)         # in front of the old doorway in the hollow wall
APPROACH = (INSPECT_XY[0], INSPECT_XY[1], -20.0)
AT_WALL = (INSPECT_XY[0], INSPECT_XY[1], 90.0)

start = ts.spawn(FOLDER, unreal.TargetPoint, 'L02_MayaStart', (START[0], START[1], 0.0), yaw=START[2])
maya = ts.take_maya()
assert maya, 'Run BuildL01Takes.py first: it creates MAYA_Take'

cabinet = ts.prop(FOLDER, 'L02_Prop_SmallCabinet', 'SmallCabinet', 'L02', 'SM_House_Kitchen_Cabinet',
                  (710.0, 830.0, 0.0), 0.0)
lamp = ts.prop(FOLDER, 'L02_Prop_StandingLamp', 'StandingLamp', 'L02', 'SM_House_Lamp_Floor',
               (1150.0, -800.0, 0.0), 0.0, cls_path='/Game/Game/Blueprints/Props/BP_StandingLampProp')

ts.area(FOLDER, 'L02_Area_Corridor_A', 'L02_Corridor', (710.0, 1020.0, 0.0), 105.0)
ts.area(FOLDER, 'L02_Area_Corridor_B', 'L02_Corridor', (710.0, 800.0, 0.0), 110.0)
ts.area(FOLDER, 'L02_Area_Corridor_C', 'L02_Corridor', (708.0, 560.0, 0.0), 110.0)
ts.area(FOLDER, 'L02_Area_HollowWall', 'L02_HollowWall', (1100.0, 330.0, 0.0), 110.0)
# Left of Laras in CINE_L02_Wall (lamp no longer stands between the camera and her), clear of her path.
ts.area(FOLDER, 'L02_Area_LampReveal', 'L02_LampReveal', (1310.0, -220.0, 0.0), 90.0)

mark = ts.director_mark(FOLDER, 'L02_DirectorMark', (1250.0, -300.0))
# Service -> secret room doorway stays closed until L02 is complete (SceneLevelRefs[L02].GateActor).
gate = ts.gate_blocker(FOLDER, 'L02_Gate_SecretRoomDoor', (880.0, 1055.0), (30.0, 250.0))

cam_corr = ts.camera(FOLDER, 'CINE_L02_Corridor', (710.0, 470.0, 165.0), yaw=90.0, pitch=-3.0)
cam_kitchen = ts.camera(FOLDER, 'CINE_L02_Kitchen', (1350.0, -500.0, 185.0), yaw=120.0, pitch=-10.0)
cam_wall = ts.camera(FOLDER, 'CINE_L02_Wall', (850.0, 0.0, 155.0), yaw=53.0, pitch=-3.0)

# Opening (6.5 s): Laras studies the corridor (floor-plan lines), then walks in.
seq = ts.sequence(SEQ_DIR, 'LS_L02_Opening', 195)
ts.maya_track(seq, maya, 195, [(0, START), (90, START), (195, OPEN_END)], [(0, 90, 'look'), (90, 195, 'walk')])
ts.camera_cuts(seq, [(0, 195, cam_corr)])
ts.save(seq)

# OBSTRUCTED (5 s): blocked in the corridor, looks for a way round, then waits.
seq = ts.sequence(SEQ_DIR, 'LS_L02_Obstructed', 150)
ts.maya_track(seq, maya, 150, [(0, OPEN_END), (12, (711.0, 945.0, -90.0))],
              [(0, 12, 'walk'), (12, 90, 'look'), (90, 150, 'wait')])
ts.camera_cuts(seq, [(0, 150, cam_corr)])
ts.save(seq)

WALK = [(0, OPEN_END), (120, DOORWAY), (230, APPROACH), (255, AT_WALL)]
WALK_CUTS = [(0, 100, cam_corr), (100, 240, cam_kitchen)]

# DARK (11.5 s): reaches the wall but cannot see the detail.
seq = ts.sequence(SEQ_DIR, 'LS_L02_Dark', 345)
ts.maya_track(seq, maya, 345, WALK,[(0, 230, 'walk'), (230, 255, 'wait'), (255, 345, 'look')])
ts.camera_cuts(seq, WALK_CUTS + [(240, 345, cam_wall)])
ts.save(seq)

# PERFECT (17.5 s): finds the outline of the old doorway.
seq = ts.sequence(SEQ_DIR, 'LS_L02_Perfect', 525)
ts.maya_track(seq, maya, 525, WALK, [(0, 230, 'walk'), (230, 255, 'wait'), (255, 525, 'look')])
ts.camera_cuts(seq, WALK_CUTS + [(240, 525, cam_wall)])
ts.save(seq)

ts.save_level()
exec(open(unreal.Paths.project_dir() + 'Tools/Cinematics/StageL02SpotlightProp.py').read())
print('L02 staged. start', start.get_path_name(), '| mark', mark.get_path_name(), '| gate', gate.get_path_name())
