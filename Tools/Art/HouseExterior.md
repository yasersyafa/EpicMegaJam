# Compact house exterior

The entrance has a small covered porch, 240 cm pedestrian approach, sidewalk,
access road and five garden beds with 31 shared opaque shrubs. Four low-poly
lamp posts and two porch lanterns use shared materials. Only the broad cool
facade fill casts shadows; the local garden lights do not.

Three new reusable meshes total 1,532 triangles. Ground, hardscape, porch and
boundary collision reuse the engine cube. Naming uses EXT_House_ for visible
exterior actors and COL_House_Exterior_ for invisible perimeter collision.

Four hidden BlockAll boxes overlap at corners and enclose the ground footprint,
including both road ends. They extend from -50 to 1150 cm, above the roof and
normal character jumping reach. They render neither geometry nor shadows.
Garden decorative borders and shrubs do not block the pedestrian approach.

HouseExteriorAudit.json and HouseExteriorPIEAudit.json record 84 capsule sweeps
at three heights around the boundary, and a clear sweep from entrance to
sidewalk. The PIE gate runs the tests against duplicated runtime actors.
These are collision sweeps, not a full keyboard traversal or FPS benchmark.

BuildHouseExterior.py regenerates the three prop sources. StageHouseExterior.py
assembles the exterior and saves; it touches only its EXT/COL actor prefixes.
VerifyHouseExterior.py runs the collision gate. Set HOUSE_EXTERIOR_TEST_PIE=1
inside an active PIE session to target the game world.

Pre-exterior level backup:
C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-Exterior/SB_GrayBox.before-exterior.umap
