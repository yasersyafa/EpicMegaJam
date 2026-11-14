"""Run focused state-machine checks against live PIE, without saving test changes."""
import unreal
import json
import os
import traceback

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
by_name={a.get_actor_label():a for a in actors}
manager=by_name['SYSTEM_GameplayTestManager']
player=manager.get_editor_property('Player')
controller=manager.get_editor_property('Controller')
result={'checks':[],'errors':[]}


def check(name,condition):
    result['checks'].append({'name':name,'passed':bool(condition)})
    assert condition,name


def get(name):return manager.get_editor_property(name)
def invoke(name,*args):
    # These checks exercise the take loop. The dedicated FunctionalTest covers
    # ACTION rejection away from the director mark.
    if name=='StartTake' or (name=='RequestActionCut' and get('State')==0):
        mark=get('ActiveDirectorMark')
        player.set_actor_location(mark.get_actor_location()+unreal.Vector(0,0,88),False,True)
    return manager.call_method(name,args)


def place(scene,index,slot):
    prop=get(f'S{scene}Prop{index}')
    names={1:['Sofa','Wardrobe'],2:['Cabinet','Lamp'],3:['Chair','Lamp']}
    target=by_name[f'S{scene:02d}_{names[scene][index-1]}_Snap_{slot}']
    prop.set_actor_location(target.get_actor_location(),False,True)
    prop.set_editor_property('CurrentSlotID',unreal.Name(f'S{scene}_P{index}_{slot}'))


try:
    check('test player and HUD spawn',player is not None and controller.get_hud().get_class().get_name()=='BP_TestHUD_C')
    manager.set_editor_property('SimulatorEnabled',False)
    for scene in range(1,4):
        invoke('SelectScene'+str(scene))
        for slot1,slot2,expected in [('A','A',1),('B','A',2),('A','C',1),('B','C',0)]:
            place(scene,1,slot1);place(scene,2,slot2)
            invoke('StartTake')
            check(f'scene {scene} slots {slot1}/{slot2}',get('State')==1 and get('Outcome')==expected)
            check('movement locks during take',controller.is_move_input_ignored())
            before=[get(f'S{scene}Prop{i}').get_actor_location() for i in [1,2]]
            invoke('CancelTake')
            check('CUT keeps committed positions',all(get(f'S{scene}Prop{i}').get_actor_location().distance(before[i-1])<.1 for i in [1,2]))
            check('CUT restores movement',get('State')==0 and not controller.is_move_input_ignored())
    invoke('SelectScene1');invoke('RestartScene')
    invoke('SetHeldProp',get('ActiveProp1'))
    count=get('TakeCount');invoke('StartTake')
    check('ACTION rejects a held prop',get('State')==0 and get('TakeCount')==count)
    invoke('SetHeldProp',None)
    for i in range(20):
        invoke('RequestActionCut');invoke('RequestActionCut')
        check(f'retake cycle {i+1}',get('State')==0 and not controller.is_move_input_ignored())
    place(1,1,'B');place(1,2,'C');invoke('StartTake');old=get('TakeID');invoke('CancelTake');invoke('StartTake')
    invoke('NotifyTakeFinished',old)
    check('stale completion ignored',get('State')==1 and get('CompletedCount')==0)
    invoke('NotifyTakeFinished',get('TakeID'))
    check('perfect take completes',get('State')==2 and get('CompletedCount')==1)
    invoke('NotifyTakeFinished',get('TakeID'));invoke('CompleteScene')
    check('duplicate completion ignored',get('CompletedCount')==1)
    invoke('RestartScene')
    check('restart clears current completion only',get('State')==0 and not get('Completed1') and get('CompletedCount')==0)
    check('restart restores initial slot IDs',str(get('ActiveProp1').get_editor_property('CurrentSlotID'))=='S1_P1_A')
    invoke('ToggleNotes');check('notes open',get('NotesVisible') and 'SCENE 1' in get('NotesText'));invoke('ToggleNotes')
    invoke('TogglePause');check('pause activates',unreal.GameplayStatics.is_game_paused(world));invoke('TogglePause');check('pause resumes',not unreal.GameplayStatics.is_game_paused(world))
    # Walk progression through all three scenes using the public completion input.
    for scene in range(1,4):
        place(scene,1,'B');place(scene,2,'C');invoke('StartTake');invoke('NotifyTakeFinished',get('TakeID'))
        check(f'scene {scene} completion',get('CompletedCount')==scene and get('State')==2)
        invoke('AdvanceScene')
    check('final intercom objective',get('State')==3)
    player.set_actor_location(unreal.Vector(300,-1750,100),False,True);invoke('InteractIntercom')
    check('intercom rejects distant use',get('State')==3)
    player.set_actor_location(get('Intercom').get_actor_location()+unreal.Vector(100,0,0),False,True);invoke('InteractIntercom')
    check('intercom ends systems run',get('State')==4)
    invoke('InteractIntercom');check('intercom repeats safely',get('State')==4)
    invoke('SelectScene1');invoke('RestartScene')
    manager.set_editor_property('SimulatorEnabled',True)
    result['passed']=True
except Exception:
    result['errors'].append(traceback.format_exc());result['passed']=False
finally:
    with open(os.path.join(unreal.Paths.project_saved_dir(),'GameplaySystemsValidation.json'),'w') as f:json.dump(result,f,indent=2)
    unreal.log('GAMEPLAY_SYSTEMS_VALIDATION '+json.dumps({'passed':result.get('passed'),'checks':len(result['checks']),'errors':result['errors']}))
