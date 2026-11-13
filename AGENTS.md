# Repository Guidelines

## Project Structure & Module Organization
This is a Blueprint-first Unreal Engine 5 Windows project for **CUT! CUT! CUT!**, a first-person narrative puzzle/horror game.
- `EpicMegaJam.uproject`: project descriptor and editor plugin configuration.
- `Content/Game/Blueprints/Player/`: player character, controller, and graybox game mode.
- `Content/Game/Levels/SB_GrayBox.umap`: current graybox level.
- `Content/Game/References/`: floor-plan image and related assets.
- `Config/Default*.ini`: shared engine, input, editor, and game settings.
- `Docs/PRD_CUT_CUT_CUT_v0.2.md`: gameplay requirements and MVP scope.

There is currently no `Source/` directory, native code module, or dedicated test suite. Keep gameplay assets under `Content/Game/`, grouped by responsibility.

## Build, Test, and Development Commands
Run these PowerShell commands from the repository root:
- `Start-Process .\EpicMegaJam.uproject`: open the project using its registered Unreal installation.
- `& "$env:UE_ROOT\Engine\Binaries\Win64\UnrealEditor.exe" "$PWD\EpicMegaJam.uproject" /Game/Game/Levels/SB_GrayBox`: open the graybox map explicitly; set `UE_ROOT` to your compatible engine installation first.

The engine association is a local installation GUID, so confirm the team's engine version before upgrading or reassociating the project. Use Play In Editor for development and **Platforms > Windows > Package Project** for a Windows build. No repository build scripts are provided. The configured default map is currently the engine OpenWorld template; explicitly select the intended gameplay map when validating or packaging.

## Coding Style & Naming Conventions
Follow existing asset names: `BP_` for Blueprint classes and descriptive PascalCase names such as `BP_PlayerCharacter`. Keep Blueprint graphs readable, group related logic into functions, and comment non-obvious state transitions. Compile and save edited Blueprints. Preserve surrounding formatting in configuration files; no formatter or linter is configured. Rename or move assets through Unreal Editor and fix redirectors to preserve references.

## Testing Guidelines
No automated framework or coverage threshold is configured. Validate changed Blueprints and maps in Play In Editor; check spawning, movement, camera control, and affected interactions. Test ACTION/CUT/RETAKE transitions when implemented. Inspect Output Log for errors and warnings, and record the map, steps, and results in the PR.

## Commit & Pull Request Guidelines
History uses concise Conventional Commit-style subjects, including `feat(level): implement floor plan` and `feat: add graybox player framework`. Follow that pattern with an appropriate type and optional scope. PRs should describe behavior changes, reference relevant requirements or issues, and include validation results plus screenshots or video for visible changes. Coordinate edits to binary `.uasset` and `.umap` files. Keep generated `Saved/`, `Intermediate/`, `Binaries/`, and `DerivedDataCache/` files out of commits.
