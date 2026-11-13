import unreal,json,os,math,re
project=unreal.Paths.project_dir()
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors=sub.get_all_level_actors()
root='/Game/Game/Art/Environment/House'
path=os.path.join(project,'Saved','HousePropsReport.json')
with open(path) as f:report=json.load(f)
issues=[]
props=[a for a in actors if a.get_actor_label().startswith('PROP_House_')]
remaining=[a.get_actor_label() for a in actors if isinstance(a,unreal.StaticMeshActor) and a.get_actor_label().startswith('GB_') and not a.get_actor_label().startswith(('GB_Floor_','GB_Wall_','GB_Lintel_','GB_RestrictedStep_'))]
if remaining:issues.append('Furniture blockout still present: '+str(remaining))
collision_issues=[]
for actor in props:
    comp=actor.static_mesh_component
    if not comp.static_mesh:issues.append('Missing mesh: '+actor.get_actor_label());continue
    for i in range(comp.get_num_materials()):
        mat=comp.get_material(i)
        if not mat or not mat.get_path_name().startswith(root):issues.append('Unassigned material: '+actor.get_actor_label())
    editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if str(comp.get_collision_profile_name())!='NoCollision' and editor.get_simple_collision_count(comp.static_mesh)+editor.get_convex_collision_count(comp.static_mesh)<1:
        collision_issues.append(actor.get_actor_label())
doorways={
 'Entrance':(-1045,1580),'GarageDining':(-560,-1085),'LobbyHall':(-560,710),
 'GarageStorage':(-1090,200),'StorageLobby':(-1078,460),'LivingDining':(-58,-600),
 'LivingHall':(-90,440),'Dressing':(225,900),'WC':(540,-1315),
 'DiningKitchen':(540,-695),'KitchenService':(705,400),'HiddenRoom':(880,1055)}
clearance=[]
for name,(x,y) in doorways.items():
    nearest=99999;label=''
    for actor in props:
        if str(actor.static_mesh_component.get_collision_profile_name())=='NoCollision':continue
        center,extent=actor.get_actor_bounds(False)
        if center.z-extent.z>200:continue
        dx=max(abs(x-center.x)-extent.x,0);dy=max(abs(y-center.y)-extent.y,0)
        distance=math.hypot(dx,dy)
        if distance<nearest:nearest=distance;label=actor.get_actor_label()
    clearance.append({'door':name,'nearest_prop_cm':round(nearest,1),'prop':label,'clear_90cm':nearest>=90})
report['verification']={'prop_actors':len(props),'remaining_blockout':remaining,'issues':issues,'collision_issues':collision_issues,'door_clearances':clearance}
baseline_file=os.path.join(project,'Tools','Art','HouseArchitectureBaseline.json')
if os.path.isfile(baseline_file):
    with open(baseline_file) as f:baseline=json.load(f)
    by_label={a.get_actor_label():a for a in actors}
    def vector_numbers(text):return tuple(float(x) for x in re.findall(r'[xyz]: (-?\d+\.\d+)',text))
    architecture_issues=[]
    for entry in baseline:
        actor=by_label.get(entry['label'])
        if not actor or vector_numbers(str(actor.get_actor_location()))!=vector_numbers(entry['location']) or vector_numbers(str(actor.get_actor_scale3d()))!=vector_numbers(entry['scale']) or actor.static_mesh_component.static_mesh.get_path_name()!=entry['mesh']:
            architecture_issues.append(entry['label'])
    report['verification']['architecture']={'checked':len(baseline),'issues':architecture_issues}
    issues.extend(architecture_issues)
report['success']=report.get('saved',False) and not issues and not collision_issues and all(c['clear_90cm'] for c in clearance)
with open(path,'w') as f:json.dump(report,f,indent=2)
unreal.log('CODEX_PROPS_VERIFIED '+str(report['success']))
