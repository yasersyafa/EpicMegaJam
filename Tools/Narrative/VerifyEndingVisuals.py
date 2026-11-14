import unreal,sys,types
m=types.ModuleType('narrative_final_visual');sys.modules['narrative_final_visual']=m
exec('''import unreal,json,os,traceback
P=unreal.Paths.project_dir();out=P+'Saved/NarrativeFinalVisual';os.makedirs(out,exist_ok=True);st={'handle':None,'seed':False,'shots':set()};r={}
def tick(dt):
 try:
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  unreal.GameplayStatics.set_global_time_dilation(w,3);now=unreal.SystemLibrary.get_game_time_in_seconds(w);by={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)};a=by['FLOW_Narrative_Sections05_14'];pc=unreal.GameplayStatics.get_player_controller(w,0)
  if not st['seed'] and now>2:
   by['FLOW_Opening_ToScene01'].call_method('FinishOpening');arrival=by['FLOW_Arrival_Tutorial_LivingRoom'];arrival.call_method('InitializeArrival');arrival.set_actor_tick_enabled(False);a.call_method('InitializeFlow');a.call_method('BeginBeat',(21,));st['seed']=True;return
  if not st['seed']:return
  block=a.get_editor_property('CurrentBlock');elapsed=now-a.get_editor_property('StartTime')
  for (b,t,name) in [(21,1.5,'evidence_call_sheet'),(21,5,'reference_photo'),(22,3,'closeup'),(22,13,'full_frame'),(22,20,'empty_foreground'),(23,2,'credits')]:
   if block==b and elapsed>t and name not in st['shots']:
    st['shots'].add(name);unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+out+'/'+name+'.png -nosuffix',pc)
    if name=='closeup':r['close_camera']=pc.get_view_target().get_actor_location().to_tuple();r['head']=by['NAR_Master_Maya'].skeletal_mesh_component.get_socket_location('head').to_tuple()
    if name=='full_frame':r['wide_camera']=pc.get_view_target().get_actor_location().to_tuple();r['focal']=pc.get_view_target().get_cine_camera_component().current_focal_length;r['bodies']=sum(not by['NAR_Master_Body_'+str(i)].get_editor_property('hidden') for i in range(4))
  if 'credits' in st['shots']:
   r['shots']=list(st['shots']);r['same_camera_position']=r['close_camera']==r['wide_camera'];json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.GameplayStatics.set_global_time_dilation(w,1);unreal.unregister_slate_post_tick_callback(st['handle'])
 except Exception:
  r['error']=traceback.format_exc();json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.unregister_slate_post_tick_callback(st['handle'])
st['handle']=unreal.register_slate_post_tick_callback(tick)
''',m.__dict__)
