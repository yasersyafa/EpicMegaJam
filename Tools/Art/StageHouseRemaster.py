"""Remaster SB_GrayBox with aged plaster, panelled walls, solid ceiling/roof and practical lighting."""
import unreal,json,os,math,traceback
P=unreal.Paths.project_dir();ROOT='/Game/Game/Art/Environment/House';SOURCE=os.path.join(P,'SourceArt/Environment/House/Remaster')
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);SM=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
R={'success':False,'assets':[],'actors':[],'errors':[],'ceiling_height_cm':340,'stair_ceiling_height_cm':430,'character_height_cm':176}
def load(p):
 a=unreal.load_asset(p)
 if not a:raise RuntimeError('Missing '+p)
 return a
def node(mat,cls,**props):
 n=M.create_material_expression(mat,cls)
 for k,v in props.items():n.set_editor_property(k,v)
 return n
def wire(a,b,pin='',out=''):
 if not M.connect_material_expressions(a,out,b,pin):raise RuntimeError('Material connection '+pin)
def custom(mat,code,inputs,typ):
 n=node(mat,unreal.MaterialExpressionCustom,code=code,output_type=typ);fields=[]
 for key in inputs:
  f=unreal.CustomInput();f.set_editor_property('input_name',key);fields.append(f)
 n.set_editor_property('inputs',fields)
 for key,v in inputs.items():wire(v,n,key)
 return n
def color(rgb):return unreal.LinearColor(r=rgb[0],g=rgb[1],b=rgb[2],a=1)
def materials():
 path=ROOT+'/Materials/Masters/M_House_AgedSurface_World'
 mat=load(path) if E.does_asset_exist(path) else T.create_asset('M_House_AgedSurface_World',ROOT+'/Materials/Masters',unreal.Material,unreal.MaterialFactoryNew())
 M.delete_all_material_expressions(mat);mat.set_editor_property('tangent_space_normal',False)
 pos=node(mat,unreal.MaterialExpressionWorldPosition);normal=node(mat,unreal.MaterialExpressionVertexNormalWS)
 inp={'P':pos,'N':normal}
 for key,val in [('BaseColor',(.16,.21,.18)),('PatinaColor',(.07,.09,.065))]:inp[key]=node(mat,unreal.MaterialExpressionVectorParameter,parameter_name=key,default_value=color(val))
 for key,val in [('Age',.6),('WoodMode',0.),('DetailScale',1.)]:inp[key]=node(mat,unreal.MaterialExpressionScalarParameter,parameter_name=key,default_value=val)
 code='''
struct AgedSurface {
 float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
}; AgedSurface s;
float3 n=abs(N);float2 uv=n.z>.7?P.xy:(n.x>n.y?float2(P.y,P.z):float2(P.x,P.z));uv*=DetailScale;
float broad=s.noise(uv*.017);float medium=s.noise(uv*.11);float fine=s.noise(uv*1.9);
float stain=smoothstep(.46,.85,broad*.72+medium*.28)*Age;
float wear=smoothstep(.68,.88,s.noise(uv*.052+19))*Age;
float lower=(1-smoothstep(0,95,P.z))*Age*.32;
float3 plaster=lerp(BaseColor,PatinaColor,saturate(stain*.68+lower))*(.87+.16*medium+.07*fine);
plaster=lerp(plaster,BaseColor*1.38,wear*.28);
float hair=pow(saturate(1-abs(s.noise(float2(uv.x*.05,uv.y*.011))-.51)*70),5)*smoothstep(.65,.85,broad);
plaster*=1-hair*Age*.24;
float grain=s.noise(float2(uv.x*.23,uv.y*2.2));float3 wood=lerp(BaseColor,PatinaColor,stain*.3)*(.82+.12*grain+.10*medium+.06*fine);
return float4(lerp(plaster,wood,WoodMode),lerp((fine-.5)*.045+medium*.015-hair*.04,(grain-.5)*.018,WoodMode));
'''
 surf=custom(mat,code,inp,unreal.CustomMaterialOutputType.CMOT_FLOAT4)
 rgb=node(mat,unreal.MaterialExpressionComponentMask,r=True,g=True,b=True,a=False);h=node(mat,unreal.MaterialExpressionComponentMask,r=False,g=False,b=False,a=True);wire(surf,rgb);wire(surf,h)
 bump=custom(mat,'''float3 n=normalize(N);float3 dx=ddx(P),dy=ddy(P);float3 a=cross(dy,n),b=cross(n,dx);float det=dot(dx,a);float3 grad=(ddx(H)*a+ddy(H)*b)/(abs(det)<.00001?.00001:det);return normalize(n-clamp(grad,-.22,.22));''',{'P':pos,'N':normal,'H':h},unreal.CustomMaterialOutputType.CMOT_FLOAT3)
 rough=node(mat,unreal.MaterialExpressionScalarParameter,parameter_name='Roughness',default_value=.85)
 for n,prop in [(rgb,unreal.MaterialProperty.MP_BASE_COLOR),(bump,unreal.MaterialProperty.MP_NORMAL),(rough,unreal.MaterialProperty.MP_ROUGHNESS)]:M.connect_material_property(n,'',prop)
 M.layout_material_expressions(mat);M.recompile_material(mat);E.save_loaded_asset(mat)
 specs={
 'Plaster_Sage':((.17,.225,.20),(.065,.085,.068),.55,0,.82),
 'Plaster_Olive':((.23,.24,.18),(.10,.105,.066),.68,0,.9),
 'Plaster_Service':((.29,.285,.23),(.12,.12,.084),.72,0,.91),
 'Timber_AgedIvory':((.48,.445,.35),(.22,.21,.145),.62,1,.72),
 'Timber_PanelInset':((.34,.325,.255),(.18,.175,.125),.5,1,.82),
 'Plaster_Ceiling':((.42,.415,.345),(.17,.18,.135),.48,0,.95),
 'Roof_Charcoal':((.038,.052,.047),(.018,.024,.02),.6,0,.88)}
 palette={}
 for key,(base,patina,age,mode,rough) in specs.items():
  name='MI_House_'+key;folder=ROOT+'/Materials/Instances/Remaster';path=folder+'/'+name
  inst=load(path) if E.does_asset_exist(path) else T.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
  M.set_material_instance_parent(inst,mat)
  for k,v in [('BaseColor',base),('PatinaColor',patina)]:M.set_material_instance_vector_parameter_value(inst,k,color(v))
  for k,v in [('Age',age),('WoodMode',mode),('Roughness',rough)]:M.set_material_instance_scalar_parameter_value(inst,k,v)
  M.update_material_instance(inst);E.save_loaded_asset(inst);palette[key]=inst;R['assets'].append(path)
 palette['Brass']=load(ROOT+'/Materials/Instances/Props/MI_House_Prop_Shelf_Gunmetal')
 palette['Glass']=load(ROOT+'/Materials/Instances/Props/MI_House_Prop_Bulb')
 return palette

def mesh_actor(label,mesh,mat,location,scale=(1,1,1),rotation=None,collision=True,folder='Architecture'):
 a=S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location));a.set_actor_label(label);a.set_folder_path('Environment/House/Remaster/'+folder)
 c=a.static_mesh_component;c.set_static_mesh(mesh)
 if mat:c.set_material(0,mat)
 c.set_mobility(unreal.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
 a.set_actor_scale3d(unreal.Vector(*scale))
 if rotation:a.set_actor_rotation(rotation,False)
 R['actors'].append(label);return a

def import_meshes(palette):
 with open(os.path.join(SOURCE,'HouseRemasterManifest.json')) as f:entries=json.load(f)
 out={};slotmap={'AgedIvory':palette['Timber_AgedIvory'],'Brass':palette['Brass'],'Glass':palette['Glass'],'PanelInset':palette['Timber_PanelInset'],'Sage':palette['Plaster_Sage']}
 for entry in entries:
  folder=ROOT+'/Meshes/Remaster';path=folder+'/'+entry['name']
  if not E.does_asset_exist(path) or os.environ.get('HOUSE_REMASTER_REIMPORT')=='1':
   opts=unreal.FbxImportUI();opts.set_editor_property('automated_import_should_detect_type',False);opts.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH);opts.set_editor_property('import_materials',False);opts.set_editor_property('import_textures',False)
   d=opts.static_mesh_import_data;d.set_editor_property('combine_meshes',True);d.set_editor_property('auto_generate_collision',False);d.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
   task=unreal.AssetImportTask();task.set_editor_property('filename',os.path.join(SOURCE,entry['file']));task.set_editor_property('destination_path',folder);task.set_editor_property('destination_name',entry['name']);task.set_editor_property('options',opts);task.set_editor_property('factory',unreal.FbxFactory());task.set_editor_property('automated',True);task.set_editor_property('save',False);task.set_editor_property('replace_existing',True);task.set_editor_property('replace_existing_settings',True);T.import_asset_tasks([task])
  mesh=load(path)
  for i,slot in enumerate(mesh.static_materials):mesh.set_material(i,slotmap[str(slot.material_slot_name)])
  SM.remove_collisions(mesh)
  if entry['triangles']>800:
   opt=unreal.StaticMeshReductionOptions();opt.set_editor_property('auto_compute_lod_screen_size',False);settings=[]
   for percent,size in [(1.,1.),(.6,.2),(.3,.065)]:
    item=unreal.StaticMeshReductionSettings();item.set_editor_property('percent_triangles',percent);item.set_editor_property('screen_size',size);settings.append(item)
   opt.set_editor_property('reduction_settings',settings);SM.set_lods(mesh,opt)
  for lod in range(SM.get_lod_count(mesh)):
   b=SM.get_lod_build_settings(mesh,lod);b.set_editor_property('build_reversed_index_buffer',False);SM.set_lod_build_settings(mesh,lod,b)
  E.save_loaded_asset(mesh);out[entry['name']]=mesh;R['assets'].append(path)
 return out,entries

def stage(palette,meshes,entries):
 # Keep original wall footprints and doors, only increase height above their existing heads.
 S.clear_actor_selection_set()
 for a in list(S.get_all_level_actors()):
  if a.get_actor_label().startswith(('RM_House_','LIGHT_House_Remaster_')):S.destroy_actor(a)
 actors=S.get_all_level_actors();cube=load('/Engine/BasicShapes/Cube')
 for a in actors:
  label=a.get_actor_label()
  if label.startswith('GB_Wall_'):
   loc=a.get_actor_location();scale=a.get_actor_scale3d();loc.z=170;scale.z=3.4;a.set_actor_location(loc,False,False);a.set_actor_scale3d(scale)
   a.static_mesh_component.set_material(0,palette['Plaster_Sage'])
  if label.startswith('GB_Lintel_'):
   loc=a.get_actor_location();scale=a.get_actor_scale3d();loc.z=290;scale.z=1.;a.set_actor_location(loc,False,False);a.set_actor_scale3d(scale);a.static_mesh_component.set_material(0,palette['Plaster_Sage'])
 floors=[a for a in actors if a.get_actor_label().startswith('GB_Floor_')]
 rooms=[]
 for a in floors:
  room=a.get_actor_label().removeprefix('GB_Floor_');o,e=a.get_actor_bounds(False);rooms.append((room,o.x,o.y,e.x,e.y))
  # Ceiling rectangles meet the wall centres to seal all room boundaries.
  mesh_actor('RM_House_Ceiling_'+room,cube,palette['Plaster_Ceiling'],(o.x,o.y,346),(e.x*2/100,e.y*2/100,.12),folder='Ceilings')
 for entry in entries:
  if entry['category']=='Architecture':mesh_actor('RM_House_Panelling_'+entry['room'],meshes[entry['name']],None,entry['location'],collision=False,folder='WallDetails')
 # Stairwell has extra headroom above the highest existing 180 cm tread.
 mesh_actor('RM_House_Ceiling_Stairwell',cube,palette['Plaster_Ceiling'],(1325,-1291,436),(5.3,6.08,.12),folder='Ceilings')
 # Raise enclosure strips only around the stairwell, without lowering its ceiling.
 for name,loc,size in [('North',(1325,-1582,385),(530,26,90)),('East',(1580,-1291,385),(26,608,90)),('West',(1070,-1291,385),(26,608,90)),('South',(1325,-1000,385),(530,26,90))]:mesh_actor('RM_House_StairwellUpper_'+name,cube,palette['Plaster_Sage'],loc,tuple(v/100 for v in size),folder='Ceilings')
 # Closed gable, wide eaves, thickness and simple collision, rather than a single one-sided plane.
 half=1660;rise=220;angle=math.degrees(math.atan2(rise,half));slope=math.hypot(half,rise)
 for sign in (-1,1):mesh_actor('RM_House_Roof_'+('West' if sign<0 else 'East'),cube,palette['Roof_Charcoal'],(sign*half/2,-1,550),(slope/100,33.5,.16),unreal.Rotator(pitch=-sign*angle,yaw=0,roll=0),folder='Roof')
 for y in (-1582,1580):mesh_actor('RM_House_Gable_'+str(y),meshes['SM_House_Roof_Gable'],None,(0,y,0),collision=False,folder='Roof')
 # Wall-height attic closure on both eaves.
 for x in (-1582,1580):mesh_actor('RM_House_Eave_'+str(x),cube,palette['Plaster_Sage'],(x,-1,395),(0.26,31.88,1.10),folder='Roof')
 # Reuse a chandelier + ceiling rose; keep all hanging geometry above player head height.
 lightdata=[]
 for room,x,y,ex,ey in rooms:
  if room in ('WC','Storage','Service'):continue
  for suffix,z,mesh in [('Rose',339,meshes['SM_House_Fixture_CeilingRose']),('Chandelier',335,meshes['SM_House_Fixture_Chandelier'])]:mesh_actor('RM_House_'+suffix+'_'+room,mesh,None,(x,y,z),collision=False,folder='Fixtures')
  light=S.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,285));light.set_actor_label('LIGHT_House_Remaster_'+room);light.set_folder_path('Environment/House/Remaster/Lighting');c=light.point_light_component;c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS)
  c.set_editor_property('intensity',2500. if room in ('Dining','Living','Garage') else 1700.);c.set_editor_property('attenuation_radius',min(1100.,max(ex,ey)+180.));c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',3100.);c.set_editor_property('source_radius',20.);c.set_editor_property('cast_shadows',room in ('Dining','Living','Lobby'));c.set_editor_property('indirect_lighting_intensity',1.2);lightdata.append({'room':room,'shadows':room in ('Dining','Living','Lobby')})
 # Modest soft fixtures for small utility rooms.
 for room,x,y,ex,ey in rooms:
  if room not in ('WC','Storage','Service'):continue
  mesh_actor('RM_House_Rose_'+room,meshes['SM_House_Fixture_CeilingRose'],None,(x,y,339),collision=False,folder='Fixtures')
  light=S.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,305));light.set_actor_label('LIGHT_House_Remaster_'+room);light.set_folder_path('Environment/House/Remaster/Lighting');c=light.point_light_component;c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_editor_property('intensity',900.);c.set_editor_property('attenuation_radius',650.);c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',3600.);c.set_editor_property('cast_shadows',False)
 for a in actors:
  if isinstance(a,unreal.DirectionalLight):a.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',1.0)
  if isinstance(a,unreal.SkyLight):a.get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity',.35)
  if a.get_actor_label()=='ART_House_SurfaceGrade':
   settings=a.get_editor_property('settings')
   for k,v in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',-1.),('auto_exposure_max_brightness',-1.),('override_auto_exposure_bias',True),('auto_exposure_bias',0.0),('override_bloom_intensity',True),('bloom_intensity',.18),('override_vignette_intensity',True),('vignette_intensity',.32)]:settings.set_editor_property(k,v)
   a.set_editor_property('settings',settings)
 exec(compile(open(os.path.join(P,'Tools/Art/TuneHouseRemasterMood.py')).read(),'TuneHouseRemasterMood.py','exec'),{'__name__':'__main__'})
 R['lights']=lightdata
 S.clear_actor_selection_set()
try:
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if world.get_name()!='SB_GrayBox':raise RuntimeError('Expected SB_GrayBox')
 palette=materials();meshes,entries=import_meshes(palette);stage(palette,meshes,entries)
 R['saved']=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();R['success']=R['saved']
 unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(-340,300,167),unreal.Rotator(pitch=-3,yaw=-62,roll=0))
except Exception:R['errors'].append(traceback.format_exc());unreal.log_error(R['errors'][-1])
finally:
 with open(os.path.join(P,'Saved/HouseRemasterReport.json'),'w') as f:json.dump(R,f,indent=2)
 unreal.log('CODEX_HOUSE_REMASTER '+str(R['success']))
