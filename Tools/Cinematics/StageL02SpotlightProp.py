"""Give the existing L02 puzzle lamp a readable film spotlight silhouette."""
import unreal

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
by={a.get_actor_label():a for a in actors.get_all_level_actors()}
lamp=by['L02_Prop_StandingLamp']
metal=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Exterior/MI_House_Exterior_Metal')
yellow=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Yellow')
paper=unreal.load_asset('/Game/Game/Art/Environment/House/Materials/Instances/Props/MI_House_Prop_Paper')
cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder')
cube=unreal.load_asset('/Engine/BasicShapes/Cube')

# Keep the BP actor and its InteractBox/placement ID so L02 scoring is unchanged.
body=lamp.get_editor_property('Mesh')
body.set_static_mesh(cylinder)
body.set_editor_property('relative_location',unreal.Vector(0,0,85))
body.set_relative_scale3d(unreal.Vector(.065,.065,1.7))
body.set_material(0,metal)
body.set_collision_profile_name('NoCollision')
lamp.get_editor_property('LampLight').set_visibility(False,True)

def part(label,mesh,location,scale,rotation=unreal.Rotator(0,0,0),material=metal):
 a=by.get(label)
 if not a:
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,lamp.get_actor_location())
  a.set_actor_label(label)
  a.set_folder_path('Gameplay/Scene02/L02/Spotlight')
 c=a.static_mesh_component
 c.set_mobility(unreal.ComponentMobility.MOVABLE)
 c.set_static_mesh(mesh)
 c.set_material(0,material)
 c.set_collision_profile_name('NoCollision')
 a.attach_to_actor(lamp,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
 a.set_actor_relative_location(location,False,False)
 a.set_actor_relative_rotation(rotation,False,False)
 a.set_actor_scale3d(scale)
 return a

part('L02_Spotlight_Base',cylinder,unreal.Vector(0,0,6),unreal.Vector(.36,.36,.12))
part('L02_Spotlight_Yoke',cube,unreal.Vector(0,0,160),unreal.Vector(.11,.13,.34),material=yellow)
part('L02_Spotlight_Head',cylinder,unreal.Vector(0,0,184),unreal.Vector(.27,.27,.46),unreal.Rotator(pitch=0,yaw=0,roll=-90),yellow)
part('L02_Spotlight_Lens',cylinder,unreal.Vector(0,25,184),unreal.Vector(.245,.245,.035),unreal.Rotator(pitch=0,yaw=0,roll=-90),paper)

spot=by.get('L02_Spotlight_Beam')
if not spot:
 spot=actors.spawn_actor_from_class(unreal.SpotLight,lamp.get_actor_location())
 spot.set_actor_label('L02_Spotlight_Beam')
 spot.set_folder_path('Gameplay/Scene02/L02/Spotlight')
spot.attach_to_actor(lamp,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
spot.set_actor_relative_location(unreal.Vector(0,28,184),False,False)
spot.set_actor_relative_rotation(unreal.Rotator(pitch=-7,yaw=109,roll=0),False,False)
light=spot.get_component_by_class(unreal.SpotLightComponent)
light.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
light.set_editor_property('intensity_units',unreal.LightUnits.LUMENS)
light.set_editor_property('intensity',850.0)
light.set_editor_property('light_color',unreal.Color(r=255,g=222,b=165,a=255))
light.set_editor_property('attenuation_radius',900.0)
light.set_editor_property('inner_cone_angle',18.0)
light.set_editor_property('outer_cone_angle',31.0)
light.set_editor_property('cast_shadows',True)
body.set_relative_scale3d(unreal.Vector(.065,.065,1.7))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('L02_SPOTLIGHT_STAGED',lamp.get_actor_label(),spot.get_actor_label())
