import json
import sys

import pytest

from config import CHARACTERS_DIR
import generate
from engine import loader
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


@pytest.mark.parametrize("character_id", ("", "   ", None, 42))
def test_blank_or_wrong_type_character_ids_fail_clearly(character_id):
    with pytest.raises(CharacterNotFoundError, match="non-empty string"):
        load_character(character_id)


def test_missing_character_file_names_the_requested_id(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "CHARACTERS_DIR", tmp_path)

    with pytest.raises(CharacterNotFoundError, match="missing"):
        load_character("missing")


def test_malformed_character_json_reports_filename_and_position(tmp_path, monkeypatch):
    (tmp_path / "broken.json").write_text('{"character_id": ', encoding="utf-8")
    monkeypatch.setattr(loader, "CHARACTERS_DIR", tmp_path)

    with pytest.raises(CharacterValidationError, match=r"broken\.json.*line"):
        load_character("broken")


def test_discovery_propagates_malformed_json_instead_of_skipping_it(tmp_path, monkeypatch):
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
    monkeypatch.setattr(loader, "CHARACTERS_DIR", tmp_path)

    with pytest.raises(CharacterValidationError, match=r"broken\.\$: invalid JSON"):
        list_character_ids()


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


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda data: data.update(identity=[]), "identity"),
        (lambda data: data["appearance"].update(body=[]), "appearance.body"),
        (lambda data: data["appearance"]["body"].update(physical_features={}), "appearance.body.physical_features"),
        (lambda data: data["appearance"].update(distinguishing_features={}), "appearance.distinguishing_features"),
        (lambda data: data.update(affinities=[]), "affinities"),
    ],
)
def test_wrong_nested_dictionary_and_list_types_fail_with_paths(mutate, path):
    data = canonical_data()
    mutate(data)

    with pytest.raises(CharacterValidationError, match=path):
        validate_character_data(data, character="luna")


@pytest.mark.parametrize("age", (17, 121, True, "21"))
def test_invalid_age_boundaries_and_types_fail(age):
    data = canonical_data()
    data["identity"]["age"] = age

    with pytest.raises(CharacterValidationError, match="identity.age"):
        validate_character_data(data, character="luna")


def test_optional_descriptive_fields_can_be_absent():
    data = canonical_data()
    data["identity"].pop("nickname", None)
    data["occupation"].pop("route", None)
    data.pop("sociality", None)
    data["occupation"].pop("focus", None)

    validate_character_data(data, character="luna")


def test_load_all_characters_propagates_invalid_record_failure(tmp_path, monkeypatch):
    data = canonical_data()
    data["identity"]["age"] = 17
    (tmp_path / "broken.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(loader, "CHARACTERS_DIR", tmp_path)

    with pytest.raises(CharacterValidationError, match="identity.age"):
        load_all_characters()


def test_cli_no_argument_summary_uses_the_loader(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["generate.py"])

    generate.main()

    output = capsys.readouterr().out
    assert "6 characters loaded" in output
    assert "luna_campbell" in output
    assert "Validation: PASS" in output
