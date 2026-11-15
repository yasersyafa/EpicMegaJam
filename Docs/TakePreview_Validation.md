# ACTION/CUT preview

Implemented on 2026-11-14 in UE 5.6, map `/Game/Game/Levels/SB_GrayBox`.

## Use

Start PIE. Press F for ACTION. Press F again for CUT, or wait eight seconds for automatic return. Each take starts at the opening shot. The preview has two cameras, a 2.39:1 filmback, and no puzzle completion or Maya performance.

`BP_FilmSceneManager` owns `E_TakeState`, `TakeCount`, `TakeID`, the sequence player, and saved camera state. Its placed instance references `LS_TakePreview`. `BP_PlayerController` caches the manager and routes `IA_ActionCut.Started` to `RequestActionCut`. `StartTake` rejects a non-null HeldProp. `EndTake` handles both manual CUT and the sequence's On Finished callback, guarded by TAKE_PLAYING before entering CUTTING.

The sequence player is created once and its finished callback is bound once at BeginPlay. Stop resets playback for the next take. No delayed take callbacks or timers are introduced. Set Cinematic Mode hides the existing HUD and player, blocks movement and look, and is reversed after restoring the original view target and control rotation. Character interaction refresh, E and RMB are gated by the controller's movement-input lock. Stop Movement Immediately removes residual velocity.

This first implementation applies presentation through the controller's cinematic mode directly; it does not introduce the proposed OnTakeStateChanged dispatcher. It does not change prop transforms or slot IDs. Maya reset and outcome evaluation remain outside this preview.

## Validation

- Modified Blueprints compiled and saved with zero compiler errors or warnings on the final graph edits.
- Injected F key-down/up through the PIE input path: ACTION entered TAKE_PLAYING, count was exactly one while held, and movement was locked. A second press restored SETUP, first-person view, and movement input.
- Invoked the Blueprint request event for 20 consecutive manual ACTION/CUT cycles: all restored movement input. Natural completion also restored SETUP and the player view target.
- Inspected both cinematic camera views in PIE. Both show letterboxing without crosshair. Captures are in `Saved/Screenshots/WindowsEditor/TakePreview_Shot1.png` and `TakePreview_Shot2.png`.
- Existing animation preview emitted REINST warnings during character recompilation. Final PIE checks did not report take-system runtime errors. Python test scripts emitted deprecation notices, separate from gameplay.
- HeldProp rejection is present in the graph but not runtime-tested: the test harness cannot assign that instance property. Prop pickup/placement regression, near-end input races, viewport resizing, and Windows packaging still need manual validation.

## Authoring

Edit `LS_TakePreview` and the two `Cine_TakePreview_*` actors to change framing. The editor-only `Tools/BuildTakePreview.py` creates preview cameras, the sequence, and input assets; gameplay runs entirely in Blueprint. The script does not reconstruct manager or controller graphs. Keep camera bindings in this persistent map.
