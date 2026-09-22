from engine.normalization import normalize_traits
from engine.resolver import resolve_all_characters, resolve_character_by_id
from engine.loader import load_character


def test_normalization_is_lowercase_split_and_alias_expanded():
    assert normalize_traits(" Natural Auburn/Copper ") >= {"natural", "auburn", "copper"}
    assert normalize_traits("soft natural wave") >= {"soft", "natural", "wave", "wavy"}
    assert normalize_traits("green-hazel") >= {"green", "hazel"}


def test_luna_resolves_category_appropriate_entries_deterministically():
    first = resolve_character_by_id("luna_campbell")
    second = resolve_character_by_id("luna")

    assert first.to_dict() == second.to_dict()
    assert any(item.entry.id == "hair_auburn_natural" for item in first.resolved_entries)
    assert any(item.entry.id == "skin_natural_freckles" for item in first.resolved_entries)
    assert any(item.entry.id == "build_soft_athletic" for item in first.resolved_entries)


def test_all_characters_resolve_without_mutating_canonical_models():
    character = load_character("luna")
    before = repr(character.appearance)
    results = resolve_all_characters()

    assert len(results) == 6
    assert repr(character.appearance) == before
    assert all(result.to_dict() == resolve_character_by_id(result.character_id).to_dict() for result in results)
    assert all("identity" not in trait.source_path for result in results for trait in result.unresolved_traits)
