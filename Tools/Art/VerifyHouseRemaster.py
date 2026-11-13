"""Validate remaster assets, preserved footprints and collision headroom."""
import unreal,json,os
P=unreal.Paths.project_dir();S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);SM=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);M=unreal.MaterialEditingLibrary
actors=list(S.get_all_level_actors());by={a.get_actor_label():a for a in actors};world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();r={'issues':[],'rooms':[],'meshes':[],'door_heights':[]}
trace=unreal.SystemLibrary.line_trace_single
for a in actors:
 name=a.get_actor_label()
 if name.startswith('GB_Floor_'):
  o,e=a.get_actor_bounds(False);hit=trace(world,unreal.Vector(o.x,o.y,200),unreal.Vector(o.x,o.y,500),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
  h=hit.to_tuple() if hit else None
  # HitResult location and distance recorded as both a textual receipt and analytic slab bounds.
  ceil=by.get('RM_House_Ceiling_'+name.removeprefix('GB_Floor_'));co,ce=ceil.get_actor_bounds(False) if ceil else (None,None)
  bottom=co.z-ce.z if ceil else 0
  r['rooms'].append({'room':name,'ceiling_bottom_cm':bottom,'capsule_clearance_cm':bottom-176,'collision_blocks':bool(h and h[0]),'collision_height_cm':h[4].z if h and h[0] else None})
  if abs(bottom-340)>1 or not (h and h[0]):r['issues'].append('Ceiling/collision missing '+name)
 if name.startswith('GB_Lintel_'):
  o,e=a.get_actor_bounds(False);bottom=o.z-e.z;r['door_heights'].append({'door':name,'clear_height_cm':bottom})
  if bottom<220:r['issues'].append('Door too low '+name)
# Highest tread has 74cm clearance above the 176cm character.
stair=by.get('RM_House_Ceiling_Stairwell');o,e=stair.get_actor_bounds(False);r['stair_ceiling_bottom_cm']=o.z-e.z
r['highest_tread_cm']=max(a.get_actor_bounds(False)[0].z+a.get_actor_bounds(False)[1].z for a in actors if a.get_actor_label().startswith('GB_RestrictedStep_'))
r['stair_character_clearance_cm']=r['stair_ceiling_bottom_cm']-r['highest_tread_cm']-176
if r['stair_character_clearance_cm']<30:r['issues'].append('Stair headroom')
meshes={a.static_mesh_component.static_mesh.get_path_name():a.static_mesh_component.static_mesh for a in actors if isinstance(a,unreal.StaticMeshActor) and a.get_actor_label().startswith('RM_House_')}
for path,mesh in meshes.items():
 count=SM.get_lod_count(mesh);entry={'mesh':path,'lod_triangles':[mesh.get_num_triangles(i) for i in range(count)],'slots':len(mesh.static_materials)}
 r['meshes'].append(entry)
 if '/Remaster/' in path and entry['lod_triangles'][0]>800 and count<3:r['issues'].append('Missing LOD '+path)
 for slot in mesh.static_materials:
  if not slot.material_interface:r['issues'].append('Missing material '+path)
  elif slot.material_interface.get_blend_mode()!=unreal.BlendMode.BLEND_OPAQUE:r['issues'].append('Overdraw material '+path)
roof_ignore=[a for a in actors if not a.get_actor_label().startswith('RM_House_Roof_')]
r['roof_collision_samples']=[]
for x in (-1500,-750,0,750,1500):
 for y in (-1500,-750,0,750,1500):
  hit=trace(world,unreal.Vector(x,y,360),unreal.Vector(x,y,900),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,roof_ignore,unreal.DrawDebugTrace.NONE,True);h=hit.to_tuple() if hit else None
  r['roof_collision_samples'].append({'x':x,'y':y,'blocks':bool(h and h[0])})
  if not (h and h[0]):r['issues'].append('Roof gap '+str((x,y)))
r['roof_slabs']=sum(a.get_actor_label().startswith('RM_House_Roof_') for a in actors)
r['shadowed_new_lights']=sum(a.point_light_component.get_editor_property('cast_shadows') for a in actors if a.get_actor_label().startswith('LIGHT_House_Remaster_'))
r['new_unique_mesh_triangles']=sum(x['lod_triangles'][0] for x in r['meshes'] if '/Remaster/' in x['mesh'])
mat=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Masters/M_House_AgedSurface_World');st=M.get_statistics(mat);r['material_statistics']={k:st.get_editor_property(k) for k in ('num_pixel_shader_instructions','num_vertex_shader_instructions','num_pixel_texture_samples','num_samplers')}
if r['material_statistics']['num_pixel_shader_instructions']==0:r['issues'].append('Shader not compiled')
r['passed']=not r['issues']
with open(os.path.join(P,'Saved/HouseRemasterAudit.json'),'w') as f:json.dump(r,f,indent=2)
unreal.log('CODEX_REMASTER_AUDIT '+str(r['passed']))
