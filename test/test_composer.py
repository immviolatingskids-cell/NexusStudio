from pathlib import Path

import pytest

from engine.character_composer import compose_all_characters, compose_character, compose_character_by_id, compose_from_resolution
from engine.loader import load_character
from engine.resolver import resolve_character_by_id
from engine.resolver_models import ResolutionResult, UnresolvedTrait


FIXTURES = Path(__file__).parent / "fixtures" / "descriptions"


def test_section_order_is_explicit_and_stable():
    description = compose_character_by_id("luna")

    assert [section.id for section in description.sections] == ["identity", "build", "skin", "face", "eyes", "hair"]
    assert description.text.startswith("Luna Campbell is")


@pytest.mark.parametrize("character_id", ("luna_campbell", "idun_braten", "charlotte_taylor_rose"))
def test_representative_descriptions_match_intentional_golden_fixtures(character_id):
    expected = (FIXTURES / f"{character_id}.txt").read_text(encoding="utf-8").strip()

    assert compose_character_by_id(character_id).text == expected


def test_all_characters_compose_deterministically_without_mutating_inputs():
    character = load_character("luna")
    resolution = resolve_character_by_id("luna")
    before_character = repr(character)
    before_resolution = resolution.to_dict()
    descriptions = compose_all_characters()

    assert len(descriptions) == 6
    assert all(description.text == compose_character_by_id(description.character_id).text for description in descriptions)
    assert all(description.text for description in descriptions)
    assert repr(character) == before_character
    assert resolution.to_dict() == before_resolution
    assert compose_from_resolution(resolution).text == compose_character(character).text


def test_safe_unresolved_visual_scalar_uses_canonical_fallback():
    result = ResolutionResult(
        "luna_campbell", (),
        (UnresolvedTrait("appearance.eyes.color", "green-hazel", "no matching vocabulary entry"),),
    )

    description = compose_from_resolution(result)

    assert "green-hazel" in description.text
    assert description.canonical_fallback_paths == ("appearance.eyes.color",)


def test_resolved_paths_do_not_also_render_canonical_fallbacks():
    description = compose_character_by_id("luna")

    assert "appearance.hair.color" not in description.canonical_fallback_paths
    assert "appearance.eyes.color" not in description.canonical_fallback_paths
