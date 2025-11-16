from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from gastitis import config_loader


def test_load_categories_contains_expected_categories() -> None:
    categories = config_loader.load_categories()

    assert set(categories) == set(config_loader.EXPECTED_CATEGORIES)
    for definition in categories.values():
        assert isinstance(definition["keywords"], list)
        assert all(isinstance(keyword, str) for keyword in definition["keywords"])


def test_load_categories_missing_expected_category_raises(tmp_path: Path) -> None:
    data = {cat: {"keywords": []} for cat in config_loader.EXPECTED_CATEGORIES}
    missing_category = config_loader.EXPECTED_CATEGORIES[0]
    data.pop(missing_category)

    file_path = tmp_path / "categories.yaml"
    file_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(config_loader.ConfigLoaderError) as excinfo:
        config_loader.load_categories(file_path)

    assert missing_category in str(excinfo.value)


def test_load_merchant_aliases_returns_pattern_lists() -> None:
    aliases = config_loader.load_merchant_aliases()

    assert aliases
    for merchant, definition in aliases.items():
        assert "patterns" in definition, merchant
        assert isinstance(definition["patterns"], list)
        assert all(isinstance(pattern, str) for pattern in definition["patterns"])


def test_load_merchant_aliases_invalid_structure(tmp_path: Path) -> None:
    file_path = tmp_path / "merchant_aliases.yaml"
    file_path.write_text("""LIDL: []""", encoding="utf-8")

    with pytest.raises(config_loader.ConfigLoaderError):
        config_loader.load_merchant_aliases(file_path)
