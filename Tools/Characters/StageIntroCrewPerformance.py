"""Stage compatible Tripo meshes for the intro, opening, crew and interlude cast."""
import unreal
assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors={a.get_actor_label():a for a in sub.get_all_level_actors()}
M='/Game/Game/Characters/Maya/';C='/Game/Game/Characters/Crew/'
mesh=unreal.load_asset(M+'SK_Maya');idle=unreal.load_asset(M+'Animations/A_Maya_ReadScript')
crew_mesh={n:unreal.load_asset(C+v) for n,v in {'A':'SK_Crew_Camera','B':'SK_Crew_Boom','Utility':'SK_Crew_Base'}.items()}
crew_idle=unreal.load_asset(C+'Animations/A_Crew_Idle');abp=unreal.load_asset('/Game/Game/Blueprints/Crew/ABP_Crew')
skeleton=crew_mesh['Utility'].get_editor_property('skeleton')
# Preserve the existing shared role IK graph and its public variables/casts.
graph=unreal.BlueprintEditorLibrary.find_graph(abp,'AnimGraph')
for node in unreal.ObjectIterator(unreal.AnimGraphNode_SequencePlayer):
 if node.get_outer()==graph:
  params=node.get_editor_property('node')
  params.set_editor_property('sequence',unreal.load_asset(C+'Animations/'+('A_Crew_Focused' if node.get_name().endswith('_0') else 'A_Crew_Idle')))
  node.set_editor_property('node',params)
abp.set_editor_property('target_skeleton',skeleton);unreal.BlueprintEditorLibrary.compile_blueprint(abp)
unreal.EditorAssetLibrary.save_loaded_asset(abp);unreal.EditorAssetLibrary.save_loaded_asset(skeleton)
def set_mesh(component,asset,animation=None):
 component.set_skeletal_mesh_asset(asset)
 component.set_editor_property('override_materials',[])
 for i,slot in enumerate(asset.get_editor_property('materials')):
  component.set_material(i,slot.material_interface)
 if animation:
  component.set_anim_instance_class(None);component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
  data=component.get_editor_property('animation_data');data.set_editor_property('anim_to_play',animation);data.set_editor_property('saved_looping',True);data.set_editor_property('saved_playing',True);component.set_editor_property('animation_data',data)
 component.set_update_animation_in_editor(True)
for label in ['CINE_Opening_Maya_StandIn','SET_Scene01_Maya_StandIn']:
 if label in actors:set_mesh(actors[label].skeletal_mesh_component,mesh,unreal.load_asset(M+'Animations/A_Maya_Confession') if label=='CINE_Opening_Maya_StandIn' else idle)
paper=actors.get('PROP_Intro_Maya_Script')
if paper:
 # Skeletal bone scale carries FBX units; the paper uses centimeters, so attach to the component root.
 paper.attach_to_component(actors['SET_Scene01_Maya_StandIn'].skeletal_mesh_component,unreal.Name('None'),unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
 paper.set_actor_relative_location(unreal.Vector(0,32,124),False,True)
 paper.set_actor_relative_rotation(unreal.Rotator(pitch=0,yaw=0,roll=60),False,True)
 paper.set_actor_scale3d(unreal.Vector(.23,.002,.31))
for label,n in {'NPC_Intro_CrewA_PropMaster':'Utility','NPC_Intro_CrewB_SetDresser':'A','NPC_Intro_CrewC_Lobby':'B','TR02_Crew_B':'B','TR02_Crew_C':'Utility'}.items():
 if label in actors:set_mesh(actors[label].skeletal_mesh_component,crew_mesh[n],crew_idle)
# Old CopyPose followers remain hidden; copying mannequin transforms is invalid on these bind rigs.
for a in actors.values():
 if a.get_class().get_name()=='BP_TripoFollower_C':a.set_actor_hidden_in_game(True)
# New instances of BP_CrewMember also inherit a compatible mesh.
crew_bp=unreal.load_asset('/Game/Game/Blueprints/Crew/BP_CrewMember')
data_sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for handle in data_sub.k2_gather_subobject_data_for_blueprint(crew_bp):
 data=unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle);obj=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
 if isinstance(obj,unreal.SkeletalMeshComponent):
  set_mesh(obj,crew_mesh['Utility']);obj.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT);obj.set_anim_instance_class(abp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(crew_bp);unreal.EditorAssetLibrary.save_loaded_asset(crew_bp)
for label,n in {'Crew_Camera':'A','Crew_Boom':'B','Crew_Gaffer':'Utility','Crew_Script':'B'}.items():
 a=actors[label];body=a.get_component_by_class(unreal.SkeletalMeshComponent)
 set_mesh(body,crew_mesh[n]);body.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
 body.set_anim_instance_class(abp.generated_class())

for label in ['Crew_Camera','Crew_Boom','Crew_Gaffer','Crew_Script','NPC_Intro_CrewA_PropMaster','NPC_Intro_CrewB_SetDresser','NPC_Intro_CrewC_Lobby','TR02_Crew_B','TR02_Crew_C']:
 if label in actors:actors[label].set_actor_hidden_in_game(True)

# Frame the script-reading mark and light Maya's face during the seated conversation.
seat=actors.get('CINE_Arrival_Director_Seated')
if seat:
 seat.set_actor_location_and_rotation(unreal.Vector(-385,210,155),unreal.Rotator(pitch=-3,yaw=-53,roll=0),False,True)
key=actors.get('CINE_Intro_Maya_Key')
if not key:
 key=sub.spawn_actor_from_class(unreal.RectLight,unreal.Vector(-330,175,210));key.set_actor_label('CINE_Intro_Maya_Key');key.set_folder_path('Cinematics/Arrival/Lighting')
key.set_actor_rotation(unreal.Rotator(pitch=-20,yaw=-58,roll=0),False)
light=key.get_component_by_class(unreal.RectLightComponent)
for prop,value in [('intensity_units',unreal.LightUnits.LUMENS),('intensity',200.0),('attenuation_radius',450.0),('source_width',100.0),('source_height',100.0),('use_temperature',True),('temperature',4500.0),('cast_shadows',False)]:light.set_editor_property(prop,value)
key.set_actor_hidden_in_game(False)
take=actors.get('MAYA_Take')
if take:
 hidden=list(take.get_editor_property('StandInsToHide'))
 if key not in hidden:hidden.append(key)
 for label in ['NPC_Intro_CrewA_PropMaster','NPC_Intro_CrewB_SetDresser','NPC_Intro_CrewC_Lobby']:
  if label in actors and actors[label] not in hidden:hidden.append(actors[label])
 take.set_editor_property('StandInsToHide',hidden)
# Opening keeps its original camera and timing, with a compatible, subtle performance.
seq=unreal.load_asset('/Game/Game/Cinematics/Opening/LS_Opening_Maya')
for binding in seq.get_bindings():
 for track in binding.get_tracks():
  if isinstance(track,unreal.MovieSceneSkeletalAnimationTrack):
   for section in track.get_sections():
    params=section.get_editor_property('params');params.set_editor_property('animation',unreal.load_asset(M+'Animations/A_Maya_Confession'));params.set_editor_property('force_custom_mode',True);section.set_editor_property('params',params)
unreal.EditorAssetLibrary.save_loaded_asset(seq)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('INTRO_CREW_STAGED')
