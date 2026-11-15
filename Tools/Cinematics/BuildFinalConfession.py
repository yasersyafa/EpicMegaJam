"""Author the final pickup, confession and same-camera reveal for SB_GrayBox."""
import sys
import unreal
sys.path.append(unreal.Paths.project_dir()+'Tools/Cinematics')
import take_staging as ts

F='Gameplay/Finale';Q='/Game/Game/Cinematics/Finale'
by=ts.by_label
camera=by('CINE_Opening_Camera_Closeup')
maya=by('CINE_Opening_Maya_StandIn')
assert camera and maya
intercom=ts.spawn(F,unreal.StaticMeshActor,'FINAL_Intercom',(1015,1330,135),yaw=90)
intercom.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
intercom.static_mesh_component.set_material(0,unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Exterior/MI_House_Exterior_Metal'))
intercom.set_actor_scale3d(unreal.Vector(.22,.10,.30))
label=ts.spawn(F,unreal.TextRenderActor,'FINAL_IntercomLabel',(1015,1310,190),yaw=90)
label.text_render.set_text('INTERCOM  [E]')
label.text_render.set_editor_property('world_size',13.)
label.text_render.set_text_render_color(unreal.Color(r=255,g=200,b=100,a=255))
sheet=ts.spawn(F,unreal.TextRenderActor,'FINAL_EvelynCallSheet',(1110,1100,105),pitch=90)
sheet.text_render.set_text('THE HOUSE THAT REMEMBERS\nEVELYN  /  ORIGINAL PRODUCTION\nSURYA  +  THREE CREW')
sheet.text_render.set_editor_property('world_size',9.)
sheet.text_render.set_text_render_color(unreal.Color(r=40,g=30,b=20,a=255))
sheet.set_actor_hidden_in_game(True)
sheet_camera=ts.camera(F,'CINE_Final_CallSheet',(1130,1080,195),yaw=130,pitch=-75,focal=40)

# Neutral end-pose stand-ins are intentionally hidden until the camera uncrops.
sources=['Crew_Camera','Crew_Boom','Crew_Gaffer','Crew_Script']
for i,xy in enumerate([(990,920),(1120,850),(1370,850),(1500,920)]):
 a=ts.spawn(F,unreal.SkeletalMeshActor,'FINAL_EndPose_'+str(i),(xy[0],xy[1],15),yaw=90,pitch=90)
 source=by(sources[i]).get_component_by_class(unreal.SkeletalMeshComponent)
 a.skeletal_mesh_component.set_skeletal_mesh_asset(source.get_editor_property('skeletal_mesh_asset'))
 a.set_actor_hidden_in_game(True)
 a.skeletal_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

def visible(seq,actor,hidden):
 b=seq.add_possessable(actor);t=b.add_track(unreal.MovieSceneVisibilityTrack)
 t.set_property_name_and_path('bHidden','bHidden');sec=t.add_section()
 sec.set_range(0,seq.get_playback_end());sec.get_all_channels()[0].set_default(hidden)
 sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)

def focal(seq,value):
 component=camera.get_cine_camera_component();b=seq.add_possessable(component)
 t=b.add_track(unreal.MovieSceneFloatTrack)
 t.set_property_name_and_path('CurrentFocalLength','CurrentFocalLength')
 sec=t.add_section();sec.set_range(0,seq.get_playback_end())
 sec.get_all_channels()[0].set_default(value)
 sec.set_completion_mode(unreal.MovieSceneCompletionMode.KEEP_STATE)

def seq(name,frames,close=True,bodies=False):
 s=ts.sequence(Q,name,frames)
 if name=='LS_FinalPickup':
  ts.camera_cuts(s,[(0,frames-150,by('CINE_L03_Wide')),(frames-150,frames,camera)])
 elif name=='LS_FinalReveal':
  ts.camera_cuts(s,[(0,60,sheet_camera),(60,120,by('CINE_L03_Reference')),
                    (120,180,by('CINE_L02_Wall')),(180,frames,camera)])
 else:
  ts.camera_cuts(s,[(0,frames,camera)])
 visible(s,maya,False)
 for i in range(4):visible(s,by('FINAL_EndPose_'+str(i)),not bodies)
 if name=='LS_FinalReveal':visible(s,sheet,False)
 focal(s,75. if close else 16.)
 ts.save(s);return s

seq('LS_Interlude03',360)
seq('LS_FinalPickup',1500)
seq('LS_FinalConfession',1440)
seq('LS_FinalReveal',720,close=False,bodies=True)
ts.save_level()
print('FINALE_STAGED',intercom.get_path_name(),camera.get_path_name())
