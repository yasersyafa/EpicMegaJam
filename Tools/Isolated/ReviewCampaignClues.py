"""Capture the actual success-shot clues; no desktop input or asset changes."""
import unreal,time,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());R={'shots':[],'errors':[]};S={'phase':0,'scene':1,'started':time.monotonic()}
def save():(P/'Saved/QA/CampaignClueReview.json').write_text(json.dumps(R,indent=2))
def finish():
    save();unreal.unregister_slate_post_tick_callback(handle);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
def tick(dt):
    try:
        if time.monotonic()-S['started']>70:raise RuntimeError('Review timeout')
        if S['phase']==0:unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play();S['phase']=1;return
        w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w:return
        m=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_actor_label()=='CAMPAIGN_Director')
        pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0)
        if not pawn:return
        if S['phase']==1:
            m.set_editor_property('SceneIndex',S['scene']);m.call_method('ConfigureScene')
            for i in [1,2]:
                p=m.get_editor_property('ActiveProp'+str(i));a=m.get_editor_property('ActiveArea'+str(i));origin,extent=p.get_actor_bounds(True);p.set_actor_location(a.get_actor_location()+p.get_actor_location()-origin+unreal.Vector(0,0,extent.z+.5),False,True)
            pawn.set_actor_location(m.get_editor_property('ActiveDirectorMark').get_actor_location()+unreal.Vector(0,0,88),False,True);m.call_method('StartTake');S['phase']=2
        elif S['phase']==2:
            seq=m.get_editor_property('SequencePlayer')
            if seq and seq.get_current_time().time.frame_number.value>seq.get_duration().time.frame_number.value*.72:
                seq.pause();m.set_editor_property('NeedPoll',False);S['hold']=time.monotonic();S['phase']=3
        elif S['phase']==3 and time.monotonic()-S['hold']>.5:
            path=str((P/'Saved/QA'/f'Campaign_Clue{S["scene"]}.png').resolve()).replace('\\','/')
            unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+path+' -nosuffix',pc);R['shots'].append(path);save();S['hold']=time.monotonic();S['phase']=4
        elif S['phase']==4 and time.monotonic()-S['hold']>.5:
            m.call_method('ReleasePlayer')
            if S['scene']==1:S['scene']=2;S['phase']=1
            else:finish()
    except Exception:R['errors'].append(traceback.format_exc());finish()
save();handle=unreal.register_slate_post_tick_callback(tick)
