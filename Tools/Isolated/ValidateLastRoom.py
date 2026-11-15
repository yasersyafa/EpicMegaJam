"""Run the isolated level in PIE without sending desktop input or saving assets."""
import unreal,time,json,traceback,warnings
warnings.simplefilter('ignore',DeprecationWarning)
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
P=Path(unreal.Paths.project_dir());OUT=P/'Saved/QA/LastRoomValidation.json'
R={'checks':[],'samples':[],'errors':[]};state={'phase':0,'start':0}

def save():OUT.write_text(json.dumps(R,indent=2),encoding='utf-8')
def check(name,value):R['checks'].append({'name':name,'passed':bool(value)});save()
def get(m,n):return m.get_editor_property(n)
def finish():
    R['passed']=all(c['passed'] for c in R['checks']) and not R['errors'];save()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(dt):
    try:
        phase=state['phase']
        if phase==0:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
            state.update(phase=1,start=time.monotonic());return
        elapsed=time.monotonic()-state['start']
        if elapsed>240:raise RuntimeError('Validation timeout')
        w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w:return
        actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
        by={a.get_actor_label():a for a in actors}
        m=by['LastRoom_Manager'];pc=unreal.GameplayStatics.get_player_controller(w,0)
        pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        intro=by['LastRoom_IntroSequence'].get_editor_property('sequence_player')
        q=intro.get_current_time()
        sequence_seconds=q.time.frame_number.value/30.
        if phase in [1,2,3] and sequence_seconds>[3,17,29][phase-1]:
            sample={'time':elapsed,'sequence_seconds':sequence_seconds,'scene':get(m,'SceneIndex'),'state':get(m,'State'),'view':pc.get_view_target().get_actor_label(),'locked':pc.is_move_input_ignored(),'visible_captions':[a.get_actor_label() for a in actors if a.get_actor_label().startswith('Caption_') and not a.get_editor_property('hidden')]}
            R['samples'].append(sample)
            if phase==1:
                check('isolated child player spawns',pawn.get_class().get_name()=='BP_LastRoomPlayer_C')
                check('scene 3 selected',get(m,'SceneIndex')==3)
                check('intro locks movement and look',pc.is_move_input_ignored() and pc.is_look_input_ignored())
                check('ACTION rejected during intro',get(m,'State')==5)
                before=get(m,'TakeCount');m.call_method('RequestActionCut');check('ACTION during intro leaves take count unchanged',get(m,'TakeCount')==before)
                check('interlude caption visible',bool(sample['visible_captions']))
            if phase==2:check('camera cuts to service passage',sample['view']=='Camera_Surya_Approach')
            if phase==3:check('approach caption visible',bool(sample['visible_captions']))
            unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+str(P/f'Saved/QA/LastRoom_{phase}.png').replace('\\','/')+' -nosuffix',pc)
            state['phase']+=1;save()
        elif phase==4 and not intro.is_playing():
            check('intro returns camera to player',pc.get_view_target()==pawn)
            check('intro restores movement and look',not pc.is_move_input_ignored() and not pc.is_look_input_ignored())
            check('intro restores setup state',get(m,'State')==0)
            check('cinematic captions hidden after intro',all(a.get_editor_property('hidden') for a in actors if a.get_actor_label().startswith('Caption_')))
            check('goal guide actors hidden',all(by['LastRoom_'+n+'_Goal'].get_editor_property('hidden') for n in ['Chair','Lamp']))
            check('start layout is not a solution',get(m,'S3Area1').call_method('ContainsProp',(get(m,'S3Prop1'),)) is False)
            # Real placement handlers and collision traces, no synthetic desktop input.
            prop=get(m,'S3Prop1');camera=pawn.get_editor_property('FirstPersonCamera')
            pawn.set_actor_location(unreal.Vector(50,220,88),False,True)
            target=prop.get_actor_location()+unreal.Vector(0,0,45)
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),target))
            pawn.call_method('RefreshFreePlacement');pawn.call_method('TryFreeInteract')
            check('E handler selects chair',pawn.get_editor_property('HeldProp')==prop)
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),unreal.Vector(350,100,0)))
            pawn.call_method('RefreshFreePlacement')
            check('clear floor provides free-placement candidate',pawn.get_editor_property('CanPlaceFreely'))
            pawn.call_method('TryFreeInteract')
            check('E handler commits a free placement',pawn.get_editor_property('HeldProp') is None)
            check('placement outside solution is permitted',not get(m,'S3Area1').call_method('ContainsProp',(prop,)))
            pawn.call_method('CancelFreePlacement')
            # Verify deterministic puzzle outcomes in this new map.
            m.set_editor_property('SimulatorEnabled',False)
            for i in [1,2]:
                prop=get(m,'S3Prop'+str(i));area=get(m,'S3Area'+str(i))
                origin,extent=prop.get_actor_bounds(True)
                prop.set_actor_location(area.get_actor_location()+(prop.get_actor_location()-origin)+unreal.Vector(0,0,extent.z+.5),False,True)
            pawn.set_actor_location(get(m,'S3DirectorMark').get_actor_location()+unreal.Vector(0,0,88),False,True)
            m.call_method('StartTake');check('reference solution produces perfect outcome',get(m,'State')==1 and get(m,'Outcome')==0)
            m.call_method('CancelTake');check('CUT returns to setup',get(m,'State')==0 and not pc.is_move_input_ignored())
            m.call_method('RestartScene');check('reset restores chair and lamp',all(get(m,'S3Prop'+str(i)).get_actor_location().distance(get(m,'S3Start'+str(i)).get_actor_location())<.1 for i in [1,2]))
            unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+str(P/'Saved/QA/LastRoom_Gameplay.png').replace('\\','/')+' -nosuffix',pc)
            state['phase']=5;state['done_at']=elapsed;save()
        elif phase==5 and elapsed>state['done_at']+2:finish()
    except Exception:
        R['errors'].append(traceback.format_exc());finish()

unreal.EditorLoadingAndSavingUtils.load_map('/Game/Game/Isolated/IbraLastRoom/L_Interlude02_LastRoom')
save();handle=unreal.register_slate_post_tick_callback(tick)
