# Reach and placement guide validation

Validated on 2026-11-13 in UE 5.6.1, map `/Game/Game/Levels/SB_GrayBox`.

## Behavior

- E on a focused prop starts a brief right-hand reach cue. `ReachAlpha` blends in and back out; the IK chain does not stretch. A 35 cm lift above the hit surface keeps the gesture visible in first person. This is a reach cue, not a physical grasp/carry animation.
- `BP_InteractionHUD` draws a crosshair and centered prompts with a dark background. `BP_GrayBoxGameMode` selects this HUD.
- A valid slot shows a green snapped ghost and `[E] PLACE`. An invalid destination shows a red preview and `NO VALID SLOT`; E cannot place there.
- RMB cancels without moving the prop from its last committed position. Existing slot compatibility and occupancy checks remain authoritative.
- Debug Print String prompts were removed. Placement is refreshed when E is pressed.

## PIE checks

| Check | Result |
| --- | --- |
| Aim at test prop, E pickup | HeldProp assigned; HUD changes to placement state |
| Reach cue | Alpha reaches 1 and returns to 0; Anim Blueprint receives it |
| Arm stretch | Disabled; observed shoulder-to-hand distance stayed below 53 cm |
| Aim away from slots, press E | Red ghost; prop and CurrentSlotID unchanged |
| Aim at SLOT_B, press E | Green ghost snaps; prop moves to SLOT_B and holding ends |
| Pick up again, RMB | Ghost hides; last committed transform and slot stay unchanged |
| Mismatching AllowedPropID | TargetSlot stays empty |
| Occupied SLOT_B | TargetSlot stays empty; E does not move the held prop |
| Look down to -89 degrees | Body bounds remain full size; shadow mesh retains its head |
| Final run after editor restart | HUD active, reach blends out, no Blueprint/animation runtime warnings |

The occupancy blocker and temporary slot edits existed only in PIE and were discarded. Edited Blueprints were compiled and saved. No Windows packaging check was performed.

## Imported character

`/Game/Game/Characters/Tripo/SK_TripoCharacter` was imported from the supplied Tripo FBX. It has an 80-bone skeleton, linked base-color and normal textures, and a height of approximately 176.14 cm. Legacy FBX import uses uniform scale 180 with scene-unit conversion off; the unscaled source was approximately 0.98 cm tall in that importer.

The imported mesh uses `TripoCharacter_Skeleton` and `PA_TripoCharacter`. The physics asset is a basic generated asset with two bodies and one constraint, not a validated ragdoll. Animation retargeting is outside this import. Source metadata points to the supplied Downloads folder rather than the temporary import copy in Saved.

The final mesh, material, and textures were visually checked using a generated thumbnail. The import was completed and saved after recovering from an editor crash during a discarded trial import.
