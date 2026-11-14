"""Author section 05-14 cinematic assets. Runtime is Blueprint + Level Sequence."""
import unreal,json,os,math,traceback
P=unreal.Paths.project_dir();E=unreal.EditorAssetLibrary;S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);T=unreal.AssetToolsHelpers.get_asset_tools();D=json.load(open(P+'Tools/Narrative/NarrativeFlow.json'));R={'success':False,'sequences':[],'routes':[],'errors':[]}
ROOT='/Game/Game/Cinematics/Narrative';A={a.get_actor_label():a for a in S.get_all_level_actors()};idle=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle');walk=unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd');sit=unreal.load_asset('/Game/Game/Cinematics/Animations/A_Maya_Record_Seated');stand=unreal.load_asset('/Game/Game/Cinematics/Animations/A_Maya_Record_Stand');maya=A['SET_Scene01_Maya_StandIn'];crew=[A['NPC_Intro_CrewA_PropMaster'],A['NPC_Intro_CrewB_SetDresser'],A['NPC_Intro_CrewC_Lobby']]
def spawn(cls,label,pos,yaw=0):
 a=A.get(label) or S.spawn_actor_from_class(cls,unreal.Vector(*pos));a.set_actor_label(label);a.set_folder_path('Cinematics/Narrative/Staging');a.set_actor_location(unreal.Vector(*pos),False,False);a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False);A[label]=a;return a
def prop(label,kind,pos,yaw=0,scale=(1,1,1),collision='BlockAll'):
 a=spawn(unreal.StaticMeshActor,label,pos,yaw);a.set_actor_scale3d(unreal.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Game/Game/Art/Environment/House/Meshes/Props/SM_House_'+kind));c.set_mobility(unreal.ComponentMobility.MOVABLE);c.set_collision_profile_name(collision);return a
def box(label,pos,size,mat):
 a=spawn(unreal.StaticMeshActor,label,pos);c=a.static_mesh_component;c.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'));a.set_actor_scale3d(unreal.Vector(*(x/100 for x in size)));c.set_collision_profile_name('NoCollision');c.set_material(0,unreal.load_asset(mat));return a
def text(label,pos,string,yaw=0,size=12):
 a=spawn(unreal.TextRenderActor,label,pos,yaw);a.text_render.set_text(string);a.text_render.set_world_size(size);a.text_render.set_text_render_color(unreal.Color(35,29,22,255));return a
def camera(label,pos,target,focal=35):
 a=spawn(unreal.CineCameraActor,label,pos);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False);c=a.get_cine_camera_component();c.set_editor_property("current_focal_length",focal);f=c.focus_settings;f.focus_method=unreal.CameraFocusMethod.DISABLE;c.focus_settings=f;return a
bindings={}
def bind(seq,a):
 k=a.get_path_name()
 if k not in bindings:bindings[k]=seq.add_possessable(a)
 return bindings[k]
def transform(seq,a,keys,end,restore=False):
 b=bind(seq,a);t=b.add_track(unreal.MovieScene3DTransformTrack);sec=t.add_section();sec.set_range(0,end);sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE if restore else unreal.MovieSceneCompletionMode.KEEP_STATE);ch=sec.get_all_channels()
 for frame,pos,yaw in keys:
  vals=list(pos)+[0.,0.,float(yaw),1.,1.,1.]
  # Preserve the actor's scale. Cameras and mannequins are unit scale.
  sc=a.get_actor_scale3d();vals[6:]=[sc.x,sc.y,sc.z]
  for x,v in zip(ch,vals):x.add_key(unreal.FrameNumber(int(frame)),float(v),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
 return b
def visible(seq,a,start,end,hidden=False,restore=True):
 b=bind(seq,a);t=b.add_track(unreal.MovieSceneVisibilityTrack);t.set_property_name_and_path('bHidden','bHidden');s=t.add_section();s.set_range(start,end);s.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE if restore else unreal.MovieSceneCompletionMode.KEEP_STATE);s.get_all_channels()[0].set_default(not hidden)
def anim(seq,a,asset,start,end):
 b=bind(seq,a);t=b.add_track(unreal.MovieSceneSkeletalAnimationTrack);s=t.add_section();s.set_range(int(start),int(end));s.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE);p=s.params;p.animation=asset;s.params=p

def route(seq,a,points,start,end,label):
 # Points are feet coordinates in centimeters; travel time follows segment length.
 dist=[math.dist(x,y) for x,y in zip(points,points[1:])];total=sum(dist)
 if label==4 and a!=crew[2]:end=min(end,start+total/70.)
 times=[start];acc=start
 for v in dist:acc+=(end-start)*v/max(total,.01);times.append(acc)
 keys=[]
 for i,(pt,tm) in enumerate(zip(points,times)):
  j=min(i,len(points)-2);v=(points[j+1][0]-points[j][0],points[j+1][1]-points[j][1]);yaw=math.degrees(math.atan2(v[1],v[0]))-90;keys.append((round(tm*30),pt,yaw))
 transform(seq,a,keys,round(D['blocks'][label]['duration']*30));anim(seq,a,walk,round(start*30),max(round(start*30)+1,round(end*30)-1));anim(seq,a,idle,max(0,round(end*30)-1),round(D['blocks'][label]['duration']*30));R['routes'].append({'beat':label,'actor':a.get_actor_label(),'points':points,'start':start,'end':end})

def shots(seq,entries,end):
 t=seq.add_track(unreal.MovieSceneCameraCutTrack)
 for lo,hi,cam in entries:
  b=bind(seq,cam);s=t.add_section();s.set_range(round(lo*30),min(end,round(hi*30)));bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',b.get_id());s.set_camera_binding_id(bid)

def fade(seq,end,blackout=False):
 t=seq.add_track(unreal.MovieSceneFadeTrack);s=t.add_section();s.set_range(0,end);s.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE);ch=s.get_all_channels()[0]
 keys=[(0,0.),(end-46 if idx==19 else end-2,0.),(end-45 if idx==19 else end-1,1.)] if blackout else [(0,1.),(12,0.),(end-13,0.),(end-1,1.)]
 for f,v in keys:ch.add_key(unreal.FrameNumber(f),v,interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT if blackout else unreal.MovieSceneKeyInterpolation.LINEAR)
try:
 # Re-dress the final room while retaining original actors for reversible recovery.
 for name in ['PROP_House_HiddenRoom_Desk_Office_01','PROP_House_HiddenRoom_Lamp_Desk_04','PROP_House_HiddenRoom_Chair_Dining_12','PROP_House_HiddenRoom_Chair_Dining_13','PROP_House_HiddenRoom_Cabinet_Tall_01']:
  a=A.get(name)
  if a:a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.static_mesh_component.set_collision_profile_name('NoCollision')
 if 'PROP_House_Dining_FlightCase_Black_01' in A:A['PROP_House_Dining_FlightCase_Black_01'].set_actor_location(unreal.Vector(450,-1420,0),False,False)
 small=prop('NAR_Prop_Scene02_Cabinet','Console',(1300,-100,0));lamp2=prop('NAR_Prop_Scene02_PracticalLamp','Lamp_Floor',(1250,220,0));chair=prop('NAR_Prop_Scene03_Chair','Chair_Dining',(1230,980,0),180);lamp3=prop('NAR_Prop_Scene03_StandingLamp','Lamp_Floor',(1410,1000,0));table=prop('NAR_Prop_Scene03_PhotoTable','Table_Side',(1100,750,0))
 paper='/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Paper';plaster='/Game/Game/Art/Environment/House/Materials/Instances/Remaster/MI_House_Plaster_Sage'
 clue1=box('NAR_Clue_Scene01_PatchedOpening',(250,-578,155),(160,2,220),plaster);clue2=box('NAR_Clue_Scene02_SealedDoorway',(1150,378,150),(180,2,250),plaster)
 for x in (160,340):box('NAR_Clue_Scene01_Seam_'+str(x),(x,-575,155),(2,1,220),paper)
 for x in (1050,1250):box('NAR_Clue_Scene02_Seam_'+str(x),(x,375,150),(2,1,250),paper)
 photo=box('NAR_Prop_Scene03_ReferencePhoto',(1100,750,57),(25,34,1),paper)
 intercom=box('NAR_Prop_Final_Intercom',(905,1190,140),(12,25,35),paper);text('NAR_Label_Intercom',(915,1185,145),'PRODUCTION\nINTERCOM',0,4)
 # One close-up source and one uncropped frame: all monologues share this physical camera.
 master=spawn(unreal.SkeletalMeshActor,'NAR_Master_Maya',(1230,1220,0));master.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'));master.skeletal_mesh_component.set_collision_profile_name('NoCollision');master.skeletal_mesh_component.override_animation_data(sit,is_looping=True,is_playing=True);master.set_actor_hidden_in_game(True)
 recchair=prop('NAR_Master_RecordingChair','Chair_Dining',(1230,1220,0),180,collision='NoCollision');recchair.set_actor_hidden_in_game(True)
 camMaster=A['CINE_Opening_Camera_Closeup'];bodies=[]
 for i,(x,y) in enumerate([(990,760),(1480,760),(990,480),(1480,480)]):
  a=spawn(unreal.SkeletalMeshActor,'NAR_Master_Body_'+str(i),(x,y,25));a.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'));a.skeletal_mesh_component.set_collision_profile_name('NoCollision');a.skeletal_mesh_component.override_animation_data(idle,is_looping=True,is_playing=True);a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=90),False);a.set_actor_hidden_in_game(True);bodies.append(a)
 # Original opening now uses the same seated mannequin performance and chair.
 opening=unreal.load_asset('/Game/Game/Cinematics/Opening/LS_Opening_Maya');proxy=A.get('CINE_Opening_Maya_StandIn')
 if proxy:proxy.set_actor_location(unreal.Vector(1230,1220,0),False,False);proxy.skeletal_mesh_component.override_animation_data(sit,is_looping=True,is_playing=True)
 for b in opening.get_bindings():
  for t in b.get_tracks():
   if isinstance(t,unreal.MovieSceneSkeletalAnimationTrack):
    for s in t.get_sections():p=s.params;p.animation=sit;s.params=p
 E.save_loaded_asset(opening)
 cams={
  'S1Wide':camera('NAR_Cam_S1_Entry',(-90,330,190),(-170,-150,95),24),'S1Med':camera('NAR_Cam_S1_Walk',(-110,-500,170),(-190,-170,110),28),'S1Detail':camera('NAR_Cam_S1_Wall',(220,-300,170),(250,-578,155),55),
  'S2Wide':camera('NAR_Cam_S2_Tracking',(850,-820,190),(1050,-100,120),24),'S2Med':camera('NAR_Cam_S2_OverShoulder',(1000,70,180),(1150,378,155),40),'S2Detail':camera('NAR_Cam_S2_Seam',(1150,150,165),(1150,378,155),60),
  'S3Wide':camera('NAR_Cam_S3_Entry',(970,1150,190),(1210,900,100),24),'S3Photo':camera('NAR_Cam_S3_Photo',(1100,800,100),(1100,750,57),55),'S3React':camera('NAR_Cam_S3_Reaction',(1230,1300,165),(1230,1130,145),55),
  'S1Talk':camera('NAR_Cam_S1_Conversation',(40,-500,165),(170,-400,125),24),'S2Talk':camera('NAR_Cam_S2_Conversation',(1050,0,170),(1120,220,135),35),'FinalPickup':camera('NAR_Cam_FinalPickup_Wide',(1100,1450,200),(1230,1220,105),24),
  'EvidenceWall':camera('NAR_Cam_Evidence_Wall',(1150,180,165),(1150,378,150),40)}
 # Physical call sheet and reference inserts for the ending evidence montage.
 board=box('NAR_Evidence_OriginalCallSheet',(3000,0,90),(2,140,100),paper);text('NAR_Evidence_CallSheetText',(3002,0,125),'ORIGINAL PRODUCTION\nEVELYN\nSURYA + THREE CREW\nUNRELEASED FOOTAGE',0,10)
 cams['EvidenceCall']=camera('NAR_Cam_Evidence_CallSheet',(3210,0,120),(3000,0,90),35)
 textActor=A['NAR_Evidence_CallSheetText'];textActor.set_actor_location(unreal.Vector(3002,0,90),False,False);textActor.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER);textActor.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER);textActor.text_render.set_world_size(5);textActor.text_render.set_text_render_color(unreal.Color(r=0,g=0,b=0,a=255))
 credits=spawn(unreal.CameraActor,'NAR_Credits_Camera',(0,0,-5000));credits.set_actor_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0),False);credits.camera_component.set_field_of_view(65)
 creditText=text('NAR_Credits_Text',(500,0,-4930),'THE HOUSE THAT REMEMBERS\nAn Unreleased Film\n\nDirected by Surya Adikara\nStarring Maya',180,24);creditText.text_render.set_text_render_color(unreal.Color(230,225,210,255));creditText.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
 # Markers and slot transforms are integration data; no snap/ACTION/CUT logic is added here.
 for scene,positions in [(1,[(-350,-147,0),(-405,-147,0),(-210,80,0)]),(2,[(1300,-100,0),(1120,220,0),(1370,100,0)]),(3,[(1230,980,0),(1120,1030,0),(1320,1080,0)])]:
  for j,pt in enumerate(positions):
   a=spawn(unreal.TargetPoint,f'NAR_Marker_Scene{scene:02}_PropSlot_{j}',pt);a.set_editor_property('is_editor_only_actor',True)
 seqs=[]
 for b in D['blocks']:
  idx=b['index'];dur=b['duration'];end=math.ceil(dur*30);folder=ROOT+('/Scene%02d'%b['scene'] if b['kind'] in ('take','failure','dialogue','traversal') else '/Recordings');name='LS_'+b['name'];path=folder+'/'+name
  q=unreal.load_asset(path) if E.does_asset_exist(path) else T.create_asset(name,folder,unreal.LevelSequence,unreal.LevelSequenceFactoryNew());bindings={}
  for bb in list(q.get_bindings()):bb.remove()
  for tt in list(q.get_tracks()):q.remove_track(tt)
  q.set_display_rate(unreal.FrameRate(30,1));q.set_playback_start(0);q.set_playback_end(end)
  if b['kind'] in ('take','failure'):
   for person in crew:visible(q,person,0,end,True)
  if idx in [0,1,2]:
   route(q,maya,[(-90,360,0),(-190,200,0),(-190,80,0),(-190,-260,0),(170,-400,0)] if idx==0 else [(-90,360,0),(-190,200,0),(-190,80,0)],0,dur*.65,idx);anim(q,maya,idle,round(dur*.65*30),end);shots(q,[(0,dur*.3,cams['S1Wide']),(dur*.3,dur*.7,cams['S1Med']),(dur*.7,dur,cams['S1Detail'] if idx==0 else cams['S1Med'])],end)
  elif idx==3:transform(q,maya,[(0,(170,-400,0),110)],end);shots(q,[(0,dur,cams['S1Talk'])],end);anim(q,maya,idle,0,end)
  elif idx==4:
   route(q,maya,[(170,-400,0),(-190,-400,0),(-90,-450,0),(-90,-700,0),(-280,-750,0),(-280,-850,0)],0,dur,idx)
   route(q,crew[0],[(230,-470,0),(-90,-470,0),(-90,-700,0),(-430,-750,0),(-430,-1280,0)],6,dur,idx)
   route(q,crew[1],[(-280,-210,0),(-190,-400,0),(-90,-470,0),(-90,-700,0),(350,-790,0)],13,dur,idx)
   route(q,crew[2],[(-1290,1270,0),(-1080,1100,0),(-1080,550,0),(-1080,0,0),(-1080,-1080,0),(-650,-1080,0),(-430,-1080,0)],0,dur,idx)
  elif idx==6:
   route(q,maya,[(-280,-850,0),(350,-790,0),(400,-695,0),(620,-695,0),(1000,-695,0),(1050,-500,0)],0,dur,idx)
   route(q,crew[1],[(350,-790,0),(400,-695,0),(620,-695,0),(950,-695,0),(1300,-500,0)],0,dur,idx)
   route(q,crew[2],[(-430,-1080,0),(-430,-790,0),(350,-790,0),(400,-695,0),(620,-695,0),(900,-695,0),(900,-350,0)],6,dur,idx)
  elif idx in [7,8,9]:
   route(q,maya,[(1050,-500,0),(1050,50,0),(1120,220,0)] if idx==7 else [(1050,-500,0),(1050,-50,0)],0,dur*.6,idx);anim(q,maya,idle,round(dur*.6*30),end);shots(q,[(0,dur*.35,cams['S2Wide']),(dur*.35,dur*.7,cams['S2Med']),(dur*.7,dur,cams['S2Detail'])],end)
  elif idx==10:transform(q,maya,[(0,(1120,220,0),162)],end);shots(q,[(0,dur,cams['S2Talk'])],end);anim(q,maya,idle,0,end)
  elif idx==11:
   route(q,maya,[(1120,220,0),(1050,180,0),(900,180,0),(705,180,0),(705,480,0),(705,1040,0),(1000,1040,0)],6,dur,idx)
   route(q,crew[2],[(900,-350,0),(900,180,0),(705,180,0),(705,480,0),(705,1040,0),(1000,1040,0),(1000,1250,0),(1230,1360,0),(1450,1400,0)],0,dur,idx)
  elif idx==13:route(q,maya,[(1000,1040,0),(1080,1040,0),(1080,860,0),(1100,850,0)],0,8,idx);anim(q,maya,idle,240,end)
  elif idx in [14,15,16]:
   route(q,maya,[(1000,1040,0),(1080,1040,0),(1100,850,0),(1080,1130,0),(1230,1130,0)] if idx==14 else [(1000,1040,0),(1080,1040,0),(1100,850,0)],0,dur*.65,idx);anim(q,maya,idle,round(dur*.65*30),end);shots(q,[(0,dur*.3,cams['S3Wide']),(dur*.3,dur*.6,cams['S3Photo']),(dur*.6,dur,cams['S3React'])],end)
  elif idx==17:transform(q,maya,[(0,(1230,1130,0),0)],end);shots(q,[(0,dur,cams['S3React'])],end);anim(q,maya,idle,0,end)
  elif idx==19:
   route(q,crew[0],[(-430,-1280,0),(-300,-1345,0),(340,-1360,0),(400,-695,0),(620,-695,0),(1000,-695,0),(1000,-500,0),(900,180,0),(705,180,0),(705,1040,0),(1000,1040,0),(1000,1280,0)],6,25,idx)
   route(q,crew[1],[(1300,-500,0),(1050,-500,0),(1050,180,0),(705,180,0),(705,1040,0),(1000,1040,0),(1410,1120,0)],0,18,idx)
   transform(q,maya,[(0,(1230,1220,0),0)],end);anim(q,maya,sit,0,end);shots(q,[(0,dur-7,cams['FinalPickup']),(dur-7,dur,camMaster)],end);fade(q,end,True)
  elif b['kind'] in ('recording','reveal'):
   visible(q,master,0,end,False);visible(q,recchair,0,end,False)
   for paperActor in S.get_all_level_actors():
    if paperActor.get_actor_label().startswith(('PROP_Intro_Maya_Script','PROP_Intro_ScriptLine_','NAR_Prop_Maya_Floorplan')):visible(q,paperActor,0,end,True,idx!=20)
   for body in bodies:visible(q,body,0,end,False)
   visible(q,chair,0,end,True)
   transform(q,master,[(0,(1230,1220,0),0)],end,True);anim(q,master,sit,0,end if idx!=22 else 240);shots(q,[(0,dur,camMaster)],end)
   cb=q.add_possessable(camMaster.get_cine_camera_component());cb.set_parent(bind(q,camMaster));ft=cb.add_track(unreal.MovieSceneFloatTrack);ft.set_property_name_and_path('CurrentFocalLength','CurrentFocalLength');fs=ft.add_section();fs.set_range(0,end);fs.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE);fc=fs.get_all_channels()[0];fc.set_default(75.)
   if idx==22:
    fc.add_key(unreal.FrameNumber(0),75.,interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT);fc.add_key(unreal.FrameNumber(240),16.,interpolation=unreal.MovieSceneKeyInterpolation.CONSTANT)
    # Replace the static transform by a seated-to-standing exit within the same camera angle.
    for t in bind(q,master).get_tracks():
     if isinstance(t,unreal.MovieScene3DTransformTrack):bind(q,master).remove_track(t)
    transform(q,master,[(0,(1230,1220,0),0),(270,(1230,1220,0),-90),(510,(1510,1220,0),-90)],end,True);anim(q,master,stand,240,270);anim(q,master,walk,270,510);fade(q,end,True)
   else:fade(q,end)
   if idx==20:
    for a in crew+[maya]:visible(q,a,0,end,True,False)
  elif idx==21:shots(q,[(0,3.3,cams['EvidenceCall']),(3.3,6.6,cams['S3Photo']),(6.6,dur,cams['EvidenceWall'])],end)
  elif idx==23:shots(q,[(0,dur,credits)],end)
  E.save_loaded_asset(q);seqs.append(q);R['sequences'].append({'index':idx,'path':path,'duration':dur,'kind':b['kind']})
 # Bind the data-driven Blueprint to the complete beat table.
 bp=unreal.load_asset('/Game/Game/Blueprints/Flow/BP_NarrativeDirector')
 for name in ['Arrival','Intercom','Credits','Maya']:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);cdo=unreal.get_default_object(bp.generated_class());import runpy
 cue_reader=runpy.run_path(P+'Tools/Narrative/BuildNarrativeData.py')
 cue_data=cue_reader['build_cue_arrays'](D)
 props={'Sequences':seqs,'Durations':[b['duration'] for b in D['blocks']],'NextBlocks':[b['next'] for b in D['blocks']],'Locks':[b['lock'] for b in D['blocks']],**cue_data,'TakeBeats':D['take_beats'],'AftermathBeats':D['aftermath_beats'],'SceneNotes':D['notes'],'SceneStarts':[unreal.Vector(-90,360,0),unreal.Vector(1050,-500,0),unreal.Vector(1000,1040,0)],'GateRadii':[250. if b['index'] in [6,13] else 0. for b in D['blocks']],'GatePositions':[unreal.Vector(900,-450,88) if b['index']==6 else unreal.Vector(1100,1040,88) for b in D['blocks']],'GateHints':['Follow the crew to the kitchen.' if b['index']==6 else 'Follow the service passage to the last room.' for b in D['blocks']]}
 for k,v in props.items():cdo.set_editor_property(k,v)
 E.save_loaded_asset(bp);director=spawn(bp.generated_class(),'FLOW_Narrative_Sections05_14',(0,0,0))
 for k,v in [('Arrival',A['FLOW_Arrival_Tutorial_LivingRoom']),('Intercom',intercom),('Credits',credits),('Maya',maya)]:director.set_editor_property(k,v)
 keynode=unreal.load_object(None,bp.get_path_name()+':EventGraph.K2Node_InputKey_0')
 if keynode:keynode.set_editor_property('bConsumeInput',False)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp);R['saved']=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();R['success']=True
except Exception:R['errors'].append(traceback.format_exc());unreal.log_error(R['errors'][-1])
json.dump(R,open(P+'Saved/NarrativeBuildReport.json','w'),indent=2);unreal.log('NARRATIVE_BUILD '+str(R['success']))


