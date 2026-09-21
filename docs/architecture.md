# NexusStudio architecture

NexusStudio keeps character identity separate from the direction of a single
scene. The canonical `characters/*.json` records describe the person, while
`characters/identity/*.json` defines visual identity anchors and constraints.
These records are authoritative; presentation vocabulary must not alter them.

`SceneBrief` is the director-facing contract. It can specify activity,
location, wardrobe, hair styling, pose, atmosphere, lighting, season and
framing. `resolve_scene()` produces stable presentation selections from its
seed, and `compose_prompt()` exposes those choices before any provider is used.

`record_take()` saves an immutable offline-preview record containing the brief,
selections, identity anchors, and both prompt fields. Output is intentionally
ignored by Git. Image-provider adapters and a browser UI will consume this
contract in later milestones; they must not duplicate identity or resolver
logic.

Run a preview from the repository root:

```powershell
python generate.py luna --activity "getting ready for a concert" --location bar --wardrobe-style streetwear --lighting neon_coloured --seed 7 --record
```

Run validation with:

```powershell
python -m pytest -q -p no:cacheprovider --basetemp .test-temp
```
