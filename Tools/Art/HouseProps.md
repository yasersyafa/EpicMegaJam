# House prop library and scene dressing

SB_GrayBox now contains 74 placed props backed by 26 reusable static meshes.
The 21 furniture blockout meshes and one unused underground cube were removed.
Floors, walls, lintels and stairs retain their meshes and transforms. Room labels
and the reference plan are editor-only. Props are static scenery; interaction
logic is not attached to the furniture.

## Content ownership

```
/Game/Game/Art/Environment/House/
  Meshes/Props/SM_House_<Type>_<Variant>
  Materials/Masters/M_House_PropSurface
  Materials/Instances/Props/MI_House_Prop_<Surface>
```

Outliner actors use `PROP_House_<Room>_<Type>_<Number>` under
`Environment/House/Props/<Room>`. Six warm practical lights use `LIGHT_House_`
labels under `Environment/House/Lighting/Practicals`.

## Mesh catalog

Three-seat sofa, two-seat sofa, armchair, coffee table, side table, dressed
meeting table, dining chair, office desk, console, yellow flight case, black
flight case, loaded equipment rack, kitchen cabinet, kitchen sink, cooker,
refrigerator, toilet, basin, illuminated vanity, clothes rail, potted plant,
floor lamp, desk lamp, bordered rug, wall mirror and tall cabinet.

Props include bevels, cushions, legs, cabinet fronts, handles, case latches,
casters, rack shelves, hangers, foliage, faucets, burners, vanity bulbs,
documents, ink marks and cups. Geometry is authored procedurally rather than
downloaded from a third-party asset pack.

## Build and import

`BuildHouseProps.py` uses standard Python only. Run it from a checkout to write
centimeter-scale OBJ/MTL source meshes under
`SourceArt/Environment/House/Props`. Pivots sit on the ground. Its right-handed
OBJ export compensates for the Unreal importer Y reflection, keeping the
runtime furniture front along local -Y. `HOUSE_PROP_PROJECT` can override the
project root when running the generator outside Tools/Art.

Run `StageHouseProps.py` inside Unreal Editor Python with SB_GrayBox open to
import and furnish the level. It reuses existing imported meshes. To reimport
changed geometry, set `HOUSE_PROPS_REIMPORT` to a comma-separated list of exact
mesh asset names before executing it. Re-staging replaces generated `PROP_House_`
and `LIGHT_House_` actors, so it resets their hand-edited transforms. The source
placement list is the canonical generated layout.

The OBJ importer does not create separate material assets. Slots bind to the
existing shared material instances and a single parameterized prop-surface
master. Repeated chairs, cases, plants and modules share static mesh resources.
Source OBJ files may be ignored by the repository's compiled-object rules;
the tracked generator reproduces them, and the imported uassets are versionable.

## Geometry and runtime budget

The whole unique library contains approximately 55,000 source triangles.
Meshes over 800 triangles have three LODs at 100%, 55% and 25% triangle targets.
Small meshes retain a single LOD. Bulk furniture uses one 26-DOP convex collision
hull per mesh; rugs, lamps and mirrors do not block movement. This conservative
collision does not model crawling under tables or using sofa seats.

Materials reuse existing oak, fabric, stone and metal families. Other colors
share M_House_PropSurface with uniform parameters, without new textures or
static-switch permutations. Six local practical lights have 260 cm attenuation
and shadows disabled. This pass does not claim a measured frame-rate gain.

## Verification and recovery

`HousePropsAudit.json` records imports, source triangle counts, LODs, collision,
placed props, material assignment and geometric door clearances. All twelve
doorway centers retain at least 90 cm clearance from blocking prop bounds.
This is an editor geometry check, not a player traversal playtest.

`HouseArchitectureBaseline.json` records the 59 original floor, wall, lintel and
stair mesh transforms, checked by `VerifyHouseProps.py`. The pre-prop level is
backed up at
`C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-Props/SB_GrayBox.before-props.umap`.
Restore it with the level closed to recover the original furniture layout.

Overview and living-room detail screenshots are stored with that backup.

## PC asset gate

26 shared meshes serve 74 static props. Imported LOD0 library: 54,860 triangles;
all placed props total 141,532 at LOD0 or 41,476 at the lowest available LOD
before culling (70.7% reduction). Each prop stays below 6,000 triangles and
five material slots. All prop materials are opaque. Reversed index buffers
are disabled because all placed scales are positive; tiny decoration sections
do not cast shadows. Cylinder cap UVs and seam vertices are authored explicitly;
zero-area source triangles are discarded before export.

AuditGameReadyProps.py records the asset gate and reapplies import optimizations.
Generated LODs have no authored MeshDescription: Unreal GetNumUVChannels returns
zero for those source descriptions, so authored UV validation targets LOD0.
Standalone PIE started successfully and stopped cleanly. This is not a packaged
build, traversal test or target-hardware frame-rate benchmark.
