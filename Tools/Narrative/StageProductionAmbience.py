"""Import the original mono room-tone loops and place spatial sources in SB_GrayBox."""
import json
from pathlib import Path

import unreal


def stage():
    editors = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = editors.get_editor_world()
    if world.get_path_name() != "/Game/Game/Levels/SB_GrayBox.SB_GrayBox":
        raise RuntimeError("Open SB_GrayBox before staging the production ambience.")
    if editors.get_game_world():
        raise RuntimeError("Stop PIE before staging the production ambience.")
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    source_dir = root / "SourceArt/Audio/Environment"
    audio_path = "/Game/Game/Audio/Environment"
    existing = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    library = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    # World space for exterior air, prop-relative space for practicals so changes in set dressing carry the sound.
    sources = [
        ("S_Porch_Air", "AMB_Exterior_PorchAir", None, (-1095, 1900, 165), 210., 590., .20),
        ("S_Practical_Ballast", "AMB_Kitchen_PracticalBallast", "NAR_Prop_Scene02_PracticalLamp", (0, 0, 122), 75., 295., .13),
        ("S_Intercom_Receiver", "AMB_FinalRoom_IntercomReceiver", "NAR_Prop_Final_Intercom", (12, 0, 0), 38., 117., .10),
    ]
    pending = []
    for filename, label, parent, _, _, _, _ in sources:
        sound_path = audio_path + "/" + filename
        if parent and parent not in existing:
            raise RuntimeError(f"Missing room tone source prop {parent}")
        if label in existing and not isinstance(existing[label], unreal.AmbientSound):
            raise RuntimeError(f"{label} is not an AmbientSound")
        if not library.does_asset_exist(sound_path):
            task = unreal.AssetImportTask()
            task.filename = str(source_dir / (filename + ".wav"))
            task.destination_path = audio_path
            task.destination_name = filename
            task.automated = True
            task.save = True
            pending.append(task)
    if pending:
        tools.import_asset_tasks(pending)
    library.make_directory(audio_path)
    measured = []
    camera = existing["CINE_Opening_Camera_Closeup"].get_actor_location()
    knock = unreal.Vector(1150, 150, 165)  # Scene 2 seam insert at the knock.
    for filename, label, parent, position, near, fade, gain in sources:
        sound = unreal.load_asset(audio_path + "/" + filename)
        if not isinstance(sound,unreal.SoundWave):
            raise RuntimeError(f"Failed to import {filename}")
        sound.set_editor_property("looping", True)
        sound.set_editor_property("virtualization_mode", unreal.VirtualizationMode.RESTART)
        if not library.save_loaded_asset(sound, only_if_is_dirty=False):
            raise RuntimeError(f"Could not save {filename}")
        actor = existing.get(label) or actors.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector())
        actor.set_actor_label(label)
        actor.set_folder_path("Audio/Environment")
        if parent:
            component = actor.audio_component
            if component.mobility != unreal.ComponentMobility.MOVABLE:
                component.set_mobility(unreal.ComponentMobility.MOVABLE)
            actor.attach_to_actor(existing[parent], "", unreal.AttachmentRule.KEEP_WORLD,
                                  unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
            # Offsets use world centimetres rather than the parent mesh's non-uniform model scale.
            actor.set_actor_location(existing[parent].get_actor_location()+unreal.Vector(*position), False, False)
        else:
            actor.set_actor_location(unreal.Vector(*position), False, False)
        att = unreal.SoundAttenuationSettings()
        att.set_editor_property("attenuate",True)
        att.set_editor_property("spatialize",True)
        att.set_editor_property("distance_algorithm",unreal.AttenuationDistanceModel.LINEAR)
        att.set_editor_property("attenuation_shape",unreal.AttenuationShape.SPHERE)
        att.set_editor_property("attenuation_shape_extents",unreal.Vector(near,0,0))
        att.set_editor_property("falloff_distance",fade)
        att.set_editor_property("enable_reverb_send",False)
        component = actor.audio_component
        component.modify()
        component.set_editor_property("attenuation_overrides",att)
        component.set_editor_property("override_attenuation",True)
        component.set_auto_activate(True)
        component.set_sound(sound)
        component.set_volume_multiplier(gain)
        actor.modify()
        result = component.get_editor_property("attenuation_overrides")
        reach = result.attenuation_shape_extents.x + result.falloff_distance
        pos = actor.get_actor_location()
        if parent and actor.get_attach_parent_actor() != existing[parent]:
            raise RuntimeError(f"{label} is detached")
        if getattr(sound,"duration") < 4 or not sound.get_editor_property("looping"):
            raise RuntimeError(f"Invalid loop for {label}")
        if not result.spatialize or not component.override_attenuation or abs(reach - (near+fade))>.01:
            raise RuntimeError(f"{label} failed spatial settings read-back")
        if (pos - camera).length() <= reach:
            raise RuntimeError(f"{label} spills into the close-up recording")
        measured.append({"actor":label,"pos_cm":list(pos.to_tuple()),"mono_channels":sound.get_editor_property("num_channels"),"duration_s":round(sound.duration,2),
                         "volume":round(component.volume_multiplier,3),"outer_radius_cm":reach,
                         "confession_camera_cm":round((pos-camera).length()),"knock_camera_cm":round((pos-knock).length())})
    if not level.save_current_level():
        raise RuntimeError("Could not save the ambient emitters to SB_GrayBox")
    print("ROOM TONE " + json.dumps(measured))


stage()
