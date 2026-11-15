"""Import the Blender Maya package into an isolated skeleton; run in Unreal Editor."""
import unreal,sys
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
sys.path.insert(0,str(ROOT/'Tools/Characters'))
from character_paths import ART_ROOT
SRC=ART_ROOT/'Maya'
DEST='/Game/Game/Characters/Maya'
def task(filename,name,options):
 t=unreal.AssetImportTask();t.filename=str(SRC/filename);t.destination_path=DEST+('/Animations' if name.startswith('A_') else '');t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True;t.options=options
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
 assert t.imported_object_paths, 'Import failed: '+filename
 print('IMPORTED',t.imported_object_paths)
 return unreal.load_asset(t.imported_object_paths[0])
old=unreal.SystemLibrary.get_console_variable_int_value('Interchange.FeatureFlags.Import.FBX')
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
try:
 ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;ui.import_as_skeletal=True;ui.import_mesh=True;ui.import_animations=False;ui.import_materials=False;ui.import_textures=False;ui.create_physics_asset=False
 data=ui.skeletal_mesh_import_data;data.set_editor_property('use_t0_as_ref_pose',False);data.set_editor_property('update_skeleton_reference_pose',True);data.convert_scene=True;data.convert_scene_unit=True;data.force_front_x_axis=False
 mesh=task('SK_Maya_Polished.fbx','SK_Maya',ui)
 assert isinstance(mesh,unreal.SkeletalMesh)
 materials=mesh.get_editor_property('materials');slot=materials[0];slot.set_editor_property('material_interface',unreal.load_asset('/Game/Game/Characters/Maya/Materials/MI_Maya') or unreal.load_asset('/Game/Characters/Tripo/Maya/M_Maya'));materials[0]=slot;mesh.set_editor_property('materials',materials)
 sk=mesh.get_editor_property('skeleton')
 for n in ['Idle','Walk','LookAround','LookAtDirector','Hesitate','Inspect','Surprised','Waiting','Turn','ReadScript','WalkWithScript','Confession','TurnLeft','TurnRight']:
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;ui.import_as_skeletal=True;ui.import_mesh=False;ui.import_animations=True;ui.import_materials=False;ui.import_textures=False;ui.skeleton=sk
  d=ui.anim_sequence_import_data;d.convert_scene=True;d.convert_scene_unit=True;d.import_uniform_scale=1;d.set_editor_property('use_default_sample_rate',False);d.set_editor_property('custom_sample_rate',30)
  anim=task('A_Maya_'+n+'.fbx','A_Maya_'+n,ui)
  assert isinstance(anim,unreal.AnimSequence)
  anim.set_editor_property('enable_root_motion',False)
  # Legacy FBX animation import strips armature object scale. Restore the bind root.
  ref=sk.get_reference_pose().get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
  controller=anim.get_editor_property('controller')
  assert controller.set_bone_track_keys('root',[ref.translation],[ref.rotation],[ref.scale3d]), 'Root normalization failed'
  unreal.EditorAssetLibrary.save_loaded_asset(anim, False)
 unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
 unreal.EditorAssetLibrary.save_loaded_asset(sk, False)
 print('MAYA_IMPORT_COMPLETE',mesh.get_bounds())
finally:
 unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX '+str(old))
