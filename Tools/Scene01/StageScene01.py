"""Stage only L_Scene01. No viewport changes, PIE, tests, or input injection."""
import unreal,json,os
E=unreal.EditorAssetLibrary;S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
P=unreal.Paths.project_dir();ROOT='/Game/Game/Blueprints/Scene01/'
assert editor.get_game_world() is None
assert editor.get_editor_world().get_path_name()=='/Game/Game/Levels/Tests/L_Scene01.L_Scene01'
assert not any(a.get_actor_label()=='SYSTEM_Scene01Flow' for a in S.get_all_level_actors()),'Already staged'

# Expose references without editing shared Blueprint assets.
editables={
 'BP_Scene01FlowDirector':['Arrival','Dialogue','Maya','CrewA','CrewB','OpeningStandIn','OpeningSequence','Sofa','Wardrobe','SofaArea','WardrobeArea','DirectorMark','MayaStart','FailureMark','WalkMark','AisleMark','InspectMark','WideCamera','MediumCamera','DetailCamera','DirectorMarkRadius','DirectorMarkHeightTolerance','MayaSpeed'],
 'BP_Scene01DialoguePlayer':['DialogueTable','Maya','CrewA','CrewB','Volume'],
 'BP_Scene01ArrivalDirector':['SceneHUD','DoorHinge','Maya','CrewA','CrewB','Scene1Sofa','Scene1Wardrobe','DirectorSeatCamera'],
}
for name,variables in editables.items():
 bp=unreal.load_asset(ROOT+name)
 for variable in variables:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,variable,True)
 if name=='BP_Scene01FlowDirector':
  flags=[]
  for i in range(100):
   node=unreal.find_object(None,ROOT+name+'.'+name+':EventGraph.K2Node_InputKey_'+str(i))
   if node:
    key=str(node.get_editor_property('InputKey').get_editor_property('KeyName'))
    node.set_editor_property('bConsumeInput',False)
    node.set_editor_property('bExecuteWhenPaused',key=='P');flags.append(key)
  assert 'P' in flags and 'SpaceBar' in flags,flags
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)

labels={a.get_actor_label():a for a in S.get_all_level_actors()}
oldarrival=labels['FLOW_Arrival_Tutorial_LivingRoom']
refs={n:oldarrival.get_editor_property(n) for n in ['DoorHinge','Maya','CrewA','CrewB','DirectorSeatCamera']}

def spawn(cls,label,loc=(0,0,0),folder='Scene01/Systems'):
 a=S.spawn_actor_from_class(cls,unreal.Vector(*loc));assert a,label;a.set_actor_label(label);a.set_folder_path(folder);return a
def marker(label,loc,yaw=0):
 a=spawn(unreal.TargetPoint,label,loc,'Scene01/Markers');a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False);return a
def replace_prop(source,label,propid):
 old=labels[source];parent=old.get_attach_parent_actor();transform=old.get_actor_transform();mesh=old.static_mesh_component
 prop=spawn(unreal.load_asset('/Game/Game/Blueprints/Props/BP_InteractableProp').generated_class(),label,folder='Scene01/Props')
 prop.set_actor_transform(transform,False,False)
 comp=next(c for c in prop.get_components_by_class(unreal.StaticMeshComponent) if c.get_name()=='Mesh')
 comp.set_static_mesh(mesh.get_editor_property('static_mesh'));comp.set_mobility(unreal.ComponentMobility.MOVABLE);comp.set_relative_location(unreal.Vector(0,0,0),False,False)
 comp.set_collision_profile_name('BlockAllDynamic');comp.set_editor_property('generate_overlap_events',True)
 for index in range(mesh.get_num_materials()):comp.set_material(index,mesh.get_material(index))
 prop.set_editor_property('PropID',unreal.Name(propid));prop.set_editor_property('SceneID',unreal.Name('Scene01'));prop.set_editor_property('CurrentSlotID',unreal.Name('None'))
 if parent:prop.attach_to_actor(parent,'',unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,unreal.AttachmentRule.KEEP_WORLD,False)
 S.destroy_actor(old);return prop

sofa=replace_prop('PROP_House_Living_Sofa_ThreeSeat_01','PROP_Scene01_Sofa_Interactable','Scene01_Sofa')
wardrobe=replace_prop('PROP_Scene01_Wardrobe','PROP_Scene01_Wardrobe_Interactable','Scene01_Wardrobe')
# Remove one decorative sofa from this copy to create space for the movable
# wardrobe and preserve the existing seated conversation camera/armchair.
S.destroy_actor(labels['PROP_House_Living_Sofa_TwoSeat_02'])
for label in ['PROP_House_Living_Table_Side_01','PROP_House_Living_Lamp_Desk_02']:S.destroy_actor(labels[label])
S.destroy_actor(oldarrival);S.destroy_actor(labels['FLOW_Opening_ToScene01'])
# Disable any older preview/test orchestration in this copied level only.
for a in list(S.get_all_level_actors()):
 if a.get_class().get_name() in ['BP_FilmSceneManager_C','BP_TestScene01_C']:
  S.destroy_actor(a)

arrival=spawn(unreal.load_asset(ROOT+'BP_Scene01ArrivalDirector').generated_class(),'FLOW_Scene01_Arrival')
for n,v in refs.items():arrival.set_editor_property(n,v)
arrival.set_editor_property('Scene1Sofa',sofa);arrival.set_editor_property('Scene1Wardrobe',wardrobe)
dialogue=spawn(unreal.load_asset(ROOT+'BP_Scene01DialoguePlayer').generated_class(),'SYSTEM_Scene01Dialogue')
for n in ['Maya','CrewA','CrewB']:dialogue.set_editor_property(n,refs[n])
dialogue.set_editor_property('DialogueTable',unreal.load_asset('/Game/Game/Audio/Scene01/DT_Scene01Dialogue'))
flow=spawn(unreal.load_asset(ROOT+'BP_Scene01FlowDirector').generated_class(),'SYSTEM_Scene01Flow')
for n,v in [('Arrival',arrival),('Dialogue',dialogue),('Sofa',sofa),('Wardrobe',wardrobe),('OpeningStandIn',labels['CINE_Opening_Maya_StandIn'])]+[(n,refs[n]) for n in ['Maya','CrewA','CrewB']]:flow.set_editor_property(n,v)

mark=marker('MARK_Scene01_Director',(180,300,0),-90);flow.set_editor_property('DirectorMark',mark)
for name,loc,yaw in [('MayaStart',(-400,-440,0),90),('FailureMark',(-400,-385,0),90),('WalkMark',(-400,-70,0),90),('AisleMark',(-190,-260,0),0),('InspectMark',(180,-300,0),-45)]:
 flow.set_editor_property(name,marker('MARK_Scene01_'+name,loc,yaw))

areas=[]
for name,prop,loc,radius in [('Sofa',sofa,(146.8,0,0),35),('Wardrobe',wardrobe,(-27.15,290,0),35)]:
 area=spawn(unreal.load_asset('/Game/Game/Blueprints/Gameplay/Testing/BP_PlacementArea').generated_class(),'AREA_Scene01_'+name,loc,'Scene01/SolutionAreas')
 area.set_editor_property('AllowedProp',prop);area.set_editor_property('Radius',float(radius));area.set_actor_hidden_in_game(True)
 flow.set_editor_property(name+'Area',area);areas.append({'prop':name,'center':loc,'radius':radius})

cube=unreal.load_asset('/Engine/BasicShapes/Cube')
def block(label,loc,scale,material,collision=True):
 a=spawn(unreal.StaticMeshActor,label,loc,'Scene01/SetDressing');a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_static_mesh(cube)
 a.static_mesh_component.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
 if material:a.static_mesh_component.set_material(0,material)
 return a
plaster=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Remaster/MI_House_Timber_AgedIvory')
clue=block('CLUE_Scene01_PatchedDoorway',(320,-488,120),(1.35,.025,2.35),plaster,False)
# Narrow border makes the old doorway legible through the detailed camera.
dark=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Burgundy')
for label,loc,scale in [('Left',(250,-485,120),(.025,.025,2.4)),('Right',(390,-485,120),(.025,.025,2.4)),('Top',(320,-485,240),(1.42,.025,.025))]:block('CLUE_Scene01_Seam_'+label,loc,scale,dark,False)

def camera(name,loc,target,focal):
 a=spawn(unreal.CineCameraActor,'CINE_Scene01_'+name,loc,'Scene01/Cameras');a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False)
 c=a.get_cine_camera_component();c.set_editor_property('current_focal_length',float(focal));focus=c.get_editor_property('focus_settings');focus.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE);c.set_editor_property('focus_settings',focus)
 flow.set_editor_property(name+'Camera',a)
 return a
camera('Wide',(-120,290,165),(-390,-240,110),24)
camera('Medium',(-145,30,155),(-400,-180,110),32)
camera('Detail',(70,-230,155),(310,-475,125),30)

# A floor mark remains visible, while solution areas remain hidden.
mat=unreal.load_asset('/Game/Game/Materials/GameplayTesting/M_DirectorMark')
pad=spawn(unreal.StaticMeshActor,'SET_Scene01_DirectorMark',(180,300,1),'Scene01/SetDressing');pad.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cylinder'));pad.static_mesh_component.set_collision_profile_name('NoCollision');pad.set_actor_scale3d(unreal.Vector(1.1,1.1,.005))
if mat:pad.static_mesh_component.set_material(0,mat)
label=spawn(unreal.TextRenderActor,'SET_Scene01_DirectorMarkLabel',(150,325,3),'Scene01/SetDressing');label.set_actor_rotation(unreal.Rotator(pitch=90,yaw=0,roll=0),False);label.text_render.set_text('DIRECTOR');label.text_render.set_world_size(12);label.text_render.set_text_render_color(unreal.Color(240,200,70,255));label.set_actor_enable_collision(False)

# Rebuild the copied opening sequence's bindings against this map. A static
# close-up pauses at 2 seconds for VO, then resumes into fade/title at completion.
seq=unreal.load_asset('/Game/Game/Cinematics/Scene01/LS_Scene01Opening')
for b in list(seq.get_bindings()):b.remove()
for t in list(seq.get_tracks()):seq.remove_track(t)
seq.set_display_rate(unreal.FrameRate(30,1));seq.set_playback_start(0);seq.set_playback_end(240)
cam=labels['CINE_Opening_Camera_Closeup'];binding=seq.add_possessable(cam)
t=binding.add_track(unreal.MovieScene3DTransformTrack);section=t.add_section();section.set_range(0,240)
loc=cam.get_actor_location();rot=cam.get_actor_rotation()
for ch,v in zip(section.get_all_channels(),[loc.x,loc.y,loc.z,rot.roll,rot.pitch,rot.yaw,1,1,1]):ch.set_default(float(v))
cuts=seq.add_track(unreal.MovieSceneCameraCutTrack);cut=cuts.add_section();cut.set_range(0,240);bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',binding.get_id());cut.set_camera_binding_id(bid)
maya=seq.add_possessable(labels['CINE_Opening_Maya_StandIn']);anim=maya.add_track(unreal.MovieSceneSkeletalAnimationTrack).add_section();anim.set_range(0,240);params=anim.get_editor_property('params');params.set_editor_property('animation',unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'));anim.set_editor_property('params',params)
fade=seq.add_track(unreal.MovieSceneFadeTrack).add_section();fade.set_range(0,240)
for frame,value in [(0,1.),(30,1.),(60,0.),(90,0.),(120,1.),(239,1.)]:fade.get_all_channels()[0].add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
fade.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
audio=seq.add_track(unreal.MovieSceneAudioTrack).add_section();audio.set_sound(unreal.load_asset('/Game/Game/Audio/Cinematics/S_Opening_CameraPower'));audio.set_range(0,21)
E.save_loaded_asset(seq);flow.set_editor_property('OpeningSequence',seq)
editor.get_editor_world().get_world_settings().set_editor_property('default_game_mode',unreal.load_asset(ROOT+'BP_Scene01GameMode').generated_class())
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
json.dump({'map':'/Game/Game/Levels/Tests/L_Scene01','tests_run':False,'pie_run':False,'packaging_run':False,'actors':len(S.get_all_level_actors()),'solution_areas':areas,'opening_sequence':seq.get_path_name(),'game_mode':ROOT+'BP_Scene01GameMode'},open(P+'Saved/Scene01Build/staging.json','w'),indent=2)
unreal.log('SCENE01_STAGED: authoring only; no runtime testing')
