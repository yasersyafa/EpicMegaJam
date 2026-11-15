# Ibra campaign — complete isolated playthrough with supplied VO

Engine: Unreal Engine 5.6.1, Windows. Baseline repository revision: `98deab4`.

## Play this map

Open **Game / Isolated / IbraCampaign / L_CUT_Campaign** and press Play, then **F** on the title screen. This is a private copy of the current house. It does not replace `SB_GrayBox`, `L_Scene01`, `L_GameplaySystems`, the earlier Last Room prototype, or the configured startup map.

The playable chain is:

**Opening → introduction → Scene 1 → aftermath / crew transition → Interlude 01 → kitchen approach → Scene 2 → aftermath / service transition → Interlude 02 → Last Room approach → Scene 3 → aftermath → Interlude 03 → intercom → final pickup → black ellipsis → confession / evidence inserts → uncropped reveal → credits → title screen.**

All three scenes use free placement. Physical placement validity is separate from solving the scene. There are no visible blue solution circles. Failed takes play Maya's reaction and the supplied technical hint, then wait for the player's CUT. Perfect takes complete only after their sequence finishes. CUT stops the current recording, restores the player camera and controls, and resets Maya while preserving confirmed prop placements.

| Control | Action |
| --- | --- |
| F at title screen | Start / replay |
| WASD, mouse | Movement and look in setup |
| E | Select a prop / confirm placement; use the final intercom |
| RMB | Cancel placement |
| F at brass director mark | ACTION with empty hands |
| F during a take | CUT at any time |
| Tab | Director's Notes |
| R in setup | Restore the active scene's two props |
| P | Pause / resume, including active sequence and CUT voice |

The inherited 3D notes are suppressed in this map so Tab presents one notes interface. In PIE, Escape can end the editor's play session; use P to test the game pause flow.

## VO integration

All **23 supplied MPEG recordings** were mapped by their spoken contents, converted locally to mono 48 kHz PCM WAV, and normalized to -18 LUFS with a -2 dB true-peak target. The original files in `Documents/VO Character` were not modified. No replacement voices were generated.

The 24 imported SoundWaves consist of those 23 recordings and a derived sofa-specific CUT cue. Narrative and take VO is embedded in Level Sequences. Player-triggered CUT uses a separate AudioComponent, which is stopped before another take/cinematic begins. Subtitles use canonical team-review wording, aligned to locally transcribed word timings. Sequence lengths follow recording duration rather than the older subtitle reading estimates.

| Recording / group | Usage |
| --- | --- |
| `Awal bgt masuk game - Maya cutscene` | Opening |
| `pre intro` | Crew / Maya introduction |
| `Scene 02 - The Arrival (Living Room)` | Scene 1 perfect performance |
| Sofa / wardrobe failure files | Scene 1 failure branches |
| `Crew Transition` | Crew leaves Scene 1 |
| `Scene 03 — Interlude 01 Out of Frame` | Interlude 01 |
| `Scene 04 — Transition to Kitchen` | Kitchen approach |
| `Scene 05 — The Hollow Wall Kitchen ACTION — Perfect Take` | Scene 2 perfect performance |
| Cabinet / incorrect-lighting failure files | Scene 2 failure branches |
| `Perfect Take — Aftermath` | Scene 2 aftermath; it contains the knocking dialogue |
| `Crew Transition — Service Passage` | Transition after Scene 2 |
| `Scene 06 — Interlude 02 The Edit` | Interlude 02 |
| `Scene 07 — Approach The Last Room` | Last Room approach |
| Incorrect-chair / incorrect-lighting-last files | Scene 3 failure branches |
| `ACTION — Perfect Take last` | Scene 3 perfect performance |
| `Scene 09 — Interlude 03 The Ending` | Interlude 03 |
| `Scene 10 - Final Pickup` | Intercom and final pickup |
| `Scene 11 - Final Confession` | Confession |
| `Final Reveal — The Full Frame` | Final reveal |
| `Manual CUT` | Early / general player-triggered CUT |

The sofa failure contains a spoken CUT beginning at approximately 7.9 s. The failure take's audio section stops at 7.6 s. Its remaining CUT is extracted from 7.72 s and plays only when the player cuts that failure. The game does not automatically speak CUT during the waiting failure.

**Missing recordings:** Scene 1 aftermath and Scene 3 aftermath were not supplied. Those two short conversations use the canonical subtitles with silent fallback timing. The Scene 2 aftermath is not reused for them. Add the correct recordings later using the corresponding narrative entries and sequence audio tracks.

ASR reported an uncertain name in the intro greeting and a few words in the service transition. Subtitle spelling follows the source script (`Surya`, `Laras`); the supplied recordings themselves are unchanged. These portions should be checked by listening before release.

## Content and presentation

- Maya and three crew use the repository's Tripo models and compatible idle/walk/wait/look/agree animations. Maya's take reset also restores her idle animation.
- Separate scripted outcomes exist for blocking, clue/composition/lighting failure, and success in each scene. Actors follow authored transforms and animation sections rather than free AI.
- Visible patched-wall and sealed-door clues were added only to this copied house.
- The Scene 3 reference photograph is captured from its actual correct chair/lamp arrangement. Solution radii are 70 cm for the chair and 65 cm for the lamp; placement is not pixel-perfect and is not snapped. Other scenes use their configured radius goals.
- Movable lamps carry local spotlights. Puzzle evaluation remains deterministic position/area evaluation; it does not sample rendered illumination or score free rotation.
- Monologues share the same physical master camera and subject position. The reveal expands that camera's sensor crop, hides the living crew, and shows four noninteractive end poses. There is no combat, chase, or violence simulation.
- The black ellipsis has an explicit fade reset in subsequent sequences. Replaying resets the master close-up crop and all progression/props.

This is a complete **playable graybox narrative pass**, not final cinematic production. Facial animation/lip-sync, polished acting and hand-to-photo contact, bespoke sitting/death animation, final Foley/music, and the final team credit roster still need an art/audio pass. Credits currently credit the game team collectively rather than inventing names. The first-playthrough 12–15-minute target has not been measured with a human playtest.

## Isolation and sharing

New runtime assets are under **`Content/Game/Isolated/IbraCampaign/`**. New authoring tools/data are under **`Tools/Isolated/`** and converted source audio under **`SourceArt/Isolated/IbraCampaign/VO/`**.

The source house is copied with Unreal's Save Map operation. Its original gameplay/director actors are removed from the copy so only one campaign director owns the flow. Existing shared meshes, animations, interaction props, radius evaluator, and the free-placement player are read-only dependencies. The campaign player is a child of the existing gameplay player.

The staging pass compared SHA-256 hashes for **321 existing Content/Config files** and found no changes. The pre-existing `.uproject` plugin-disable edits and earlier isolated/QA work are separate pending changes; do not include them merely to share this campaign. Generated `Saved/`, `Intermediate/`, plugin binaries, installer files, ASR model caches, and Python environments are not deliverables.

Do not add this director to the live production map alongside the existing opening/arrival/film-scene managers. Integration into the team's main map should explicitly replace or hand off those responsibilities.

## Reproduction and QA evidence

Runtime needs Blueprint, Sequencer, and the imported assets. It does not need Python, Whisper, or the MCP editor bridge.

Authoring order:

1. `PrepareCampaignVO.py` — local conversion/transcription. Requires `faster-whisper==1.2.1`, `av==16.0.1`, and `imageio-ffmpeg`; the local environment is ignored by Git. Set `CAMPAIGN_VO_SOURCE` to use a different original-audio folder.
2. `PrepareCampaignNarrative.py` — canonical subtitle alignment and the split sofa CUT.
3. `BuildCampaignBlueprints.py` — create/update private director, HUD, player and mode via the editor bridge.
4. `StageCampaign.py` inside Unreal Python — create the copied campaign map, import audio, and build its cast/props/sequences. It refuses a rebuild unless `CAMPAIGN_REBUILD=1` is explicitly set. Rebuilding replaces staged actors; back up manual changes first.
5. `FinalizeCampaign.py` — input flags, camera crop resets, crew framing, fade resets, and final-pickup cast visibility.
6. `CaptureCampaignReference.py` — actual solution photograph; temporarily changes and then restores only the private scene. It detaches its callback before import/reimport to avoid recursive Slate execution.
7. `PolishCampaign.py` — final reveal framing, compatible walking animation, end-pose fill light, and removal of non-diegetic guidance from the final frame.
8. `ValidateCampaign.py` — accelerated muted PIE regression, without desktop input or gameplay asset saves.

Local evidence: `Saved/QA/CampaignStage.json`, `CampaignFinalize.json`, `CampaignReference.json`, `CampaignValidation.json`, `CampaignGraphs/*_compile.json`, the final editor log and `Campaign_*.png` captures. Automated checks invoke Blueprint input handlers and real camera traces; they do not establish physical-keyboard/controller coverage or audible playback quality. Manual listening, packaged Windows play, and target-hardware performance remain separate checks.

### Final verification — 15 November 2026

- **97/97 runtime checks passed** in the final polished PIE run: three scenes, both failure branches, held-prop/off-mark rejection, actual free-placement traces and handlers, early CUT, stale finish rejection, twenty repeated retakes, pause/resume, progression/gates, intercom, one Maya in final pickup, expanded master crop, four end poses, credits, and replay.
- **93/93 asset/audio-binding checks passed**: matching supplied recording, positive duration, non-looping SoundWave, recording/trim-aligned section length, and explicit silent fallbacks.
- **23/23 original recordings unchanged** by SHA-256; **24/24 converted WAVs** have valid mono 48 kHz PCM16 format, nonzero duration, and no full-scale clipping.
- The campaign director, HUD, player and game mode compiled with **zero errors and warnings**. A redundant-cast informational compiler note is harmless.
- Opening, failure and final reveal captures were visually inspected. This caught and corrected crew blocking a take camera, a black fade leaking into confession, an unreadable subtitle placement in the earlier prototype, and guide text/marks intruding on the final shot.
- No existing tracked Content or Config file was modified by this campaign task. The staging hash audit covered 321 pre-existing files.

The native FunctionalTest scheduler is not used for these checks. Narrative playback is accelerated and muted during regression, so the results are not a real-time human playthrough, a listening test, or a 12–15-minute pacing measurement. Earlier authoring/harness failures are superseded by the final run and are not counted as player-facing game defects.
