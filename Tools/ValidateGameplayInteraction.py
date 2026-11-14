"""Manual Enhanced Input validation for free placement. Start PIE before running."""
from GameplayBridge import call,python
from pathlib import Path
import json
import time

BOOTSTRAP='''import unreal,sys,types,json
m=types.ModuleType('gameplay_input_test');sys.modules['gameplay_input_test']=m
exec("""import unreal,json
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world, 'Start PIE manually before running this validation.'
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
manager=next(a for a in actors if a.get_actor_label()=='SYSTEM_GameplayTestManager')
player=manager.get_editor_property('Player')
controller=manager.get_editor_property('Controller')
checks=[]
def record(name,condition):
 checks.append({'name':name,'passed':bool(condition)})
 json.dump({'checks':checks,'passed':all(x['passed'] for x in checks)},open(unreal.Paths.project_saved_dir()+'GameplayInteractionValidation.json','w'),indent=2)
 assert condition,name
def aim(actor):
 point=actor.get_actor_location()
 player.set_actor_location(unreal.Vector(point.x-250,point.y,88),False,True)
 controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(player.get_editor_property('FirstPersonCamera').get_world_location(),point))
def aim_ground(point):
 player.set_actor_location(unreal.Vector(point.x-250,point.y,88),False,True)
 controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(player.get_editor_property('FirstPersonCamera').get_world_location(),point))
def select(scene):
 manager.call_method('SelectScene'+str(scene));manager.call_method('RestartScene')
def start_take():
 mark=manager.get_editor_property('ActiveDirectorMark')
 player.set_actor_location(mark.get_actor_location()+unreal.Vector(0,0,88),False,True)
 manager.call_method('StartTake')
def prop(index):return manager.get_editor_property('ActiveProp'+str(index))
def area(index):return manager.get_editor_property('ActiveArea'+str(index))
def inside(index):return area(index).call_method('ContainsProp',(prop(index),))
def state():return manager.get_editor_property('State')
""",m.__dict__)
'''


def run(code):
    python('import gameplay_input_test as t; '+code)
    time.sleep(.15)


def press(action):
    call('press_input',inputAction=action)
    time.sleep(.25)


def check(code):
    run(code)
    result=json.loads(Path('Saved/GameplayInteractionValidation.json').read_text())
    assert result['passed'],result


def main():
    python('exec('+repr(BOOTSTRAP)+')')
    run('t.select(1); t.start_take()')
    time.sleep(2.3)
    check("t.record('failed take waits for CUT',t.state()==1); t.manager.call_method('CancelTake')")
    run('t.aim(t.prop(1)); t.initial=t.prop(1).get_actor_location()')
    press('IA_Interact')
    check("t.record('E selects the prop',t.player.get_editor_property('HeldProp')==t.prop(1))")
    check("t.start_take(); t.record('ACTION rejects a held prop',t.state()==0)")
    run('t.controller.set_control_rotation(unreal.Rotator(pitch=85,yaw=90,roll=0))')
    press('IA_Interact')
    check("t.record('no surface preserves selection and position',t.player.get_editor_property('HeldProp')==t.prop(1) and t.prop(1).get_actor_location().distance(t.initial)<.1)")
    press('IA_Cancel')
    check("t.record('RMB cancels without moving the prop',t.player.get_editor_property('HeldProp') is None and t.prop(1).get_actor_location().distance(t.initial)<.1)")
    run('t.aim(t.prop(1))');press('IA_Interact')
    run('t.aim_ground(unreal.Vector(-80,-2300,0))');press('IA_Interact')
    check("t.record('free placement outside the goal is allowed',t.player.get_editor_property('HeldProp') is None and not t.inside(1))")
    for scene in range(1,4):
        run(f't.select({scene})')
        for index in [1,2]:
            run(f't.aim(t.prop({index}))');press('IA_Interact')
            check(f"t.record('scene {scene} pickup {index}',t.player.get_editor_property('HeldProp')==t.prop({index}))")
            run(f't.aim_ground(t.area({index}).get_actor_location())')
            check(f"t.record('scene {scene} clear floor allows placement {index}',t.player.get_editor_property('CanPlaceFreely'))")
            press('IA_Interact')
            check(f"t.record('scene {scene} prop {index} inside its radius',t.player.get_editor_property('HeldProp') is None and t.inside({index}))")
        run('t.start_take()')
        time.sleep(2.3)
        check(f"t.record('scene {scene} auto CUT from radius conditions',t.state()==2 and t.manager.get_editor_property('Completed{scene}'))")
        if scene<3:run("t.manager.call_method('AdvanceScene')")
    run("t.manager.call_method('AdvanceScene'); t.player.set_actor_location(unreal.Vector(300,-1750,88),False,True)")
    press('IA_Interact')
    check("t.record('intercom rejects distant input',t.state()==3)")
    run("t.aim(t.manager.get_editor_property('Intercom'))");press('IA_Interact')
    check("t.record('intercom completes the run',t.state()==4 and t.manager.get_editor_property('CompletedCount')==3)")
    print(Path('Saved/GameplayInteractionValidation.json').read_text())


if __name__=='__main__':main()
