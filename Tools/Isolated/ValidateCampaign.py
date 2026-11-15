"""Accelerated, muted PIE regression through the complete isolated campaign.

Invokes Blueprint handlers and real placement traces; no desktop input, no asset saves.
"""
import unreal,time,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());OUT=P/'Saved/QA/CampaignValidation.json'
R={'checks':[],'beats':[],'errors':[],'method':'Muted background PIE; Blueprint input handlers; narrative playback accelerated after opening sample.'}
S={'phase':'boot','started':time.monotonic(),'scene':1,'seen':set(),'opening_shot':False}

def save():OUT.write_text(json.dumps(R,indent=2),encoding='utf-8')
def check(name,ok):R['checks'].append({'name':name,'passed':bool(ok)});save();return bool(ok)
def get(m,n):return m.get_editor_property(n)
def call(m,n,*args):return m.call_method(n,args)
def marker(m,pawn):pawn.set_actor_location(get(m,'ActiveDirectorMark').get_actor_location()+unreal.Vector(0,0,88),False,True)
def place(m,index,inside=True):
    p=get(m,'ActiveProp'+str(index));a=get(m,'ActiveArea'+str(index));origin,extent=p.get_actor_bounds(True)
    p.set_actor_location(a.get_actor_location()+(p.get_actor_location()-origin)+unreal.Vector(0,0,extent.z+.5)+(unreal.Vector() if inside else unreal.Vector(300,0,0)),False,True)
def shot(world,pc,name):unreal.SystemLibrary.execute_console_command(world,'Shot ShowUI filename='+str((P/'Saved/QA'/('Campaign_'+name+'.png')).resolve()).replace('\\','/')+' -nosuffix',pc)
def end():
    R['passed']=not R['errors'] and all(c['passed'] for c in R['checks']);R['real_seconds']=round(time.monotonic()-S['started'],2);save()
    unreal.unregister_slate_post_tick_callback(handle)
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w:unreal.GameplayStatics.set_global_time_dilation(w,1.)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()

def tick(dt):
    try:
        if time.monotonic()-S['started']>300:raise RuntimeError('Campaign validation timed out: '+str(S))
        if S['phase']=='boot':
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play();S['phase']='menu';return
        w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w:return
        actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);by={a.get_actor_label():a for a in actors}
        m=by.get('CAMPAIGN_Director');pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        if not m or not pawn:return
        seq=get(m,'SequencePlayer');pending=get(m,'PendingStep')
        if get(m,'NeedPoll') and pending not in S['seen']:
            S['seen'].add(pending);R['beats'].append({'step':pending,'scene':get(m,'SceneIndex'),'state':get(m,'State')});save()
        if seq and seq.is_playing() and S['phase']!='opening':seq.set_play_rate(12. if pending!=18 else 1.)
        phase=S['phase'];scene=S['scene']
        if phase=='menu':
            if time.monotonic()-S['started']<2:return
            check('main menu is initial state',get(m,'State')==7)
            check('campaign player spawns',pawn.get_class().get_name()=='BP_CampaignPlayer_C')
            check('campaign HUD spawns',pc.get_hud().get_class().get_name()=='BP_CampaignHUD_C')
            shot(w,pc,'Menu');call(m,'RequestActionCut');S['phase']='opening'
        elif phase=='opening':
            if seq and seq.get_current_time().time.frame_number.value>90:
                check('opening locks movement and look',pc.is_move_input_ignored() and pc.is_look_input_ignored())
                check('opening has synchronized caption',bool(get(m,'SubtitleText')))
                check('opening uses master confession camera',pc.get_view_target()==by['CAMPAIGN_MasterConfession'])
                call(m,'TogglePause');check('pause suspends active sequence',unreal.GameplayStatics.is_game_paused(w) and not seq.is_playing());call(m,'TogglePause');check('resume continues active sequence',not unreal.GameplayStatics.is_game_paused(w) and seq.is_playing())
                count=get(m,'TakeCount');call(m,'RequestActionCut');check('ACTION ignored during narrative',get(m,'TakeCount')==count)
                shot(w,pc,'Opening');seq.set_play_rate(12.);S['phase']='wait_setup'
        elif phase=='wait_setup' and get(m,'State')==0 and get(m,'SceneIndex')==scene:
            check(f'scene {scene} has controllable setup',not pc.is_move_input_ignored() and not pc.is_look_input_ignored())
            check(f'scene {scene} completion count on entry',get(m,'CompletedCount')==scene-1)
            check(f'scene {scene} starts unsolved',not get(m,'ActiveArea1').call_method('ContainsProp',(get(m,'ActiveProp1'),)))
            call(m,'ToggleNotes');check(f'scene {scene} notes open',get(m,'NotesVisible') and bool(get(m,'NotesText')));call(m,'ToggleNotes')
            # Actual camera trace and E-handler pickup/commit, including placement outside solution.
            pickup={1:(-350,140,88),2:(710,1100,88),3:(1250,1410,88)}[scene]
            stand={1:(300,100,88),2:(1200,-400,88),3:(1120,1330,88)}[scene]
            target={1:(80,-100,0),2:(1000,-700,0),3:(1420,1350,0)}[scene]
            prop=get(m,'ActiveProp1');pawn.set_actor_location(unreal.Vector(*pickup),False,True)
            origin,extent=prop.get_actor_bounds(True);camera=pawn.get_editor_property('FirstPersonCamera')
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),origin))
            call(pawn,'RefreshFreePlacement');call(pawn,'TryFreeInteract')
            check(f'scene {scene} trace E selects prop',pawn.get_editor_property('HeldProp')==prop)
            marker(m,pawn);count=get(m,'TakeCount');call(m,'StartTake')
            check(f'scene {scene} ACTION rejects held prop',get(m,'State')==0 and get(m,'TakeCount')==count)
            pawn.set_actor_location(unreal.Vector(*stand),False,True);pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),unreal.Vector(*target)))
            call(pawn,'RefreshFreePlacement');check(f'scene {scene} clear floor permits placement',pawn.get_editor_property('CanPlaceFreely'))
            call(pawn,'TryFreeInteract');check(f'scene {scene} E commits free placement',pawn.get_editor_property('HeldProp') is None)
            check(f'scene {scene} outside-goal placement allowed',not get(m,'ActiveArea1').call_method('ContainsProp',(prop,)))
            call(pawn,'CancelFreePlacement');call(m,'ResetScene')
            check(f'scene {scene} reset restores both props',all(get(m,'ActiveProp'+str(i)).get_actor_location().distance(get(m,f'S{scene}Start{i}').get_actor_location())<.1 for i in [1,2]))
            marker(m,pawn);count=get(m,'TakeCount')
            pawn.set_actor_location(get(m,'ActiveDirectorMark').get_actor_location()+unreal.Vector(600,0,88),False,True);call(m,'StartTake')
            check(f'scene {scene} ACTION rejects off-mark',get(m,'State')==0 and get(m,'TakeCount')==count)
            marker(m,pawn);call(m,'StartTake');check(f'scene {scene} first failure selected',get(m,'State')==1 and get(m,'Outcome')==1)
            check(f'scene {scene} take locks movement',pc.is_move_input_ignored());S['phase']='fail1'
        elif phase=='fail1' and get(m,'State')==1 and not get(m,'NeedPoll'):
            check(f'scene {scene} failed take waits for player CUT',get(m,'WaitingForCut') and get(m,'CompletedCount')==scene-1)
            shot(w,pc,f'S{scene}_Failure');S['sample_at']=time.monotonic();S['phase']='fail1cut'
        elif phase=='fail1cut' and time.monotonic()-S['sample_at']>.5:
            positions=[get(m,'ActiveProp'+str(i)).get_actor_location() for i in [1,2]]
            call(m,'CancelTake')
            check(f'scene {scene} CUT preserves props',all(get(m,'ActiveProp'+str(i)).get_actor_location().distance(positions[i-1])<.1 for i in [1,2]))
            check(f'scene {scene} CUT restores controls',get(m,'State')==0 and not pc.is_move_input_ignored() and not pc.is_look_input_ignored())
            check(f'scene {scene} CUT resets Maya',get(m,'Maya').get_actor_location().distance(get(m,'ActiveMayaStart').get_actor_location())<.1)
            call(m,'TogglePause');check(f'scene {scene} pause works',unreal.GameplayStatics.is_game_paused(w));call(m,'TogglePause')
            place(m,1);marker(m,pawn);call(m,'StartTake');check(f'scene {scene} second failure selected',get(m,'State')==1 and get(m,'Outcome')==2);S['phase']='fail2'
        elif phase=='fail2' and get(m,'State')==1 and not get(m,'NeedPoll'):
            check(f'scene {scene} second failure also waits for CUT',get(m,'WaitingForCut'))
            call(m,'CancelTake');place(m,2);marker(m,pawn);call(m,'StartTake')
            check(f'scene {scene} correct arrangement selects perfect take',get(m,'Outcome')==0 and get(m,'State')==1)
            check(f'scene {scene} success not granted before performance',get(m,'CompletedCount')==scene-1)
            call(m,'CancelTake');call(m,'OnClipFinished')
            check(f'scene {scene} early CUT and stale finish do not complete scene',get(m,'State')==0 and get(m,'CompletedCount')==scene-1)
            if scene==1:
                for i in range(20):call(m,'StartTake');call(m,'CancelTake')
                check('20 consecutive retakes restore controls',get(m,'State')==0 and not pc.is_move_input_ignored() and not pc.is_look_input_ignored())
            marker(m,pawn);call(m,'StartTake');S['phase']='transition'
        elif phase=='transition':
            if scene<3 and get(m,'State')==0 and get(m,'SceneIndex')==scene+1:
                check(f'scene {scene} completes exactly once',get(m,'CompletedCount')==scene)
                check(f'scene {scene} gate opens',not get(m,'Gate'+str(scene)).get_actor_enable_collision())
                S['scene']+=1;S['phase']='wait_setup'
            elif scene==3 and get(m,'State')==3:
                check('three scenes reach final intercom objective',get(m,'CompletedCount')==3 and all(get(m,'Completed'+str(i)) for i in [1,2,3]))
                pawn.set_actor_location(unreal.Vector(1200,500,88),False,True);call(m,'Interact');check('intercom rejects distant interaction',get(m,'State')==3)
                pawn.set_actor_location(get(m,'Intercom').get_actor_location()+unreal.Vector(100,0,-37),False,True)
                prop=get(m,'ActiveProp1');pawn.set_actor_location(unreal.Vector(1230,1450,88),False,True)
                origin,extent=prop.get_actor_bounds(True);camera=pawn.get_editor_property('FirstPersonCamera');pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),origin));call(pawn,'RefreshFreePlacement');call(pawn,'TryFreeInteract')
                pawn.set_actor_location(get(m,'Intercom').get_actor_location()+unreal.Vector(100,0,-37),False,True)
                check('final objective prop can be selected for held guard',pawn.get_editor_property('HeldProp')==prop)
                call(m,'Interact');check('intercom rejects a held prop',get(m,'State')==3);call(pawn,'CancelFreePlacement')
                call(m,'Interact');check('intercom starts final pickup',get(m,'State')==5 and get(m,'PendingStep')==15);S['phase']='final'
        elif phase=='final':
            if pending==15 and seq and seq.get_current_time().time.frame_number.value>45 and not S.get('pickup_shot'):
                check('final pickup shows only one Maya',by['CAMPAIGN_Maya'].get_editor_property('hidden') and not by['CAMPAIGN_ConfessionMaya'].get_editor_property('hidden'));S['pickup_shot']=True
            if pending==18 and seq and seq.get_current_time().time.frame_number.value>220 and not S.get('reveal_shot'):
                filmback=by['CAMPAIGN_MasterConfession'].get_cine_camera_component().get_editor_property('filmback')
                check('final reveal expands the same camera crop',filmback.sensor_width>80)
                check('final reveal shows four end poses',all(not by['CAMPAIGN_FinalPose'+str(i)].get_editor_property('hidden') for i in range(4)))
                fade_tracks=[t for t in get(m,'Clip_Reveal').get_tracks() if isinstance(t,unreal.MovieSceneFadeTrack)]
                check('reveal explicitly clears the black ellipsis fade',bool(fade_tracks) and all(abs(s.get_all_channels()[0].get_default())<.01 for t in fade_tracks for s in t.get_sections()))
                shot(w,pc,'Reveal');S['reveal_shot']=True
            if get(m,'State')==6:
                check('ending reaches credits',True);shot(w,pc,'Credits');unreal.GameplayStatics.set_global_time_dilation(w,10.);S['phase']='credits'
        elif phase=='credits' and get(m,'State')==7:
            check('credits return to main menu',True);unreal.GameplayStatics.set_global_time_dilation(w,1.);call(m,'RequestActionCut');S['phase']='replay'
        elif phase=='replay' and pending==0 and seq and seq.get_current_time().time.frame_number.value>40:
            check('replay clears progression',get(m,'CompletedCount')==0 and not any(get(m,'Completed'+str(i)) for i in [1,2,3]))
            fb=by['CAMPAIGN_MasterConfession'].get_cine_camera_component().get_editor_property('filmback');check('replay restores close-up crop',abs(fb.sensor_width-36)<.1)
            check('all narrative continuation steps exercised',set(range(19)).issubset(S['seen']))
            end()
    except Exception:
        R['errors'].append(traceback.format_exc());end()

save();handle=unreal.register_slate_post_tick_callback(tick)
