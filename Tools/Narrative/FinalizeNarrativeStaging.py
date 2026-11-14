"""Finalize failure feedback and diegetic production equipment, without implementing take logic."""
import unreal,json,math
P=unreal.Paths.project_dir();E=unreal.EditorAssetLibrary;S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);A={a.get_actor_label():a for a in S.get_all_level_actors()};D=json.load(open(P+'Tools/Narrative/NarrativeFlow.json'));R=json.load(open(P+'Saved/NarrativeBuildReport.json'));maya=A['SET_Scene01_Maya_StandIn'];idle=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle');walk=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd')
def visibility(q,a,end,show=True):
 b=q.add_possessable(a);t=b.add_track(unreal.MovieSceneVisibilityTrack);s=t.add_section();s.set_range(0,end);s.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE);s.get_all_channels()[0].set_default(show)
def equipment(label,kind,parent,offset):
 a=A.get(label) or S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0));a.set_actor_label(label);a.set_folder_path('Cinematics/Narrative/ProductionEquipment');c=a.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Game/Game/Art/Environment/House/Meshes/Props/SM_House_'+kind));c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_profile_name('NoCollision');a.attach_to_actor(parent,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False);a.set_actor_relative_location(unreal.Vector(*offset),False,False);a.set_actor_hidden_in_game(True);return a
case=equipment('NAR_Carry_ProductionCase','FlightCase_Black',A['NPC_Intro_CrewA_PropMaster'],(0,65,65));kit=equipment('NAR_Carry_LightingStand','Lamp_Floor',A['NPC_Intro_CrewB_SetDresser'],(0,65,25));trolley=equipment('NAR_Carry_EquipmentTrolley','FlightCase_Black',A['NPC_Intro_CrewC_Lobby'],(0,75,0))
# Small clapperboard is a reused low-poly box with contrasting top stripes.
clap=A.get('NAR_Carry_Clapperboard') or S.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0));clap.set_actor_label('NAR_Carry_Clapperboard');c=clap.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_profile_name('NoCollision');c.set_material(0,unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Exterior/MI_House_Exterior_Metal'));clap.set_actor_scale3d(unreal.Vector(.35,.025,.28));clap.attach_to_component(A['NPC_Intro_CrewC_Lobby'].skeletal_mesh_component,'hand_r',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False);clap.set_actor_relative_location(unreal.Vector(5,0,0),False,False);clap.set_actor_hidden_in_game(True)
for idx,items in [(4,[case,kit]),(6,[kit,trolley]),(11,[trolley]),(19,[case,kit,clap])]:
 q=unreal.load_asset(R['sequences'][idx]['path']);end=q.get_playback_end()
 for a in items:visibility(q,a,end)
 E.save_loaded_asset(q)
for idx in [1,2,8,9,15,16]:
 q=unreal.load_asset(R['sequences'][idx]['path']);end=q.get_playback_end();b=next(b for b in q.get_bindings() if b.get_name()==maya.get_name()) if False else None
 # Find the existing actor binding by its stored object path instead of display name.
 for candidate in q.get_bindings():
  if candidate.get_possessed_object_class()==unreal.SkeletalMeshActor and any(isinstance(t,unreal.MovieScene3DTransformTrack) for t in candidate.get_tracks()):b=candidate;break
 if b is None:continue
 for t in list(b.get_tracks()):
  if isinstance(t,(unreal.MovieScene3DTransformTrack,unreal.MovieSceneSkeletalAnimationTrack)):b.remove_track(t)
 if idx==1:pts=[(-190,260,0),(-190,190,0),(-150,200,0),(-190,190,0)];yaw=65;cam=A['NAR_Cam_S1_Walk']
 elif idx==2:pts=[(160,-280,0),(160,-360,0),(160,-360,0),(160,-360,0)];yaw=110;cam=A['NAR_Cam_S1_Conversation']
 elif idx==8:pts=[(1050,-150,0),(1050,-50,0),(1050,-50,0),(1050,-50,0)];yaw=180;cam=A['NAR_Cam_S2_Tracking']
 elif idx==9:pts=[(1120,100,0),(1120,220,0),(1120,220,0),(1120,220,0)];yaw=162;cam=A['NAR_Cam_S2_Conversation']
 else:pts=[(1100,920,0),(1100,850,0),(1100,850,0),(1100,850,0)];yaw=0;cam=A['NAR_Cam_S3_Entry']
 tr=b.add_track(unreal.MovieScene3DTransformTrack);s=tr.add_section();s.set_range(0,end);s.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
 for i,(f,p) in enumerate(zip([0,45,65,90],pts)):
  vals=list(p)+[0,0,yaw+(20 if i==2 else 0),1,1,1]
  for ch,v in zip(s.get_all_channels(),vals):ch.add_key(unreal.FrameNumber(f),float(v),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 for lo,hi,asset in [(0,45,walk),(45,end,idle)]:
  tr=b.add_track(unreal.MovieSceneSkeletalAnimationTrack);sec=tr.add_section();sec.set_range(lo,hi);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE);params=sec.params;params.animation=asset;sec.params=params
 for t in list(q.get_tracks()):
  if isinstance(t,unreal.MovieSceneCameraCutTrack):q.remove_track(t)
 cb=q.add_possessable(cam);tr=q.add_track(unreal.MovieSceneCameraCutTrack);sec=tr.add_section();sec.set_range(0,end);bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',cb.get_id());sec.set_camera_binding_id(bid);E.save_loaded_asset(q)
 R['routes']=[r for r in R['routes'] if r['beat']!=idx];R['routes'].append({'beat':idx,'actor':maya.get_actor_label(),'points':pts,'start':0,'end':3})
# Explicit role tags and runtime IDs aid teammate discovery.
for label,tags in [('PROP_House_Living_Sofa_ThreeSeat_01',['Scene01','Sofa']),('PROP_Scene01_Wardrobe',['Scene01','Wardrobe']),('NAR_Prop_Scene02_Cabinet',['Scene02','Cabinet']),('NAR_Prop_Scene02_PracticalLamp',['Scene02','Lamp']),('NAR_Prop_Scene03_Chair',['Scene03','Chair']),('NAR_Prop_Scene03_StandingLamp',['Scene03','Lamp'])]:A[label].tags=tags
for a in S.get_all_level_actors():
 if a.get_actor_label().startswith('NAR_Marker_Scene') and '_PropSlot_' in a.get_actor_label():S.destroy_actor(a)
json.dump(R,open(P+'Saved/NarrativeBuildReport.json','w'),indent=2);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
