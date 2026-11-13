"""Stage a compact garden, entrance walk and access road; invisible collision encloses the lot."""
import unreal,os,json,math,traceback,random
P=unreal.Paths.project_dir();ROOT='/Game/Game/Art/Environment/House';S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;T=unreal.AssetToolsHelpers.get_asset_tools();SM=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
R={'success':False,'actors':[],'blockers':[],'errors':[]};mat={};mesh={}
def load(p):
 a=unreal.load_asset(p)
 if not a:raise RuntimeError('Missing '+p)
 return a
def col(rgb):return unreal.LinearColor(r=rgb[0],g=rgb[1],b=rgb[2],a=1)
def make_materials():
 aged=load(ROOT+'/Materials/Masters/M_House_AgedSurface_World');plain=load(ROOT+'/Materials/Masters/M_House_PropSurface')
 specs={'Ground':((.035,.048,.028),(.012,.021,.01),.95),'Grass':((.035,.075,.027),(.014,.035,.012),.97),'Paving':((.21,.225,.20),(.08,.095,.075),.88),'Asphalt':((.035,.04,.038),(.018,.021,.018),.95),'Stone':((.16,.18,.15),(.065,.08,.06),.85)}
 for key,(base,patina,rough) in specs.items():
  folder=ROOT+'/Materials/Instances/Exterior';name='MI_House_Exterior_'+key;path=folder+'/'+name
  inst=load(path) if E.does_asset_exist(path) else T.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());M.set_material_instance_parent(inst,aged)
  for k,v in [('BaseColor',base),('PatinaColor',patina)]:M.set_material_instance_vector_parameter_value(inst,k,col(v))
  for k,v in [('Age',.45),('WoodMode',0.),('Roughness',rough)]:M.set_material_instance_scalar_parameter_value(inst,k,v)
  M.update_material_instance(inst);E.save_loaded_asset(inst);mat[key]=inst
 for key,rgb,rough,metal,emit in [('LeafDark',(.018,.06,.024),.85,0,(0,0,0)),('LeafSage',(.045,.095,.04),.8,0,(0,0,0)),('Metal',(.025,.035,.032),.55,.6,(0,0,0)),('Bulb',(.7,.48,.23),.5,0,(2.5,1.3,.45))]:
  folder=ROOT+'/Materials/Instances/Exterior';name='MI_House_Exterior_'+key;path=folder+'/'+name
  inst=load(path) if E.does_asset_exist(path) else T.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew());M.set_material_instance_parent(inst,plain)
  M.set_material_instance_vector_parameter_value(inst,'BaseColor',col(rgb));M.set_material_instance_vector_parameter_value(inst,'EmissiveColor',col(emit));M.set_material_instance_scalar_parameter_value(inst,'Roughness',rough);M.set_material_instance_scalar_parameter_value(inst,'Metallic',metal);M.update_material_instance(inst);E.save_loaded_asset(inst);mat[key]=inst

def import_meshes():
 source=os.path.join(P,'SourceArt/Environment/House/Exterior');entries=json.load(open(os.path.join(source,'HouseExteriorManifest.json')))
 for entry in entries:
  folder=ROOT+'/Meshes/Exterior';path=folder+'/'+entry['name']
  if not E.does_asset_exist(path):
   opt=unreal.FbxImportUI();opt.set_editor_property('automated_import_should_detect_type',False);opt.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH);opt.set_editor_property('import_materials',False);opt.set_editor_property('import_textures',False);d=opt.static_mesh_import_data;d.set_editor_property('combine_meshes',True);d.set_editor_property('auto_generate_collision',False);d.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
   task=unreal.AssetImportTask();task.set_editor_property('filename',os.path.join(source,entry['file']));task.set_editor_property('destination_path',folder);task.set_editor_property('destination_name',entry['name']);task.set_editor_property('factory',unreal.FbxFactory());task.set_editor_property('options',opt);task.set_editor_property('automated',True);task.set_editor_property('save',False);T.import_asset_tasks([task])
  a=load(path)
  for i,slot in enumerate(a.static_materials):a.set_material(i,mat[str(slot.material_slot_name)])
  SM.remove_collisions(a)
  b=SM.get_lod_build_settings(a,0);b.set_editor_property('build_reversed_index_buffer',False);SM.set_lod_build_settings(a,0,b);E.save_loaded_asset(a);mesh[entry['name'].removeprefix('SM_House_Exterior_')]=a
 mesh['Cube']=load('/Engine/BasicShapes/Cube')

def place(name,kind,loc,size=(1,1,1),material=None,block=False,yaw=0,folder='Garden'):
 a=S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc));a.set_actor_label('EXT_House_'+name);a.set_folder_path('Environment/House/Exterior/'+folder);a.set_actor_scale3d(unreal.Vector(*size));a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False);c=a.static_mesh_component;c.set_static_mesh(mesh[kind]);c.set_mobility(unreal.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if block else 'NoCollision')
 if material:c.set_material(0,mat[material])
 if kind in ('WallLantern','LampPost','Shrub'):c.set_editor_property('cast_shadow',False)
 R['actors'].append(a.get_actor_label());return a

def box(name,loc,size,material,block=True,folder='Hardscape'):return place(name,'Cube',loc,tuple(v/100 for v in size),material,block,folder=folder)
def point(name,x,y,z,power,radius=650):
 a=S.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,z));a.set_actor_label('EXT_House_Light_'+name);a.set_folder_path('Environment/House/Exterior/Lighting');c=a.point_light_component;c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_editor_property('intensity',float(power));c.set_editor_property('attenuation_radius',float(radius));c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',3400.);c.set_editor_property('cast_shadows',False);c.set_editor_property('source_radius',12.)

def stage():
 S.clear_actor_selection_set()
 for a in list(S.get_all_level_actors()):
  if a.get_actor_label().startswith(('EXT_House_','COL_House_Exterior_')):S.destroy_actor(a)
 box('Ground',(0,500,-32),(4800,5600,40),'Ground',folder='Ground')
 box('Porch',(-1045,1730,-8),(400,300,16),'Paving')
 # Compact portico and exterior casing align with the true 204 cm entrance opening.
 for i,x in enumerate((-1215,-875)):box('PorchColumn_'+str(i),(x,1840,132),(18,18,264),'Paving')
 box('PorchBeam',(-1045,1840,267),(380,24,14),'Stone')
 box('PorchCanopy',(-1045,1730,282),(420,360,16),'Stone')
 for i,x in enumerate((-1151,-939)):box('EntranceCasing_'+str(i),(x,1599,120),(8,10,240),'Paving',False)
 box('EntranceHeader',(-1045,1599,245),(220,10,10),'Paving',False)
 for name,x,w in [('West',-1375,440),('East',329,2528)]:box('FacadePlinth_'+name,(x,1597,16),(w,8,32),'Stone',False)
 # A 240 cm clear pedestrian approach; all lips are below the player's step height.
 for i in range(8):box('Walk_Slab_%02d'%i,(-1045,1935+i*80,-5),(238,78,14),'Paving')
 box('Sidewalk',(0,2460,-8),(4680,240,16),'Paving')
 box('Road',(0,2860,-12),(4680,560,16),'Asphalt')
 for y in (2575,3145):box('RoadCurb_'+str(y),(0,y,0),(4680,16,20),'Stone')
 # Leave two lowered kerb crossings exactly on the entrance route.
 # The continuous front kerb is just 10 cm high, below BP_PlayerCharacter's normal step height.
 rng=random.Random(17)
 beds=[('FrontWest',-1740,2100,660,400),('FrontEast',400,2070,2140,470),('WestSide',-1990,150,360,1900),('EastSide',1990,100,360,2200),('Rear',0,-1990,2800,330)]
 for label,x,y,w,d in beds:
  box('Lawn_'+label,(x,y,-6),(w,d,12),'Grass',False,'Garden')
  for side,loc,size in [('N',(x,y-d/2,1),(w+24,18,20)),('S',(x,y+d/2,1),(w+24,18,20)),('W',(x-w/2,y,1),(18,d,20)),('E',(x+w/2,y,1),(18,d,20))]:box('BedEdge_'+label+'_'+side,loc,size,'Stone',False,'Garden')
  n=3 if w<800 and d<800 else 7
  for i in range(n):
   if w>d:px=x-w*.38+(i/max(1,n-1))*w*.76;py=y+rng.uniform(-d*.18,d*.18)
   else:px=x+rng.uniform(-w*.18,w*.18);py=y-d*.38+(i/max(1,n-1))*d*.76
   scale=rng.uniform(.85,1.18);place('Shrub_'+label+'_'+str(i),'Shrub',(px,py,0),(scale,scale,scale),yaw=rng.uniform(0,360))
 # Low perimeter rail gives a visible edge; collision walls below enforce the actual play boundary.
 for i,x in enumerate(range(-2200,2201,400)):
  box('FencePost_%02d'%i,(x,3220,48),(20,20,120),'Stone',False,'Boundary')
 for z in (50,96):box('FenceRail_'+str(z),(0,3220,z),(4460,8,6),'Metal',False,'Boundary')
 for i,(x,y) in enumerate([(-1810,2440),(1550,2440),(-2050,600),(2050,700)]):
  place('LampPost_'+str(i),'LampPost',(x,y,0),folder='Lighting');point('Garden_'+str(i),x,y,310,2000,1000)
 for i,x in enumerate((-1235,-855)):
  place('PorchLantern_'+str(i),'WallLantern',(x,1602,225),folder='Lighting');point('Porch_'+str(i),x,1645,222,700,500)
 # Soft cool facade fill; one shadowed area light keeps its light out of the closed house.
 a=S.spawn_actor_from_class(unreal.RectLight,unreal.Vector(-200,2520,700));a.set_actor_label('EXT_House_Light_MoonFill');a.set_folder_path('Environment/House/Exterior/Lighting');a.set_actor_rotation(unreal.Rotator(pitch=-25,yaw=-90,roll=0),False);c=a.get_component_by_class(unreal.RectLightComponent)
 for k,v in [('intensity_units',unreal.LightUnits.LUMENS),('intensity',2200.),('attenuation_radius',2600.),('source_width',1800.),('source_height',500.),('use_temperature',True),('temperature',6200.),('cast_shadows',True)]:c.set_editor_property(k,v)
 # Invisible collision encloses the entire ground footprint, including the road ends.
 for name,loc,size in [('West',(-2350,500,550),(60,5600,1200)),('East',(2350,500,550),(60,5600,1200)),('Rear',(0,-2250,550),(4760,60,1200)),('Front',(0,3250,550),(4760,60,1200))]:
  a=box('Boundary_'+name,loc,size,'Stone',True,'Collision');a.set_actor_label('COL_House_Exterior_'+name);a.set_folder_path('Environment/House/Exterior/Collision');a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.static_mesh_component.set_editor_property('cast_shadow',False);R['blockers'].append(a.get_actor_label())
 S.clear_actor_selection_set()
try:
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if world.get_name()!='SB_GrayBox':raise RuntimeError('Expected SB_GrayBox')
 make_materials();import_meshes();stage();R['saved']=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();R['success']=R['saved']
 unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(-1600,3050,235),unreal.Rotator(pitch=-6,yaw=-64,roll=0));unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_set_game_view(True)
except Exception:R['errors'].append(traceback.format_exc());unreal.log_error(R['errors'][-1])
finally:
 with open(os.path.join(P,'Saved/HouseExteriorReport.json'),'w') as f:json.dump(R,f,indent=2)
 unreal.log('CODEX_EXTERIOR '+str(R['success']))
