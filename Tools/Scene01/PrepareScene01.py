"""Run inside editor, without PIE or asset-editor windows."""
import unreal, json, hashlib, shutil, os
P=unreal.Paths.project_dir(); E=unreal.EditorAssetLibrary
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
assert not E.does_asset_exist('/Game/Game/Blueprints/Scene01/BP_Scene01FlowDirector'),'Integration already exists; refusing to replace the level'
out=P+'Saved/Scene01Build/';os.makedirs(out,exist_ok=True)
baseline={}
for root,dirs,files in os.walk(P+'Content'):
 for f in files:
  path=os.path.join(root,f)
  if f.endswith(('.uasset','.umap')) and f!='L_Scene01.umap':baseline[os.path.relpath(path,P)]=hashlib.sha256(open(path,'rb').read()).hexdigest()
for root,dirs,files in os.walk(P+'Config'):
 for f in files:
  path=os.path.join(root,f);baseline[os.path.relpath(path,P)]=hashlib.sha256(open(path,'rb').read()).hexdigest()
json.dump(baseline,open(out+'protected_hashes.json','w'),indent=2)
target=P+'Content/Game/Levels/Tests/L_Scene01.umap'
if os.path.exists(target):shutil.copy2(target,out+'L_Scene01.before-integration.umap')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Game/Levels/SB_GrayBox')
assert unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),'/Game/Game/Levels/Tests/L_Scene01')
assert level.load_level('/Game/Game/Levels/Tests/L_Scene01')
copies={
 '/Game/Game/Blueprints/Flow/BP_ArrivalDirector':'/Game/Game/Blueprints/Scene01/BP_Scene01ArrivalDirector',
 '/Game/Game/UI/Scene01/WBP_Scene01Objective':'/Game/Game/UI/Scene01/Integration/WBP_Scene01Objective',
 '/Game/Game/Blueprints/Gameplay/Testing/BP_FreePlacementPlayerBase':'/Game/Game/Blueprints/Scene01/BP_Scene01Player',
 '/Game/Game/Blueprints/Gameplay/Testing/ABP_FreePlacementPlayer':'/Game/Game/Blueprints/Scene01/ABP_Scene01Player',
 '/Game/Game/Blueprints/Player/BP_PlayerController':'/Game/Game/Blueprints/Scene01/BP_Scene01Controller',
 '/Game/Game/Cinematics/Opening/LS_Opening_Maya':'/Game/Game/Cinematics/Scene01/LS_Scene01Opening',
}
for source,dest in copies.items():
 assert not E.does_asset_exist(dest),dest
 assert E.duplicate_asset(source,dest),dest
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
json.dump([{'label':a.get_actor_label(),'class':a.get_class().get_name(),'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation())} for a in actors],open(out+'source_actors.json','w'),indent=2)
assert level.save_current_level()
unreal.log('SCENE01_PREPARED_BACKGROUND_ONLY; no tests run')
