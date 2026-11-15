"""Read-only final package and scene checks, then leave the test map ready."""
from GameplayBridge import call,python
from BuildGameplaySystems import MANAGER,PLAYER,HUD,MODE
import json,hashlib
from pathlib import Path

print(python("import unreal; assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None; unreal.EditorLoadingAndSavingUtils.load_map('/Game/Game/Levels/Tests/L_GameplaySystems'); a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(); m=next(x for x in a if x.get_actor_label()=='SYSTEM_GameplayTestManager'); assert all(m.get_editor_property('S'+str(s)+'Prop'+str(p)) is not None for s in range(1,4) for p in range(1,3)); texts=[x for x in a if isinstance(x,unreal.TextRenderActor)]; assert all(abs(x.get_actor_rotation().yaw-180)<.01 and abs(x.get_actor_rotation().pitch)<.01 and abs(x.get_actor_rotation().roll)<.01 for x in texts); assert unreal.get_default_object(unreal.load_asset('/Game/Game/Blueprints/Gameplay/Testing/BP_GameplayTestMode').generated_class()).get_editor_property('default_pawn_class')==unreal.load_class(None,'/Game/Game/Blueprints/Gameplay/Testing/BP_GameplayPlayer.BP_GameplayPlayer_C'); unreal.get_editor_subsystem(unreal.EditorActorSubsystem).set_selected_level_actors([m]); unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(-250,-800,1600),unreal.Rotator(-35,20,0)); print('MAP_REFERENCES_AND_TEXT_ROTATIONS_VERIFIED '+str(len(texts)))"))
compiles={}
for path in [PLAYER,MANAGER,HUD,MODE]:
    result=call('compile_blueprint',path=path)
    assert result['success'] and result['errorCount']==0 and result['warningCount']==0,result
    compiles[path]=result
    call('save_blueprint',path=path)
python("import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()")
Path('Saved/GameplaySystemsFinalCompile.json').write_text(json.dumps(compiles,indent=2))
baseline=json.loads(Path('Saved/GameplaySystemsBuild/protected_hashes.json').read_text())
changed=[name for name,digest in baseline.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
assert not changed,changed
Path('Saved/GameplaySystemsIsolation.json').write_text(json.dumps({'protected_files':len(baseline),'changed':changed},indent=2))
print('COMPILE_AND_ISOLATION_VERIFIED')
