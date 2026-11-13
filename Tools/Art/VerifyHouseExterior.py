import unreal,json,os
pie=os.environ.get('HOUSE_EXTERIOR_TEST_PIE')=='1'
u=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w=u.get_game_world() if pie else u.get_editor_world()
if not w:raise RuntimeError('Requested world not running')
actors=list(unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor));walls=[a for a in actors if a.get_actor_label().startswith('COL_House_Exterior_')];ignore=[a for a in actors if a not in walls];r={'issues':[],'boundary_sweeps':[],'world':w.get_path_name()}
def sweep(start,end,ignored):
 h=unreal.SystemLibrary.capsule_trace_single(w,unreal.Vector(*start),unreal.Vector(*end),34.,88.,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignored,unreal.DrawDebugTrace.NONE,True)
 return h.to_tuple() if h else None
for z in (100,500,950):
 for y in (-2100,-1500,-500,500,1500,2500,2860,3150):
  for side,sign in [('West',-1),('East',1)]:
   h=sweep((sign*2220,y,z),(sign*2480,y,z),ignore);ok=bool(h and h[0] and h[9] and h[9].get_actor_label()=='COL_House_Exterior_'+side);r['boundary_sweeps'].append({'side':side,'along':y,'height':z,'blocked':ok})
   if not ok:r['issues'].append('Boundary leak '+str((side,y,z)))
 for x in (-2200,-1500,-500,500,1500,2200):
  for side,a,b in [('Rear',-2100,-2400),('Front',3100,3400)]:
   h=sweep((x,a,z),(x,b,z),ignore);ok=bool(h and h[0] and h[9] and h[9].get_actor_label()=='COL_House_Exterior_'+side);r['boundary_sweeps'].append({'side':side,'along':x,'height':z,'blocked':ok})
   if not ok:r['issues'].append('Boundary leak '+str((side,x,z)))
r['invisible_walls']=[{'actor':a.get_actor_label(),'hidden_in_game':a.get_editor_property('hidden'),'collision_profile':str(a.static_mesh_component.get_collision_profile_name()),'simple_shapes':None if pie else unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_simple_collision_count(a.static_mesh_component.static_mesh)} for a in walls]
if len(walls)!=4 or any(not a['hidden_in_game'] or a['collision_profile']!='BlockAll' for a in r['invisible_walls']):r['issues'].append('Incorrect invisible wall configuration')
h=sweep((-1045,1500,100),(-1045,2460,100),[]);r['entrance_approach_clear']=not(h and h[0]);r['approach_hit']=h[9].get_actor_label() if h and h[0] and h[9] else None
if not r['entrance_approach_clear']:r['issues'].append('Entrance approach blocked')
ex=[a for a in actors if a.get_actor_label().startswith('EXT_House_') and isinstance(a,unreal.StaticMeshActor)];r['static_mesh_actors']=len(ex);r['shrubs']=sum('Shrub_' in a.get_actor_label() for a in ex)
meshes={a.static_mesh_component.static_mesh.get_path_name():a.static_mesh_component.static_mesh for a in ex if '/Meshes/Exterior/' in a.static_mesh_component.static_mesh.get_path_name()};r['new_library_triangles']=sum(m.get_num_triangles(0) for m in meshes.values());r['passed']=not r['issues']
with open(os.path.join(unreal.Paths.project_dir(),'Saved/HouseExteriorPIEAudit.json' if os.environ.get('HOUSE_EXTERIOR_TEST_PIE')=='1' else 'Saved/HouseExteriorAudit.json'),'w') as f:json.dump(r,f,indent=2)
unreal.log('CODEX_EXTERIOR_AUDIT '+str(r['passed']))

