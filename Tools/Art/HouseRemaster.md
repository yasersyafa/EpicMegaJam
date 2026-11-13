# House interior remaster

SB_GrayBox now uses muted sage plaster, aged ivory timber panelling, chair rails,
stepped cornices and door architraves. A shared world-aligned opaque material
adds plaster mottling, patina, hairline marks, timber grain and subtle normal detail.
The procedural surface avoids stretched UVs when walls change height.

Walls are 340 cm tall; door openings retain their original 240 cm clear height.
Every existing floor rectangle has a 340 cm ceiling. The stairwell ceiling is
430 cm; the highest tread is 180 cm. BP_PlayerCharacter has an 88 cm capsule half
height, giving 74 cm headroom above the highest tread. Original XY wall footprints,
existing prop placement and gameplay Blueprints are unchanged by the scripts.

The solid two-slope gable roof has simple collision, eaves, attic closure and
pentagonal gable ends. Ceilings use the engine cube's simple collision. Decorative
wall details have no collision, so their combined mesh hulls cannot block rooms.

## Runtime cost

Fourteen unique new meshes total 25,744 LOD0 triangles. Wall details are combined
per room with two shared material slots; larger meshes have three distance LODs.
Existing optimized furniture is reused. All new surfaces are opaque. Reversed
index buffers are disabled on the new mesh library. The new lighting uses eleven
room lights, with only three shadow-casting main lights; existing practical lights
remain. Chandelier meshes do not cast distracting ceiling shadows.

The aged material reports 342 pixel instructions, three pixel texture samples
and one sampler in the editor's material statistics (including engine paths).
This is an asset budget check, not a measured target-hardware FPS guarantee.

## Authoring

BuildHouseRemaster.py regenerates source OBJ files from the preserved room/wall
snapshot in SourceArt/Environment/House/Remaster/HouseRemasterInput.json.
StageHouseRemaster.py imports missing meshes, assembles the remaster and saves.
Set HOUSE_REMASTER_REIMPORT=1 inside the editor to replace imported mesh sources.
TuneHouseRemasterMood.py applies the final exposure and light balance.
VerifyHouseRemaster.py records collision raycasts, headroom, LOD and material gates.
HouseRemasterAudit.json is the latest saved validation receipt.

Backup before remaster:
C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-Remaster/SB_GrayBox.before-remaster.umap

Keep lighting and grading edits in the named scripts when regenerating this pass.
This pass changes the room shell and atmosphere; it does not add new gameplay.

## Door trim correction

Door intervals are inferred from adjacent solid wall endpoints rather than lintel
widths. Casings sit outside the clear openings; low panelling and rails stop
8.1 cm before each jamb edge, leaving a 1 mm fitting tolerance at the casing.
Cornices union wall and lintel spans to avoid double coplanar strips.
HouseTrimFitAudit.json verifies all 12 openings and 24 generated casing faces.
FixHouseTrim.py reimports only the eleven room-detail meshes, retaining actor
placements, lighting and material settings.
