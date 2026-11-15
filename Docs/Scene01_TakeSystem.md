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
5. **Perfect end.** `HandlePerfectTake` (once, `bSuccessHandled`): auto CUT → `POST_TAKE` → `SCENE COMPLETE` + `SuccessDialogueIDs` → `FinishPostTake`. If the config has an `InterludeSequence`, it plays first (`TakePhase` 3, cinematic mode, `InterludeDialogueIDs`, F ignored because the state stays `POST_TAKE`); its end runs `ResetTake`. Then `AdvanceScene`: gate opens, next config, `SETUP`.
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

## L02 rules (Kitchen & Corridor)

`Tools/Cinematics/BuildL02Takes.py` stages it. Both build scripts share `take_staging.py`.

- **Corridor** = the Service passage (x 540..880). **Hollow wall** = `GB_Wall_KitchenServiceE` (y = 400, kitchen side), which hides the secret room.
- **Maya path:** corridor north end (710, 1300) → service door (705, 400) → hollow wall (1100, 270), facing the wall.
- **Props:** `SmallCabinet` (start in the corridor at (710, 830)) and `StandingLamp` (`BP_StandingLampProp`, a real point light, start in the far kitchen corner at (1150, -800)).

| Flag | Rule |
|---|---|
| `bPathClear` | ForbidAny `SmallCabinet@L02_Corridor`, `StandingLamp@L02_Corridor` |
| `bDoorVisible` | ForbidAny `SmallCabinet@L02_HollowWall` |
| `bClueLit` | RequireAny `StandingLamp@L02_LampReveal`, `StandingLamp@L02_Corridor` |

Outcomes: OBSTRUCTED (`bPathClear`, `bDoorVisible`), DARK (`bClueLit`), PERFECT. Putting the lamp in the corridor is the PRD trap: it lights the wall but blocks the path. To solve, move the cabinet out of the corridor and away from the wall, and put the lamp in the reveal zone at (880, 180).

Gates (`SceneLevelRefs[...].GateActor`, invisible BlockAll walls hidden by `OpenSceneGate`):

| Gate | Doorway | Opens after |
|---|---|---|
| `L01_Gate_KitchenDoor` | dining → kitchen (540, -695) | L01 |
| `L02_Gate_SecretRoomDoor` | service → secret room (880, 1055) | L02 |

The director mark is at (1250, -300) in the kitchen. The 27 dialogue rows come from catalog pages 6–7; hint 2 uses the PRD text, and the outcome CUT lines are new.

## Interlude 01 and Transition 07

`Tools/Cinematics/BuildInterludes.py` stages both beats (actors in `Gameplay/Interludes`) and fills the config fields. Run it after the L01 and L02 scripts.

| Beat | When | What |
|---|---|---|
| Interlude 01 "Out of Frame" | After the L01 success lines | `LS_Interlude01` (20.5 s): Maya close-up monologue on Ibra's opening set at (1230, 1230) with our own `CINE_IL01_Closeup` and his `CINE_Opening_KeyLight`. Lines `IL01_MAYA_01..05` (catalog p.5). Then first-person, L02 `SETUP` |
| Transition 07 "A Different Kind of Scene" | First time the player reaches the kitchen doorway in L02 `SETUP` | `TR02_DialogueTrigger` (`BP_DialogueTrigger`, `SceneID` L02, box at (420, -695)) calls `PlayTransition`, which plays `TransitionDialogueIDs` (`TR02_01..07`, catalog p.6) once. Staging: Crew B with a floor lamp, Crew C with a flight case, Maya waiting by the dining table |

- `PDA_SceneConfig` fields: `InterludeSequence`, `InterludeDialogueIDs`, `TransitionDialogueIDs`. An empty `InterludeSequence` skips the interlude.
- `L02_MayaStart` is now at the dining table (160, -980), so Maya waits there in L02 `SETUP` and after every CUT. `LS_L02_*` still start her in the corridor on frame 0.
- `PlayTransition` only plays when `CurrentSceneID` matches and the state is `SETUP`. Otherwise the trigger stays armed.
- `BP_Maya.SetMayaState` skips invalid stand-ins: Ibra's opening destroys `CINE_Opening_Maya_StandIn` at runtime.

## Menus

| Asset | Role |
|---|---|
| `L_MainMenu` + `BP_MenuGameMode` | `GameDefaultMap`. Shows `WBP_MainMenu` (PLAY → `SB_GrayBox`, CREDITS, QUIT), UI-only input, mouse cursor |
| `WBP_Credits` | 40 s `Scroll` animation (cast, team, thanks), then returns to `L_MainMenu`. SKIP returns immediately |
| `WBP_PauseMenu` | RESUME / MAIN MENU / QUIT |
| `IA_Pause` (Esc, P) | `BP_PlayerController.TogglePause`. `bTriggerWhenPaused` is on. In PIE, Esc stops play, so use P |

`BP_PlayerController` BeginPlay restores Game-only input and hides the cursor, because the menu's UI-only input mode survives `OpenLevel`.

## Verified in PIE

- ACTION with the start layout gives BLOCKED, then WAITING_FOR_CUT, the hint (`FailCount BLOCKED=1`) and `[F] CUT`.
- CUT plays the BLOCKED line, Maya returns to the start, state is SETUP.
- Sofa out of the path gives flags `bPathClear=T, bWallVisible=F` and MISSED_CLUE. The camera and Maya hold through WAITING.
- Wardrobe also moved gives PERFECT: walk, turn to the wall, auto CUT, `SCENE COMPLETE`, success dialogue, then `bLevel1Complete=true`, scene index 1, SETUP.
- ACTION → immediate CUT gives `bCutWasEarly=true` and `L01_CUT_EARLY`. `TakeID` increments on both. State stays SETUP afterwards (stale finish ignored).
- L02 flags for four layouts:
  - start → OBSTRUCTED
  - lamp in corridor (trap) → OBSTRUCTED with `bClueLit` T
  - cabinet moved → DARK
  - lamp in reveal → PERFECT, then 12 success lines, `bLevel2Complete`, secret room gate open (hidden, no collision), scene index 2, SETUP
- Menus:
  - main menu renders; CREDITS scrolls; SKIP → menu; PLAY → `SB_GrayBox`
  - TogglePause pauses with the menu shown; a second toggle resumes
- Director mark: ACTION off the mark stays SETUP (`TakeCount` 0). On the mark it starts TAKE_PLAYING. CUT still works.
- Interlude: L01 perfect → success lines → `TakePhase` 3, `IL01_MAYA_01..05`, close-up camera → L02 `SETUP`, view back on the player pawn, Maya at `L02_MayaStart`.
- Transition: entering the kitchen doorway box in L02 `SETUP` sets `bPlayed` and queues `TR02_01..07`.
- `BP_PlayerCharacter`: pick up sofa → valid ghost → place moves the prop and clears `HeldProp`.

## Known issues

1. ~~ACTION is not gated~~. Fixed: ACTION needs the L01 director mark (`L01_DirectorMark`, orange disc at (240, -220) on the east side of the living room). F during Ibra's opening/intro is rejected because the player is not on the mark.
2. Ibra's `WBP_Scene01Objective` tutorial text sits in the same bottom area as `WBP_GameHUD` subtitles and overlaps them.
3. Ibra's static `PROP_Scene01_Wardrobe` and `CREW_Intro_SetDresser` (near the inspection point) are still in the room. Maya ends right next to that crew member.
4. `BP_PlacementArea` is used in production but lives under `Gameplay/Testing/`. Move it in the editor when Yaser agrees.
5. L03, the intercom, the ending cinematic and the credits trigger after the ending are not built yet. Director's Notes text from the config is not shown. After L02 the objective is empty until L03 is complete.
6. Gates are invisible walls. A visible barrier (tape, crate) would read better.
7. Unfocused PIE can jump game time (noted in the 15 Nov devlog). Click the viewport before timing tests.
8. Ibra's opening owns the view for the first seconds of PIE. A take started before it ends saves his camera as `SavedViewTarget`, so test takes only after the view is back on the pawn.
9. Interlude 01 uses Ibra's opening set (the room with the desk), not a new set. The transition crew are static idle poses; no carry animation.
