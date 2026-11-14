"""Build the director's runtime subtitle arrays from the authored performance timings."""
import json
from pathlib import Path


def build_cue_arrays(flow):
    starts, counts, times, texts = [], [], [], []
    for expected_index, block in enumerate(flow["blocks"]):
        if expected_index != block["index"]:
            raise ValueError(f"Unexpected block order at {block['name']}")
        cues = block["cues"]
        starts.append(len(times))
        duration = block["duration"]
        for i, cue in enumerate(cues):
            start = cue["time"]
            limit = cues[i + 1]["time"] if i + 1 < len(cues) else duration
            if not (0 <= start < limit <= duration):
                raise ValueError(f"Invalid cue timing in {block['name']}: {start} to {limit}")
            body = cue["text"].strip()
            speaker = cue["speaker"].strip()
            if not body or not speaker:
                raise ValueError(f"Empty line or speaker in {block['name']}")
            times.append(start)
            texts.append(f"{speaker}\n{body}")
            # Give the line reading time, then let an actor listen or a sound play in silence.
            # Keep the last line during a failed take so the player can act on the direction.
            hold_for_cut = block["kind"] == "failure" and i + 1 == len(cues)
            clear_at = round(start + max(2.15, len(body) / 15.0 + 0.55), 2)
            if not hold_for_cut and limit - clear_at >= 0.9:
                times.append(clear_at)
                texts.append("")
        counts.append(len(times) - starts[-1])
    return dict(CueStarts=starts, CueCounts=counts, CueTimes=times, CueTexts=texts)


def sync_to_director():
    import unreal

    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    flow = json.loads((root / "Tools/Narrative/NarrativeFlow.json").read_text(encoding="utf-8"))
    arrays = build_cue_arrays(flow)
    bp = unreal.load_asset("/Game/Game/Blueprints/Flow/BP_NarrativeDirector")
    defaults = unreal.get_default_object(bp.generated_class())
    durations = list(defaults.get_editor_property("Durations"))
    if len(durations) != len(flow["blocks"]) or any(
        abs(d - block["duration"]) > .02 for d, block in zip(durations, flow["blocks"])
    ):
        raise ValueError("The performance timings differ from the active director sequences.")
    defaults.modify()
    for name, values in arrays.items():
        defaults.set_editor_property(name, values)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError("Could not save narrative director subtitle arrays.")
    director = next(
        a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        if a.get_actor_label() == "FLOW_Narrative_Sections05_14"
    )
    for name, values in arrays.items():
        actual = list(director.get_editor_property(name))
        if name == "CueTimes":
            matches = len(actual) == len(values) and all(abs(a - b) < 0.002 for a, b in zip(actual, values))
        else:
            matches = actual == values
        if not matches:
            raise RuntimeError(f"The level director does not inherit the updated {name} values.")
    spoken = sum(bool(text) for text in arrays["CueTexts"])
    print(f"Verified level director: {spoken} spoken cues, {len(arrays['CueTimes']) - spoken} quiet intervals.")


if __name__ == "__main__":
    try:
        import unreal
    except ImportError:
        flow_path = Path(__file__).with_name("NarrativeFlow.json")
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        result = build_cue_arrays(flow)
        print(f"Validated {len(result['CueStarts'])} sequences and {len(result['CueTimes'])} caption changes.")
    else:
        sync_to_director()
