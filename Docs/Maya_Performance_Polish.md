# Maya, intro and crew performance polish

The stretched Maya in the reported screenshot came from `LS_Interlude01`: it still played mannequin animations after the take mesh changed to Tripo. The earlier pass missed that binding. The corrected opening, intro, takes and interlude now use compatible meshes and animations. The shared staging helper rejects mismatched Maya skeletons before authoring a track.

## Source art

All Blender files and character FBX source files live outside the Unreal project:

`D:/Gamedev/Art/EpicMegaJam/Characters/`

- `Maya/Maya_Performance.blend`: packed textures, fourteen actions, 30 fps, 1.68 m character.
- `Crew/Crew_Utility.blend`, `Crew/Crew_A.blend`, `Crew/Crew_B.blend`: packed textures, consistent bone axes, 1.78 m characters.
- `Original` folders preserve the input FBX files. `Audit` holds investigation files and archived intermediate Unreal assets.

`Tools/Characters/character_paths.py` derives this directory beside the `Unreal` workspace under `Gamedev/Art`. No Blender files remain in this project's source-art or character-audit directories.

The exported rigs use centimeters and root scale 1. This avoids inherited FBX scale affecting skinning, role IK and attached props. Meshes keep their own proportions; crew bone orientations follow one common convention. Crew translations retarget to each mesh, with pelvis scaling. Maya's horizontal pelvis travel is removed from walk so Sequencer alone owns world movement.

## Runtime changes

- `/Game/Game/Characters/Maya/SK_Maya` and its `Animations` folder own the Maya package.
- `/Game/Game/Characters/Crew/SK_Crew_Base`, `SK_Crew_Camera`, `SK_Crew_Boom` and `Animations` own the crew package.
- Maya has distinct idle, walk, look around, director glance, hesitation, inspection, surprise, waiting, script reading and script-carrying walk. Directional turn actions counterbalance the legs while Sequencer supplies actor rotation.
- Opening and interlude preserve existing dialogue timing and camera cuts. Interlude faces Maya toward its camera.
- Intro uses the actual Tripo cast. Maya holds the script while standing and walking. The script attaches to the component root in centimeters, avoiding bone-scale inheritance. The seated camera frames her reading mark; an intro key light reveals her face and is hidden at the take handoff.
- `ABP_Crew` remains the single shared Animation Blueprint. Relaxed idle and focused performance retain the existing role IK and hand props. Scene Manager still owns crew focus and scene placement.
- Take Maya stays hidden until the intro handoff. `WAITING` loops until CUT; the existing Scene Manager sequence-stop and reset path remains responsible for cancellation.
- Old CopyPose followers remain hidden. They are retained for recovery and no longer provide the visible intro cast.

## Rebuild

The authoritative Maya source is now `Maya/Maya_Performance.blend` (reviewed grip, confession and directional turns). Export it with `Tools/Characters/ExportCharacterPackages.py` using Blender 4.3. This exporter also exports the three existing crew sources. Do not rerun `BuildMayaPerformance.py` or `BuildMayaIntroPerformance.py` over production sources: those bootstrap generators replace the reviewed actions. Archive source files before regenerating art.

With PIE stopped, run `ImportMayaPerformance.py` and `ImportCrewPerformance.py` inside Unreal Python. Run `PatchMayaWaiting.py` and `PatchIntroAnimationCalls.py` with Blender's bundled Python through the existing local editor bridge. Then run `StageMayaPerformance.py` and `StageIntroCrewPerformance.py` inside Unreal Python.

The original cinematic builders now use compatible character assets. Run the two character staging scripts after rebuilding cinematics to reapply detailed reaction timing, intro prop placement and camera/light polish.

## Verification and limits

`ValidateIntroCrewPerformance.py` checks live level bindings, every frame of the new intro actions and all three crew meshes against the shared animation library. Its PIE pass exercises the production intro conversation, all four focus/relax transitions, the real interlude sequence and reset. It skips the door/tutorial inputs to concentrate on character behavior. Screenshots and the report are under `Saved/CharacterPolish/IntroCrewValidation`.

`ValidateMayaPerformance.py` covers the remaining Maya actions, looping waiting, sequence cancellation and five repeated resets. Run it during PIE in a module namespace. `PreviewMayaPerformance.py` produces Blender pose previews.

Bone checks alone did not catch the initial rendered artifacts. Validation therefore also checks unit root scale and skeleton references, and runtime screenshots were inspected. Facial lip sync and a full manual keyboard playthrough remain outside this pass.

Recovery copies of the pre-edit map, character Blueprints and sequences remain under `Saved/CharacterPolish/Backup` and `IntroCrewBackup`. Restore binary backups only with Unreal closed. Original `/Game/Characters/Tripo` assets remain available.

## Recorded result (15 November 2026)

- 31 live level animation bindings match their mesh skeletons.
- 2,360 offline pose frames passed across Maya and the three crew meshes.
- Runtime intro/script scale, four crew focus transitions, the reported interlude and interlude reset passed. Screenshots were inspected for rendered deformation.
- Outcome playback, cancellation, waiting animation and five repeated Maya resets passed again after centimeter normalization.
- Four affected Blueprints compiled with zero errors and zero warnings.

Proof: `Saved/CharacterPolish/IntroCrewValidation/report.json`, `intro_script.png`, `interlude_fixed.png`, `Saved/CharacterPolish/unreal_validation.json` and `compile_results.json`.

## Reported visual fixes (15 November 2026, follow-up)

- Opening still referenced mannequin Idle; it now uses the compatible, camera-facing `A_Maya_Confession`. Interlude uses the same calm performance.
- Maya base color comes from the requested Tripo conversion. UV topology/hash matches the production mesh, so the existing skeleton and skin weights are preserved. Stable texture source: `Maya/Textures/Maya_BaseColor.jpg` outside Unreal. The requested base-color atlas is retained. The later close-up A/B traced the unwanted facial facets to normal-map shading, not base color.
- Crew skeletal mesh slots were empty. `FixCharacterMaterials.py` assigns the three role materials and Maya's new material using reflected struct setters, then explicitly saves packages.
- Four take crew are hidden until intro handoff; intro extras are hidden after handoff. `PatchCrewVisibility.py` owns these Blueprint transitions. The redundant lobby extra stays hidden.
- Reading and carrying actions use reviewed elbow/wrist planes and finger curl. The thin script attaches to the mesh component root without inherited socket scaling.
- Sequencer matches walk playback to the authored 114.5038 cm/s stride. L02 crosses the doorway before rounding the kitchen corner; its final turn uses a dedicated right pivot. Opening travel uses 0.8234 rate; Dark/Perfect use 1.179.
- Recovery copies for this follow-up: `Saved/CharacterVisualFixBackup`. Blender sources remain outside the Unreal repository.

Targeted runtime validation passed with zero errors and approximately 2,926 pose samples, including intro visibility handoff, material presence, crew focus/relax and interlude/reset. Full route evidence is written separately under `Saved/VisualQA_CharacterFixes`; consult its report for completed phases and any failures. The implemented demo ends after L02; this does not establish completion of the full PRD.

### Completed follow-up QA

The final normal-speed PIE run completed in 460.59 seconds with no harness assertions: menu, full opening, door/notes tutorial, intro/handoff, L01 blocked/early CUT/missed clue/perfect, interlude, L02 obstructed/dark/perfect, credits and return menu. Screenshots were inspected for opening orientation, reading grip, interlude pose, kitchen corner and inspection, credits and menu.

This was assisted visual QA: production Blueprint handlers supplied interactions; props were arranged directly in PIE; director marks used teleport after movement stalled near the cast. It does not certify physical key input or unrestricted collision navigation. Log still reports `InputMode:UIOnly - Attempting to focus Non-Focusable widget` on menu/credits. No Blueprint runtime exception was found in the completed run. The WaitingAnim static lint warning is contradicted by the reloaded CDO's valid animation default.

L02 live walk samples: median Dark 134.67 cm/s and Perfect 135.14 cm/s; minimum travel-facing dot 0.9754 and 0.9618 respectively (1 means forward). Stride rate is matched to authored speed; these measurements do not establish perfect foot locking on every frame.

After PIE, all four skeletal mesh materials, Maya material/texture and Maya Blueprint were explicitly saved and reloaded from disk. Material slots and the requested base-color parameter survived reload. Evidence: `Saved/VisualQA_CharacterFixes/report.json` (`completed: true`), `persistence.json`, and PNG captures. No packaging build was run for these follow-up fixes.

### Opening face correction

The earlier visual assessment incorrectly attributed facial seams/facets to the Tripo base-color art. Same-camera 1000x1000 opening renders (`Saved/MayaTextureAB/editor_old.png` and `editor_no_normal.png`) isolate the cause: `NormalMapWeight=1` produces dark seams and polygonal shading; zero removes them with the same mesh, base color, camera and lighting. Old/new conversion normal JPG hashes are identical, so a different normal file is not the explanation.

`MI_Maya` now uses `NormalMapWeight=0`, preserving the requested base color and smooth mesh normals. The package was saved and reloaded; the zero weight and correct base-color texture survived. `FixCharacterMaterials.py` preserves this setting on rebuild. This intentionally removes normal-map surface detail until a compatible bake is available. No level switch or PIE interruption was required to persist the material correction. Backup/report and the A/B images are in `Saved/MayaTextureAB`.
