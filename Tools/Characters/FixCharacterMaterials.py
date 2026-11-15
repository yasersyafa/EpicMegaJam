"""Repair persistent material slots and apply Maya's UV-compatible texture update."""
import unreal,sys,shutil
from pathlib import Path
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
sys.path.insert(0,str(ROOT/'Tools/Characters'))
from character_paths import ART_ROOT
source=Path(r'C:/Users/ASUS TUF/Downloads/tripo_convert_19286742-5274-43b6-9671-6c476cd166c1/tripo_convert_19286742-5274-43b6-9671-6c476cd166c1.fbm/tripo_rgb_ca58f5ba-7ab6-46b0-9786-5e57ba7b6d6e.jpg')
stable=ART_ROOT/'Maya/Textures/Maya_BaseColor.jpg';stable.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,stable)
path='/Game/Game/Characters/Maya/Materials/Textures';task=unreal.AssetImportTask();task.filename=str(stable);task.destination_path=path;task.destination_name='T_Maya_BaseColor';task.automated=True;task.replace_existing=True;task.save=True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
texture=unreal.load_asset(task.imported_object_paths[0]);texture.set_editor_property('srgb',True);unreal.EditorAssetLibrary.save_loaded_asset(texture, False)
mi_path='/Game/Game/Characters/Maya/Materials/MI_Maya'
mi=unreal.load_asset(mi_path)
if not mi:mi=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_Maya','/Game/Game/Characters/Maya/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
unreal.MaterialEditingLibrary.set_material_instance_parent(mi,unreal.load_asset('/Game/Characters/Tripo/Maya/M_Maya'))
unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi,'DiffuseColorMap',texture)
assert unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi,'DiffuseColorMap')==texture
# The supplied normal atlas produces facial seams in the exported rig (same-camera A/B).
# Preserve the requested base color and use the mesh normals until a compatible bake exists.
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi,'NormalMapWeight',0.0)
unreal.MaterialEditingLibrary.update_material_instance(mi);unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
materials={'/Game/Game/Characters/Maya/SK_Maya':mi}
for suffix,variant in [('Base','Utility'),('Camera','A'),('Boom','B')]:
 material=unreal.load_asset('/Game/Characters/Tripo/Crew/MI_Crew_'+variant);assert material
 materials['/Game/Game/Characters/Crew/SK_Crew_'+suffix]=material
for asset_path,material in materials.items():
 mesh=unreal.load_asset(asset_path);slots=mesh.get_editor_property('materials');slot=slots[0]
 # Use reflected setters: assigning a Python attribute on a struct does not persist this field.
 slot.set_editor_property('material_interface',material);slots[0]=slot;mesh.set_editor_property('materials',slots)
 assert mesh.get_editor_property('materials')[0].get_editor_property('material_interface')==material
 unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
 print('MATERIAL_REPAIRED',asset_path,material.get_path_name())
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
 for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
  mesh=component.get_editor_property('skeletal_mesh_asset')
  if mesh and mesh.get_path_name().split('.')[0] in materials:component.set_material(0,materials[mesh.get_path_name().split('.')[0]])
print('MAYA_TEXTURE_AND_CREW_SLOTS_FIXED')
