# Voice-over dialog in SB_GrayBox — 16 November 2026

The production graybox now uses the available recordings for its existing L01/L02 dialogue. `Tools/Cinematics/PrepareGrayBoxDialogueVO.py` extracted 37 mono WAV clips from the supplied local campaign WAVs: nine intro lines, 22 scene/transition lines, four Surya hints, full early CUT, and sofa CUT. The source recordings were read without modification. `Tools/Cinematics/InstallGrayBoxDialogueVO.py` imported the clips to `/Game/Game/Audio/VoiceOver` and filled 29 previously empty `VoiceSound` rows in the production `DT_Dialogue` (27 exact cue matches plus two early CUT rows). Clip durations extend subtitle timers only when necessary.

`BP_FilmSceneManager` retains the active dialog AudioComponent. The next line and `StopDialogue` stop it; reset, new take, and EndPlay already call the manager's dialog cleanup. A missing audio device leaves the subtitle fallback and does not call Play on a null component. `WBP_Scene01Objective` starts each intro clip at its corresponding caption change and stops the previous clip; longer recordings extend that caption's delay. Widget destruction and `BP_ArrivalDirector.FinishIntroduction` stop intro VO. The existing Sequencer VO sections remain the only owners of Maya's take/opening/interlude lines.

Manual CUT chooses between full recorded speech and the existing short shout. L01 sofa CUT and early CUT in L01/L02 use their full recordings without also playing `S_Director_Cut`; CUT lines without matching full recordings keep the short shout and subtitle. `PlayCutAudio` remains the fallback path. No new story progression was added.

## Verification

- Three modified Blueprints (`BP_FilmSceneManager`, `WBP_Scene01Objective`, `BP_ArrivalDirector`) compiled and saved with 0 errors/warnings.
- Hidden SB_GrayBox PIE with deterministic internal audio passed **116 assertions**: all 37 SoundWaves load, all nine intro clips play and stop, all 27 directly mapped dialog clips play and stop, selected missing VO uses silent subtitle fallback, and representative row bindings exist. `Saved/GrayBoxAudio/DialogueRuntime.json` contains the results.
- A focused CUT runtime check passed **five assertions**: the full early CUT clip plays/stops, no simultaneous short shout is present on that direct path, and the short shout fallback plays/stops. `Saved/GrayBoxAudio/CutRuntime.json` contains the results. This check invokes the two playback functions directly; it does not establish a complete player-driven ACTION/CUT route.
- The widget EventGraph contains nine sound references matching the nine intro cue IDs. Existing Sequencer audio was not edited in this integration.
- Runtime testing used a hidden editor with `-RenderOffscreen -NullRHI -DeterministicAudio`, BelowNormal priority and no OS input or physical speaker. No manual listening or packaged build was performed.

The audio source importer emitted a handled BINKA decoder ensure while importing the first clip; all 37 imported SoundWaves loaded and played in the later deterministic PIE run. The first no-sound PIE attempt could not create AudioComponents, so the playback nodes were guarded. A separate harness attempt called opening cleanup before its widget existed and logged an `OpeningOverlay` error; that call was removed from the final focused runtime checks.

## Remaining gaps

- L01 aftermath has no supplied recording. Four alternative hints and L01/L02 CUT variants without an exact recording remain subtitles with the generic short CUT shout.
- L03 through ending still require story-flow integration into SB_GrayBox. Their existing recordings remain in the isolated campaign.
- Exact subtitle and audio synchronization, perceived loudness, all natural narrative triggers, and the full player-driven playthrough still need a listening/visual QA pass. The focused checks verify asset binding and runtime playback/cleanup, not those subjective results.

Pre-change binary backups are in `Saved/GrayBoxAudio/Backup`. The local assets, source clips, and scripts are the deliverables; `Saved/` contains verification outputs and is ignored by Git.
