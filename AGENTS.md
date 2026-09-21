# Repository Guidelines

## Project Structure & Module Organization

NexusStudio is a Python prompt-direction pipeline. Canonical character records
live in `characters/*.json`; immutable visual anchors and exclusions live in
`characters/identity/*.json`. Keep identity facts in those records, not in
scene vocabulary. The `engine/` package loads data, resolves seeded scenes,
composes prompts, scores entries, and records takes. Reusable vocabulary is
grouped by domain under `pools/`; style presets are in `styles/`. Tests are in
`test/`, architecture notes in `docs/`, and generated preview records belong
in ignored `output/`.

## Build, Test, and Development Commands

Run commands from the repository root.

```powershell
python -m pytest -q -p no:cacheprovider --basetemp .test-temp
python generate.py luna --activity "getting ready for a concert" --location bar --wardrobe-style streetwear --lighting neon_coloured --seed 7 --record
```

The first command runs the pytest suite without the shared cache and uses a
workspace-local temporary directory. The second resolves a deterministic scene
and writes an offline-preview take to `output/`.

## Coding Style & Naming Conventions

Use Python with four-space indentation, `snake_case` for functions, modules,
and JSON fields, and `PascalCase` for classes such as `SceneBrief`. Prefer
small, typed domain models and explicit data flow over hidden mutation.
Preserve the distinction between canonical identity and presentation choices:
resolver or pool changes must never override identity anchors or negative
constraints. Keep pool categories and IDs consistent with `pools/registry.py`.

## Testing Guidelines

Add pytest tests in `test/test_<area>.py` and name them `test_<behavior>`.
Cover both successful data loading and boundary behavior. Resolver tests should
assert deterministic output with a fixed seed and verify identity safety, rather
than merely checking that a prompt is non-empty. Run the full command above
before submitting changes.

## Commits & Pull Requests

Use short imperative subjects, for example
`Preserve identity constraints during resolution`. Keep commits focused. Pull
requests should state the affected layer, explain any data-contract impact,
list tests run, and include a sample generated take when prompt output changes.
