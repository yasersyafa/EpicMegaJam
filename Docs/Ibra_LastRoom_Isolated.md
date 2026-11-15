# Interlude 02 and Last Room — isolated playable previs

## Open and play

In Content Browser, open **Game / Isolated / IbraLastRoom / L_Interlude02_LastRoom**, then Play. This level is not linked from `SB_GrayBox` and does not change the project startup map.

- First 14 seconds: Maya's **The Edit** monologue, using the six lines supplied in Team Review v3.0.
- Next 38 seconds: a guided first-person camera approach through the service passage, followed by the eight Last Room introduction lines and a preparation card.
- At 52 seconds: camera, HUD, movement, and look return to the player inside the room. Playback timing is game time; a heavily loaded editor may take longer in real time.
- E selects a prop or confirms a free placement. RMB cancels. Green/red ghost indicates physical placement validity, not puzzle correctness.
- Arrange the chair and standing lamp using the small reference composition on the side table. There are no snap slots and no visible blue solution circles.
- Return to the brass director mark and press F for ACTION. F again performs CUT. R resets both props. Tab shows inherited test notes; P pauses.

The inherited test manager still offers 1/2/3, N, and F6 debug controls. They are not production UI. All scene-selector references point to the isolated chair/lamp fixtures so they cannot enter a different production scene.

## Scope and limits

This implements the **Interlude 02 → Approach → Scene 03 preparation** handoff as a self-contained prototype. The approach is a timed cinematic camera move, not an arrival/proximity-triggered free-roam conversation. Maya and Crew A are mannequin stand-ins with idle animation. The small tabletop composition is a blockout reference, not the final photograph. No dialogue voice-over or lip-sync is provided.

The interview stand-in preserves the existing opening's relative camera setup: a locked 75 mm close-up, camera 230 cm in front of Maya, height 122 cm. It is a separate previs setup, not a newly authored continuous master confession recording. Final animation, clothing, framing continuity, and the eventual uncropped reveal still require the cinematic pass.

The free-placement puzzle inherits the existing tested radius evaluator. The chair goal radius is 90 cm; the lamp goal radius is 75 cm. Acceptance uses horizontal prop-bounds center distance, with no snap and no rotation scoring. Start positions are outside their solution areas. The lamp's position is evaluated; this prototype does not implement a lighting simulation or a new movable-light component.

ACTION/CUT uses the inherited test simulator: a valid arrangement completes after four seconds. It does not yet play Scene 03's full Maya performance, failure acting, or final pickup/ending. A successful simulator run is not completion of the production story sequence.

## Ownership and merge safety

New runtime assets are confined to `/Game/Game/Isolated/IbraLastRoom/`:

- `L_Interlude02_LastRoom`
- `Blueprints/BP_LastRoomManager`, `BP_LastRoomPlayer`, `BP_LastRoomMode`
- `Cinematics/LS_Interlude02_Approach`
- Local room and caption materials

The three Blueprints are children of the existing gameplay test classes. They read shared meshes, animation, input, HUD, and interaction logic; the source assets are not edited. This avoids binary merge conflicts in the production level, though later parent-class changes can affect inherited behavior.

The build verified SHA-256 hashes for 46 existing production/config files and found zero changes. `EpicMegaJam.uproject` already had the two editor plugins disabled before this task; that pre-existing change is unrelated. Do not include it just to share this level.

Share the new `Content/Game/Isolated/IbraLastRoom/`, `Tools/Isolated/`, and this guide. Do not include `Saved/`, `Intermediate/`, or generated caches.

## Authoring and validation

`Tools/Isolated/BuildLastRoom.py` builds only this isolated map/assets. It refuses to overwrite a successful build unless `LASTROOM_REBUILD=1` is explicitly set in the launching environment. Rebuilding replaces this map's staged actors; do not run it over manual edits without backing up the isolated assets.

`Tools/Isolated/ValidateLastRoom.py` opens the isolated level and runs PIE in a separate background editor. It checks intro state/input locks, camera transitions, captions, player handoff, real free-placement handler/trace behavior, placement outside the solution, the correct arrangement, CUT, and reset. It invokes Blueprint methods rather than physical keyboard input. It does not save gameplay changes.

Final results and images are local in `Saved/QA/LastRoomValidation.json`, `LastRoomValidation.log`, `LastRoom_1.png`, `LastRoom_2.png`, `LastRoom_3.png`, and `LastRoom_Gameplay.png`. Build isolation evidence is in `Saved/QA/LastRoomBuild.json`. Audio, packaged Windows play, physical-input regression, and final art remain untested.

Final validation on 15 November 2026: **21/21 checks passed**, zero harness errors, and no `Accessed None`, Blueprint error, or script warning found in the final validation log. The final build again reported zero changes to the 46 protected production/config files. Interlude and approach captures were visually inspected for text orientation, caption framing, and contrast.
