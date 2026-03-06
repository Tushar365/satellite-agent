"""Tests for src.config — settings loading, validation, knowledge base."""

import os

import pytest


@pytest.fixture(autouse=True)
def _env_defaults(monkeypatch):
    """Ensure required env vars are set for every test in this module."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-1234")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-1234")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    # Clear the lru_cache so each test gets fresh settings
    from src.config import get_settings
    get_settings.cache_clear()


def test_settings_load():
    """Settings() loads from env vars without error."""
    from src.config import Settings

    s = Settings()
    assert s.anthropic_api_key == "sk-test-key-1234"
    assert s.database_url == "postgresql+asyncpg://u:p@localhost/testdb"
    assert isinstance(s.cloud_cover_default_max, int)
    assert isinstance(s.sentinel2_rgb_bands, list)


def test_settings_sync_url():
    """sync_database_url swaps asyncpg to psycopg2."""
    from src.config import Settings

    s = Settings()
    assert "+asyncpg" not in s.sync_database_url
    assert s.sync_database_url.startswith("postgresql://")


def test_validate_settings_raises_on_placeholder():
    """validate_settings rejects placeholder API keys."""
    from src.config import Settings, validate_settings

    os.environ["ANTHROPIC_API_KEY"] = "your_key_here"
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        validate_settings(Settings())


def test_validate_settings_passes_real_keys():
    """validate_settings accepts non-placeholder keys."""
    from src.config import Settings, validate_settings

    s = Settings()
    validate_settings(s)  # should not raise


def test_knowledge_base_keys():
    """KNOWLEDGE_BASE has expected satellite platforms."""
    from src.config import KNOWLEDGE_BASE

    assert "sentinel2" in KNOWLEDGE_BASE
    assert "landsat" in KNOWLEDGE_BASE
    assert KNOWLEDGE_BASE["sentinel2"]["stac_collection"] == "sentinel-2-l2a"
    assert KNOWLEDGE_BASE["landsat"]["revisit_days"] == 8


def test_spectral_indices():
    """SPECTRAL_INDICES has core indices with band mappings."""
    from src.config import SPECTRAL_INDICES

    for idx in ("NDVI", "NDWI", "NDBI"):
        assert idx in SPECTRAL_INDICES
        assert "formula" in SPECTRAL_INDICES[idx]
        assert "bands_s2" in SPECTRAL_INDICES[idx]
        assert "bands_ls" in SPECTRAL_INDICES[idx]


def test_knowledge_base_bands_match_settings():
    """Band lists in KNOWLEDGE_BASE are consistent with Settings defaults."""
    from src.config import KNOWLEDGE_BASE, Settings

    s = Settings()
    kb_s2_bands = set(KNOWLEDGE_BASE["sentinel2"]["resolution_m"].keys())
    for band in s.sentinel2_required_bands:
        assert band in kb_s2_bands, f"{band} missing from KNOWLEDGE_BASE sentinel2"
