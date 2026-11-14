> Updated handoff: see ArrivalFlow.md. The cinematic stand-in is now destroyed after playback;
> arrival tutorial creates the HUD and gates dialogue on reaching the living room.
> Earlier staging scripts/receipts below describe the original prototype, not the current handoff.

# Opening -> Scene 01 setup

Play SB_GrayBox. FLOW_Opening_ToScene01 runs LS_Opening_Maya (30 seconds at 30 fps),
locks movement/look and hides the normal HUD/player. It creates WBP_OpeningOverlay
for English subtitles, then the title. Space skips. When the sequence stops,
FinishOpening runs once, removes the overlay, restores the player view and inputs,
reveals the Scene 01 stand-in and displays WBP_Scene01Objective. The director stops
ticking and disables its input component after handoff, releasing the skip key.

The Level Sequence owns camera cuts, the locked camera transform, idle animation,
fades and an original generated camera-power beep. Subtitles/title timings are in
the overlay EventGraph. Both currently target a 30-second opening; update the UI
cue delays if editorial duration changes. The director detects actual playback
completion rather than using a fixed end delay. No Python/editor plugin is used
by this flow at game startup.

Maya is TEMP previs using Epic's Quinn mannequin and idle animation. Final Maya
mesh, seated performance, facial animation and voice-over remain production work.
The stand-in is not the final confession performance. Its opening actor stays
bound in the hidden room; a separate stand-in is revealed in the playable living
room after opening. The handoff starts Scene 01 preparation; its full ACTION/CUT
puzzle and crew transition are separate gameplay work.

Runtime Blueprints:
/Game/Game/Blueprints/Cinematics/BP_OpeningDirector
/Game/Game/UI/Cinematics/WBP_OpeningOverlay
/Game/Game/UI/Scene01/WBP_Scene01Objective

Sequence: /Game/Game/Cinematics/Opening/LS_Opening_Maya
The level retains BP_GrayBoxGameMode, BP_PlayerCharacter and BP_InteractionHUD.
Blueprint movement, interaction and prop-slot graphs are preserved.
OpeningValidation.json records the PIE checks. The temporary validation log node was removed after testing.

BuildOpeningSequence.py rebuilds this sequence and its CINE_Opening_ actors.
Run StageOpeningFlow.py afterward to rebind the director's opening actor reference.
StageOpeningFlow.py exposes the three director references and saves the level.
OpeningGraphReceipts.json records the graph authoring payloads for review.

Backup before this work:
C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-Opening/SB_GrayBox.before-opening.umap
