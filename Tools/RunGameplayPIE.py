from GameplayBridge import call, python
import sys
if 'start' in sys.argv:
    print(call('start_pie',numPlayers=1,listenServer=False))
elif 'stop' in sys.argv:
    print(call('stop_pie'))
else:
    print(python("import unreal; w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); print(w); m=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_actor_label()=='SYSTEM_GameplayTestManager'); print([(n,str(m.get_editor_property(n))) for n in ['State','SceneIndex','Player','Controller','ActiveProp1','ActiveProp2','StatusText']]); print(unreal.GameplayStatics.get_player_controller(w,0).get_hud())"))
