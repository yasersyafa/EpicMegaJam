# Sections 05–14 cinematic and level delivery

Runtime entry: existing opening → seated arrival conversation → BP_NarrativeDirector.
Read GameplayHandoff.md for the three events that the ACTION/CUT programmer must call.
No F binding, scoring, snap solver or automatic perfect-result decision is installed.

24 Level Sequences cover three perfect performances, six failure performances, aftermath,
crew transitions, three interludes, final pickup, confession, evidence montage, same-camera
wide reveal and film credits. NarrativeFlow.json holds the English performance script and its timing against the staged action.
BuildNarrativeData.py applies it to the director and clears captions for listening beats and room tone. Runtime is Blueprint/Sequencer only; the Python files are editor authoring/tests.

Authored scene equipment uses existing low-poly shared meshes/materials. Each scene has
its two puzzle props and six slot markers. Reference texture is an in-engine render of the
canonical chair/lamp arrangement, 512 square with mipmaps/compression. Its original source
is in SourceArt/Narrative. Hidden-room dressing is reduced for the puzzle/reveal, with the
original desk/chairs/cabinet retained hidden rather than deleted.

Authoring order (only when intentionally rebuilding this delivery):
BuildNarrativeData.py → BuildMayaRecordingPoses.py → StageNarrativeCinematics.py →
StageNarrativeDetails.py → StageNarrativeAudio.py → FinalizeNarrativeStaging.py.
Blueprint graph assets are already authored; these scripts stage their data/scene bindings.
Do not rerun these scripts casually over artist edits. Back up the map first and rebind
Arrival on FLOW_Narrative_Sections05_14 after rebuilding arrival actors.

Tests: VerifyNarrativeFlow.py expects the existing seated-arrival validation driver to run
first (Tools/Cinematics/VerifySeatedConversation.py), then simulates gameplay callbacks.
Use saved validation JSON and preview images for reviewer evidence. The harness deliberately
accelerates game time and moves the test player to traversal gates; normal gameplay never
teleports the player through traversal. AuditNarrativeRoutes.py checks 50 cm-radius capsules
against static geometry in canonical prop placement. AuditNPCSpacing.py samples the scripted
moving-character timelines for 85 cm center spacing. Wrong prop layouts remain the gameplay
owner's responsibility when selecting a failure variant.

Production limits: mannequins, stock locomotion and authored seated/stand-up blocking poses;
final facial acting, voiced lines, carry/hand animation and real team-credit names are pending.
The film-credit names supplied by the narrative are implemented. Timings are estimates,
not a verified 12–15 minute first-play experience.
