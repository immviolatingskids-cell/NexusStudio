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
provider metadata, and checksums. CharacterStudio v1.1 is prompt-first: locked
identity and scene direction feed a deterministic compiler; optional Gemini
text refinement can improve the prose; TXT or JSON exports preserve both the
compiled and refined prompts with the lock version. The user generates images
manually in ChatGPT or Gemini and reviews identity drift externally. The active
workflow does not call image-generation APIs. The optional text refiner uses
`GEMINI_API_KEY`, the `google-genai` package, and `GEMINI_TEXT_MODEL` (default
`gemini-2.5-flash`). Legacy image-provider code remains experimental and is not
part of the v1.1 prompt workflow. There is no browser UI or application HTTP API.

Manual visual QA stays outside CharacterStudio: export a prompt, generate the
image in ChatGPT or Gemini, inspect it against the canonical reference, then
update the relevant locked identity only when the observation is supported.
Classify observed drift as `GEOMETRY_DRIFT`, `EYE_DRIFT`, `HAIR_DRIFT`,
`COLOR_DRIFT`, `BODY_DRIFT`, `FEATURE_OMISSION`, `EXPRESSION_DRIFT`, or
`STYLE_CONTAMINATION`. Keep `reference_images/` for canonical references; the
future presentation and generated-image library is out of scope for v1.1 and
must not become an identity source.

Run a preview from the repository root:

```powershell
python generate.py luna --activity "getting ready for a concert" --location bar --wardrobe-style streetwear --lighting neon_coloured --seed 7 --record
python generate.py ayami --activity "reading quietly" --location cafe --seed 2 --density detailed --refinement rich --export output/ayami-prompt.txt
python generate.py ayami --activity "reading quietly" --location cafe --seed 2 --density detailed --refinement off --export output/ayami-prompt.json
python generate.py --audit
python generate.py --migrate-character luna
python stress_test_identity.py --output output/identity-prompts.json
python stress_test_identity.py --refinement rich --output output/identity-prompts-refined.json
```

The desktop Studio follows the same prompt-first workflow: select a character,
set scene direction, choose identity density and optional text refinement, then
copy or export the final prompt. It does not generate images. The stress runner
exercises each character's scene cases and exports prompts for manual visual QA.
`--generate` and image-provider code are retained only as experimental legacy
functionality.

Run validation with:

```powershell
python -m pytest -q -p no:cacheprovider --basetemp .test-temp
```
