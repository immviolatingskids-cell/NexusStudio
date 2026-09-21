"""Framework-neutral application service for the NexusStudio desktop client."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from config import OUTPUT_DIR, reference_image_for
from engine.composer import compose_negative_prompt, compose_prompt
from engine.identity import IdentityProfile, load_identity_profile
from engine.loader import list_character_ids, load_character
from engine.prompts import PromptDocument, compose_prompt_document
from engine.providers import GenerationProvider, get_provider
from engine.resolver import reroll_scene, resolve_scene
from engine.scene_models import ResolvedScene, SceneBrief
from engine.takes import list_takes, load_take, new_take_id, record_take, verify_take
from pools.registry import entries_for


class DesktopStudioController:
    """The single desktop-facing route into the existing authoritative engine."""

    def __init__(self, *, output_dir: Path | None = None) -> None:
        self.character = None
        self.profile: IdentityProfile | None = None
        self.scene: ResolvedScene | None = None
        self.parent_take_id: str | None = None
        self.output_dir = output_dir or OUTPUT_DIR

    def list_characters(self) -> list[object]:
        return [load_character(character_id) for character_id in list_character_ids()]

    def choose_character(self, character_key: str) -> object:
        self.character = load_character(character_key)
        self.profile = load_identity_profile(self.character.character_id)
        self.scene = None
        self.parent_take_id = None
        return self.character

    def reference_image(self) -> Path | None:
        return reference_image_for(self._character().character_id)

    def choices(self, dimension: str) -> tuple[object, ...]:
        categories = {
            "location": "location", "atmosphere": "atmosphere", "wardrobe": "style",
            "pose": "base_pose", "lighting": "lighting_setup", "framing": "framing",
        }
        if dimension not in categories:
            raise ValueError(f"Unsupported curated dimension '{dimension}'.")
        return entries_for(categories[dimension])

    def build_scene(self, direction_text: str | None = None, **direction: object) -> ResolvedScene:
        character = self._character()
        brief = SceneBrief(character_id=character.character_id, activity=direction_text or None, **direction)
        self.scene = resolve_scene(brief, self._profile(), character.affinities)
        return self.scene

    def update_direction(self, direction_text: str | None = None, **direction: object) -> ResolvedScene:
        current = self._scene()
        allowed = set(SceneBrief.__dataclass_fields__) - {"character_id", "locks", "locked_selections", "schema_version"}
        invalid = set(direction) - allowed
        if invalid:
            raise ValueError(f"Unsupported scene direction: {', '.join(sorted(invalid))}.")
        values = {key: value for key, value in direction.items() if value is not None}
        if direction_text is not None:
            values["activity"] = direction_text or None
        brief = replace(current.brief, **values, locked_selections={})
        self.scene = resolve_scene(brief, self._profile(), self._character().affinities)
        return self.scene

    def lock(self, dimension: str, locked: bool = True) -> ResolvedScene:
        scene = self._scene()
        if dimension not in scene.selection_ids:
            raise ValueError(f"'{dimension}' is not a lockable resolved dimension.")
        locks = set(scene.brief.locks)
        locks.discard(dimension) if not locked else locks.add(dimension)
        locked_selections = {key: scene.selection_ids[key] for key in locks}
        self.scene = resolve_scene(replace(scene.brief, locks=frozenset(locks), locked_selections=locked_selections), self._profile(), self._character().affinities)
        return self.scene

    def reroll(self, dimension: str | None = None) -> ResolvedScene:
        self.scene = reroll_scene(self._scene(), self._profile(), self._character().affinities, dimension=dimension)
        return self.scene

    def preview(self) -> tuple[ResolvedScene, PromptDocument]:
        scene = self._scene()
        return scene, compose_prompt_document(scene)

    def save(self) -> Path:
        return record_take(self._scene(), parent_take_id=self.parent_take_id)

    def generate(self, provider_name: str = "fake", *, scene: ResolvedScene | None = None, parent_take_id: str | None = None) -> Path:
        """Generate from a captured scene, safe for a background UI worker."""
        scene = scene or self._scene()
        provider: GenerationProvider = get_provider(provider_name)
        provider.validate()
        reference = reference_image_for(scene.brief.character_id)
        result = provider.generate(compose_prompt_document(scene), (reference,) if reference and reference.is_file() else ())
        take_id = new_take_id()
        suffix = ".png" if result.mime_type == "image/png" else ".txt"
        output_path = self.output_dir / "images" / f"{take_id}{suffix}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(result.image_bytes)
        return record_take(scene, provider=result.provider, model=result.model, parent_take_id=parent_take_id if parent_take_id is not None else self.parent_take_id, output_path=output_path, provider_metadata=result.metadata, take_id=take_id)

    def inspect_takes(self) -> list[dict]:
        return list_takes()

    def inspect_take(self, take_id: str) -> dict:
        return load_take(take_id)

    def verify_take(self, take_id: str) -> bool:
        return verify_take(take_id)

    def replay_take(self, take_id: str) -> ResolvedScene:
        stored = load_take(take_id)
        brief_data = dict(stored["scene"]["brief"])
        brief_data["locks"] = frozenset(brief_data.get("locks", ()))
        self.choose_character(brief_data["character_id"])
        self.parent_take_id = take_id
        self.scene = resolve_scene(SceneBrief(**brief_data), self._profile(), self._character().affinities)
        return self.scene

    def prompt_preview(self) -> tuple[str, str]:
        scene = self._scene()
        return compose_prompt(scene), compose_negative_prompt(scene)

    def _character(self):
        if self.character is None:
            raise RuntimeError("Choose a character before directing a scene.")
        return self.character

    def _profile(self) -> IdentityProfile:
        if self.profile is None:
            raise RuntimeError("Choose a character before resolving a scene.")
        return self.profile

    def _scene(self) -> ResolvedScene:
        if self.scene is None:
            raise RuntimeError("Build a scene before previewing, saving, or generating.")
        return self.scene
