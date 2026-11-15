"""Capture Scene 03's actual solution as a photograph, restoring all staged transforms."""
import unreal,json,traceback
from pathlib import Path
P=Path(unreal.Paths.project_dir());ROOT='/Game/Game/Isolated/IbraCampaign'
A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
director=actors['CAMPAIGN_Director'];world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for old in list(A.get_all_level_actors()):
    if isinstance(old,unreal.SceneCapture2D) and old.get_actor_label()=='CAMPAIGN_ReferenceCapture':A.destroy_actor(old)
snapshot=[]
for i in [1,2]:
    actor=director.get_editor_property('S3Prop'+str(i));snapshot.append((actor,actor.get_actor_transform()))
    area=director.get_editor_property('S3Area'+str(i));actor.set_actor_location(area.get_actor_location(),False,True)
hidden=[]
for label,a in actors.items():
    if any(x in label for x in ['Maya','Crew','FinalPose','ReferenceCaption','ReferencePhoto','DirectorMark']):hidden.append((a,a.get_editor_property('hidden')));a.set_actor_hidden_in_game(True)
capture=A.spawn_actor_from_class(unreal.SceneCapture2D,unreal.Vector(1000,1470,190),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(1000,1470,190),unreal.Vector(1230,1220,70)))
capture.set_actor_label('CAMPAIGN_ReferenceCapture')
component=capture.get_component_by_class(unreal.SceneCaptureComponent2D);rt=unreal.RenderingLibrary.create_render_target2d(world,1024,768,unreal.TextureRenderTargetFormat.RTF_RGBA8)
component.set_editor_property('texture_target',rt);component.set_editor_property('capture_source',unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR);component.set_editor_property('fov_angle',60.)
state={'frames':0}

def tick(dt):
    if state.get('busy'):return
    state['frames']+=1
    if state['frames']<12:return
    state['busy']=True
    # Import/reimport can pump Slate recursively. Detach before touching assets.
    unreal.unregister_slate_post_tick_callback(handle)
    result={'success':False,'errors':[]}
    try:
        component.capture_scene()
        folder=P/'SourceArt/Isolated/IbraCampaign/Reference';folder.mkdir(parents=True,exist_ok=True)
        unreal.RenderingLibrary.export_render_target(world,rt,str(folder),'Scene03_Reference.png')
        task=unreal.AssetImportTask();task.set_editor_property('filename',str(folder/'Scene03_Reference.png'));task.set_editor_property('destination_path',ROOT+'/Reference');task.set_editor_property('destination_name','T_Scene03Reference');task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture=unreal.load_asset(ROOT+'/Reference/T_Scene03Reference');assert texture
        path=ROOT+'/Reference/M_Scene03Reference'
        mat=unreal.load_asset(path) if E.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Scene03Reference',ROOT+'/Reference',unreal.Material,unreal.MaterialFactoryNew())
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
        tex=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-250,0);tex.set_editor_property('texture',texture)
        unreal.MaterialEditingLibrary.connect_material_property(tex,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
        unreal.MaterialEditingLibrary.recompile_material(mat);E.save_loaded_asset(mat)
        actors['CAMPAIGN_ReferencePhoto'].static_mesh_component.set_material(0,mat)
        result.update(success=True,texture=texture.get_path_name(),source=str(folder/'Scene03_Reference.png'))
    except Exception:result['errors'].append(traceback.format_exc())
    finally:
        for actor,transform in snapshot:actor.set_actor_transform(transform,False,True)
        for actor,was_hidden in hidden:actor.set_actor_hidden_in_game(was_hidden)
        A.destroy_actor(capture)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        (P/'Saved/QA/CampaignReference.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

handle=unreal.register_slate_post_tick_callback(tick)
