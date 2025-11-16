"""Load YAML-based configuration for categories and merchant aliases."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "ConfigLoaderError",
    "EXPECTED_CATEGORIES",
    "get_valid_categories",
    "load_categories",
    "load_merchant_aliases",
]


class ConfigLoaderError(RuntimeError):
    """Raised when configuration files are missing or malformed."""


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CATEGORIES_PATH = CONFIG_DIR / "categories.yaml"
MERCHANT_ALIASES_PATH = CONFIG_DIR / "merchant_aliases.yaml"

EXPECTED_CATEGORIES: tuple[str, ...] = (
    "Casa",
    "Luz",
    "Prepaga",
    "Internet",
    "Alquiler",
    "Seguro",
    "Gasolina",
    "Furgo",
    "Romi",
    "Pitu",
    "Mercado",
    "Farmacia",
    "Comer Afuera",
    "Transporte",
    "Ocio",
    "Viaje",
    "Ingresos",
    "Otros",
    "Ropa",
    "Transferencia",
    "IA",
    "Amazon",
)


def _load_yaml_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise ConfigLoaderError(f"Configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:  # pragma: no cover - exercised via tests
        raise ConfigLoaderError(f"Invalid YAML in {path}") from exc


def _ensure_mapping(data: Any, *, path: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigLoaderError(f"{path} must define a mapping.")
    return data


def _string_list(data: Any, *, context: str, field_name: str) -> list[str]:
    if data in (None, []):
        return []
    if not isinstance(data, list) or any(not isinstance(item, str) for item in data):
        raise ConfigLoaderError(f"{context} -> {field_name} must be a list of strings.")
    return data


def _coerce_path(path: Path | str | None, *, default: Path) -> Path:
    return default if path is None else Path(path)


def load_categories(path: Path | str | None = None) -> dict[str, dict[str, list[str]]]:
    """Load and validate category definitions."""

    file_path = _coerce_path(path, default=CATEGORIES_PATH)
    payload = _ensure_mapping(_load_yaml_file(file_path), path=file_path)

    categories: dict[str, dict[str, list[str]]] = {}
    for name, config in payload.items():
        if not isinstance(config, dict):
            raise ConfigLoaderError(
                f"Category '{name}' must map to a dictionary with a 'keywords' list."
            )
        keywords = _string_list(
            config.get("keywords"), context=f"Category '{name}'", field_name="keywords"
        )
        categories[name] = {"keywords": keywords}

    missing = [cat for cat in EXPECTED_CATEGORIES if cat not in categories]
    if missing:
        raise ConfigLoaderError(
            "Missing categories: " + ", ".join(missing)
        )

    return categories


def load_merchant_aliases(
    path: Path | str | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Load merchant alias normalization rules."""

    file_path = _coerce_path(path, default=MERCHANT_ALIASES_PATH)
    payload = _ensure_mapping(_load_yaml_file(file_path), path=file_path)

    aliases: dict[str, dict[str, list[str]]] = {}
    for canonical_name, config in payload.items():
        if not isinstance(config, dict):
            raise ConfigLoaderError(
                f"Merchant '{canonical_name}' must map to a dictionary with a 'patterns' list."
            )
        patterns = _string_list(
            config.get("patterns"),
            context=f"Merchant '{canonical_name}'",
            field_name="patterns",
        )
        aliases[canonical_name] = {"patterns": patterns}

    return aliases


def get_valid_categories() -> list[str]:
    """Return the list of canonical category names."""

    return list(EXPECTED_CATEGORIES)
