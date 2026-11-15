"""Import the reviewed grip, turn and camera-facing performance without changing the rig."""
import unreal,sys,shutil
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
sys.path.insert(0,str(ROOT/'Tools/Characters'))
from character_paths import ART_ROOT
review=ART_ROOT/'PolishReview';source=ART_ROOT/'Maya'
for name in ['ReadScript','WalkWithScript','TurnLeft','TurnRight','Confession']:
 shutil.copy2(review/('A_Maya_'+name+'.fbx'),source/('A_Maya_'+name+'.fbx'))
shutil.copy2(review/'Maya_Polish_v2.blend',source/'Maya_Performance.blend')
skeleton=unreal.load_asset('/Game/Game/Characters/Maya/SK_Maya_Skeleton')
ref=skeleton.get_reference_pose().get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
assert ref.scale3d.distance(unreal.Vector(1,1,1))<.001
old=unreal.SystemLibrary.get_console_variable_int_value('Interchange.FeatureFlags.Import.FBX');unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
try:
 for name in ['ReadScript','WalkWithScript','TurnLeft','TurnRight','Confession']:
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;ui.import_mesh=False;ui.import_animations=True;ui.import_materials=False;ui.import_textures=False;ui.skeleton=skeleton
  data=ui.anim_sequence_import_data;data.convert_scene=True;data.convert_scene_unit=True;data.set_editor_property('use_default_sample_rate',False);data.set_editor_property('custom_sample_rate',30)
  task=unreal.AssetImportTask();task.filename=str(source/('A_Maya_'+name+'.fbx'));task.destination_path='/Game/Game/Characters/Maya/Animations';task.destination_name='A_Maya_'+name;task.automated=True;task.replace_existing=True;task.save=True;task.options=ui
  unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
  anim=unreal.load_asset(task.imported_object_paths[0]);assert anim.get_editor_property('skeleton')==skeleton
  assert anim.get_editor_property('controller').set_bone_track_keys('root',[ref.translation],[ref.rotation],[ref.scale3d])
  anim.set_editor_property('enable_root_motion',False);unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
  print('REVIEW_ANIMATION_IMPORTED',name)
finally:unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX '+str(old))
