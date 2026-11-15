"""Import the crew package; all three meshes use one Animation Blueprint skeleton."""
import unreal,sys,json
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
sys.path.insert(0,str(ROOT/'Tools/Characters'))
from character_paths import ART_ROOT
SRC=ART_ROOT/'Crew';DEST='/Game/Game/Characters/Crew'
def run(file,name,ui):
 t=unreal.AssetImportTask();t.filename=str(SRC/file);t.destination_path=DEST+('/Animations' if name.startswith('A_') else '');t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True;t.options=ui
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths,(file,'import failed')
 return unreal.load_asset(t.imported_object_paths[0])
old=unreal.SystemLibrary.get_console_variable_int_value('Interchange.FeatureFlags.Import.FBX')
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
try:
 skeleton=None
 for n in ['Utility','A','B']:
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;ui.import_as_skeletal=True;ui.import_mesh=True;ui.import_animations=False;ui.import_materials=False;ui.import_textures=False;ui.create_physics_asset=False
  if skeleton:ui.skeleton=skeleton
  d=ui.skeletal_mesh_import_data;d.set_editor_property('use_t0_as_ref_pose',False);d.set_editor_property('update_skeleton_reference_pose',skeleton is None);d.convert_scene=True;d.convert_scene_unit=True
  mesh=run('SK_Crew_'+n+'.fbx',{'Utility':'SK_Crew_Base','A':'SK_Crew_Camera','B':'SK_Crew_Boom'}[n],ui)
  if not skeleton:skeleton=mesh.get_editor_property('skeleton')
  assert mesh.get_editor_property('skeleton')==skeleton
  materials=mesh.get_editor_property('materials');slot=materials[0];slot.set_editor_property('material_interface',unreal.load_asset('/Game/Characters/Tripo/Crew/MI_Crew_'+n));materials[0]=slot;mesh.set_editor_property('materials',materials)
  unreal.EditorAssetLibrary.save_loaded_asset(mesh, False);print('CREW MESH',n,mesh.get_bounds())
 ref=skeleton.get_reference_pose().get_bone_pose('root',unreal.AnimPoseSpaces.LOCAL)
 for n in ['Idle','Walk','Focused']:
  ui=unreal.FbxImportUI();ui.automated_import_should_detect_type=False;ui.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;ui.import_mesh=False;ui.import_animations=True;ui.import_materials=False;ui.import_textures=False;ui.skeleton=skeleton
  d=ui.anim_sequence_import_data;d.convert_scene=True;d.convert_scene_unit=True;d.set_editor_property('use_default_sample_rate',False);d.set_editor_property('custom_sample_rate',30)
  a=run('A_Crew_'+n+'.fbx','A_Crew_'+n,ui);a.get_editor_property('controller').set_bone_track_keys('root',[ref.translation],[ref.rotation],[ref.scale3d]);a.set_editor_property('enable_root_motion',False)
  unreal.EditorAssetLibrary.save_loaded_asset(a, False);print('CREW ANIM',n)
 parts=[];names=skeleton.get_reference_pose().get_bone_names()
 for i,bone in enumerate(skeleton.get_editor_property('bone_tree')):
  mode=unreal.BoneTranslationRetargetingMode.ANIMATION if str(names[i])=='root' else unreal.BoneTranslationRetargetingMode.ANIMATION_SCALED if str(names[i])=='pelvis' else unreal.BoneTranslationRetargetingMode.SKELETON
  bone.set_editor_property('translation_retargeting_mode',mode);parts.append(bone.export_text())
 payload={'path':skeleton.get_path_name(),'property':'BoneTree','value':'('+','.join(parts)+')'}
 (ROOT/'Saved/CharacterPolish/crew_bone_tree.json').write_text(json.dumps(payload))
 unreal.EditorAssetLibrary.save_loaded_asset(skeleton, False)
finally:unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX '+str(old))
