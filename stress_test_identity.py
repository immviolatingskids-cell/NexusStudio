"""Export the v1.1 identity stress prompts, optionally refining them with text-only Gemini."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

from engine.composer import compose_prompt_document
from engine.loader import list_character_ids
from engine.scene_models import SceneBrief
from engine.resolver import resolve_scene
from engine.identity import load_identity_profile
from engine.providers import GeminiProvider, ProviderError
from engine.prompt_models import PromptResult, PromptSection
from engine.prompt_refiner import REFINEMENT_MODES, refine_prompt


@dataclass(frozen=True)
class StressCase:
    label: str
    location: str
    wardrobe_style: str
    framing: str
    lighting: str
    pose: str
    activity: str
    hair_style: str
    expression: str


CASES: dict[str, tuple[StressCase, StressCase, StressCase]] = {
    "ayami_tanaka": (
        StressCase("portrait", "cafe", "smart casual", "medium", "window light", "sitting", "taking a quiet break", "long hair worn loose", "small smile"),
        StressCase("lifestyle", "city street", "modern streetwear", "medium", "golden hour", "walking", "walking through the city", "hair loosely tied back", "focused"),
        StressCase("environmental", "library", "formal evening", "full body", "overcast daylight", "standing", "pausing by the bookshelves", "low ponytail", "calm"),
    ),
    "luna_campbell": (
        StressCase("athletic", "workshop", "athleisure", "medium", "daylight", "standing", "finishing a gym workout", "copper hair in a ponytail", "energized"),
        StressCase("casual", "city street", "casual", "medium", "overcast daylight", "walking", "meeting a friend", "hair worn loose", "small smile"),
        StressCase("night_out", "bar", "formal evening", "full body", "neon coloured", "standing", "enjoying a night out", "hair half-up", "amused"),
    ),
    "naomi": (
        StressCase("athletic", "beach", "athleisure", "medium", "daylight", "standing", "finishing a swim", "hair tied back", "focused"),
        StressCase("casual", "park", "casual clothing", "medium", "overcast daylight", "walking", "walking outdoors", "hair worn loose", "calm"),
        StressCase("environmental", "mountains", "seasonal", "full body", "golden hour", "standing", "taking in the mountain view", "hair loosely braided", "small smile"),
    ),
    "zara": (
        StressCase("work", "library", "professional", "medium", "window light", "standing", "helping a reader find a book", "dark bob tucked behind one ear", "thoughtful"),
        StressCase("casual", "living room", "loungewear", "medium", "indoor ambient", "sitting", "reading at home without glasses", "dark bob worn loose", "relaxed"),
        StressCase("dressed_up", "restaurant", "formal evening", "full body", "candlelight", "standing", "meeting friends for dinner", "dark bob with a side part", "small smile"),
    ),
    "idun_braten": (
        StressCase("work", "kitchen", "practical workwear", "medium", "indoor ambient", "standing", "preparing a meal at work", "hair tied back", "focused"),
        StressCase("outdoors", "forest", "seasonal", "full body", "overcast daylight", "walking", "walking on a forest trail", "hair worn loose", "calm"),
        StressCase("evening", "restaurant", "formal evening", "medium", "warm", "standing", "having dinner with friends", "hair softly waved", "small smile"),
    ),
    "charlotte_taylor_rose": (
        StressCase("creator", "creative studio", "casual", "medium", "indoor ambient", "sitting", "streaming to her audience", "hair tied up casually", "amused"),
        StressCase("lifestyle", "beach", "seasonal", "medium", "golden hour", "walking", "enjoying a relaxed Queensland afternoon", "hair worn loose", "small smile"),
        StressCase("editorial", "city street", "smart casual outfit", "full body", "mixed lighting", "standing", "heading out for an event", "hair swept to one side", "confident"),
    ),
}


def load_local_env(path: Path | None = None) -> None:
    """Load the project-local Gemini key without displaying or persisting it."""
    env_path = path or Path(__file__).resolve().parent / ".env"
    if not env_path.is_file() or os.getenv("GEMINI_API_KEY"):
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if candidate.startswith("export "):
            candidate = candidate.removeprefix("export ").lstrip()
        name, separator, value = candidate.partition("=")
        if separator and name.strip() == "GEMINI_API_KEY":
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if value:
                os.environ["GEMINI_API_KEY"] = value
                return


def _prompt(character_id: str, case: StressCase):
    brief = SceneBrief(
        character_id=character_id,
        activity=case.activity,
        location=case.location,
        wardrobe_style=case.wardrobe_style,
        framing=case.framing,
        lighting=case.lighting,
        pose=case.pose,
        hair_style=case.hair_style,
        expression=case.expression,
        seed=17,
    )
    return resolve_scene(brief, load_identity_profile(character_id))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character", choices=("all", *list_character_ids()), default="all")
    parser.add_argument("--refine", action="store_true", help="Compatibility alias for rich text-only refinement.")
    parser.add_argument("--refinement", choices=REFINEMENT_MODES, default="off", help="Select off, balanced, or rich text refinement.")
    parser.add_argument("--output", type=Path, default=Path("output/identity-prompts.json"), help="JSON prompt export path.")
    parser.add_argument("--model", help="Override the text model (default: GEMINI_TEXT_MODEL or gemini-2.5-flash).")
    args = parser.parse_args()
    refinement_mode = args.refinement if args.refinement != "off" else ("rich" if args.refine else "off")
    if refinement_mode != "off":
        load_local_env()
        try:
            provider = GeminiProvider(args.model)
            provider.validate()
        except ProviderError as exc:
            parser.error(str(exc))

    selected = list_character_ids() if args.character == "all" else (args.character,)
    total = 0
    exported = []
    for character_id in selected:
        for case in CASES[character_id]:
            scene = _prompt(character_id, case)
            document = compose_prompt_document(scene, "detailed")
            prompt_plan = {
                "mode": case.label,
                "image_intent": "photorealistic image prompt",
                "style": scene.brief.image_style,
                "scene_style": case.label,
                "wardrobe": scene.selections.get("wardrobe"),
                "activity": scene.selections.get("activity"),
                "pose": scene.selections.get("pose"),
                "environment": scene.selections.get("location"),
                "composition": scene.selections.get("framing"),
                "lighting": scene.selections.get("lighting"),
                "atmosphere": scene.selections.get("atmosphere"),
                "identity_constraints": list(document.identity),
            }
            prompt_result = PromptResult(
                character_id=character_id,
                adapter_name="deterministic-compiler",
                positive_prompt=document.render(),
                source_scene_mode=case.label,
                sections=tuple(PromptSection(str(i), text) for i, text in enumerate((*document.identity, *document.direction, *document.technical))),
                negative_prompt="; ".join(document.negative),
                source_metadata={"density": "detailed", "prompt_plan": prompt_plan, "identity_diagnostics": document.identity_diagnostics},
            )
            refined = refine_prompt(prompt_result, refinement_mode, provider if refinement_mode != "off" else None, profile=load_identity_profile(character_id))
            exported.append({"character_id": character_id, "case": case.label, **refined.to_dict(), "identity_diagnostics": document.identity_diagnostics})
            total += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(exported, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported {total} identity prompts to {args.output} ({'refined with ' + provider.model if refinement_mode != 'off' else 'engine-compiled'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
