"""Stage a complete voiced graybox campaign in a private copy of the house.

Requires BuildCampaignBlueprints.py first. Never saves source levels or classes.
"""
import unreal,json,math,hashlib,traceback,os,textwrap
from pathlib import Path
P=Path(unreal.Paths.project_dir());ROOT='/Game/Game/Isolated/IbraCampaign';MAP=ROOT+'/L_CUT_Campaign'
A=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);E=unreal.EditorAssetLibrary;T=unreal.AssetToolsHelpers.get_asset_tools()
N=json.loads((P/'Tools/Isolated/CampaignNarrative.json').read_text(encoding='utf-8'))
VO=json.loads((P/'Tools/Isolated/CampaignVO.json').read_text(encoding='utf-8'))
REPORT={'success':False,'map':MAP,'errors':[],'clips':{},'missing_vo':N['missing_vo']}
protected={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['Content','Config'] for p in (P/base).rglob('*') if p.is_file() and 'IbraCampaign' not in p.parts}
PROP='/Game/Game/Art/Environment/House/Meshes/Props/'
MAT='/Game/Game/Art/Environment/House/Materials/Instances/'
ANIM='/Game/Characters/Tripo/Anims/'
IDLE=unreal.load_asset(ANIM+'A_Tripo_Idle');WAIT=unreal.load_asset(ANIM+'A_Tripo_Wait')
SCENES={
 1:dict(start=(-90,380,0),end=(-170,-160,0),yaw=-90,spawn=(240,-80,88),mark=(240,-220,0),
        props=[('Sofa','SM_House_Sofa_TwoSeat',(-140,140,0),(-370,50,0),90,95),('Wardrobe','SM_House_Cabinet_Tall',(-490,-440,0),(160,-400,0),90,85)],
        cameras=[((420,250,180),(-120,100,90),27),((-20,-20,155),(-470,-440,100),32)],
        blocked=(-112,284,0),clue=(-550,-440,130)),
 2:dict(start=(710,1300,0),end=(1100,270,0),yaw=-90,spawn=(1250,-450,88),mark=(1250,-300,0),
        props=[('Cabinet','SM_House_Kitchen_Cabinet',(710,830,0),(1250,-600,0),0,90),('Lamp','SM_House_Lamp_Floor',(1150,-800,0),(880,180,0),0,85)],
        cameras=[((710,470,165),(710,1000,90),27),((1350,-500,185),(1000,200,100),32),((850,0,155),(1100,330,120),45)],
        blocked=(710,1020,0),clue=(1100,395,130)),
 3:dict(start=(980,1055,0),end=(1320,1070,0),yaw=0,spawn=(1020,1055,88),mark=(1000,1150,0),
        props=[('Chair','SM_House_Chair_Dining',(1050,1380,0),(1230,1220,0),0,70),('Lamp','SM_House_Lamp_Floor',(1440,1400,0),(1070,1130,0),0,65)],
        cameras=[((990,1490,180),(1240,1120,95),24),((1470,940,155),(1320,1080,105),35),((1400,1360,145),(1230,1220,105),38)],
        blocked=(1120,1100,0),clue=(1230,1220,60)),
}

def rot(yaw=0,pitch=0,roll=0):return unreal.Rotator(pitch=pitch,yaw=yaw,roll=roll)
def spawn(cls,label,pos,folder='Set',rotation=None):
    a=A.spawn_actor_from_class(cls,unreal.Vector(*pos),rotation or rot());assert a,label
    a.set_actor_label('CAMPAIGN_'+label);a.set_folder_path('IbraCampaign/'+folder);return a
def point(label,pos,yaw=0):return spawn(unreal.TargetPoint,label,pos,'Markers',rot(yaw))
def mesh(label,path,pos,scale=(1,1,1),yaw=0,collision=True,material=None,folder='Set'):
    a=spawn(unreal.StaticMeshActor,label,pos,folder,rot(yaw));c=a.static_mesh_component;c.set_static_mesh(unreal.load_asset(path));a.set_actor_scale3d(unreal.Vector(*scale))
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    if material:
        for i in range(max(c.get_num_materials(),1)):c.set_material(i,material)
    return a
def block(label,pos,size,material=None,collision=True):return mesh(label,'/Engine/BasicShapes/Cube',pos,tuple(v/100 for v in size),collision=collision,material=material)
def text(label,value,pos,size=15,yaw=0):
    a=spawn(unreal.TextRenderActor,label,pos,'Guidance',rot(yaw));a.text_render.set_text(value);a.text_render.set_world_size(size);a.text_render.set_text_render_color(unreal.Color(235,218,171,255));return a
def npc(label,asset,pos,yaw=0):
    a=spawn(unreal.SkeletalMeshActor,label,pos,'Cast',rot(yaw));c=a.skeletal_mesh_component;c.set_skeletal_mesh_asset(unreal.load_asset(asset));c.set_collision_profile_name('NoCollision');c.override_animation_data(unreal.load_asset('/Game/Characters/Surya/Anims/MM_Idle_Surya') if '/Surya/' in asset else WAIT,is_looping=True,is_playing=True);return a
def camera(label,pos,target,focal=32):
    c=spawn(unreal.CineCameraActor,label,pos,'Cameras',unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)))
    cc=c.get_cine_camera_component();cc.set_editor_property('current_focal_length',float(focal));cc.set_editor_property('filmback',unreal.CameraFilmbackSettings(sensor_width=36.,sensor_height=20.25))
    focus=cc.get_editor_property('focus_settings');focus.set_editor_property('focus_method',unreal.CameraFocusMethod.DISABLE);cc.set_editor_property('focus_settings',focus);return c
def sequence(key,seconds):
    path=ROOT+'/Cinematics/LS_'+key
    s=unreal.load_asset(path) if E.does_asset_exist(path) else T.create_asset('LS_'+key,ROOT+'/Cinematics',unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
    for b in list(s.get_bindings()):b.remove()
    for t in list(s.get_tracks()):s.remove_track(t)
    end=math.ceil(seconds*30);s.set_display_rate(unreal.FrameRate(30,1));s.set_playback_start(0);s.set_playback_end(end)
    return s,end
def transforms(s,actor,end,keys):
    b=s.add_possessable(actor);sec=b.add_track(unreal.MovieScene3DTransformTrack).add_section();sec.set_range(0,end);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
    for frame,position,yaw in keys:
        for ch,v in zip(sec.get_all_channels(),[*position,0.,0.,float(yaw),1.,1.,1.]):ch.add_key(unreal.FrameNumber(int(frame)),float(v),interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
    return b
def animation(b,end,pieces):
    tr=b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    for i,(start,stop,name) in enumerate(pieces):
        sec=tr.add_section();sec.set_range(int(start),int(stop));sec.set_row_index(i%2);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
        params=sec.get_editor_property('params');params.set_editor_property('animation',unreal.load_asset(ANIM+name));sec.set_editor_property('params',params)
def visibility(s,actor,end,show):
    b=s.add_possessable(actor);tr=b.add_track(unreal.MovieSceneVisibilityTrack);tr.set_property_name_and_path('bHidden','bHidden');sec=tr.add_section();sec.set_range(0,end);sec.get_all_channels()[0].set_default(show);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
def cuts(s,end,shots):
    tr=s.add_track(unreal.MovieSceneCameraCutTrack);known={}
    for start,stop,cam in shots:
        if cam not in known:known[cam]=s.add_possessable(cam).get_id()
        sec=tr.add_section();sec.set_range(int(start),int(stop));bid=unreal.MovieSceneObjectBindingID();bid.set_editor_property('guid',known[cam]);sec.set_camera_binding_id(bid);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
def captions(s,end,record,delay):
    binding=s.add_possessable(director);tr=binding.add_track(unreal.MovieSceneStringTrack);tr.set_property_name_and_path('SubtitleText','SubtitleText');sec=tr.add_section();sec.set_range(0,end);sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
    ch=sec.get_all_channels()[0];ch.set_default('')
    for cue in record['cues']:
        start=max(0,round((delay+cue['start'])*30));stop=min(end-1,round((delay+cue['end'])*30))
        value=cue['speaker']+': '+cue['text'];value='\n'.join(textwrap.wrap(value,85))
        ch.add_key(unreal.FrameNumber(start),value);ch.add_key(unreal.FrameNumber(max(start+1,stop)),'')
def voice(s,end,record,delay):
    if record.get('sound'):
        tr=s.add_track(unreal.MovieSceneAudioTrack);sec=tr.add_section();sec.set_sound(unreal.load_asset(record['sound']));sec.set_range(round(delay*30),round((delay+record['audio_duration'])*30))
def cast_visibility(s,end,recording=False,dead=False,take=False,pickup=False):
    visibility(s,maya,end,not recording and not dead and not pickup);visibility(s,confession_maya,end,recording or dead or pickup)
    for a in corpses:visibility(s,a,end,dead)
    for a in crew:visibility(s,a,end,not recording and not dead and not take)
def light(label,pos,intensity=1000):
    a=spawn(unreal.PointLight,label,pos,'Lighting');c=a.point_light_component;c.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);c.set_editor_property('intensity',float(intensity));c.set_editor_property('attenuation_radius',700.);c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',4400.);return a

try:
    assert E.does_asset_exist(ROOT+'/Blueprints/BP_CampaignDirector'),'Author campaign Blueprints first.'
    if not E.does_asset_exist(MAP):
        levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        assert levels.load_level('/Game/Game/Levels/SB_GrayBox')
        assert unreal.EditorLoadingAndSavingUtils.save_map(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),MAP)
    else:assert os.environ.get('CAMPAIGN_REBUILD')=='1','Refusing to overwrite a campaign map without CAMPAIGN_REBUILD=1.'
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    removed=[]
    # Preserve only native environment in our copied house. Old flow/director actors never run.
    keep_native=(unreal.StaticMeshActor,unreal.Light,unreal.SkyAtmosphere,unreal.ExponentialHeightFog,unreal.PostProcessVolume,unreal.WorldSettings)
    for a in list(A.get_all_level_actors()):
        label=a.get_actor_label();folder=str(a.get_folder_path())
        keep=isinstance(a,keep_native) and not label.startswith(('CAMPAIGN_','CINE_','L01_','L02_','PROP_Intro_','PROP_Scene01_','DOOR_Entrance_'))
        if isinstance(a,unreal.StaticMeshActor):
            if 'PROP_House_' in label and any(n in label for n in ['Living','Kitchen','HiddenRoom','Service']):keep=False
            if label.startswith(('Cine_','TEST_','FINAL_','SET_','S01_','S02_','S03_')):keep=False
        if a.get_class().get_name().startswith('BP_'):keep=False
        if not keep:removed.append(label);A.destroy_actor(a)
    REPORT['removed_from_copy_only']=removed
    # Import normalized, portable sources. The originals in Documents are untouched.
    tasks=[]
    audio_entries=[dict(wav=c['wav'],asset=c['asset']) for c in VO['clips'].values()]+[N['cut_sofa']]
    for entry in audio_entries:
        if E.does_asset_exist(entry['asset']):continue
        task=unreal.AssetImportTask();task.set_editor_property('filename',str(P/entry['wav']));task.set_editor_property('destination_path',ROOT+'/Audio');task.set_editor_property('destination_name',entry['asset'].split('/')[-1]);task.set_editor_property('automated',True);task.set_editor_property('save',True);tasks.append(task)
    if tasks:T.import_asset_tasks(tasks)
    for entry in audio_entries:
        sound=unreal.load_asset(entry['asset']);assert isinstance(sound,unreal.SoundWave),entry['asset']
        sound.set_editor_property('sound_group',unreal.SoundGroup.SOUNDGROUP_VOICE);sound.set_editor_property('looping',False);E.save_loaded_asset(sound)
    # Editing only the new campaign Blueprint defaults/flags.
    bp=unreal.load_asset(ROOT+'/Blueprints/BP_CampaignDirector')
    for name in [v['name'] for v in json.loads((P/'Saved/QA/CampaignVariables.json').read_text())]:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
    for i in range(80):
        node=unreal.find_object(None,bp.get_path_name()+':EventGraph.K2Node_InputKey_'+str(i))
        if node:
            node.set_editor_property('bConsumeInput',False)
            if str(node.get_editor_property('InputKey').get_editor_property('KeyName')) in ['P','Escape']:node.set_editor_property('bExecuteWhenPaused',True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    settings=unreal.MovieSceneSequencePlaybackSettings(finish_completion_state_override=unreal.MovieSceneCompletionModeOverride.FORCE_KEEP_STATE)
    unreal.get_default_object(bp.generated_class()).set_editor_property('PlaybackSettings',settings);E.save_loaded_asset(bp)
    director=spawn(bp.generated_class(),'Director',(0,0,0),'Systems')
    director.set_editor_property('CutSound',unreal.load_asset(VO['clips']['ManualCut']['asset']));director.set_editor_property('CutSofaSound',unreal.load_asset(N['cut_sofa']['asset']))
    maya=npc('Maya','/Game/Characters/Tripo/Maya/SKM_Maya',SCENES[1]['start'],-90)
    confession_maya=npc('ConfessionMaya','/Game/Characters/Tripo/Maya/SKM_Maya',(1230,1220,0),0);confession_maya.set_actor_hidden_in_game(True)
    director.set_editor_property('Maya',maya);director.set_editor_property('MayaMesh',maya.skeletal_mesh_component);director.set_editor_property('MayaIdle',IDLE)
    crew=[npc('Crew'+str(i),'/Game/Characters/Tripo/Crew/'+asset,pos,yaw) for i,asset,pos,yaw in [
        (1,'SKM_Crew_A',(400,-500,0),-90),(2,'SKM_Crew_B',(350,-500,0),-90),(3,'SKM_Crew_Utility',(450,-400,0),0)]]
    for i,a in enumerate(crew,1):director.set_editor_property('Crew'+str(i),a)
    corpses=[]
    for i,asset,pos in [(0,'/Game/Characters/Surya/SKM_Surya',(1010,720,35)),(1,'/Game/Characters/Tripo/Crew/SKM_Crew_A',(1170,650,30)),(2,'/Game/Characters/Tripo/Crew/SKM_Crew_B',(1340,680,30)),(3,'/Game/Characters/Tripo/Crew/SKM_Crew_Utility',(1450,780,30))]:
        a=npc('FinalPose'+str(i),asset,pos);a.skeletal_mesh_component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE);a.skeletal_mesh_component.stop();a.set_actor_rotation(rot(yaw=90,pitch=90),False);a.set_actor_hidden_in_game(True);corpses.append(a)
    gold=unreal.load_asset('/Game/Game/Materials/GameplayTesting/M_DirectorMark')
    propclass=unreal.load_class(None,'/Game/Game/Blueprints/Props/BP_InteractableProp.BP_InteractableProp_C')
    areaclass=unreal.load_class(None,'/Game/Game/Blueprints/Gameplay/Testing/BP_PlacementArea.BP_PlacementArea_C')
    camera_sets={};puzzle_props={}
    for i,data in SCENES.items():
        for n,pos in [('MayaStart',data['start']),('Spawn',data['spawn']),('DirectorMark',data['mark'])]:director.set_editor_property(f'S{i}'+n,point(f'S{i}_'+n,pos,data['yaw'] if n=='MayaStart' else 0))
        mesh(f'S{i}_DirectorMark','/Engine/BasicShapes/Cylinder',(data['mark'][0],data['mark'][1],.7),(2.2,2.2,.01),collision=False,material=gold)
        text(f'S{i}_MarkLabel','DIRECTOR / SCENE 0'+str(i),(data['mark'][0]-70,data['mark'][1],3),12,0)
        camera_sets[i]=[camera(f'S{i}_Shot{j}',pos,target,lens) for j,(pos,target,lens) in enumerate(data['cameras'])]
        for j,(name,asset,start,goal,yaw,radius) in enumerate(data['props'],1):
            p=spawn(propclass,f'S{i}_{name}',start,f'Gameplay/Scene0{i}',rot(yaw));puzzle_props[(i,j)]=p
            c=next(c for c in p.get_components_by_class(unreal.StaticMeshComponent) if c.get_name()=='Mesh');c.set_static_mesh(unreal.load_asset(PROP+asset));c.set_relative_location(unreal.Vector(),False,False);c.set_collision_profile_name('BlockAllDynamic')
            p.set_editor_property('PropID',unreal.Name(f'S{i}_{name}'));p.set_editor_property('CurrentSlotID',unreal.Name('None'))
            area=spawn(areaclass,f'S{i}_{name}_Goal',goal,'HiddenGoals');area.set_editor_property('AllowedProp',p);area.set_editor_property('Radius',float(radius));area.set_actor_hidden_in_game(True)
            director.set_editor_property(f'S{i}Prop{j}',p);director.set_editor_property(f'S{i}Area{j}',area);director.set_editor_property(f'S{i}Start{j}',point(f'S{i}_{name}_Start',start,yaw))
            if name=='Lamp':
                lamp=spawn(unreal.SpotLight,f'S{i}_MovableLampLight',start,'Lighting')
                lc=lamp.spot_light_component;lc.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);lc.set_editor_property('intensity',900.);lc.set_editor_property('attenuation_radius',650.);lc.set_editor_property('outer_cone_angle',50.)
                lamp.attach_to_actor(p,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False);lamp.set_actor_relative_location(unreal.Vector(0,0,145),False,False);lamp.set_actor_relative_rotation(rot(yaw=30 if i==2 else 35,pitch=-25),False,False)
    # Door blockers affect only this private copy. They disappear after the corresponding take.
    for i,pos,size in [(1,(540,-695,140),(30,250,280)),(2,(880,1055,140),(30,250,280))]:
        gate=block('Gate'+str(i),pos,size);gate.set_actor_hidden_in_game(True);director.set_editor_property('Gate'+str(i),gate)
    # Visible architecture clues, deliberately distinct from the actual access door.
    patch=unreal.load_asset(MAT+'Remaster/MI_House_Plaster_Service')
    block('PatchedLivingWall',(-548,-440,130),(3,160,225),patch,False)
    trim=unreal.load_asset(MAT+'Remaster/MI_House_Timber_AgedIvory')
    for label,pos,size in [('SealedDoorLeft',(1030,385,115),(5,3,230)),('SealedDoorRight',(1170,385,115),(5,3,230)),('SealedDoorTop',(1100,385,228),(145,3,5))]:block(label,pos,size,trim,False)
    mesh('ReferenceTable',PROP+'SM_House_Table_Side',(1430,1030,0))
    # Photograph material is filled by CaptureCampaignReference.py after geometry has rendered.
    reference=mesh('ReferencePhoto','/Engine/BasicShapes/Plane',(1430,1030,56),(.48,.36,1),collision=False)
    text('ReferenceCaption','REFERENCE / MATCH CHAIR + LIGHT',(1460,1030,95),10,180)
    intercom=point('Intercom',(950,1400,125));director.set_editor_property('Intercom',intercom)
    block('IntercomHousing',(895,1400,125),(12,35,45),trim)
    text('IntercomLabel','PRODUCTION\nINTERCOM',(910,1400,175),10,0)
    # Same physical master camera and subject position for every monologue.
    master=camera('MasterConfession',(1230,1450,145),(1230,1220,145),55)
    comp=master.get_cine_camera_component();comp.set_editor_property('current_focal_length',55.)
    light('ConfessionSoftKey',(1110,1410,225),900)
    light('LivingFaceFill',(100,150,220),650);light('KitchenWorkFill',(1120,-100,250),900)
    intro_cam=camera('IntroDirector',(-330,120,165),(-140,-100,125),28)
    corridor_cam=camera('ServiceApproach',(710,1300,155),(710,800,145),24)
    photo_cam=camera('ReferencePhotoCamera',(1000,1470,190),(1230,1220,80),32)
    def actor_clip(s,end,scene=1,kind='idle'):
        data=SCENES[scene];start=data['start'];dest=data['end'];endwalk=min(round(end*.4),150)
        if kind=='blocked':dest=data['blocked'];endwalk=45
        keys=[(0,start,data['yaw']),(endwalk,dest,data['yaw']),(min(endwalk+25,end-1),dest,0 if scene==3 else (-144 if scene==1 else 90))]
        b=transforms(s,maya,end,keys)
        animation(b,end,[(0,endwalk,'A_Tripo_Walk'),(endwalk,end,'A_Tripo_Wait' if kind=='blocked' else ('A_Tripo_LookAround' if kind=='fail' else 'A_Tripo_Agree'))])
    # Every supplied clip is attached to the matching beat, with actual audio duration.
    for key,record in N['clips'].items():
        failed='_Fail' in key;take=failed or key.endswith('_Perfect');delay=2.5 if failed else (1.5 if take else .6)
        seconds=delay+record['audio_duration']+(5. if key=='Reveal' else (7. if key=='Confession' else 1.0))
        s,end=sequence(key,seconds);captions(s,end,record,delay);voice(s,end,record,delay)
        recording=key in ['Opening','Interlude01','Interlude02','Interlude03','Confession','Reveal'];cast_visibility(s,end,recording,key=='Reveal',take,key=='FinalPickup')
        fade=s.add_track(unreal.MovieSceneFadeTrack);fs=fade.add_section();fs.set_range(0,end);fs.get_all_channels()[0].set_default(0.);fs.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
        if recording:
            b=transforms(s,confession_maya,end,[(0,(1230,1220,0),0)])
            animation(b,end,[(0,end,'A_Tripo_Idle')]);cuts(s,end,[(0,end,master)])
            if key!='Reveal':
                cb=s.add_possessable(comp)
                for prop,value in [('Filmback.SensorWidth',36.),('Filmback.SensorHeight',20.25)]:
                    tr=cb.add_track(unreal.MovieSceneFloatTrack);tr.set_property_name_and_path(prop.split('.')[-1],prop);sec=tr.add_section();sec.set_range(0,end);sec.get_all_channels()[0].set_default(value);sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)
            if key=='Confession':
                # Three short evidence inserts reconnect the clues after Evelyn's identity is revealed.
                for tr in list(s.get_tracks()):
                    if isinstance(tr,unreal.MovieSceneCameraCutTrack):s.remove_track(tr)
                f=round((delay+record['audio_duration']+.6)*30)
                clue1=camera('EvidenceLiving',(-370,-260,160),(-550,-440,125),50)
                clue2=camera('EvidenceDoor',(1000,180,160),(1100,392,130),50)
                cuts(s,end,[(0,f,master),(f,f+55,clue1),(f+55,f+110,clue2),(f+110,min(f+165,end),photo_cam),(min(f+165,end),end,master)])
            if key=='Reveal':
                for tr in list(b.get_tracks()):
                    if isinstance(tr,(unreal.MovieScene3DTransformTrack,unreal.MovieSceneSkeletalAnimationTrack)):b.remove_track(tr)
                walk=transforms(s,confession_maya,end,[(0,(1230,1220,0),0),(115,(1230,1220,0),-90),(210,(1480,1220,0),-90)])
                animation(walk,end,[(0,115,'A_Tripo_Wait'),(115,210,'A_Tripo_Walk'),(210,end,'A_Tripo_Wait')])
                cb=s.add_possessable(comp)
                for prop,startv,endv in [('Filmback.SensorWidth',36.,90.),('Filmback.SensorHeight',20.25,50.625)]:
                    tr=cb.add_track(unreal.MovieSceneFloatTrack);tr.set_property_name_and_path(prop.split('.')[-1],prop);sec=tr.add_section();sec.set_range(0,end);sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
                    ch=sec.get_all_channels()[0]
                    for frame,value in [(0,startv),(115,startv),(190,endv),(end-1,endv)]:ch.add_key(unreal.FrameNumber(frame),value,interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)
                for a in crew:visibility(s,a,end,False)
        elif take:
            scene=int(key[2]);data=SCENES[scene];kind='blocked' if ('Blocking' in key) else ('fail' if failed else 'perfect')
            actor_clip(s,end,scene,kind)
            cams=camera_sets[scene]
            if kind=='blocked':cuts(s,end,[(0,end,cams[0])])
            else:
                split=round(end*.4);cuts(s,end,[(0,split,cams[0]),(split,end,cams[-1])])
        else:
            scene=1 if key in ['Intro','L01_Aftermath','L01_CrewTransition'] else (2 if key in ['KitchenApproach','L02_Aftermath','ServiceTransition'] else 3)
            data=SCENES[scene]
            b=transforms(s,maya,end,[(0,data['end'],180 if scene!=3 else 0)]);animation(b,end,[(0,end,'A_Tripo_Wait')])
            cam=intro_cam if scene==1 else (camera_sets[2][1] if scene==2 else camera_sets[3][0])
            cuts(s,end,[(0,end,cam)])
            if key in ['L01_CrewTransition','ServiceTransition','FinalPickup']:
                for j,a in enumerate(crew):
                    if key=='L01_CrewTransition':start=(300+j*60,-50,0);finish=(300+j*60,-550,0);yaw=-90
                    elif key=='ServiceTransition':start=(710,700+j*110,0);finish=(710,1240+j*75,0);yaw=90
                    else:start=(1000+j*100,1470,0);finish=(1000+j*130,1120,0);yaw=-90
                    b=transforms(s,a,end,[(0,start,yaw),(min(end-1,150),finish,yaw)]);animation(b,end,[(0,min(end-1,150),'A_Tripo_Walk'),(min(end-1,150),end,'A_Tripo_Crew_Idle')])
            if key=='FinalPickup':
                for tr in list(s.get_tracks()):
                    if isinstance(tr,unreal.MovieSceneCameraCutTrack):s.remove_track(tr)
                cuts(s,end,[(0,max(1,end-120),camera_sets[3][0]),(max(1,end-120),end,master)])
                visibility(s,confession_maya,end,True)
        E.save_loaded_asset(s);director.set_editor_property('Clip_'+key,s)
        REPORT['clips'][key]={'sequence':s.get_path_name(),'seconds':end/30,'has_vo':record['vo'],'source':record.get('source')}
    # A visible editorial ellipsis; no combat or violence simulation.
    s,end=sequence('BlackEllipsis',2.5)
    tr=s.add_track(unreal.MovieSceneFadeTrack);sec=tr.add_section();sec.set_range(0,end);sec.get_all_channels()[0].set_default(1.);sec.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
    E.save_loaded_asset(s);director.set_editor_property('Clip_BlackEllipsis',s)
    modebp=unreal.load_asset(ROOT+'/Blueprints/BP_CampaignMode');mode=unreal.get_default_object(modebp.generated_class())
    mode.set_editor_property('default_pawn_class',unreal.load_class(None,ROOT+'/Blueprints/BP_CampaignPlayer.BP_CampaignPlayer_C'))
    mode.set_editor_property('hud_class',unreal.load_class(None,ROOT+'/Blueprints/BP_CampaignHUD.BP_CampaignHUD_C'));E.save_loaded_asset(modebp)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',modebp.generated_class())
    spawn(unreal.PlayerStart,'PlayerStart',SCENES[1]['spawn'],'Markers')
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    changed=[name for name,digest in protected.items() if hashlib.sha256((P/name).read_bytes()).hexdigest()!=digest]
    assert not changed,changed
    REPORT.update(success=True,protected_files=len(protected),changed_protected_files=changed,audio_assets=len(audio_entries),actor_count=len(A.get_all_level_actors()))
except Exception:
    REPORT['errors'].append(traceback.format_exc());unreal.log_error(REPORT['errors'][-1])
finally:
    (P/'Saved/QA/CampaignStage.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
