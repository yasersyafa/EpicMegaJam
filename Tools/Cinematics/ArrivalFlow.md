# Arrival tutorial and living-room introduction

SB_GrayBox starts with the existing 30-second Maya opening (Space skips). After
playback stops, the cinematic Maya actor is destroyed. The separate gameplay Maya
is retained for the introduction and Scene 01; it is not a duplicate cinematic actor.

BP_ArrivalDirector then runs this ordered, one-shot progression:

1. Walk at least 120 cm from the exterior PlayerStart.
2. Look at least 25 degrees away from the initial view.
3. Approach within 280 cm of the front door hinge and press E to open it.
4. Press Tab to open Director's Notes. Tab toggles notes throughout gameplay.
5. Walk through the lobby/hall to the living-room crew (arrival radius 85 cm
   around -160,220,88). Waiting outside never starts the conversation.
6. Crew A's three document lines play while Crew A places the wardrobe and Crew B finishes positioning the sofa.
7. Maya walks along a fixed clear aisle toward the director with an attached script prop, then her six-line
   conversation plays. Afterward she returns to her Scene 01 start marker.
8. Tutorial text clears; notes update to preparation. The director stops ticking.

Tutorial hints/subtitles use WBP_Scene01Objective; the old permanent scene/control HUD
is hidden. Scene details are available only while Notes is open. This widget has no
Construct dialogue chain: crew and Maya captions require explicit arrival events.
Dialogue remains English source wording from page 3 of Team Review v3.0, with
speaker labels and reading estimates. No voice-over is supplied.

Three crew mannequins and Quinn are temporary blocking, with stock idle/walk cycles.
Movement uses short authored component paths, not a finished NPC navigation/acting system.
The gameplay ACTION/CUT/retake puzzle remains a separate feature.

Exterior restoration reuses StageHouseExterior.py and its existing optimized meshes:
garden walk, road, 31 shrubs, porch lighting and four invisible BlockAll boundaries.
The new entrance door uses a hinge actor and a collision leaf; it swings inward.
Both E and Tab input bindings have Consume Input disabled to preserve player interactions.

Validation evidence: ArrivalValidation.json, ArrivalKeyValidation.json, and
ArrivalExteriorValidation.json in this folder. Screenshots are in Previews/Arrival/.
Tests cover idle gating, all nine arrival lines, crew case placement, Maya approach/return,
notes update, final caption clearance, movement restoration, actual E/Tab input and
84 boundary capsule sweeps. Runtime uses Blueprint/Level Sequence only; Python scripts
are editor authoring/verification tools, not startup dependencies.

Recovery point: C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-Arrival/.
Do not rerun StageOpeningFlow.py or the old subtitle graph receipt over this flow;
those earlier staging recipes predate arrival-gated dialogue and may reset level references.

## Revised NPC blocking

The earlier player-route test did not validate NPC paths; NPCs consequently clipped the
user-adjusted sofas. The revised layout preserves those final sofa transforms, repositions
crew in clear work areas, and uses fixed Maya approach/return markers instead of blindly
moving to an offset from any player position. Crew C waits clear of lobby furniture.
The generic carried case is replaced with Scene 01's actual sofa and wardrobe, using the
existing optimized mesh library. Props detach when placed. These remain blocking animations;
stock walk cycles are not final load-bearing carry/push performances.

NPCBlockingValidation.json records frame-by-frame 55 cm horizontal body-clearance checks
against live living-room/lobby furniture bounds throughout opening, prep, approach and return.
The test also verifies both final prop positions and all nine introduction lines. These
checks validate the current authored layout; revalidate if furniture or markers change.

## Seated conversation

StartConversation calls SeatDirector before the first crew line. A fixed first-person
camera at the armchair seat (-350,155,125), facing the approach marker, blends in over
0.6 seconds. Movement and look input are locked with one matched pair of controller
ignore-input calls. The standing player mesh is hidden while that view is active;
this is a seated POV, not a finished third-person sitting animation.
Maya reaches -190,80,0 and faces yaw 65 toward the armchair. After her dialogue and
return to the start mark, StandDirector restores the pawn view, visibility and both
input channels. The standing pawn remains at the safe arrival mark, so standing up
never teleports a capsule inside the armchair. Revalidate framing if furniture moves.
StageSeatedConversation.py rebinds the seat camera after restaging arrival actors.
