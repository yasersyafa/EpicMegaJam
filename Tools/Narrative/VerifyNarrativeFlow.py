import unreal,sys,types
m=types.ModuleType('narrative_validation');sys.modules['narrative_validation']=m
exec('''import unreal,json,os,time,traceback
P=unreal.Paths.project_dir();out=P+'Saved/NarrativeValidation';os.makedirs(out,exist_ok=True);r={'props_preserved_on_cut':True,'manual_cut_restores_input':True,'blocks':[],'failures_held':[],'captures':[],'errors':[]};st={'handle':None,'seed':False,'last':-999,'phase':{},'holdUntil':0,'holdKey':None,'start':time.monotonic(),'textset':set()}
def tick(dt):
 try:
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  unreal.GameplayStatics.set_global_time_dilation(w,6)
  actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);by={a.get_actor_label():a for a in actors};pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0);a=by['FLOW_Narrative_Sections05_14'];arrival=by['FLOW_Arrival_Tutorial_LivingRoom'];now=unreal.SystemLibrary.get_game_time_in_seconds(w)
  if not a.get_editor_property('bInitialized'):return
  block=a.get_editor_property('CurrentBlock');scene=a.get_editor_property('CurrentScene');active=a.get_editor_property('bBeatActive');elapsed=now-a.get_editor_property('StartTime')
  if block!=st['last']:r['blocks'].append(block);st['last']=block
  hud=a.get_editor_property('HUD');text=str(hud.get_editor_property('DialogueCaption').get_text());st['textset'].add(text)
  captureAt={0:8,5:5,7:8,12:5,14:8,18:5,20:12,21:1.5,22:13,23:4}
  if active and block in captureAt and elapsed>captureAt[block] and block not in r['captures']:
   r['captures'].append(block);unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+out+'/beat_'+str(block)+'.png -nosuffix',pc)
   if block==22:r['reveal_camera']=pc.get_view_target().get_actor_location().to_tuple();r['reveal_focal']=pc.get_view_target().get_cine_camera_component().current_focal_length;r['visible_bodies']=sum(not by['NAR_Master_Body_'+str(i)].get_editor_property('hidden') for i in range(4))
  if a.get_editor_property('bAwaitingTake'):
   phase=st['phase'].get(scene,0);positions={n:by[n].get_actor_location().to_tuple() for n in ['PROP_House_Living_Sofa_ThreeSeat_01','PROP_Scene01_Wardrobe','NAR_Prop_Scene02_Cabinet','NAR_Prop_Scene03_Chair']};old=st.setdefault('scene_props',{}).setdefault(scene,positions);r['props_preserved_on_cut']=r['props_preserved_on_cut'] and positions==old;r['manual_cut_restores_input']=r['manual_cut_restores_input'] and not pc.is_move_input_ignored();variant=[1,2,0][phase] if phase<3 else 0;a.call_method('OnTakeAction',(scene,variant));return
  if a.get_editor_property('bWaitingManualCut'):
   key=(scene,block)
   if st['holdKey']!=key:st['holdKey']=key;st['holdUntil']=now+2;return
   if now<st['holdUntil']:return
   phase=st['phase'].get(scene,0)
   if phase<2:r['failures_held'].append({'scene':scene,'variant':phase+1,'block':block});a.call_method('OnManualCut');st['phase'][scene]=phase+1
   else:a.call_method('OnPerfectTake',(scene,));st['phase'][scene]=3
  if a.get_editor_property('bAwaitingArrival'):
   pending=a.get_editor_property('PendingBeat');r.setdefault('arrival_gates',[])
   if pending not in r['arrival_gates']:r['arrival_gates'].append(pending)
   pawn.set_actor_location(unreal.Vector(900,-450,90) if pending==6 else unreal.Vector(1100,1040,90),False,False)
  if a.get_editor_property('bAwaitingIntercom'):
   r['intercom_required']=True;pawn.set_actor_location(unreal.Vector(1020,1190,90),False,False);a.call_method('HandleIntercom')
  if a.get_editor_property('bEnded'):
   r['ended']=True;r['caption_count']=len([x for x in st['textset'] if x.strip()]);r['seconds']=time.monotonic()-st['start'];json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.GameplayStatics.set_global_time_dilation(w,1);unreal.unregister_slate_post_tick_callback(st['handle'])
  if time.monotonic()-st['start']>180:
   raise RuntimeError('Narrative validation timeout block '+str(block)+' active '+str(active))
 except Exception:
  r['errors'].append(traceback.format_exc());json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.unregister_slate_post_tick_callback(st['handle'])
st['handle']=unreal.register_slate_post_tick_callback(tick)
''',m.__dict__)
