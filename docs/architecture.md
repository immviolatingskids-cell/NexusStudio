# NexusStudio architecture

NexusStudio keeps character identity separate from the direction of a single
scene. The canonical `characters/*.json` records describe the person, while
`characters/identity/*.json` defines visual identity anchors and constraints.
These records are authoritative; presentation vocabulary must not alter them.

`SceneBrief` is the director-facing, versioned contract. It can specify
activity, location, wardrobe, hair styling, pose, atmosphere, lighting, season
and framing. `resolve_scene()` records stable pool IDs and labels; rerolls only
change unlocked dimensions. Prompt output is a separately versioned
`PromptDocument` with identity, direction, technical guidance, and negatives.

`record_take()` writes immutable records plus an ignored take manifest. Every
record captures source fingerprints, resolved IDs, contract versions, prompts,
provider metadata, and checksums. The `fake` provider is deterministic and
default; Gemini is an opt-in CLI adapter that requires `GEMINI_API_KEY` and the
optional `google-genai` package. There is deliberately no browser UI or
application HTTP API.

Run a preview from the repository root:

```powershell
python generate.py luna --activity "getting ready for a concert" --location bar --wardrobe-style streetwear --lighting neon_coloured --seed 7 --record
python generate.py --audit
python generate.py luna --activity "concert preparation" --generate --provider fake --seed 7
python generate.py --migrate-character luna
```

For a friendlier directing flow, run `python studio.py`. It guides character
selection and scene direction, then lets you lock details, reroll only what is
unlocked, save a preview, or run the deterministic fake provider. It is a thin
CLI layer over the same `SceneBrief` and resolver contracts; `generate.py`
remains the explicit automation interface.

Run validation with:

```powershell
python -m pytest -q -p no:cacheprovider --basetemp .test-temp
```
