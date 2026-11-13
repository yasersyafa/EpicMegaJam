"""Import the house prop library, apply shared materials, replace furniture blockout.

Run inside Unreal Editor Python with SB_GrayBox open. Source geometry is in
SourceArt/Environment/House/Props; BuildHouseProps.py regenerates it offline.
"""
import unreal, json, os, math, traceback

PROJECT=unreal.Paths.project_dir()
ROOT='/Game/Game/Art/Environment/House'
SOURCE=os.path.join(PROJECT,'SourceArt','Environment','House','Props')
EAL=unreal.EditorAssetLibrary
MEL=unreal.MaterialEditingLibrary
SUB=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SME=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
REPORT=os.path.join(PROJECT,'Saved','HousePropsReport.json')
report={'success':False,'meshes':[],'placements':[],'removed_placeholders':[],'errors':[]}

def load(path):
    obj=unreal.load_asset(path)
    if not obj:raise RuntimeError('Missing asset: '+path)
    return obj

def make_palette():
    folder=ROOT+'/Materials/Instances/Props'
    basepath=ROOT+'/Materials/Masters/M_House_PropSurface'
    if EAL.does_asset_exist(basepath):base=load(basepath)
    else:
        base=TOOLS.create_asset('M_House_PropSurface',ROOT+'/Materials/Masters',unreal.Material,unreal.MaterialFactoryNew())
        for name,cls,value,prop in (
            ('BaseColor',unreal.MaterialExpressionVectorParameter,unreal.LinearColor(r=.5,g=.5,b=.5,a=1),unreal.MaterialProperty.MP_BASE_COLOR),
            ('Roughness',unreal.MaterialExpressionScalarParameter,.6,unreal.MaterialProperty.MP_ROUGHNESS),
            ('Metallic',unreal.MaterialExpressionScalarParameter,0.,unreal.MaterialProperty.MP_METALLIC),
            ('EmissiveColor',unreal.MaterialExpressionVectorParameter,unreal.LinearColor(r=0,g=0,b=0,a=1),unreal.MaterialProperty.MP_EMISSIVE_COLOR)):
            node=MEL.create_material_expression(base,cls)
            node.set_editor_property('parameter_name',name)
            node.set_editor_property('default_value',value)
            node.set_editor_property('group','Surface')
            MEL.connect_material_property(node,'',prop)
        MEL.layout_material_expressions(base);MEL.recompile_material(base);EAL.save_loaded_asset(base)
    palette={
      'Wood':load(folder+'/MI_House_Prop_Oak'),
      'Fabric':load(folder+'/MI_House_Prop_Fabric_Charcoal'),
      'Metal':load(folder+'/MI_House_Prop_Shelf_Gunmetal'),
      'Stone':load(folder+'/MI_House_Prop_Counter_Stone')}
    specs={
      'Tan':((.26,.19,.12),.93,0), 'Rubber':((.012,.016,.018),.86,0),
      'Yellow':((.43,.23,.035),.50,0), 'Ivory':((.66,.63,.55),.28,0),
      'Paper':((.67,.65,.58),.92,0), 'Ink':((.015,.022,.02),.75,0),
      'Mirror':((.63,.67,.69),.06,1), 'Bulb':((.9,.57,.22),.3,0),
      'Leaf':((.035,.115,.014),.75,0), 'Soil':((.032,.014,.006),1.,0),
      'Terracotta':((.24,.075,.025),.87,0), 'Burgundy':((.15,.03,.023),.90,0)}
    for name,(rgb,rough,metal) in specs.items():
        assetname='MI_House_Prop_'+name
        path=folder+'/'+assetname
        inst=load(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(assetname,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(inst,base)
        MEL.set_material_instance_vector_parameter_value(inst,'BaseColor',unreal.LinearColor(r=rgb[0],g=rgb[1],b=rgb[2],a=1))
        MEL.set_material_instance_scalar_parameter_value(inst,'Roughness',rough)
        MEL.set_material_instance_scalar_parameter_value(inst,'Metallic',metal)
        if name=='Bulb':MEL.set_material_instance_vector_parameter_value(inst,'EmissiveColor',unreal.LinearColor(r=8,g=3,b=.7,a=1))
        MEL.update_material_instance(inst);EAL.save_loaded_asset(inst);palette[name]=inst
    return palette

def import_meshes(palette):
    with open(os.path.join(SOURCE,'HousePropsManifest.json')) as f:manifest=json.load(f)
    meshes={}
    for entry in manifest:
        name=entry['name'];path=ROOT+'/Meshes/Props/'+name
        if not EAL.does_asset_exist(path) or name in os.environ.get('HOUSE_PROPS_REIMPORT','').split(','):
            options=unreal.FbxImportUI()
            options.set_editor_property('automated_import_should_detect_type',False)
            options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
            options.set_editor_property('import_mesh',True)
            options.set_editor_property('import_materials',False)
            options.set_editor_property('import_textures',False)
            data=options.static_mesh_import_data
            data.set_editor_property('combine_meshes',True)
            data.set_editor_property('auto_generate_collision',True)
            data.set_editor_property('generate_lightmap_u_vs',True)
            data.set_editor_property('normal_import_method',unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
            task=unreal.AssetImportTask()
            task.set_editor_property('filename',os.path.join(SOURCE,name+'.obj'))
            task.set_editor_property('destination_path',ROOT+'/Meshes/Props')
            task.set_editor_property('destination_name',name)
            task.set_editor_property('factory',unreal.FbxFactory())
            task.set_editor_property('options',options)
            task.set_editor_property('automated',True)
            task.set_editor_property('save',False)
            task.set_editor_property('replace_existing',True)
            task.set_editor_property('replace_existing_settings',True)
            TOOLS.import_asset_tasks([task])
        mesh=load(path)
        for index,slot in enumerate(mesh.static_materials):
            slotname=str(slot.material_slot_name)
            if slotname not in palette:raise RuntimeError('Unmapped slot '+slotname+' on '+name)
            mesh.set_material(index,palette[slotname])
        decorative=any(word in name for word in ('Rug_','Lamp_','Mirror_'))
        collision_count=SME.get_simple_collision_count(mesh)+SME.get_convex_collision_count(mesh)
        if collision_count != (0 if decorative else 1):
            SME.remove_collisions(mesh)
            if not decorative and SME.add_simple_collisions(mesh,unreal.ScriptCollisionShapeType.NDOP26)<0:
                raise RuntimeError('Simple collision creation failed: '+name)
        if entry['triangles']>800:
            lod=unreal.StaticMeshReductionOptions()
            lod.set_editor_property('auto_compute_lod_screen_size',False)
            settings=[]
            for percent,size in ((1.,1.),(.55,.25),(.25,.08)):
                item=unreal.StaticMeshReductionSettings()
                item.set_editor_property('percent_triangles',percent)
                item.set_editor_property('screen_size',size)
                settings.append(item)
            lod.set_editor_property('reduction_settings',settings)
            if SME.set_lods(mesh,lod)<1:raise RuntimeError('LOD generation failed: '+name)
        EAL.save_loaded_asset(mesh)
        meshes[name.removeprefix('SM_House_')]=mesh
        report['meshes'].append({'asset':mesh.get_path_name(),'source_triangles':entry['triangles'],'lod_count':SME.get_lod_count(mesh),'material_slots':len(mesh.static_materials),'collision_shapes':SME.get_simple_collision_count(mesh)+SME.get_convex_collision_count(mesh)})
    return meshes

def populate(meshes,palette):
    placements=[]
    def put(mesh,room,x,y,z=0,yaw=0,scale=1.,variant=None):
        placements.append(dict(mesh=mesh,room=room,location=(x,y,z),yaw=yaw,scale=scale,variant=variant))
    # Dining / production meeting area.
    put('Table_Meeting','Dining',-10,-1100)
    for x in (-185,-68,49,166):
        put('Chair_Dining','Dining',x,-1250,yaw=180,scale=1.15)
        put('Chair_Dining','Dining',x,-950,scale=1.15)
    put('Chair_Dining','Dining',-290,-1100,yaw=90,scale=1.15)
    put('Chair_Dining','Dining',270,-1100,yaw=-90,scale=1.15)
    put('Plant_Potted','Dining',-445,-1450,scale=1.3)
    put('Console','Dining',380,-1440,yaw=180)
    put('FlightCase_Black','Dining',420,-1200)
    put('Lamp_Desk','Dining',365,-1440,80)
    # Garage: equipment shelving on the west, cases along the east, clear central aisle.
    for y in (-1390,-1040,-690,-340,10):put('Rack_Equipment','Garage',-1485,y,yaw=90)
    for i,y in enumerate((-1430,-850,-490,-80)):
        put('FlightCase_Yellow' if i%2==0 else 'FlightCase_Black','Garage',-690,y,yaw=-90)
    put('FlightCase_Black','Garage',-1330,-1480,yaw=90)
    put('FlightCase_Yellow','Garage',-1120,-1460,yaw=180)
    put('FlightCase_Yellow','Garage',-1120,-1460,75,yaw=180)
    put('FlightCase_Black','Garage',-900,-1460,yaw=180)
    put('FlightCase_Yellow','Garage',-690,-1240,yaw=-90)
    put('FlightCase_Yellow','Storage',-1420,330,yaw=90)
    put('FlightCase_Black','Storage',-760,330,yaw=-90)
    # Living room conversation group and decorative surfaces.
    put('Rug_Bordered','Living',-10,-80,scale=(2.45,1.85,1))
    put('Sofa_ThreeSeat','Living',-65,-427,yaw=180,scale=1.2)
    put('Sofa_TwoSeat','Living',364,-50,yaw=-90,scale=1.25)
    put('Sofa_TwoSeat','Living',100,280,scale=1.1,variant='Burgundy')
    put('Armchair','Living',-350,155,yaw=45,scale=1.15)
    put('Table_Coffee','Living',-30,-60,yaw=90,scale=1.2)
    put('Table_Side','Living',-360,-420)
    put('Lamp_Desk','Living',-360,-420,55)
    put('Lamp_Floor','Living',435,245)
    put('Plant_Potted','Living',-430,310,scale=1.15)
    put('Console','Living',435,-335,yaw=-90)
    # Lobby / waiting area.
    put('Rug_Bordered','Lobby',-1050,1110,scale=(1.25,1.5,1))
    put('Sofa_TwoSeat','Lobby',-1440,1050,yaw=90,scale=1.15)
    put('Console','Lobby',-1450,1390,yaw=90)
    put('Lamp_Desk','Lobby',-1450,1390,80)
    put('Plant_Potted','Lobby',-1460,635,scale=1.4)
    put('Table_Side','Lobby',-1370,800)
    # Hall circulation stays open.
    put('Console','ProductionHall',445,650,yaw=-90)
    put('Plant_Potted','ProductionHall',420,795)
    # Kitchen: modular run along the east wall and a freestanding fridge to the west.
    for mesh,y in (('Kitchen_Cabinet',-880),('Kitchen_Sink',-665),('Kitchen_Cooker',-450),('Kitchen_Cabinet',-235),('Kitchen_Cabinet',-20),('Kitchen_Cabinet',195)):
        put(mesh,'Kitchen',1490,y,yaw=-90,scale=(1.65,1,1))
    put('Kitchen_Refrigerator','Kitchen',645,-90,yaw=90)
    put('Plant_Potted','Kitchen',1370,290,scale=.6)
    # Bathroom.
    put('Bathroom_Toilet','WC',800,-1485,yaw=180,scale=1.2)
    put('Bathroom_Basin','WC',990,-1180,yaw=-90,scale=1.15)
    put('Mirror_Wall','WC',1044,-1180,yaw=-90,scale=1.15)
    # Dressing: lit vanity on the east, hanging wardrobe opposite.
    put('Rug_Bordered','Dressing',-5,1230,scale=(1.1,1.1,1))
    put('Vanity_Illuminated','Dressing',445,1230,yaw=-90,scale=1.2)
    put('Chair_Dining','Dressing',280,1230,yaw=-90,scale=1.2)
    put('ClothesRail','Dressing',-445,1190,yaw=90,scale=1.3)
    put('Sofa_TwoSeat','Dressing',-30,1460,scale=.95,variant='Tan')
    put('FlightCase_Black','Dressing',-450,1480)
    # Hidden office.
    put('Rug_Bordered','HiddenRoom',1230,1020,scale=(1.6,1.6,1))
    put('Desk_Office','HiddenRoom',1210,1000,scale=1.25)
    put('Lamp_Desk','HiddenRoom',1270,1030,97.5)
    put('Chair_Dining','HiddenRoom',1140,830,yaw=180,scale=1.15)
    put('Chair_Dining','HiddenRoom',1280,830,yaw=180,scale=1.15)
    put('Cabinet_Tall','HiddenRoom',1480,1255,yaw=-90,scale=1.1)
    put('Plant_Potted','HiddenRoom',1000,1460,scale=1.1)
    existing=SUB.get_all_level_actors()
    # Populate completely before removing the furniture placeholders.
    for actor in existing:
        if actor.get_actor_label().startswith(('PROP_House_','LIGHT_House_')):SUB.destroy_actor(actor)
    counts={}
    for p in placements:
        counts[p['mesh']]=counts.get(p['mesh'],0)+1
        actor=SUB.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*p['location']),unreal.Rotator(pitch=0,yaw=p['yaw'],roll=0))
        actor.set_actor_label('PROP_House_'+p['room']+'_'+p['mesh']+'_'+str(counts[p['mesh']]).zfill(2))
        actor.set_folder_path('Environment/House/Props/'+p['room'])
        comp=actor.static_mesh_component
        comp.set_static_mesh(meshes[p['mesh']])
        scale=p['scale'] if isinstance(p['scale'],tuple) else (p['scale'],)*3
        actor.set_actor_scale3d(unreal.Vector(*scale))
        if p['variant']:
            for i,slot in enumerate(meshes[p['mesh']].static_materials):
                if str(slot.material_slot_name)=='Fabric':comp.set_material(i,palette[p['variant']])
        if p['mesh'].startswith(('Rug_','Lamp_','Mirror_')):comp.set_collision_profile_name('NoCollision')
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        p['actor']=actor.get_actor_label()
        report['placements'].append(p)
    oldlabels=[]
    for actor in existing:
        label=actor.get_actor_label()
        furniture=label.startswith('GB_') and isinstance(actor,unreal.StaticMeshActor) and not label.startswith(('GB_Floor_','GB_Wall_','GB_Lintel_','GB_RestrictedStep_'))
        if furniture or label=='Cube':
            oldlabels.append(label)
            if not SUB.destroy_actor(actor):raise RuntimeError('Could not remove blockout: '+label)
        elif label.startswith('GB_Label_'):
            actor.set_editor_property('is_editor_only_actor',True)
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)
        elif label=='Reference_FloorPlan':
            actor.set_editor_property('is_editor_only_actor',True)
    report['removed_placeholders']=oldlabels
    # Small non-shadowing practicals provide restrained warm pools near real fixtures.
    for room,x,y,z,intensity in (
        ('Living',-360,-420,102,350),('Living',435,245,150,600),
        ('Lobby',-1450,1390,125,300),('Dining',365,-1440,125,300),
        ('Dressing',350,1230,150,1000),('HiddenRoom',1270,1030,140,400)):
        light=SUB.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,z))
        light.set_actor_label('LIGHT_House_'+room+'_Practical_'+str(x).replace('-','N'))
        light.set_folder_path('Environment/House/Lighting/Practicals')
        c=light.point_light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS)
        c.set_editor_property('intensity',float(intensity))
        c.set_editor_property('attenuation_radius',260.)
        c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',2900.)
        c.set_editor_property('cast_shadows',False)
    SUB.clear_actor_selection_set()

try:
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if 'SB_GrayBox' not in world.get_path_name():raise RuntimeError('Expected SB_GrayBox.')
    palette=make_palette()
    meshes=import_meshes(palette)
    populate(meshes,palette)
    audit_path=os.path.join(PROJECT,'Tools','Art','AuditGameReadyProps.py')
    if os.path.isfile(audit_path):exec(compile(open(audit_path).read(),audit_path,'exec'),{'__name__':'__main__'})
    report['saved']=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    probe=ROOT+'/Meshes/Props/SM_House_ImportProbe'
    if EAL.does_asset_exist(probe):EAL.delete_asset(probe)
    report['success']=report['saved']
except Exception:
    report['errors'].append(traceback.format_exc());unreal.log_error(report['errors'][-1])
finally:
    with open(REPORT,'w') as f:json.dump(report,f,indent=2)
    unreal.log('CODEX_HOUSE_PROPS '+str(report['success']))
