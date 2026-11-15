"""PIE-only visual verification in a hidden renderer; never sends desktop input."""
import unreal,types,sys,time,json,traceback
from pathlib import Path
m=types.ModuleType('ui_runtime');sys.modules[m.__name__]=m;m.__dict__.update(unreal=unreal,time=time,json=json,traceback=traceback,Path=Path)
exec(r'''
ROOT=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()));OUT=ROOT/'Saved/UIRefresh/Runtime';OUT.mkdir(parents=True,exist_ok=True)
r={'mode':'offscreen PIE; native WidgetComponent render targets','checks':[],'captures':[],'errors':[]}
st={'phase':'boot','at':time.monotonic(),'deadline':time.monotonic()+420,'size_index':0,'capture_step':0,'views':[(1280,720),(1920,1080),(2560,1080)]}
def save(): (OUT/'report.json').write_text(json.dumps(r,indent=2))
def check(name,value):
 r['checks'].append({'name':name,'passed':bool(value)});save();assert value,name

def widgets(instance):return {w.get_name():w for w in unreal.ObjectIterator(unreal.Widget) if w.get_outer() and w.get_outer().get_outer()==instance}
def instances(w,name):return [a for a in unreal.ObjectIterator(unreal.UserWidget) if a.get_world()==w and a.get_class().get_name()==name+'_C']
def capture(w,name):
 comp=st['component'];comp.request_redraw();rt=comp.get_render_target();assert rt,'widget render target unavailable'
 options=unreal.ImageWriteOptions();options.format=unreal.DesiredImageFormat.PNG;options.async_=False;options.overwrite_file=True;unreal.ImageWriteBlueprintLibrary.export_to_disk(rt,str(OUT/(name+'.png')),options);r['captures'].append(name);save()
def mount(widget,size):
 widget.remove_from_parent();st['player'].set_editor_property('bNotesUp',True);st['player'].set_actor_hidden_in_game(False);comp=st['component'];comp.set_visibility(True);comp.set_hidden_in_game(False);comp.set_manually_redraw(False);comp.set_redraw_time(0);comp.set_tick_when_offscreen(True);comp.set_draw_at_desired_size(False);comp.set_draw_size(unreal.Vector2D(*size));comp.set_widget_space(unreal.WidgetSpace.WORLD);comp.set_tick_mode(unreal.TickMode.ENABLED);comp.set_component_tick_enabled(True);widget.set_visibility(unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE);comp.set_widget(widget);widget.force_layout_prepass();comp.request_render_update();
 if widget.get_class().get_name() in ['WBP_GameHUD_C','WBP_Scene01Objective_C']:widget.call_method('RefreshCinematicPresentation')
 st['mounted']=widget;st['at']=time.monotonic()
def tick(dt):
 try:
  now=time.monotonic();assert now<st['deadline'],'UI runtime timeout'
  if st['phase']=='boot':
   if now-st['at']<3:return
   unreal.SystemLibrary.execute_console_command(None,'t.MaxFPS 15');unreal.SystemLibrary.execute_console_command(None,'r.ScreenPercentage 50')
   unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play();st.update(phase='opening',at=now);return
  w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
  if not w:return
  if st['phase']=='opening':
   if now-st['at']<8:return
   p=unreal.GameplayStatics.get_player_pawn(w,0);comp=p.get_editor_property('NotesWidget');st.update(player=p,component=comp,notes=comp.get_user_widget_object(),original_size=comp.get_draw_size())
   overlay=instances(w,'WBP_OpeningOverlay')[0];st['overlay']=overlay;mount(overlay,st['views'][0]);st.update(phase='opening_matrix');return
  if st['phase']=='opening_matrix' and now-st['at']>.8:
   ww=widgets(st['overlay']);check('opening caption populated',bool(str(ww['Caption'].get_text())));check('opening Arial font',ww['Caption'].get_editor_property('font').font_object.get_name()=='F_UI');capture(w,'opening_'+str(st['views'][st['size_index']][0]))
   st['size_index']+=1
   if st['size_index']<3:mount(st['overlay'],st['views'][st['size_index']]);return
   actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);arrival=next(a for a in actors if a.get_class().get_name()=='BP_ArrivalDirector_C');arrival.set_actor_tick_enabled(False)
   opening=next(a for a in actors if a.get_class().get_name()=='BP_OpeningDirector_C');opening.call_method('FinishOpening');arrival.call_method('InitializeArrival');arrival.set_actor_tick_enabled(False)
   manager=next(a for a in actors if a.get_class().get_name()=='BP_FilmSceneManager_C');st['manager']=manager;manager.call_method('OnIntroFinished');manager.call_method('StopDialogue');st['hud']=manager.get_editor_property('HUD');st['size_index']=0
   st.update(phase='intro_wait',at=now);return
  if st['phase']=='intro_wait' and now-st['at']>.5:
   intro=instances(w,'WBP_Scene01Objective');check('intro caption widget exists',bool(intro));st['intro']=intro[0];widgets(st['intro'])['DialogueCaption'].set_text('MAYA\nMorning, Mr. Surya.');st['size_index']=0;mount(st['intro'],st['views'][0]);st.update(phase='intro_matrix');return
  if st['phase']=='intro_matrix' and now-st['at']>.8:
   ww=widgets(st['intro']);check('intro uses shared Arial font',ww['DialogueCaption'].get_editor_property('font').font_object.get_name()=='F_UI');capture(w,'intro_'+str(st['views'][st['size_index']][0]));st['size_index']+=1
   if st['size_index']<3:mount(st['intro'],st['views'][st['size_index']]);return
   widgets(st['intro'])['DialogueCaption'].set_text('');st['size_index']=0
   st['manager'].call_method('PlaySequenceAsset',args=(unreal.load_asset('/Game/Game/Cinematics/L01/LS_L01_Perfect'),));st['hud'].call_method('ShowSubtitle',args=(unreal.Text('MAYA'),unreal.Text('I thought I would remember every corner of this place. But something about this wall feels different.')))
   mount(st['hud'],st['views'][0]);st.update(phase='hud_matrix');return
  if st['phase']=='hud_matrix' and now-st['at']>.8:
   ww=widgets(st['hud']);check('objective hidden in cinematic',ww['ObjectiveText'].get_visibility()==unreal.SlateVisibility.COLLAPSED);check('Arial shared font applied',ww['LineText'].get_editor_property('font').font_object.get_name()=='F_UI');capture(w,'take_'+str(st['views'][st['size_index']][0]))
   st['size_index']+=1
   if st['size_index']<3:mount(st['hud'],st['views'][st['size_index']]);return
   st['hud'].call_method('SetCutHintVisible',args=(True,));st['hud'].call_method('RefreshCinematicPresentation');st.update(phase='cut_prompt',at=now);return
  if st['phase']=='cut_prompt' and now-st['at']>.8:
   capture(w,'take_cut_prompt_2560');st['manager'].call_method('ResetTake');unreal.GameplayStatics.get_player_controller(w,0).set_view_target_with_blend(st['player'],0);st['hud'].call_method('RefreshCinematicPresentation');st.update(phase='restored',at=now);return
  if st['phase']=='restored' and now-st['at']>.5:
   ww=widgets(st['hud']);check('objective restored after cinematic',ww['ObjectiveText'].get_visibility()==unreal.SlateVisibility.VISIBLE)
   st['component'].set_widget(st['notes']);st['component'].set_draw_size(unreal.Vector2D(440,600));st['manager'].call_method('RefreshDirectorNotes');st['player'].set_editor_property('bNotesUp',True);st.update(phase='notes1',at=now);return
  if st['phase'] in ['notes1','notes2'] and now-st['at']>.9:
   i=1 if st['phase']=='notes1' else 2;ww=widgets(st['notes']);tex=ww['ClueImage'].get_editor_property('brush').resource_object;check('held notes scene '+str(i)+' reference',tex and tex.get_name()=='T_Storyboard_L0'+str(i));check('held notes checklist hidden',all(ww[x].get_visibility()==unreal.SlateVisibility.COLLAPSED for x in ['Todo1','Todo2','Todo3']));check('held notes annotations minimal',len(str(ww['Objective'].get_text()).split())<=6);capture(w,'notes_L0'+str(i))
   if i==1:st['manager'].call_method('AdvanceScene');st['manager'].call_method('RefreshDirectorNotes');st.update(phase='notes2',at=now);return
   st['player'].set_editor_property('bNotesUp',False);st.update(phase='end',at=now);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();return
 except Exception:
  r['errors'].append(traceback.format_exc());r['failed_phase']=st['phase'];save();unreal.unregister_slate_post_tick_callback(st['handle']);unreal.unregister_slate_post_tick_callback(st['end_handle']);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();unreal.SystemLibrary.quit_editor()
def end_tick(dt):
 if st['phase']=='end' and unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None:
  r['completed']=True;save();unreal.unregister_slate_post_tick_callback(st['handle']);unreal.unregister_slate_post_tick_callback(st['end_handle']);unreal.SystemLibrary.quit_editor()
st['handle']=unreal.register_slate_post_tick_callback(tick);st['end_handle']=unreal.register_slate_post_tick_callback(end_tick);save();print('UI_RUNTIME_READY')
''',m.__dict__)
