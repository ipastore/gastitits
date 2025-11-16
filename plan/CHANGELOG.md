# CHANGELOG

## 2025-11-16 – Step 1: Configuration Loader and YAML Setup

- **What**: Aligned `config/categories.yaml` and `config/merchant_aliases.yaml` with the canonical taxonomy, created `src/gastitis/config_loader.py` (with `load_categories`, `load_merchant_aliases`, `get_valid_categories`, `ConfigLoaderError`), and added pytest coverage in `tests/test_config_loader.py`.
- **Why**: Establishes a single, validated source for categorization/merchant rules so downstream parsers and pipelines can depend on consistent config and fail fast when the YAML structure drifts.
- **Verification**: `uv run pytest` (all tests pass).
- **Notes**: Loader enforces the exact category list from the plan; adjusting categories now requires updating both the YAML file and `EXPECTED_CATEGORIES` + associated tests.
