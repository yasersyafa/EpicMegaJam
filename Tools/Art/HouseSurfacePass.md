# SB_GrayBox surface pass

Eight shared master materials and twelve material instances are stored under
`/Game/Game/Art/Environment/House/Materials`.
The original surface pass covered 80 `GB_` static meshes; the subsequent prop replacement is documented in [HouseProps.md](HouseProps.md). Room geometry, mesh transforms,
and collision remain unchanged. The existing light direction was raised and
softened, and `ART_House_SurfaceGrade` adds restrained exposure compensation.

Room finishes: warm oak for the lobby, dining, production hall, dressing and
service areas; dark oak for storage and the hidden room; slate tile for the
garage; charcoal tile for the WC; tan/charcoal checker tile for the kitchen;
taupe carpet for the living room; limestone for the stairs. Furniture uses oak,
fabric, stone and gunmetal.

## Source and generation

The oak image was generated using the built-in ImageGen tool. It was copied to
`SourceArt/Environment/House/Textures/T_House_OakPlanks_BC.png` and imported as
`/Game/Game/Art/Environment/House/Textures/Wood/T_House_OakPlanks_BC`. SourceArt PNGs are ignored
by this repository's existing rules; the imported texture asset is versionable.
Other surface patterns are procedural material graphs, with world-space scale.

Final image-generation prompt:

> Create one production game texture: seamless tileable albedo texture of warm medium dark smoked oak hardwood flooring matching an elegant old house floor plan. Orthographic straight down view, perfectly flat uniform diffuse illumination, no shadows, no ambient occlusion, no perspective, no vignette, no borders, no text, no objects. Narrow long wooden planks with staggered short end joints, plank direction strictly vertical. Rich natural walnut-brown and honey undertones, restrained realistic grain, subtle age and fine scratches, no dramatic knots, satin wood. Entire square filled edge to edge. Planks should be about 1/12 image width and have varying lengths around half image height. Tileable in both directions. Square 1024x1024 texture intended to repeat at 180 cm in Unreal Engine. Save output image.

The delivered image is 1254 square; Unreal resamples it to power-of-two dimensions
for mipmaps. Final world-space repeat is 256 cm to keep boards near realistic width.

## Recovery and verification

The saved pre-edit level is at
`C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-TexturePass/SB_GrayBox.before-textures.umap`.
Close the level before restoring that file to `Content/Game/Levels/SB_GrayBox.umap`.
The backup contains the entire pre-pass level, including its original lighting.

`Saved/HouseSurfaceOrganization.json` records assignments, save status, layout
checks, shader statistics, and redirector cleanup. A copy is included beside this
note. `OrganizeHouseSurfaces.py` performs the asset refactor; the initial creation
scripts are archived with the pre-refactor backup outside the repository.

## Asset conventions

Use `M_House_<Surface>_<Projection>` for master materials,
`MI_House_<Use>_<Surface>_<Variant>` for material instances and
`T_House_<Surface>_<Channel>` for textures. `BC` means base color; normal and
packed masks should use `N` and `ORM` if introduced later. Do not make a new
master for a color, roughness or tile-size variation.

```
Environment/House/
  Materials/Masters/
  Materials/Instances/Floors/
  Materials/Instances/Walls/
  Materials/Instances/Props/
  Textures/Wood/
```

Architecture and furnished props use material instances, never masters. Wood variants share one
master; the three tile variants share one master with uniform color and tile
size parameters. The other six distinct procedural surface models retain their
own masters. This reduces master count from 12 to 8 without adding static-switch
permutations. Actor labels stay stable; Outliner folders group architecture,
props, lighting and blockout references by ownership.

## Texture and performance budget

The oak texture uses a 1024 maximum cooked resolution, default color compression
without alpha (DXT1 on the current Windows target), sRGB, World LOD group,
generated mipmaps, and normal texture streaming. The live `ListTextures` audit
reported 11 mips, 704 KB maximum residency and 48 KB current residency at the
overview camera. Residency changes with camera distance. The original source is
retained for later quality adjustments.

Shader statistics are recorded in the audit JSON. A lower material count is not
a measured FPS improvement; frame time and packaged-build budgets need their own
target-hardware profiling. The existing 4096 reference-floorplan texture is a
separate blockout asset and is outside this surface-pass texture budget.

## Refactor backup

`C:/Users/asus/Documents/ChatGPT/ibra/Backups/EpicMegaJam-MaterialOrganization/`
contains the pre-refactor surface assets and level. Restore both together if
rolling back this organization pass.

