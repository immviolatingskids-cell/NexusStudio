import json

import pytest

from config import CHARACTERS_DIR
from engine.loader import CharacterNotFoundError, list_character_ids, load_all_characters, load_character
from engine.rules import CharacterValidationError, validate_character_data


CANONICAL_IDS = {
    "ayami_tanaka",
    "charlotte_taylor_rose",
    "idun_braten",
    "luna_campbell",
    "naomi",
    "zara",
}


def canonical_data() -> dict:
    return json.loads((CHARACTERS_DIR / "luna.json").read_text(encoding="utf-8"))


def test_discovery_returns_all_and_only_canonical_character_ids(tmp_path, monkeypatch):
    (tmp_path / "notes.txt").write_text("not a character", encoding="utf-8")
    monkeypatch.setattr("engine.loader.CHARACTERS_DIR", tmp_path)
    for character_id in ("one", "two"):
        data = canonical_data()
        data["character_id"] = character_id
        (tmp_path / f"{character_id}.json").write_text(json.dumps(data), encoding="utf-8")

    assert list_character_ids() == ["one", "two"]


def test_all_canonical_characters_use_the_same_loader_pipeline():
    characters = load_all_characters()

    assert {character.character_id for character in characters} == CANONICAL_IDS
    assert all(character.identity.name for character in characters)


def test_load_by_canonical_id_and_filename_alias():
    assert load_character("luna_campbell").character_id == "luna_campbell"
    assert load_character("luna").character_id == "luna_campbell"


def test_unknown_character_has_a_useful_error():
    with pytest.raises(CharacterNotFoundError, match="does-not-exist"):
        load_character("does-not-exist")


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda data: data.pop("character_id"), "character_id"),
        (lambda data: data.pop("identity"), "identity"),
        (lambda data: data["identity"].update(age=17), "identity.age"),
        (lambda data: data["hobbies"].append({"not": "a string"}), "hobbies"),
        (lambda data: data["appearance"].update(eyes=[]), "appearance.eyes"),
    ],
)
def test_invalid_required_values_report_a_field_path(mutate, path):
    data = canonical_data()
    mutate(data)

    with pytest.raises(CharacterValidationError, match=path):
        validate_character_data(data, character="luna")


def test_optional_descriptive_fields_can_be_absent():
    data = canonical_data()
    data["identity"].pop("nickname", None)
    data["occupation"].pop("route", None)

    validate_character_data(data, character="luna")
