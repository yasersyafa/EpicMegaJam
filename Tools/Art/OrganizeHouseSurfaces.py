"""Normalize the existing house surface pass without changing room geometry.

Run with Unreal Editor Python while SB_GrayBox is open. Re-running is supported.
The editor's asset rename APIs preserve references; no uasset files are moved
with filesystem operations. Two material families share uniform-driven masters.
"""
import unreal
import os
import json
import traceback

OLD = '/Game/Game/Art/HouseSurfaces'
ROOT = '/Game/Game/Art/Environment/House'
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUB = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT_PATH = os.path.join(unreal.Paths.project_dir(), 'Saved', 'HouseSurfaceOrganization.json')
report = {'success': False, 'renames': [], 'instances': [], 'assignments': [], 'errors': []}
STATS = ['num_pixel_shader_instructions', 'num_vertex_shader_instructions', 'num_pixel_texture_samples', 'num_samplers']


def stats(material):
    result = MEL.get_statistics(material)
    return {k:result.get_editor_property(k) for k in STATS}


def rename(old, new):
    if EAL.does_asset_exist(new):
        return unreal.load_asset(new)
    if not EAL.does_asset_exist(old):
        raise RuntimeError('Missing source asset: ' + old)
    EAL.make_directory(new.rsplit('/', 1)[0])
    if not EAL.rename_asset(old, new):
        raise RuntimeError('Asset rename failed: ' + old)
    report['renames'].append({'from':old, 'to':new})
    return unreal.load_asset(new)


def expr(material, cls, **props):
    result = MEL.create_material_expression(material, cls)
    for key, value in props.items():
        result.set_editor_property(key, value)
    return result


def wire(a, b, pin='', output=''):
    if not MEL.connect_material_expressions(a, output, b, pin):
        raise RuntimeError('Material connection failed: ' + pin)


def out(node, prop):
    if not MEL.connect_material_property(node, '', prop):
        raise RuntimeError('Material output connection failed')


def custom(material, code, inputs, output_type):
    node = expr(material, unreal.MaterialExpressionCustom, code=code, output_type=output_type)
    fields = []
    for name in inputs:
        item = unreal.CustomInput()
        item.set_editor_property('input_name', name)
        fields.append(item)
    node.set_editor_property('inputs', fields)
    for name, source in inputs.items():
        wire(source, node, name)
    return node


def instance(name, folder, parent, vectors=None, scalars=None):
    path = ROOT + '/Materials/Instances/' + folder + '/' + name
    EAL.make_directory(path.rsplit('/', 1)[0])
    material = unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(name, path.rsplit('/', 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(material, parent)
    for param, value in (vectors or {}).items():
        if param not in [str(n) for n in MEL.get_vector_parameter_names(parent)]:
            raise RuntimeError('Missing vector parameter: ' + param)
        MEL.set_material_instance_vector_parameter_value(material, param, unreal.LinearColor(r=value[0], g=value[1], b=value[2], a=1.0))
        actual = MEL.get_material_instance_vector_parameter_value(material, param)
        if any(abs(a-b)>0.0001 for a,b in zip((actual.r,actual.g,actual.b),value)):
            raise RuntimeError('Vector parameter read-back failed: ' + param)
    for param, value in (scalars or {}).items():
        if param not in [str(n) for n in MEL.get_scalar_parameter_names(parent)]:
            raise RuntimeError('Missing scalar parameter: ' + param)
        MEL.set_material_instance_scalar_parameter_value(material, param, value)
        if abs(MEL.get_material_instance_scalar_parameter_value(material,param)-value)>0.0001:
            raise RuntimeError('Scalar parameter read-back failed: ' + param)
    MEL.update_material_instance(material)
    EAL.save_loaded_asset(material)
    report['instances'].append({'path':path, 'parent':parent.get_path_name()})
    return material


try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if 'SB_GrayBox' not in world.get_path_name():
        raise RuntimeError('SB_GrayBox must be the current editor level.')
    before = {}
    for actor in SUB.get_all_level_actors():
        if isinstance(actor, unreal.StaticMeshActor):
            comp = actor.static_mesh_component
            before[actor.get_actor_label()] = {'location':tuple(actor.get_actor_location().to_tuple()), 'scale':tuple(actor.get_actor_scale3d().to_tuple()), 'mesh':comp.static_mesh.get_path_name(), 'material':comp.get_material(0).get_path_name() if comp.get_material(0) else None}
    report['before_masters'] = {}
    for path in EAL.list_assets(OLD + '/Materials', recursive=True):
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.Material):
            report['before_masters'][asset.get_name()] = stats(asset)
    if os.path.isfile(REPORT_PATH):
        with open(REPORT_PATH) as f:
            previous = json.load(f)
        if previous.get('before_masters'):
            report['before_masters'] = previous['before_masters']
    texture = rename(OLD + '/Textures/T_Oak_Albedo', ROOT + '/Textures/Wood/T_House_OakPlanks_BC')
    texture.set_editor_property('max_texture_size', 1024)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
    texture.set_editor_property('compression_no_alpha', True)
    texture.set_editor_property('srgb', True)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_WORLD)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    texture.set_editor_property('power_of_two_mode', unreal.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
    texture.set_editor_property('never_stream', False)
    EAL.save_loaded_asset(texture)
    wood = rename(OLD + '/Materials/M_Oak_Warm', ROOT + '/Materials/Masters/M_House_Wood_WorldXY')
    tile = rename(OLD + '/Materials/M_Garage_Slate60', ROOT + '/Materials/Masters/M_House_Tile_WorldXY')
    MEL.delete_all_material_expressions(tile)
    tile.set_editor_property('tangent_space_normal', False)
    pos = expr(tile, unreal.MaterialExpressionWorldPosition)
    ca = expr(tile, unreal.MaterialExpressionVectorParameter, parameter_name='TileColorA', default_value=unreal.LinearColor(r=0.18,g=0.18,b=0.17,a=1))
    cb = expr(tile, unreal.MaterialExpressionVectorParameter, parameter_name='TileColorB', default_value=unreal.LinearColor(r=0.17,g=0.17,b=0.16,a=1))
    size = expr(tile, unreal.MaterialExpressionScalarParameter, parameter_name='TileSizeCm', default_value=60.0)
    rough = expr(tile, unreal.MaterialExpressionScalarParameter, parameter_name='Roughness', default_value=0.83)
    metal = expr(tile, unreal.MaterialExpressionScalarParameter, parameter_name='Metallic', default_value=0.0)
    code = '''
struct SurfaceNoise {
 float hash(float2 q) { return frac(sin(dot(q,float2(127.1,311.7)))*43758.5453); }
 float noise(float2 q) {
  float2 i=floor(q),f=frac(q); f=f*f*(3.0-2.0*f);
  return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1.0),f.x),f.y);
 }
};
SurfaceNoise sn;
float2 q=P.xy/max(TileSize,1.0);
float2 cell=floor(q), f=frac(q);
float edge=min(min(f.x,1-f.x),min(f.y,1-f.y));
float grout=smoothstep(0.006,0.018,edge);
float check=fmod(abs(cell.x+cell.y),2.0);
float grain=sn.noise(P.xy*0.13)*0.07+sn.noise(P.xy*1.8)*0.025;
float variation=0.92+sn.hash(cell)*0.12;
float3 col=lerp(ColorA,ColorB,check)*variation*(0.94+grain);
return float4(lerp(float3(0.075,0.067,0.055),col,grout),grout*0.10+grain*0.05);
'''
    surface = custom(tile, code, {'P':pos,'TileSize':size,'ColorA':ca,'ColorB':cb}, unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    rgb = expr(tile, unreal.MaterialExpressionComponentMask, r=True,g=True,b=True,a=False)
    height = expr(tile, unreal.MaterialExpressionComponentMask, r=False,g=False,b=False,a=True)
    wire(surface, rgb)
    wire(surface, height)
    normal = expr(tile, unreal.MaterialExpressionVertexNormalWS)
    normal_code = '''
float3 n = normalize(N);
float3 dx = ddx(P), dy = ddy(P);
float3 r1 = cross(dy,n), r2 = cross(n,dx);
float det = dot(dx,r1);
float3 grad = (ddx(H)*r1 + ddy(H)*r2) / (abs(det) < 0.00001 ? 0.00001 : det);
return normalize(n - clamp(grad, -0.6, 0.6));
'''
    bump = custom(tile, normal_code, {'P':pos,'N':normal,'H':height}, unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    out(rgb, unreal.MaterialProperty.MP_BASE_COLOR)
    out(bump, unreal.MaterialProperty.MP_NORMAL)
    out(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    out(metal, unreal.MaterialProperty.MP_METALLIC)
    MEL.layout_material_expressions(tile)
    MEL.recompile_material(tile)
    EAL.save_loaded_asset(tile)
    replacements = {}
    def register(old_name, name, folder, parent, vectors=None, scalars=None):
        result = instance(name, folder, parent, vectors, scalars)
        replacements[old_name] = result
        return result
    register('M_Oak_Warm','MI_House_Floor_Oak_Warm','Floors',wood,{'WoodTint':(0.75,0.80,0.88)},{'Roughness':0.58})
    register('M_Oak_Dark','MI_House_Floor_Oak_Dark','Floors',wood,{'WoodTint':(0.43,0.44,0.48)},{'Roughness':0.58})
    register('M_Oak_Furniture','MI_House_Prop_Oak','Props',wood,{'WoodTint':(0.58,0.60,0.63)},{'Roughness':0.58})
    register('M_Garage_Slate60','MI_House_Floor_Garage_Slate_60cm','Floors',tile,{'TileColorA':(0.18,0.18,0.17),'TileColorB':(0.17,0.17,0.16)},{'TileSizeCm':60,'Roughness':0.83})
    register('M_WC_Charcoal30','MI_House_Floor_WC_Charcoal_30cm','Floors',tile,{'TileColorA':(0.12,0.135,0.135),'TileColorB':(0.13,0.14,0.14)},{'TileSizeCm':30,'Roughness':0.52})
    register('M_Kitchen_Checker55','MI_House_Floor_Kitchen_Checker_55cm','Floors',tile,{'TileColorA':(0.40,0.31,0.22),'TileColorB':(0.14,0.145,0.14)},{'TileSizeCm':55,'Roughness':0.58})
    specialized = [
        ('M_Warm_Ivory_Plaster','M_House_Plaster_World','MI_House_Wall_Plaster_Ivory','Walls'),
        ('M_Limestone_Stairs','M_House_Limestone_World','MI_House_Stair_Limestone','Floors'),
        ('M_Living_Woven_Taupe','M_House_Carpet_WorldXY','MI_House_Floor_Carpet_Taupe','Floors'),
        ('M_Upholstery_Charcoal','M_House_Fabric_World','MI_House_Prop_Fabric_Charcoal','Props'),
        ('M_Counter_Warm_Stone','M_House_StoneVein_World','MI_House_Prop_Counter_Stone','Props'),
        ('M_Shelf_Gunmetal','M_House_Metal_World','MI_House_Prop_Shelf_Gunmetal','Props'),
    ]
    masters = [wood,tile]
    for old_name,master_name,instance_name,folder in specialized:
        parent = rename(OLD + '/Materials/' + old_name, ROOT + '/Materials/Masters/' + master_name)
        masters.append(parent)
        register(old_name,instance_name,folder,parent)
    # Actor labels remain stable for existing editor workflows; folders carry ownership.
    floor_rooms = {}
    with unreal.ScopedEditorTransaction('Organize house surfaces and shared material families'):
        for actor in SUB.get_all_level_actors():
            label = actor.get_actor_label()
            if not isinstance(actor, unreal.StaticMeshActor) or not label.startswith('GB_'):
                continue
            comp = actor.static_mesh_component
            original = before[label]['material'] or ''
            old_name = original.rsplit('.',1)[-1]
            old_name = {'M_House_Wood_WorldXY':'M_Oak_Warm','M_House_Tile_WorldXY':'M_Garage_Slate60'}.get(old_name,old_name)
            # Renamed source pointers already point at the new master; the saved baseline
            # taken before the rename is what identifies the intended visual variant.
            if old_name not in replacements:
                if isinstance(comp.get_material(0),unreal.MaterialInstanceConstant):
                    continue
                raise RuntimeError('Unmapped material on ' + label + ': ' + old_name)
            actor.modify()
            comp.set_material(0,replacements[old_name])
            if label.startswith('GB_Floor_'):
                folder = 'Environment/House/Architecture/Floors'
            elif label.startswith('GB_Wall_'):
                folder = 'Environment/House/Architecture/Walls'
            elif label.startswith('GB_Lintel_'):
                folder = 'Environment/House/Architecture/Lintels'
            elif label.startswith('GB_RestrictedStep_'):
                folder = 'Environment/House/Architecture/Stairs'
            else:
                folder = 'Environment/House/Props'
            actor.set_folder_path(folder)
            report['assignments'].append({'actor':label,'material':replacements[old_name].get_path_name()})
        for actor in SUB.get_all_level_actors():
            if actor.get_actor_label() in ('DirectionalLight','SkyLight','SkyAtmosphere','ExponentialHeightFog','VolumetricCloud'):
                actor.set_folder_path('Environment/House/Lighting')
            elif actor.get_actor_label() == 'ART_House_SurfaceGrade':
                actor.set_folder_path('Environment/House/Lighting')
            elif actor.get_actor_label().startswith('GB_Label_') or actor.get_actor_label() == 'Reference_FloorPlan':
                actor.set_folder_path('Blockout/References')
    # Consolidate redundant base materials only after all placed actors use instances.
    for old_name in ('M_Oak_Dark','M_Oak_Furniture','M_WC_Charcoal30','M_Kitchen_Checker55'):
        path = OLD + '/Materials/' + old_name
        if EAL.does_asset_exist(path):
            legacy = unreal.load_asset(path)
            EAL.consolidate_assets(replacements[old_name].parent, [legacy])
    for parent in masters:
        EAL.save_loaded_asset(parent)
    report['saved'] = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report['layout_issues'] = []
    for actor in SUB.get_all_level_actors():
        label = actor.get_actor_label()
        if label in before:
            original = before[label]
            if actor.get_actor_location().to_tuple() != original['location'] or actor.get_actor_scale3d().to_tuple() != original['scale'] or actor.static_mesh_component.static_mesh.get_path_name() != original['mesh']:
                report['layout_issues'].append(label)
    report['masters'] = {parent.get_path_name():stats(parent) for parent in masters}
    report['texture'] = {'path':texture.get_path_name(),'max_resolution':texture.get_editor_property('max_texture_size'),'srgb':texture.get_editor_property('srgb'),'streaming':not texture.get_editor_property('never_stream'),'compression':str(texture.get_editor_property('compression_settings'))}
    report['success'] = bool(report['saved']) and not report['layout_issues']
except Exception:
    report['errors'].append(traceback.format_exc())
    unreal.log_error(report['errors'][-1])
finally:
    with open(REPORT_PATH,'w') as f:
        json.dump(report,f,indent=2)
    unreal.log('CODEX_HOUSE_ORGANIZED ' + str(report['success']))
