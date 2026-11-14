"""Exercise Enhanced Input and real placement in PIE through the editor bridge."""
from GameplayBridge import call, python
from pathlib import Path
import json
import time

BOOTSTRAP='''import unreal,sys,types,json,os
m=types.ModuleType('gameplay_input_test');sys.modules['gameplay_input_test']=m
exec("""import unreal,json,os
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
labels={a.get_actor_label():a for a in actors}
manager=labels['SYSTEM_GameplayTestManager']
player=manager.get_editor_property('Player')
controller=manager.get_editor_property('Controller')
checks=[]
def record(name,condition):
 checks.append({'name':name,'passed':bool(condition)})
 json.dump({'checks':checks,'passed':all(x['passed'] for x in checks)},open(unreal.Paths.project_saved_dir()+'GameplayInteractionValidation.json','w'),indent=2)
 assert condition,name
def aim(actor):
 location=actor.get_actor_location()
 player.set_actor_location(unreal.Vector(location.x-250,location.y,90),False,True)
 camera=player.get_editor_property('FirstPersonCamera')
 controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),location))
def select(scene):
 manager.call_method('SelectScene'+str(scene));manager.call_method('RestartScene')
def start_take():
 mark=manager.get_editor_property('ActiveDirectorMark')
 player.set_actor_location(mark.get_actor_location()+unreal.Vector(0,0,88),False,True)
 manager.call_method('StartTake')
def prop(index):return manager.get_editor_property('ActiveProp'+str(index))
def state():return manager.get_editor_property('State')
""",m.__dict__)
'''
python('exec('+repr(BOOTSTRAP)+')')


def run(code):
    python("import gameplay_input_test as t; "+code)
    time.sleep(.15)


def press(action):
    call('press_input',inputAction=action)
    time.sleep(.25)


def check(code):
    run(code)
    result=json.loads(Path('Saved/GameplayInteractionValidation.json').read_text())
    assert result['passed'],result


run("t.select(1); t.aim(t.prop(1))")
run("t.start_take()")
time.sleep(2.3)
check("t.record('failed take never auto cuts',t.state()==1); t.manager.call_method('CancelTake')")
run("t.aim(t.prop(1))")
press('IA_Interact')
check("t.record('E picks up sofa',t.player.get_editor_property('HeldProp')==t.prop(1))")
check("t.start_take(); t.record('ACTION rejects actual held prop',t.state()==0)")
run("t.controller.set_control_rotation(unreal.Rotator(-85,90,0))")
press('IA_Interact')
check("t.record('invalid placement retains selection and committed slot',t.player.get_editor_property('HeldProp')==t.prop(1) and str(t.prop(1).get_editor_property('CurrentSlotID'))=='S1_P1_A')")
press('IA_Cancel')
check("t.record('RMB cancels selection',t.player.get_editor_property('HeldProp') is None and str(t.prop(1).get_editor_property('CurrentSlotID'))=='S1_P1_A')")
for index,name,slot in [(1,'Sofa','B'),(2,'Wardrobe','C')]:
    run(f't.aim(t.prop({index}))')
    press('IA_Interact')
    check(f"t.record('pickup {name}',t.player.get_editor_property('HeldProp')==t.prop({index}))")
    run(f"t.aim(t.labels['S01_{name}_Snap_{slot}'])")
    check(f"t.record('compatible target {name}',t.player.get_editor_property('TargetSlot')==t.labels['S01_{name}_Snap_{slot}'])")
    press('IA_Interact')
    check(f"t.record('commit {name} {slot}',t.player.get_editor_property('HeldProp') is None and str(t.prop({index}).get_editor_property('CurrentSlotID'))=='S1_P{index}_{slot}')")
run("t.start_take()")
check("t.record('perfect take starts from actual placements',t.state()==1 and t.manager.get_editor_property('Outcome')==0)")
time.sleep(2.3)
check("t.record('simulator automatically completes perfect take',t.state()==2 and t.manager.get_editor_property('Completed1') and not t.controller.is_move_input_ignored())")
run("t.aim(t.prop(1))")
press('IA_Interact')
run("t.saved_wardrobe=t.prop(2).get_actor_location(); t.prop(2).set_actor_location(t.labels['S01_Sofa_Snap_C'].get_actor_location(),False,True); t.aim(t.labels['S01_Sofa_Snap_C'])")
check("t.record('occupied slot rejects placement',t.player.get_editor_property('HeldProp')==t.prop(1) and t.player.get_editor_property('TargetSlot') is None)")
run("t.prop(2).set_actor_location(t.saved_wardrobe,False,True); t.aim(t.labels['S01_Wardrobe_Snap_B'])")
check("t.record('wrong prop type rejects placement',t.player.get_editor_property('TargetSlot') is None)")
press('IA_Cancel')
for scene,names in [(2,['Cabinet','Lamp']),(3,['Chair','Lamp'])]:
    run(f't.select({scene})')
    for index,name,slot in [(1,names[0],'B'),(2,names[1],'C')]:
        run(f't.aim(t.prop({index}))');press('IA_Interact')
        check(f"t.record('scene {scene} pickup {name}',t.player.get_editor_property('HeldProp')==t.prop({index}))")
        run(f"t.aim(t.labels['S{scene:02d}_{name}_Snap_{slot}'])")
        check(f"t.record('scene {scene} target {name}',t.player.get_editor_property('TargetSlot')==t.labels['S{scene:02d}_{name}_Snap_{slot}'])")
        press('IA_Interact')
        check(f"t.record('scene {scene} commit {name}',t.player.get_editor_property('HeldProp') is None and str(t.prop({index}).get_editor_property('CurrentSlotID'))=='S{scene}_P{index}_{slot}')")
    run("t.start_take()")
    time.sleep(2.3)
    check(f"t.record('scene {scene} auto CUT from real placements',t.state()==2 and t.manager.get_editor_property('Completed{scene}'))")
run("t.manager.call_method('AdvanceScene'); t.player.set_actor_location(unreal.Vector(300,-1750,90),False,True)")
press('IA_Interact')
check("t.record('intercom input rejects distant use',t.state()==3)")
run("t.aim(t.manager.get_editor_property('Intercom'))")
press('IA_Interact')
check("t.record('intercom input completes the full run',t.state()==4 and t.manager.get_editor_property('CompletedCount')==3)")
print(Path('Saved/GameplayInteractionValidation.json').read_text())
