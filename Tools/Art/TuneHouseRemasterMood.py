import unreal
S=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in S.get_all_level_actors():
 label=a.get_actor_label()
 if label.startswith('LIGHT_House_Remaster_'):a.point_light_component.set_editor_property('temperature',3800.)
 if label.startswith(('RM_House_Chandelier_','RM_House_Rose_')):a.static_mesh_component.set_editor_property('cast_shadow',False)
 if label=='ART_House_SurfaceGrade':
  st=a.get_editor_property('settings')
  for k,v in [('auto_exposure_min_brightness',2.),('auto_exposure_max_brightness',2.),('override_white_temp',True),('white_temp',4200.),('override_color_saturation',True),('color_saturation',unreal.Vector4(.9,.92,.9,1.))]:st.set_editor_property(k,v)
  a.set_editor_property('settings',st)
S.clear_actor_selection_set()
unreal.log('MOOD_TUNED')
