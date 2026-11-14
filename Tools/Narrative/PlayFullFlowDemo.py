import unreal,sys,types
m=types.ModuleType('cut_full_playthrough');sys.modules['cut_full_playthrough']=m
exec('''import unreal,math,json,time,traceback,os
P=unreal.Paths.project_dir();out=P+'Saved/FullPlaythroughDemo';os.makedirs(out,exist_ok=True)
st={'handle':None,'route':None,'index':0,'last':None,'since':0,'notes':{},'notes_since':0,'hold':None,'hold_since':0,'started':time.monotonic(),'original_speed':None,'stuck_since':0,'last_pos':None};report={'events':[],'errors':[],'mode':'normal-speed, gameplay callback simulation; character movement uses collision'}
routes={
 'entrance':[(-1045,1770)],
 'lobby':[(-1045,1450),(-1045,710),(-750,710),(-350,710),(-90,710),(-90,390),(-160,220)],
 'dining':[(-150,160),(-190,-250),(-190,-430),(-90,-450),(-90,-700),(-120,-800)],
 'kitchen':[(350,-790),(400,-695),(620,-695),(900,-450)],
 'service':[(1050,-450),(1050,80),(900,180),(705,180),(705,480),(705,1040),(1000,1040),(1170,1120)],
 'intercom':[(1050,1190)]}
def turn(pc,target,dt,pitch=0):
 rot=pc.get_control_rotation();delta=(target-rot.yaw+180)%360-180;pc.set_control_rotation(unreal.Rotator(pitch=rot.pitch+max(-55*dt,min(55*dt,pitch-rot.pitch)),yaw=rot.yaw+max(-80*dt,min(80*dt,delta)),roll=0))
def move(name,pawn,pc,dt,speed=150):
 if st['route']!=name:st['route']=name;st['index']=0
 pts=routes[name]
 if st['index']>=len(pts):return True
 pos=pawn.get_actor_location();pt=pts[st['index']];dx=pt[0]-pos.x;dy=pt[1]-pos.y;dist=math.hypot(dx,dy)
 if dist<22:st['index']+=1;return st['index']>=len(pts)
 pawn.character_movement.max_walk_speed=speed;turn(pc,math.degrees(math.atan2(dy,dx)),dt);pawn.add_movement_input(unreal.Vector(dx/dist,dy/dist,0),min(1.,dist/65),False)
 if st['last_pos'] and pos.distance(st['last_pos'])<.02:
  if not st['stuck_since']:st['stuck_since']=time.monotonic()
  elif time.monotonic()-st['stuck_since']>8:raise RuntimeError('Character blocked on '+name+' waypoint '+str(st['index']))
 else:st['stuck_since']=0
 st['last_pos']=pos;return False
def tick(dt):
 try:
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0);by={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)};arrival=by['FLOW_Arrival_Tutorial_LivingRoom'];n=by['FLOW_Narrative_Sections05_14'];stage=arrival.get_editor_property('Stage');block=n.get_editor_property('CurrentBlock');now=unreal.SystemLibrary.get_game_time_in_seconds(w)
  if st['original_speed'] is None:st['original_speed']=pawn.character_movement.max_walk_speed
  key=(stage,block,n.get_editor_property('bAwaitingTake'),n.get_editor_property('bAwaitingArrival'),n.get_editor_property('bAwaitingIntercom'))
  if key!=st['last']:
   st['last']=key;st['since']=now;report['events'].append({'time':now,'arrival_stage':stage,'beat':block,'awaiting_take':key[2]});json.dump({'stage':stage,'block':block,'scene':n.get_editor_property('CurrentScene'),'time':now,'route':st['route'],'waypoint':st['index'],'ended':False},open(out+'/status.json','w'),indent=2)
  if not n.get_editor_property('bInitialized'):
   if stage==0:return
   if stage==1:move('entrance',pawn,pc,dt);return
   if stage==2:turn(pc,-40,dt);return
   if stage==3:
    if move('entrance',pawn,pc,dt) and now-st['since']>2:arrival.call_method('HandleDoor')
    return
   if stage==4:
    if now-st['since']>2:arrival.call_method('HandleNotes');st['notes_since']=now
    return
   if stage==5:
    hud=arrival.get_editor_property('ArrivalHUD')
    if hud.get_editor_property('bNotesOpen'):
     if now-st['notes_since']>5:arrival.call_method('HandleNotes')
     return
    move('lobby',pawn,pc,dt);return
   return
  if n.get_editor_property('bAwaitingTake'):
   scene=n.get_editor_property('CurrentScene');phase=st['notes'].get(scene,0)
   if phase==0:arrival.call_method('HandleNotes');st['notes_since']=now;st['notes'][scene]=1
   elif phase==1 and now-st['notes_since']>5:
    arrival.call_method('HandleNotes');st['notes'][scene]=2;n.call_method('OnTakeAction',(scene,0))
   return
  if n.get_editor_property('bWaitingManualCut'):
   if st['hold']!=block:st['hold']=block;st['hold_since']=now
   elif now-st['hold_since']>1:n.call_method('OnPerfectTake',(n.get_editor_property('CurrentScene'),))
   return
  if n.get_editor_property('bAwaitingIntercom'):
   if move('intercom',pawn,pc,dt) and now-st['since']>3:n.call_method('HandleIntercom')
   return
  if n.get_editor_property('bAwaitingArrival'):
   move('kitchen' if n.get_editor_property('PendingBeat')==6 else 'service',pawn,pc,dt);return
  if block==4:move('dining',pawn,pc,dt,115)
  elif block==6:move('kitchen',pawn,pc,dt,130)
  elif block==11:move('service',pawn,pc,dt,115)
  if n.get_editor_property('bEnded'):
   report['ended']=True;report['duration_seconds']=time.monotonic()-st['started'];json.dump(report,open(out+'/proof.json','w'),indent=2);json.dump({'ended':True,'block':block},open(out+'/status.json','w'));pawn.character_movement.max_walk_speed=st['original_speed'];unreal.unregister_slate_post_tick_callback(st['handle'])
 except Exception:
  report['errors'].append(traceback.format_exc());json.dump(report,open(out+'/proof.json','w'),indent=2);json.dump({'error':report['errors'][-1]},open(out+'/status.json','w'));unreal.unregister_slate_post_tick_callback(st['handle'])
st['handle']=unreal.register_slate_post_tick_callback(tick)
''',m.__dict__)
