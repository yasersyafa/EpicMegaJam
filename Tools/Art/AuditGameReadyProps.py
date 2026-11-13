"""PC prop asset gate. Also removes buffers and tiny section shadows unused here."""
import unreal, json, os
project=unreal.Paths.project_dir()
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
root='/Game/Game/Art/Environment/House/Meshes/Props'
actors=[a for a in sub.get_all_level_actors() if a.get_actor_label().startswith('PROP_House_')]
report={'target':'Current Windows PC editor; asset validation, not a minimum-hardware FPS guarantee','issues':[],'assets':[],'optimizations':[]}
report['positive_scale_only']=all(min(a.get_actor_scale3d().to_tuple())>0 for a in actors)
if not report['positive_scale_only']:report['issues'].append('Mirrored props require reversed index buffers')
mesh_by_path={a.static_mesh_component.static_mesh.get_path_name():a.static_mesh_component.static_mesh for a in actors}
for path,mesh in sorted(mesh_by_path.items()):
    lods=[];changed=False
    for lod in range(editor.get_lod_count(mesh)):
        build=editor.get_lod_build_settings(mesh,lod)
        before={key:build.get_editor_property(key) for key in ('build_reversed_index_buffer','use_full_precision_u_vs','use_high_precision_tangent_basis')}
        if report['positive_scale_only'] and before['build_reversed_index_buffer']:
            build.set_editor_property('build_reversed_index_buffer',False)
            editor.set_lod_build_settings(mesh,lod,build)
            changed=True
            report['optimizations'].append({'mesh':mesh.get_name(),'lod':lod,'change':'Removed unused reversed index buffer'})
        sections=mesh.get_num_sections(lod)
        disabled=[]
        for section in range(sections):
            slot_index=editor.get_lod_material_slot(mesh,lod,section)
            if slot_index>=0 and slot_index<len(mesh.static_materials):
                name=str(mesh.static_materials[slot_index].material_slot_name)
                if name in ('Paper','Ink','Bulb','Mirror') and editor.is_section_cast_shadow_enabled(mesh,lod,section):
                    editor.enable_section_cast_shadow(mesh,False,lod,section)
                    disabled.append(name);changed=True
        if disabled:report['optimizations'].append({'mesh':mesh.get_name(),'lod':lod,'change':'Disabled tiny decoration shadow sections','slots':disabled})
        lods.append({'triangles':mesh.get_num_triangles(lod),'vertices':mesh.get_num_vertices(lod),'sections':sections,'uv_channels':editor.get_num_uv_channels(mesh,lod),'reversed_index_buffer':editor.get_lod_build_settings(mesh,lod).get_editor_property('build_reversed_index_buffer')})
    if changed:unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    slots=[]
    for slot in mesh.static_materials:
        mat=slot.material_interface
        if not mat:report['issues'].append('Missing material on '+mesh.get_name());continue
        blend=mat.get_blend_mode()
        if blend!=unreal.BlendMode.BLEND_OPAQUE:report['issues'].append('Non-opaque prop material on '+mesh.get_name())
        slots.append({'name':str(slot.material_slot_name),'material':mat.get_path_name(),'blend':str(blend)})
    collision=editor.get_simple_collision_count(mesh)+editor.get_convex_collision_count(mesh)
    decorative=any(word in mesh.get_name() for word in ('Rug_','Lamp_','Mirror_'))
    if lods[0]['triangles']>6000:report['issues'].append('Above 6000 triangle prop budget: '+mesh.get_name())
    if len(slots)>5:report['issues'].append('Above 5 slot hero-prop ceiling: '+mesh.get_name())
    if lods[0]['triangles']>800 and len(lods)<3:report['issues'].append('Missing distance LODs: '+mesh.get_name())
    if not decorative and collision!=1:report['issues'].append('Expected one convex hull: '+mesh.get_name())
    if decorative and collision:report['issues'].append('Unnecessary decoration collision: '+mesh.get_name())
    # UE GetNumUVChannels reads authored MeshDescription, absent on generated LODs.
    if lods[0]['uv_channels']<1:report['issues'].append('Missing UV channels: '+mesh.get_name())
    report['assets'].append({'mesh':mesh.get_path_name(),'lods':lods,'material_slots':slots,'collision_shapes':collision})
by_mesh={a['mesh']:a for a in report['assets']}
report['prop_actors']=len(actors)
report['unique_meshes']=len(mesh_by_path)
report['unique_library_lod0_triangles']=sum(a['lods'][0]['triangles'] for a in report['assets'])
report['scene_lod0_triangles_before_culling']=sum(by_mesh[a.static_mesh_component.static_mesh.get_path_name()]['lods'][0]['triangles'] for a in actors)
report['scene_lod2_triangles_before_culling']=sum(by_mesh[a.static_mesh_component.static_mesh.get_path_name()]['lods'][-1]['triangles'] for a in actors)
report['all_static']=all(a.static_mesh_component.mobility==unreal.ComponentMobility.STATIC for a in actors)
if not report['all_static']:report['issues'].append('A prop has unnecessary movable mobility')
report['mesh_draw_command_instancing']=unreal.SystemLibrary.get_console_variable_int_value('r.MeshDrawCommands.DynamicInstancing')
report['lights']=[{'actor':a.get_actor_label(),'cast_shadows':a.point_light_component.get_editor_property('cast_shadows'),'radius':a.point_light_component.get_editor_property('attenuation_radius')} for a in sub.get_all_level_actors() if a.get_actor_label().startswith('LIGHT_House_')]
report['passed']=not report['issues']
with open(os.path.join(project,'Saved','HousePropsGameReadyAudit.json'),'w') as f:json.dump(report,f,indent=2)
unreal.log('CODEX_GAME_READY_ASSET_GATE '+str(report['passed']))
