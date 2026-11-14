# Scene 01 take system (free placement, BP_Maya, LS_L01, hint/subtitle)

Implemented 15 Nov 2026 on `dev/falih`, UE 5.6, map `SB_GrayBox`.

## What runs

`BP_FilmSceneManager` is the single owner of take state. F calls `RequestActionCut`:

| State | F does |
|---|---|
| SETUP | `StartTake`: rejected while holding a prop, with no active config, or when the player is off the scene's director mark (`F_SceneLevelRefs.DirectorMark`, within `DirectorMarkRadius` 100 cm and `DirectorMarkHeightTolerance` 120 cm, as in Yaser's test level). Off the mark, a 2.5 s subtitle says "Stand on the director's mark…". An empty mark means no gate |
| TAKE_PLAYING / AWKWARD / WAITING_FOR_CUT | `ManualCut` |
| other states | ignored |

Take flow:

1. **ACTION.** `TakeID++`, `EvaluateSetup` runs once (flags → outcome, and Print String shows `[Take] flag ...` and `outcome = ...`), crew focus, cinematic mode, Maya `PERFORMING`.
2. **Opening.** `OpeningSequence` and `IntroDialogueIDs` play.
3. **Outcome.** The selected `OutcomeSequence` and `PerformanceDialogueIDs` play. A non-perfect outcome sets `AWKWARD`.
4. **Non-perfect end.** `WAITING_FOR_CUT`. After `HintDelaySeconds` one hint plays (index = `Min(FailCount-1, last)`) and `[F] CUT` shows. Nothing ends the take automatically.
5. **Perfect end.** `HandlePerfectTake` (once, `bSuccessHandled`): auto CUT → `POST_TAKE` → `SCENE COMPLETE` + `SuccessDialogueIDs` → `FinishPostTake` → gate opens, next config, `SETUP`.
6. **Manual CUT.** `TakeID++` → `ResetTake` → CUT line (early cut during the opening or a perfect take, otherwise the outcome's `CutDialogueID`) → `SETUP`.

`ResetTake` is the single reset path. It clears the hint timer and dialogue timer/queue, stops the sequence, restores the view and input, relaxes the crew and puts Maya back at her start point. Sequence-finished callbacks are ignored unless `SequenceTakeID == TakeID`, and hints are ignored unless `HintTakeID == TakeID`.

The old 8-second auto-end from `LS_TakePreview` is gone. `TakeSequence` (`LS_TakePreview`) is only used to create the sequence player at BeginPlay.

## Assets

| Asset | Role |
|---|---|
| `Blueprints/Player/BP_PlayerCharacter` | Free placement ported from Yaser's `BP_FreePlacementPlayerBase`. The old slot logic was removed |
| `Blueprints/Gameplay/Testing/BP_PlacementArea` | New `AreaID` and `IsActorInside(Actor)`. `ContainsProp` is unchanged for Yaser's tests |
| `Blueprints/Film/Data/` | `PDA_SceneConfig`, `F_Placement`, `F_FlagRule`, `F_OutcomeRule`, `F_SceneLevelRefs`, `F_DialogueRow`, `E_FlagRuleType`, `E_MayaReaction`, `E_MayaState`, `E_DialogueCategory` |
| `Data/Scenes/DA_SceneConfig_L01` | L01 rules and outcome data |
| `Data/Dialogue/DT_Dialogue` | 23 L01 rows. Subtitle-only works: `VoiceSound` is optional and `Duration` drives timing |
| `Blueprints/Characters/BP_Maya` | Tripo Maya. Holds `MayaState`, `ResetToStart`, `SetStartFrom`. Hidden until the first ACTION, which also hides `StandInsToHide` (Ibra's intro Maya) |
| `UI/HUD/WBP_GameHUD` | Objective, subtitle (speaker + line), `[F] CUT`, `SCENE COMPLETE` |
| `Cinematics/L01/LS_L01_Opening/Blocked/MissedClue/Perfect` | Possess `MAYA_L01`, `CINE_L01_Wide`, `CINE_L01_Wall`. Sections use **Keep State**, so Maya holds her pose while waiting for CUT |
| `Characters/Tripo/Maya/SKM_Maya` | **Fixed.** The committed mesh had `Skeleton = None` and a deleted material. It now uses `SK_Tripo_Humanoid` + `M_Maya` |

Level actors live in the `Gameplay/Scene01/L01` folder. `Tools/Cinematics/BuildL01Takes.py` re-stages them and rebuilds the four sequences idempotently. It reuses actors by label, so manager references survive a re-run.

## L01 rules (free placement)

| Flag | Rule |
|---|---|
| `bPathClear` | ForbidAny `Sofa@L01_Path`, `Wardrobe@L01_Path` |
| `bWallVisible` | ForbidAny `Wardrobe@L01_WallFront` |

Outcomes, in priority order: BLOCKED (`bPathClear`), MISSED_CLUE (`bWallVisible`), PERFECT.

Start layout: sofa across the path at (-140, 140), wardrobe against the odd west wall at (-490, -440). This gives BLOCKED on the first take. To solve, move the sofa and the wardrobe anywhere outside both zones.

## Verified in PIE

- ACTION with the start layout gives BLOCKED, then WAITING_FOR_CUT, the hint (`FailCount BLOCKED=1`) and `[F] CUT`.
- CUT plays the BLOCKED line, Maya returns to the start, state is SETUP.
- Sofa out of the path gives flags `bPathClear=T, bWallVisible=F` and MISSED_CLUE. The camera and Maya hold through WAITING.
- Wardrobe also moved gives PERFECT: walk, turn to the wall, auto CUT, `SCENE COMPLETE`, success dialogue, then `bLevel1Complete=true`, scene index 1, SETUP.
- ACTION → immediate CUT gives `bCutWasEarly=true` and `L01_CUT_EARLY`. `TakeID` increments on both. State stays SETUP afterwards (stale finish ignored).
- Director mark: ACTION off the mark stays SETUP (`TakeCount` 0). On the mark it starts TAKE_PLAYING. CUT still works.
- `BP_PlayerCharacter`: pick up sofa → valid ghost → place moves the prop and clears `HeldProp`.

## Known issues

1. ~~ACTION is not gated~~. Fixed: ACTION needs the L01 director mark (`L01_DirectorMark`, orange disc at (240, -220) on the east side of the living room). F during Ibra's opening/intro is rejected because the player is not on the mark.
2. Ibra's `WBP_Scene01Objective` tutorial text sits in the same bottom area as `WBP_GameHUD` subtitles and overlaps them.
3. Ibra's static `PROP_Scene01_Wardrobe` and `CREW_Intro_SetDresser` (near the inspection point) are still in the room. Maya ends right next to that crew member.
4. `BP_PlacementArea` is used in production but lives under `Gameplay/Testing/`. Move it in the editor when Yaser agrees.
5. L02/L03 configs, gates (`GateActor`), the intercom and Director's Notes text from the config are not wired yet. After L01 the objective is empty until L03 is complete.
6. Unfocused PIE can jump game time (noted in the 15 Nov devlog). Click the viewport before timing tests.
