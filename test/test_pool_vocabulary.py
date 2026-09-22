import pytest

from pool_models import PoolEntry
from pools.registry import get_entry, get_pool, iter_entries, list_pools, validate_vocabulary
from pools.validation import PoolValidationError, validate_pools
from inspect_pools import character_coverage
from tags import is_valid_tag_name, registered_tags


def test_pool_entry_is_immutable_and_validates_its_core_fields():
    entry = PoolEntry("example", "example text", {"hair"}, weight=2)

    assert entry.tags == frozenset({"hair"})
    assert entry.weight == 2.0
    with pytest.raises(ValueError, match="id"):
        PoolEntry("", "text", {"hair"})
    with pytest.raises(ValueError, match="text"):
        PoolEntry("id", "", {"hair"})
    with pytest.raises(ValueError, match="weight"):
        PoolEntry("id", "text", {"hair"}, weight=0)


def test_registered_pools_are_discoverable_and_entries_are_unique():
    pools = list_pools()

    assert set(pools) == {"hair", "skin", "face", "build", "fashion"}
    assert get_pool("hair")
    assert get_entry("hair_auburn_natural").text == "natural auburn hair"
    ids = [entry.id for entry in iter_entries()]
    assert len(ids) == len(set(ids))
    with pytest.raises(KeyError, match="Unknown pool"):
        get_pool("missing")


def test_all_registered_pool_tags_are_controlled_and_well_named():
    assert all(tag in registered_tags() and is_valid_tag_name(tag) for entry in iter_entries() for tag in entry.tags)
    validate_vocabulary()


def test_pool_validation_rejects_duplicate_and_unknown_tags():
    valid = PoolEntry("one", "one", {"hair"})
    duplicate = PoolEntry("one", "two", {"hair"})
    unknown = PoolEntry("unknown", "unknown", {"not_registered"})

    with pytest.raises(PoolValidationError, match="duplicate PoolEntry id"):
        validate_pools({"hair": (valid,), "skin": (duplicate,)}, allowed_tags=registered_tags())
    with pytest.raises(PoolValidationError, match="unknown tag 'not_registered'"):
        validate_pools({"hair": (unknown,)}, allowed_tags=registered_tags())
    with pytest.raises(PoolValidationError, match="must not be empty"):
        validate_pools({"hair": ()}, allowed_tags=registered_tags())


def test_character_coverage_is_read_only_and_reports_unrepresented_traits():
    coverage = character_coverage()

    assert "auburn hair" in coverage["luna_campbell"]["covered"]
    assert "green_hazel eyes" in coverage["luna_campbell"]["missing"]
