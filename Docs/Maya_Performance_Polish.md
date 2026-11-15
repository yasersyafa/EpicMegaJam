# Maya, intro and crew performance polish

The stretched Maya in the reported screenshot came from `LS_Interlude01`: it still played mannequin animations after the take mesh changed to Tripo. The earlier pass missed that binding. The corrected opening, intro, takes and interlude now use compatible meshes and animations. The shared staging helper rejects mismatched Maya skeletons before authoring a track.

## Source art

All Blender files and character FBX source files live outside the Unreal project:

`D:/Gamedev/Art/EpicMegaJam/Characters/`

- `Maya/Maya_Performance.blend`: packed textures, eleven actions, 30 fps, 1.68 m character.
- `Crew/Crew_Utility.blend`, `Crew/Crew_A.blend`, `Crew/Crew_B.blend`: packed textures, consistent bone axes, 1.78 m characters.
- `Original` folders preserve the input FBX files. `Audit` holds investigation files and archived intermediate Unreal assets.

`Tools/Characters/character_paths.py` derives this directory beside the `Unreal` workspace under `Gamedev/Art`. No Blender files remain in this project's source-art or character-audit directories.

The exported rigs use centimeters and root scale 1. This avoids inherited FBX scale affecting skinning, role IK and attached props. Meshes keep their own proportions; crew bone orientations follow one common convention. Crew translations retarget to each mesh, with pelvis scaling. Maya's horizontal pelvis travel is removed from walk so Sequencer alone owns world movement.

## Runtime changes

- `/Game/Game/Characters/Maya/SK_Maya` and its `Animations` folder own the Maya package.
- `/Game/Game/Characters/Crew/SK_Crew_Base`, `SK_Crew_Camera`, `SK_Crew_Boom` and `Animations` own the crew package.
- Maya has distinct idle, walk, look around, director glance, hesitation, inspection, surprise, waiting, script reading and script-carrying walk. Turn reuses in-place stepping while Sequencer supplies rotation.
- Opening and interlude preserve existing dialogue timing and camera cuts. Interlude faces Maya toward its camera.
- Intro uses the actual Tripo cast. Maya holds the script while standing and walking. The script attaches to the component root in centimeters, avoiding bone-scale inheritance. The seated camera frames her reading mark; an intro key light reveals her face and is hidden at the take handoff.
- `ABP_Crew` remains the single shared Animation Blueprint. Relaxed idle and focused performance retain the existing role IK and hand props. Scene Manager still owns crew focus and scene placement.
- Take Maya stays hidden until the intro handoff. `WAITING` loops until CUT; the existing Scene Manager sequence-stop and reset path remains responsible for cancellation.
- Old CopyPose followers remain hidden. They are retained for recovery and no longer provide the visible intro cast.

## Rebuild

Run these Blender scripts in order with Blender 4.3, from the repository root:

1. `Tools/Characters/BuildMayaPerformance.py`
2. `Tools/Characters/BuildMayaIntroPerformance.py`
3. `Tools/Characters/BuildCrewPerformance.py`
4. `Tools/Characters/ExportCharacterPackages.py`

Use `blender.exe --background --factory-startup --python <script>`. The final export step normalizes the editable files and FBX packages to centimeters.

With PIE stopped, run `ImportMayaPerformance.py` and `ImportCrewPerformance.py` inside Unreal Python. Run `PatchMayaWaiting.py` and `PatchIntroAnimationCalls.py` with Blender's bundled Python through the existing local editor bridge. Then run `StageMayaPerformance.py` and `StageIntroCrewPerformance.py` inside Unreal Python.

The original cinematic builders now use compatible character assets. Run the two character staging scripts after rebuilding cinematics to reapply detailed reaction timing, intro prop placement and camera/light polish.

## Verification and limits

`ValidateIntroCrewPerformance.py` checks live level bindings, every frame of the new intro actions and all three crew meshes against the shared animation library. Its PIE pass exercises the production intro conversation, all four focus/relax transitions, the real interlude sequence and reset. It skips the door/tutorial inputs to concentrate on character behavior. Screenshots and the report are under `Saved/CharacterPolish/IntroCrewValidation`.

`ValidateMayaPerformance.py` covers the remaining Maya actions, looping waiting, sequence cancellation and five repeated resets. Run it during PIE in a module namespace. `PreviewMayaPerformance.py` produces Blender pose previews.

Bone checks alone did not catch the initial rendered artifacts. Validation therefore also checks unit root scale and skeleton references, and runtime screenshots were inspected. Facial lip sync, dedicated pivot footwork and a full manual player-input playthrough remain outside this pass.

Recovery copies of the pre-edit map, character Blueprints and sequences remain under `Saved/CharacterPolish/Backup` and `IntroCrewBackup`. Restore binary backups only with Unreal closed. Original `/Game/Characters/Tripo` assets remain available.

## Recorded result (15 November 2026)

- 31 live level animation bindings match their mesh skeletons.
- 2,360 offline pose frames passed across Maya and the three crew meshes.
- Runtime intro/script scale, four crew focus transitions, the reported interlude and interlude reset passed. Screenshots were inspected for rendered deformation.
- Outcome playback, cancellation, waiting animation and five repeated Maya resets passed again after centimeter normalization.
- Four affected Blueprints compiled with zero errors and zero warnings.

Proof: `Saved/CharacterPolish/IntroCrewValidation/report.json`, `intro_script.png`, `interlude_fixed.png`, `Saved/CharacterPolish/unreal_validation.json` and `compile_results.json`.
