# Sections 05–14: gameplay integration

Map: `/Game/Game/Levels/SB_GrayBox`.
Actor: `FLOW_Narrative_Sections05_14`, class
`/Game/Game/Blueprints/Flow/BP_NarrativeDirector`.

The level/cinematic implementation deliberately does not bind F or implement snap selection,
take scoring, ACTION, manual CUT, or automatic CUT. Those belong to the gameplay teammate.
The existing arrival tutorial remains the entry point. Once the seated conversation releases
control, narrative enters Scene 01 preparation and waits for the gameplay system.

Call these Blueprint custom events on the level's director instance:

| Event | Parameters | Responsibility |
| --- | --- | --- |
| `OnTakeAction` | `SceneID` 1–3, `Variant` 0–2 | Play the requested authored performance. 0 = perfect, 1 = obstruction/chair failure, 2 = sightline/light failure. |
| `OnManualCut` | none | Stop performance, restore Surya view/control, return Maya to that scene's start; leave prop configuration untouched. |
| `OnPerfectTake` | `SceneID` 1–3 | After the gameplay system accepts the perfect result, start aftermath and the next narrative chain. |

Useful observable state: `CurrentScene`, `CurrentBlock`, `bAwaitingTake`,
`bWaitingManualCut`, `bBeatActive`, `bAwaitingArrival`, `bAwaitingIntercom`, `bEnded`.
At the end of a take/failure performance, `bWaitingManualCut` becomes true and the
sequence holds its last frame. **This is an integration signal, not automatic success or CUT.**
The gameplay owner decides whether to call OnManualCut or OnPerfectTake. Never infer
success solely from sequence completion. Failure performances wait indefinitely for CUT.

`NarrativeFlow.json` is the source-page-indexed beat/caption table. Level Sequences are under
`/Game/Game/Cinematics/Narrative/Scene01`, `Scene02`, `Scene03`, and `Recordings`.
`PropSlots.json` supplies two props × three proposed snap transforms per scene;
editor-only TargetPoints have matching labels. These markers are layout data, not
runtime slot actors. Build the snap system from this manifest or copy transforms into it.
Prop mesh actors: `PROP_House_Living_Sofa_ThreeSeat_01`, `PROP_Scene01_Wardrobe`,
`NAR_Prop_Scene02_Cabinet`, `NAR_Prop_Scene02_PracticalLamp`,
`NAR_Prop_Scene03_Chair`, `NAR_Prop_Scene03_StandingLamp`.
Movable practical SpotLights are attached to the lamp roots. Photo table is static.

The director owns E only for the final production intercom, with Consume Input disabled.
After Interlude 03 the player must approach the intercom and press E. Arrival conversations
for kitchen and last room wait for proximity before playing. Traversal retains player control;
cinematic/take beats lock input and restore it on handoff.

All monologues share the opening's physical camera, Quinn mesh, seated previs animation,
recording chair and light. The reveal changes focal length 75 → 16 mm from the same camera
transform. Four non-graphic prone mannequin stand-ins remain outside the tight crop.
The black cut between pickup and confession omits the confrontation entirely.

Current animation is mannequin previs: stock walk/idle, authored seated/stand-up poses,
and prone placeholder end poses. Final acting, lip sync, carry/grip animation and VO are
production replacements. Caption times are reading estimates. Film credits contain only
the fictional names provided by the document; real team credits require the team's names.

Editor authoring scripts and test harnesses are in this folder. They do not run in a build.
The verification harness simulates the missing gameplay callbacks; it must never be installed
as startup logic or treated as the actual ACTION/CUT system.

CUT-side spoken reactions remain owned by the gameplay programmer. The source catalog is
Tools/Cinematics/DialogueCatalog.en.json (including P04_07). Early-cut wording from page 13:
"CUT! Hold on, I need to tidy up the scene." This layer does not decide which CUT reaction to use.


Normal-speed playthrough follow-up: RequestBeat now calls ReleaseCinematic before a
traversal arrival gate. The earlier callback test teleported its test pawn to gates and
did not expose the retained input lock. PlayFullFlowDemo.py uses CharacterMovement input
and collision for walking; ACTION/CUT outcomes are still simulated integration callbacks.
The first demonstration found the lock after Interlude 01; after the fix it resumed at
that checkpoint and reached credits through both traversal gates and the intercom.
