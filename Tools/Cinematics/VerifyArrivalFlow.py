import unreal,sys,types
m=types.ModuleType('arrival_test');sys.modules['arrival_test']=m
exec('''import unreal,json,os,traceback
out=unreal.Paths.project_dir()+'Saved/ArrivalValidation';os.makedirs(out,exist_ok=True)
r={'samples':[],'errors':[]};st={'handle':None,'step':0,'wait':0,'texts':set()}
def tick(dt):
 try:
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  unreal.GameplayStatics.set_global_time_dilation(w,3)
  now=unreal.SystemLibrary.get_game_time_in_seconds(w);actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
  a=next(x for x in actors if x.get_actor_label()=='FLOW_Arrival_Tutorial_LivingRoom');stage=a.get_editor_property('Stage');pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0);hud=a.get_editor_property('ArrivalHUD')
  text=str(hud.get_editor_property('DialogueCaption').get_text()) if hud else ''
  if text not in st['texts']:
   st['texts'].add(text);r['samples'].append({'t':now,'stage':stage,'text':text})
  def shot(name):unreal.SystemLibrary.execute_console_command(w,'Shot ShowUI filename='+out+'/'+name+'.png -nosuffix',pc)
  if st['step']==0 and stage==1:
   r['initial_no_dialogue']=not any(t.startswith(('MAYA','CREW','SURYA')) for t in st['texts']);r['outside_spawn']=pawn.get_actor_location().y>1600;r['opening_dummy_removed']=not any(x.get_actor_label()=='CINE_Opening_Maya_StandIn' for x in actors);shot('garden_tutorial');st['wait']=now+5;st['step']=1
  elif st['step']==1 and now>st['wait']:
   r['idle_does_not_progress']=stage==1;pawn.set_actor_location(unreal.Vector(-1045,2100,100),False,False);st['step']=2
  elif st['step']==2 and stage==2:
   pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=-40,roll=0));st['step']=3
  elif st['step']==3 and stage==3:
   pawn.set_actor_location(unreal.Vector(-1045,1770,100),False,False);a.call_method('HandleDoor');st['step']=4
  elif st['step']==4 and stage==4:
   r['door_open']=abs(a.get_editor_property('DoorHinge').get_actor_rotation().yaw)>90;a.call_method('HandleNotes');st['step']=5;st['wait']=now+2
  elif st['step']==5 and stage==5 and now>st['wait']:
   shot('notes');a.call_method('HandleNotes');r['still_no_living_dialogue']=not text.startswith(('CREW','MAYA','SURYA'));pawn.set_actor_location(unreal.Vector(-280,270,90),False,False);pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0));st['step']=6;st['wait']=now+2
  elif st['step']==6 and now>st['wait']:
   shot('crew_conversation');r['crew_case_moves']=a.get_editor_property('CrewB').get_actor_location().y<140;st['step']=7
  elif st['step']==7 and stage==7:
   shot('maya_script');r['maya_approached']=a.get_editor_property('Maya').get_actor_location().y>0;st['step']=8
  elif st['step']==8 and stage==8:
   st['step']=9;st['wait']=now+5
  elif st['step']==9 and now>st['wait']:
   r['finished_blank']=not text.strip();p=a.get_editor_property('Maya').get_actor_location();r['maya_at_start']=p.distance(unreal.Vector(-340,-170,0))<5;r['movement_enabled']=not pc.is_move_input_ignored();r['case_placed']=a.get_editor_property('CrewCase').get_actor_location().distance(unreal.Vector(330,-365,0))<5;r['notes_updated']='Crew and Maya are ready.' in str(hud.get_editor_property('Objective').get_text());r['dialogue_lines']=sum(t.startswith(('CREW','MAYA','SURYA')) for t in st['texts']);shot('scene01_ready');json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.GameplayStatics.set_global_time_dilation(w,1);unreal.unregister_slate_post_tick_callback(st['handle'])
 except Exception:
  r['errors'].append(traceback.format_exc());json.dump(r,open(out+'/proof.json','w'),indent=2);unreal.unregister_slate_post_tick_callback(st['handle'])
st['handle']=unreal.register_slate_post_tick_callback(tick)
''',m.__dict__)

