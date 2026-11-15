# UI presentation and illustrated director notes

The primary SB_GrayBox UI uses a shared runtime-cached font, `/Game/Game/UI/Fonts/F_UI`, containing imported Arial Regular and Bold faces. Arial is the approved temporary substitute for Helvetica. Change the Regular/Bold faces in this one font asset when Helvetica becomes available. Main menu, pause, credits, opening overlay, intro captions, take HUD, held notes and the legacy interaction Canvas prompt use the shared font. Isolated campaign and prototype integration widgets are not restyled.

## Cinematic text

Opening, intro and take text is anchored to a lower black UI strip of 160 logical Slate units. The strip extends the existing camera letterbox where necessary, without changing camera settings. Speaker, dialogue and CUT/skip occupy separate vertical regions; the take subtitle group is lifted eight units to leave a clear gap above the hint. The long runtime sample wraps to two dialogue lines. Opening title presentation remains separate.

Gameplay dialogue subtitles remain visible while their text is nonempty, including when the player walks as director. Their black CinematicBand is independently gated by a CameraActor view (including CineCameraActor). Intro/take bands additionally require caption content or an active take hint; opening's band stays present during its cinematic camera view. The opening overlay's own caption remains cinematic-only. Empty dialogue captions collapse in both modes. Caption visibility uses text content rather than previous visibility, so changing cameras cannot prevent subtitles from appearing again. The take objective hides during cinematic camera views and returns during director gameplay. Dialogue text and timers are unchanged.

`Tools/UI/FixCinematicVisibility.py` owns this visibility graph and is called by `PatchPresentation.py`, so rebuilding presentation preserves the policy. Focused runtime verification uses `Saved/UIRefresh/VerifyVisibility.py` and records `Saved/UIRefresh/visibility-result.json`. It checks live widget properties by invoking the presentation function directly in hidden PIE on SB_GrayBox, rather than rendered pixels or natural Tick timing. Pre-fix packages are in `Saved/UIRefresh/VisibilityBackup`.

The corrected gameplay-subtitle policy passed 41 runtime assertions on 16 November. All three widget Blueprints compiled and saved with zero errors/warnings. Gameplay captions stay visible with nonempty dialogue, their bands stay collapsed, and cinematic camera views restore the bands over three repeated cycles. Empty captions collapse. No desktop input or foreground activation was used.


## Notes

Scene Config `ReferenceImage` now selects the L01/L02 storyboard. The manager's existing `RefreshDirectorNotes` still applies scene title/body, then calls the widget's `SetReferenceImage(Texture2D)`. The actual player-held NotesWidget component renders this widget. The image scales to fit the paper without distortion; pose, clipboard and Tab bindings remain unchanged.

L01 annotations: `Entrance / Odd wall`. L02: `Floor plan / Sealed wall`. Header, scene title and a small TAB footer are retained. Checklist widgets remain collapsed, including after scene refresh. No exact slot positions, correct-state indicators or mission tasks are shown. Original source art and exact built-in Imagegen prompts are in `SourceArt/UI/DirectorNotes`; runtime textures are in `/Game/Game/UI/Notes/Textures`.

## Authoring and proof

Run `Tools/UI/BuildPresentation.py` with Blender's bundled Python from the project root while the authoring editor is reachable on bridge port 8765 and PIE is stopped. This imports assets, applies fonts/layout and patches only the responsible UI/notes Blueprint paths. The two source PNGs and font files must be present. Backups are under `Saved/UIRefresh/Backup`.

All behavioral verification ran in Play In Editor in a separate hidden process with `-RenderOffscreen -NoSound -unattended -nosplash -nop4 -NoVSync -MCPBridgePort=8775`, BelowNormal priority, 15 FPS and 50% 3D screen percentage. No OS keyboard/mouse input or foreground activation was used, and no Edit Mode unit tests were run.

The runtime harness renders the live opening/intro/HUD widget instances through a native WidgetComponent at 1280x720, 1920x1080 and 2560x1080. Presentation refresh is invoked explicitly for these offscreen captures because a hidden Slate window does not reliably tick or cache layout geometry. PNG pixel inspection checks actual painted glyph bounds, rather than relying on those empty geometry caches. These are UI-layer captures, not full desktop or first-person scene composites.

Twenty-three runtime assertions passed: shared font references, intro caption availability, objective hide/restore, notes scene changes through the production Scene Manager, correct storyboard texture, hidden checklist and minimal annotations. Ten rendered pixel checks passed: opening, intro and take text at all three sizes plus a separate CUT prompt sample stay inside the lower strip. The two held-component render targets at their actual 440x600 resolution were visually inspected for readability. Physical Tab key input was not injected; player Blueprint byte identity protects the original binding and pose implementation.

Evidence: `Saved/UIRefresh/summary.json`, `Runtime/report.json`, `Runtime/pixel_bounds.json` and twelve PNG captures. Source hashes confirm all existing cinematic sequence assets, their audio/timing, SB_GrayBox.umap and BP_PlayerCharacter are unchanged. No packaging build or commit/push was performed for this UI pass.
