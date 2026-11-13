# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**CUT! CUT! CUT!** is a game jam entry (4-day scope) made in Unreal Engine 5. It is a first-person narrative puzzle / psychological horror game in which the player is a film director (Surya). The player arranges props on set, starts a take (ACTION), watches the actress Maya perform through scripted cinematics, and stops the take (CUT) to fix the set. There are 3 levels, then an ending cinematic and credits.

- Engine: UE 5.6 (confirmed from the asset headers, `++UE5+Release-5.6`). Give API, node and menu advice for this version only.
- Spec: `Docs/PRD_CUT_CUT_CUT_v0.2.md` is the design spec and the source of truth for gameplay rules, slot/flag/outcome tables per level (§8) and the Blueprint architecture (§11). Most of it is written in Indonesian. Read the relevant section before implementing or advising on a feature. If a request conflicts with the PRD, point out the conflict before proceeding.

## Nature of the codebase

- **Blueprint-only project.** It has no `Source/` folder, no C++ modules, no build scripts, no tests and no lint. All logic lives in binary `.uasset`/`.umap` files under `Content/`. Claude cannot read or edit these directly.
- What Claude can edit: `Config/*.ini`, `EpicMegaJam.uproject`, `CLAUDE.md` and the files under `Docs/`.
- Assets are committed as plain git binaries (no Git LFS). Binary assets can't be merged, so avoid concurrent edits to the same `.uasset`/`.umap` across branches.
- `EngineAssociation` in the `.uproject` is a GUID, which points to a locally registered engine build rather than a launcher version string. Do not change it.
- Input uses Enhanced Input (set as the default player input and input component classes in `DefaultInput.ini`).
- Rendering defaults to Lumen GI and reflections, virtual shadow maps, ray tracing and DX12/SM6 (`DefaultEngine.ini`).
- `GameDefaultMap` is still the template `/Engine/Maps/Templates/OpenWorld`. The working level is `Content/Game/Levels/SB_GrayBox.umap`. (TODO: point `GameDefaultMap` / `EditorStartupMap` at the real map once it exists.)

## Running and validating

There are no build scripts. Open the project with `Start-Process .\EpicMegaJam.uproject`, then test in Play In Editor. Package with **Platforms > Windows > Package Project**, and pick the gameplay map explicitly while `GameDefaultMap` is still the template. Rename or move assets only inside the Unreal Editor, then fix up redirectors. `AGENTS.md` has the full style, testing and PR guidelines.

## How to help with Blueprint work

- Give step-by-step editor instructions: which asset to open, exact node names as they appear in the Blueprint context menu, pin-to-pin connections, variable names and types, and default values.
- Use the asset and variable names from the PRD (`BP_FilmSceneManager`, `PDA_SceneConfig`, `F_OutcomeRule`, `E_TakeState`, ...) so code and spec stay aligned.
- When a fix depends on an existing graph, ask the user to select the nodes, press Ctrl+C and paste the result. Pasted Blueprint nodes are plain text and can be read.
- When an answer would change a whole function or graph, describe the full updated graph rather than only the changed nodes.

## Content layout

Everything for the game lives under `Content/Game/`:
- `Blueprints/Player/`: `BP_PlayerCharacter`, `BP_PlayerController`, `BP_GrayBoxGameMode` (the current graybox framework)
- `Levels/`: `SB_GrayBox` (sandbox/graybox level, blocked out from the floor plan)
- `References/`: `FloorPlan` texture and material used as a blockout guide

The PRD names the director character `BP_DirectorCharacter`. In the repo it is `BP_PlayerCharacter`. Use `BP_PlayerCharacter` in instructions; treat both names as the same class.

## Planned architecture (PRD §11)

These are the core rules to follow when designing or advising on systems:

- **`BP_FilmSceneManager` is the single source of truth** for take state, take lifecycle, evaluation and progression flags. Other actors don't own game state.
- **`E_TakeState` transitions** (not a linear chain):
  - `SETUP → TAKE_PLAYING` on ACTION (F, only if the player is not holding a prop).
  - `TAKE_PLAYING → AWKWARD → WAITING_FOR_CUT` when a non-perfect outcome plays.
  - `TAKE_PLAYING / AWKWARD / WAITING_FOR_CUT → CUTTING → SETUP` on manual CUT (F).
  - `TAKE_PLAYING → PERFECT_TAKE → POST_TAKE → SETUP` (next scene) when the perfect sequence reaches its end.
  - After Level 3: `POST_TAKE → SETUP` (intercom objective) `→ FINALE → CREDITS`. Gameplay never returns to SETUP after FINALE starts.
  - F is ignored in `CUTTING`, `PERFECT_TAKE`, `POST_TAKE`, `FINALE` and `CREDITS`.
- **Data-driven, deterministic evaluation:** slot → flag → outcome. Each level is a `DA_SceneConfig_L0x` instance of `PDA_SceneConfig`, holding `F_FlagRule`s (RequireAll/RequireAny/ForbidAny over `F_Placement` PropID+SlotID pairs) and ordered `F_OutcomeRule`s (array order is priority, and the single `bIsPerfect` rule comes last). One shared evaluation function serves all levels (algorithm in PRD §11.4). It runs once, on ACTION. Never evaluate on Tick.
- Data Assets can't reference level actors, so per-scene actor refs (`F_SceneLevelRefs`) live on the Scene Manager instance as `Map<SceneID, F_SceneLevelRefs>`.
- **Props** (`BP_InteractableProp`) snap only to predefined `BP_PropSlot`s. A prop occupies one slot, a slot holds one prop, and the player holds one prop at a time. Props keep their positions across retakes. The standing lamp uses the same pickup/place system, and its lighting effect comes from its slot alone.
- **Cinematics:** a shared opening Level Sequence, then the selected outcome sequence (e.g. `LS_L01_Opening` → `LS_L01_Blocked` / `LS_L01_MissedClue` / `LS_L01_Perfect`). Only one take sequence may be active at a time.
- **CUT must be clean:** a single centralized reset path stops the sequence, cancels timers, dialogue and pending callbacks, resets Maya to her start point, restores the first-person camera and input, and returns to SETUP. No event from an old take may leak into a new one: increment a `TakeID` on every ACTION and CUT, and make every delayed callback check its captured `TakeID` before running. Success must be processed exactly once (`bSuccessHandled`), even if a sequence event fires twice, and a manual CUT before the perfect sequence finishes cancels the success.
- Dialogue rows (DialogueID, Speaker, SubtitleText, VoiceSound, DialogueCategory, SceneID) live in a Data Table or Data Asset and must work subtitle-only. Hints escalate per outcome through `FailCountByOutcome`, and each hint plays at most once per take.
- One persistent house map holds all three levels (Living Room → Kitchen & Corridor → Secret Room). The Scene Manager gates access between areas through progression flags.
- Surya's dialogue in Levels 1–3 must never reveal that he is the killer. The reveal happens only in the ending cinematic.
- Non-goals: free AI, physics placement, branching dialogue or endings, inventory, multiplayer, and custom shaders or VFX.

## Communication

- Reply in informal Bahasa Indonesia. Keep code, asset names, node names and error strings in English, exactly as they appear in the engine.

## Git conventions

- Commits use Conventional Commits with an optional scope, e.g. `feat(level): ...`, `feat(character): ...`, `docs(prd): ...`.
- Personal work happens on `dev/<name>` branches, and `main` is the main branch.
- Only stage files Claude actually changed. Never stage or commit `.uasset`/`.umap` changes unless the user asks. Ask before pushing.