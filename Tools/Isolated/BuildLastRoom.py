"""Author an isolated Interlude 02 / Last Room previs. Run with Unreal Python.

Creates only /Game/Game/Isolated/IbraLastRoom. Existing assets are read-only.
Runtime is native Level Sequence plus inherited Blueprint free placement.
"""
import unreal, json, hashlib, traceback, os
from pathlib import Path

P = Path(unreal.Paths.project_dir())
ROOT = '/Game/Game/Isolated/IbraLastRoom'
MAP = ROOT + '/L_Interlude02_LastRoom'
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
E = unreal.EditorAssetLibrary
T = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report = {'map': MAP, 'success': False, 'errors': [], 'subtitles': []}
protected = {str(p.relative_to(P)): hashlib.sha256(p.read_bytes()).hexdigest()
             for base in ['Content/Game/Blueprints', 'Content/Game/Levels', 'Content/Game/UI', 'Content/Game/Cinematics', 'Config']
             for p in (P/base).rglob('*') if p.is_file()}

def spawn(cls, name, pos, folder='Set', rot=None):
    unreal.log('LASTROOM_SPAWN '+name)
    actor = A.spawn_actor_from_class(cls, unreal.Vector(*pos), rot or unreal.Rotator())
    assert actor, name
    actor.set_actor_label(name)
    actor.set_folder_path('IbraLastRoom/'+folder)
    return actor

def material(name, rgb, emissive=False):
    if E.does_asset_exist(ROOT+'/Materials/'+name):return unreal.load_asset(ROOT+'/Materials/'+name)
    m = T.create_asset(name, ROOT+'/Materials', unreal.Material, unreal.MaterialFactoryNew())
    c = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -250,0)
    c.set_editor_property('constant',unreal.LinearColor(*rgb,1))
    unreal.MaterialEditingLibrary.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR if emissive else unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    unreal.MaterialEditingLibrary.recompile_material(m)
    E.save_loaded_asset(m)
    return m

def mesh(name, path, pos, scale=(1,1,1), mat=None, collision=True, folder='Set', yaw=0):
    a=spawn(unreal.StaticMeshActor,name,pos,folder,unreal.Rotator(pitch=0,yaw=yaw,roll=0))
    c=a.static_mesh_component
    c.set_static_mesh(unreal.load_asset(path))
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    if mat:
        for i in range(max(1,c.get_num_materials())):c.set_material(i,mat)
    a.set_actor_scale3d(unreal.Vector(*scale))
    return a

def block(name,pos,size,mat,collision=True):
    return mesh(name,'/Engine/BasicShapes/Cube',pos,tuple(x/100 for x in size),mat,collision)

def text(name, message, pos, size=16, yaw=180, folder='Signs'):
    a=spawn(unreal.TextRenderActor,name,pos,folder,unreal.Rotator(pitch=0,yaw=yaw,roll=0))
    c=a.text_render
    c.set_text(message)
    c.set_world_size(size)
    c.set_text_render_color(unreal.Color(240,234,220,255))
    c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a

def child(name,parent):
    if E.does_asset_exist(ROOT+'/Blueprints/'+name):return unreal.load_asset(ROOT+'/Blueprints/'+name)
    factory=unreal.BlueprintFactory()
    factory.set_editor_property('parent_class',unreal.load_class(None,parent))
    bp=T.create_asset(name,ROOT+'/Blueprints',unreal.Blueprint,factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    return bp

def point(name,pos):return spawn(unreal.TargetPoint,name,pos,'Markers')

def transform_track(seq,actor,keys,keep=False):
    binding=seq.add_possessable(actor)
    track=binding.add_track(unreal.MovieScene3DTransformTrack)
    sec=track.add_section();sec.set_range(0,1560)
    sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE if keep else unreal.MovieSceneCompletionMode.RESTORE_STATE)
    for frame,xyz,yaw in keys:
        vals=[*xyz,0.,0.,float(yaw),1.,1.,1.]
        for channel,value in zip(sec.get_all_channels(),vals):
            channel.add_key(unreal.FrameNumber(frame),float(value),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    return binding

def visible(seq,actor,start,end):
    a=seq.add_possessable(actor)
    tr=a.add_track(unreal.MovieSceneVisibilityTrack)
    tr.set_property_name_and_path('bHidden','bHidden')
    sec=tr.add_section();sec.set_range(0,1560)
    sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
    ch=sec.get_all_channels()[0]
    ch.set_default(False)
    for frame,value in [(0,False),(start,True),(end,False)]:ch.add_key(unreal.FrameNumber(frame),value)
    actor.set_actor_hidden_in_game(True)

def caption(seq,camera,name,line,start,end):
    # World text fixed to camera gives cinematic-only captions without modifying HUD.
    a=text(name,line,(0,0,0),1.1 if start<14 else 2.2,180,'Cinematics/Captions')
    a.text_render.set_text_material(caption_text)
    a.text_render.set_mobility(unreal.ComponentMobility.MOVABLE)
    a.attach_to_actor(camera,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
    a.set_actor_relative_location(unreal.Vector(100,0,-10 if start<14 else -30),False,False)
    a.set_actor_relative_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False,False)
    visible(seq,a,round(start*30),round(end*30))
    panel=mesh(name+'_Backing','/Engine/BasicShapes/Cube',(0,0,0),(.002,.48 if start<14 else 1.30,.065 if start<14 else .10),caption_black,False,'Cinematics/CaptionBacking')
    panel.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    panel.static_mesh_component.set_editor_property('cast_shadow',False)
    panel.attach_to_actor(camera,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
    panel.set_actor_relative_location(unreal.Vector(101,0,-9.5 if start<14 else -29.5),False,False)
    visible(seq,panel,round(start*30),round(end*30))
    report['subtitles'].append({'text':line,'start':start,'end':end})

try:
    receipt=P/'Saved/QA/LastRoomBuild.json'
    assert os.environ.get('LASTROOM_REBUILD')=='1' or not receipt.exists() or not json.loads(receipt.read_text()).get('success'), 'Completed isolated build exists; refusing overwrite.'
    if E.does_asset_exist(MAP):
        unreal.EditorLoadingAndSavingUtils.load_map(MAP)
        for old in list(A.get_all_level_actors()):
            if not isinstance(old,unreal.WorldSettings):A.destroy_actor(old)
    else:
        assert L.new_level(MAP)
    wall=material('M_LastRoom_Plaster',(.17,.19,.16))
    wood=material('M_LastRoom_RedTimber',(.16,.055,.035))
    dark=material('M_LastRoom_Trim',(.045,.035,.025))
    gold=material('M_LastRoom_Mark',(.52,.30,.06))
    paper=material('M_LastRoom_Paper',(.68,.62,.48))
    caption_black=material('M_CaptionBacking',(.003,.003,.003),True)
    caption_text_path=ROOT+'/Materials/M_CaptionText'
    caption_text=unreal.load_asset(caption_text_path) if E.does_asset_exist(caption_text_path) else E.duplicate_asset('/Engine/EngineMaterials/DefaultTextMaterialOpaque',caption_text_path)
    caption_text.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    white=unreal.MaterialEditingLibrary.create_material_expression(caption_text,unreal.MaterialExpressionConstant3Vector,-250,200)
    white.set_editor_property('constant',unreal.LinearColor(1,1,1,1))
    unreal.MaterialEditingLibrary.connect_material_property(white,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(caption_text);E.save_loaded_asset(caption_text)
    # Connected, single-storey service passage and final room. Clear doorway 180 cm.
    block('ServiceFloor',(-550,0,-15),(900,280,30),dark)
    block('RoomFloor',(400,0,-15),(1000,900,30),wood)
    for n,pos,size in [
        ('ServiceNorth',(-550,150,135),(900,20,270)),('ServiceSouth',(-550,-150,135),(900,20,270)),
        ('ServiceEnd',(-1010,0,135),(20,320,270)),('RoomNorth',(400,460,135),(1040,20,270)),
        ('RoomSouth',(400,-460,135),(1040,20,270)),('RoomEast',(910,0,135),(20,940,270)),
        ('RoomWestNorth',(-110,305,135),(20,290,270)),('RoomWestSouth',(-110,-305,135),(20,290,270)),
        ('DoorHeader',(-110,0,255),(20,320,30)),('ServiceCeiling',(-550,0,280),(900,320,20)),
        ('RoomCeiling',(400,0,280),(1040,940,20))]:block(n,pos,size,wall)
    for y in [-445,445]:block('Skirting_'+str(y),(400,y,12),(1000,7,24),dark)
    props='/Game/Game/Art/Environment/House/Meshes/Props/'
    mesh('ReferenceTable',props+'SM_House_Table_Side',(600,-190,0))
    mesh('CrewEquipmentCase',props+'SM_House_FlightCase_Black',(-520,90,0))
    mesh('CrewEquipmentRack',props+'SM_House_Rack_Equipment',(-820,95,0),(.7,.7,.7))
    text('LastSetSign','LAST SET  /  STAGE 03',(-150,140,218),15,180)
    text('ControlCard','SCENE 03 / RECONSTRUCTION\nE pick up / place | RMB cancel\nF ACTION / CUT at brass mark\nTab notes | R reset | P pause',(875,0,195),13,180)
    text('ReferenceLabel','MATCH THE COMPOSITION\nChair near the back wall.\nLamp to its left.',(600,-245,110),10,180)
    # A diagram is an explicit previs reference; final photograph is a later art pass.
    block('ReferenceCard',(600,-190,56),(45,32,1),paper,False)
    block('ReferenceChairSymbol',(606,-190,58),(11,10,2),wood,False)
    mesh('ReferenceLampSymbol','/Engine/BasicShapes/Cylinder',(592,-206,58),(.045,.045,.015),gold,False)
    manager_bp=child('BP_LastRoomManager','/Game/Game/Blueprints/Gameplay/Testing/BP_GameplayTestManager.BP_GameplayTestManager_C')
    player_bp=child('BP_LastRoomPlayer','/Game/Game/Blueprints/Gameplay/Testing/BP_GameplayPlayer.BP_GameplayPlayer_C')
    mode_bp=child('BP_LastRoomMode','/Game/Game/Blueprints/Gameplay/Testing/BP_GameplayTestMode.BP_GameplayTestMode_C')
    md=unreal.get_default_object(manager_bp.generated_class());md.set_editor_property('SceneIndex',3);md.set_editor_property('SimulatorSeconds',4.)
    mode=unreal.get_default_object(mode_bp.generated_class());mode.set_editor_property('default_pawn_class',player_bp.generated_class())
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode',mode_bp.generated_class())
    start=spawn(unreal.PlayerStart,'LastRoom_PlayerStart',(40,0,95),'Markers')
    manager=spawn(manager_bp.generated_class(),'LastRoom_Manager',(0,0,0),'Systems')
    mark=point('LastRoom_DirectorMark',(120,0,0))
    mesh('DirectorMark','/Engine/BasicShapes/Cylinder',(120,0,.5),(1.8,1.8,.008),gold,False)
    text('DirectorMarkLabel','DIRECTOR',(120,0,2),12,180)
    propclass=unreal.load_class(None,'/Game/Game/Blueprints/Props/BP_InteractableProp.BP_InteractableProp_C')
    areaclass=unreal.load_class(None,'/Game/Game/Blueprints/Gameplay/Testing/BP_PlacementArea.BP_PlacementArea_C')
    puzzle=[]
    for idx,name,asset,pos,goal,radius in [
        (1,'Chair','SM_House_Chair_Dining',(280,220,0),(660,60,0),90.),
        (2,'Lamp','SM_House_Lamp_Floor',(320,-270,0),(510,-100,0),75.)]:
        p=spawn(propclass,'LastRoom_'+name,pos,'Gameplay')
        c=next(c for c in p.get_components_by_class(unreal.StaticMeshComponent) if c.get_name()=='Mesh')
        c.set_static_mesh(unreal.load_asset(props+asset));c.set_relative_location(unreal.Vector(),False,False);c.set_collision_profile_name('BlockAllDynamic')
        p.set_editor_property('PropID',unreal.Name('L03_'+name));p.set_editor_property('CurrentSlotID',unreal.Name('None'))
        origin=point('LastRoom_'+name+'_Start',pos)
        area=spawn(areaclass,'LastRoom_'+name+'_Goal',goal,'Gameplay/HiddenGoals')
        area.set_editor_property('AllowedProp',p);area.set_editor_property('Radius',radius)
        area.set_actor_hidden_in_game(True)
        # Inherit the tested evaluator; all debug scene selectors stay inside this map.
        for s in range(1,4):
            for prop,value in [('Prop',p),('Start',origin),('Area',area)]:manager.set_editor_property(f'S{s}{prop}{idx}',value)
        puzzle.append({'name':name,'actor':p.get_path_name(),'start':pos,'goal':goal,'radius':radius})
    for s in range(1,4):manager.set_editor_property(f'S{s}DirectorMark',mark)
    intercom=point('LastRoom_Intercom',(700,-400,125));manager.set_editor_property('Intercom',intercom)
    block('IntercomHousing',(700,-435,125),(28,12,42),dark)
    text('IntercomSign','PRODUCTION INTERCOM',(700,-420,170),10,90)
    # Grounded warm practical lights; no horror cue or jumpscare.
    for i,pos in enumerate([(-650,0,235),(200,0,230),(680,80,230)]):
        light=spawn(unreal.PointLight,'Practical_'+str(i),pos,'Lighting')
        light.point_light_component.set_editor_property('intensity',2200.)
        light.point_light_component.set_editor_property('attenuation_radius',800.)
        light.point_light_component.set_editor_property('use_temperature',True)
        light.point_light_component.set_editor_property('temperature',4200.)
    # Separate neutral interview corner outside playable bounds; Maya stand-in.
    block('InterviewFloor',(2400,0,-12),(600,600,24),dark)
    block('InterviewBackground',(2400,-200,150),(600,20,300),wall)
    mesh('InterviewChair',props+'SM_House_Chair_Dining',(2400,0,0))
    maya=spawn(unreal.SkeletalMeshActor,'Maya_Interview_StandIn',(2400,0,-35),'Characters',unreal.Rotator(pitch=0,yaw=0,roll=0))
    maya.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'))
    maya.skeletal_mesh_component.set_collision_profile_name('NoCollision')
    maya.skeletal_mesh_component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    maya.skeletal_mesh_component.override_animation_data(unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'),True,True,0.,1.)
    for name,pos in [('Maya_OnSet',(640,260,0)),('CrewA_OnSet',(-20,100,0))]:
        a=spawn(unreal.SkeletalMeshActor,name,pos,'Characters',unreal.Rotator(pitch=0,yaw=90,roll=0))
        a.skeletal_mesh_component.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'))
        a.skeletal_mesh_component.set_collision_profile_name('NoCollision')
        a.skeletal_mesh_component.override_animation_data(unreal.load_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle'),True,True,0.,1.)
    light=spawn(unreal.PointLight,'InterviewSoftKey',(2280,150,220),'Lighting')
    light.point_light_component.set_editor_property('intensity',1800.);light.point_light_component.set_editor_property('attenuation_radius',600.)
    seqpath=ROOT+'/Cinematics/LS_Interlude02_Approach'
    seq=unreal.load_asset(seqpath) if E.does_asset_exist(seqpath) else T.create_asset('LS_Interlude02_Approach',ROOT+'/Cinematics',unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
    for binding in list(seq.get_bindings()):binding.remove()
    for track in list(seq.get_tracks()):seq.remove_track(track)
    seq.set_display_rate(unreal.FrameRate(30,1));seq.set_playback_start(0);seq.set_playback_end(1560)
    interview=spawn(unreal.CineCameraActor,'Camera_Confession_Closeup',(2400,230,122),'Cinematics',unreal.Rotator(pitch=0,yaw=-90,roll=0))
    approach=spawn(unreal.CineCameraActor,'Camera_Surya_Approach',(-880,0,155),'Cinematics',unreal.Rotator(pitch=0,yaw=0,roll=0))
    for cam,focal in [(interview,75.),(approach,24.)]:
        comp=cam.get_cine_camera_component();comp.set_editor_property('current_focal_length',focal)
        comp.set_editor_property('filmback',unreal.CameraFilmbackSettings(sensor_width=36.,sensor_height=20.25))
        f=comp.get_editor_property('focus_settings');f.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE);comp.set_editor_property('focus_settings',f)
    b1=transform_track(seq,interview,[(0,(2400,230,122),-90)])
    b2=transform_track(seq,approach,[(0,(-880,0,155),0),(420,(-880,0,155),0),(690,(-150,0,155),0),(840,(40,0,155),0),(1559,(40,0,155),0)])
    cuts=seq.add_track(unreal.MovieSceneCameraCutTrack)
    for binding,startf,endf in [(b1,0,420),(b2,420,1560)]:
        sec=cuts.add_section();sec.set_range(startf,endf);bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',binding.get_id());sec.set_camera_binding_id(bid)
    lines=[
        (0.4,2.2,"MAYA: And then there's editing."),(2.3,5.1,'MAYA: You can take two completely different moments...'),
        (5.2,6.8,'MAYA: Put them together...'),(6.9,9.0,'MAYA: And suddenly, they tell a story.'),
        (10.,12.7,"MAYA: But that doesn't mean it's what really happened."),(12.8,14.,'MAYA: Does it?'),
        (15.,18.,'CREW A: This is the last set, sir.'),(18.2,21.,"SURYA: Good. Let's make it count."),
        (23.,27.5,'MAYA: So this is where Laras finally\nfinds out what happened?'),
        (27.8,32.,'SURYA: Yes. Everything should come together here.'),(32.3,33.5,'MAYA: Right.'),
        (34.,36.5,"MAYA: It's a good ending."),(37.,40.5,"SURYA: Let's hope we do it justice."),
        (41.,43.5,"MAYA: I'll do my best."),
        (45.,51.5,'SCENE 03 / MATCH THE REFERENCE\nFree placement: chair + lamp. Then return to the director mark.')]
    for i,(startt,endt,line) in enumerate(lines):caption(seq,interview if startt<14 else approach,'Caption_%02d'%i,line,startt,endt)
    # Prevent ACTION during the introduction. Original state restores at sequence end.
    mb=seq.add_possessable(manager);track=mb.add_track(unreal.MovieSceneIntegerTrack);track.set_property_name_and_path('State','State')
    sec=track.add_section();sec.set_range(0,1560);sec.get_all_channels()[0].set_default(5);sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
    player=spawn(unreal.LevelSequenceActor,'LastRoom_IntroSequence',(0,0,0),'Cinematics')
    player.set_sequence(seq)
    settings=player.get_editor_property('playback_settings')
    for k,v in [('auto_play',True),('disable_movement_input',True),('disable_look_at_input',True),('hide_player',True),('hide_hud',True)]:settings.set_editor_property(k,v)
    settings.set_editor_property('finish_completion_state_override',unreal.MovieSceneCompletionModeOverride.FORCE_RESTORE_STATE)
    player.set_editor_property('playback_settings',settings)
    for bp in [manager_bp,player_bp,mode_bp]:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp);E.save_loaded_asset(bp)
    E.save_loaded_asset(seq)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(-350,-650,650),unreal.Rotator(pitch=-30,yaw=40,roll=0))
    assert L.save_current_level()
    changed=[name for name,digest in protected.items() if hashlib.sha256((P/name).read_bytes()).hexdigest()!=digest]
    assert not changed, changed
    report.update(success=True,protected_files=len(protected),changed_protected_files=changed,puzzle=puzzle,duration_seconds=52,stand_ins=True)
except Exception:
    report['errors'].append(traceback.format_exc());unreal.log_error(report['errors'][-1])
finally:
    (P/'Saved/QA').mkdir(parents=True,exist_ok=True)
    (P/'Saved/QA/LastRoomBuild.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
