from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Satellite data acquisition agent configuration."""

    # ── API Keys ──────────────────────────────────────────────
    anthropic_api_key: str
    tavily_api_key: str

    # ── Database ──────────────────────────────────────────────
    database_url: str

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str

    # ── Storage ───────────────────────────────────────────────
    scenes_dir: str = "./scenes"
    log_level: str = "INFO"

    # ── Catalog Endpoints ─────────────────────────────────────
    pc_stac_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    element84_url: str = "https://earth-search.aws.element84.com/v1"
    nasa_cmr_url: str = "https://cmr.earthdata.nasa.gov/stac"

    # ── Quality Gate Constants ────────────────────────────────
    cloud_cover_default_max: int = 15
    aoi_coverage_min_pct: float = 95.0
    nodata_max_pct: float = 5.0
    required_processing_level: str = "L2A"

    # ── Fetch Constants ───────────────────────────────────────
    cog_header_bytes: int = 16384
    thumbnail_max_kb: int = 200
    http_timeout_seconds: int = 15
    http_retry_attempts: int = 3

    # ── Agent Constants ───────────────────────────────────────
    claude_model: str = "claude-haiku-4-5-20251001"
    max_tokens_per_node: int = 150
    max_candidate_scenes: int = 8
    signed_url_expiry_minutes: int = 60

    # ── Satellite Band Definitions ────────────────────────────
    sentinel2_rgb_bands: list = ["B04", "B03", "B02"]
    sentinel2_required_bands: list = ["B02", "B03", "B04", "B08"]
    landsat_rgb_bands: list = ["B4", "B3", "B2"]
    landsat_required_bands: list = ["B2", "B3", "B4", "B5"]

    model_config = ConfigDict(env_file=".env", extra="ignore")

    @property
    def sync_database_url(self) -> str:
        """Return a sync driver URL for Alembic (swap asyncpg → psycopg2)."""
        return self.database_url.replace("+asyncpg", "")


_PLACEHOLDER_VALUES = {
    "your_key_here",
    "sk-placeholder",
    "CHANGE_ME",
    "your-api-key",
    "",
}


def validate_settings(settings: Settings) -> None:
    """Validate that API keys are not placeholder values."""
    if settings.anthropic_api_key in _PLACEHOLDER_VALUES:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set — replace the placeholder in .env"
        )
    if settings.tavily_api_key in _PLACEHOLDER_VALUES:
        raise ValueError(
            "TAVILY_API_KEY is not set — replace the placeholder in .env"
        )


# ── Knowledge Base ──────────────────────────────────────────────────────

KNOWLEDGE_BASE: dict = {
    "sentinel2": {
        "platform": "Sentinel-2",
        "constellation": ["S2A", "S2B"],
        "revisit_days": 5,
        "resolution_m": {
            "B02": 10, "B03": 10, "B04": 10, "B08": 10,
            "B05": 20, "B06": 20, "B07": 20, "B8A": 20,
            "B01": 60, "B09": 60, "B10": 60,
        },
        "processing_levels": ["L1C", "L2A"],
        "stac_collection": "sentinel-2-l2a",
    },
    "landsat": {
        "platform": "Landsat",
        "constellation": ["L8", "L9"],
        "revisit_days": 8,
        "resolution_m": {
            "B1": 30, "B2": 30, "B3": 30, "B4": 30,
            "B5": 30, "B6": 30, "B7": 30, "B10": 100,
        },
        "processing_levels": ["L2SP", "L2SR"],
        "stac_collection": "landsat-c2-l2",
    },
}

SPECTRAL_INDICES: dict = {
    "NDVI": {
        "formula": "(NIR - RED) / (NIR + RED)",
        "bands_s2": ("B08", "B04"),
        "bands_ls": ("B5", "B4"),
    },
    "NDWI": {
        "formula": "(GREEN - NIR) / (GREEN + NIR)",
        "bands_s2": ("B03", "B08"),
        "bands_ls": ("B3", "B5"),
    },
    "NDBI": {
        "formula": "(SWIR - NIR) / (SWIR + NIR)",
        "bands_s2": ("B11", "B08"),
        "bands_ls": ("B6", "B5"),
    },
}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance, validated on first call."""
    settings = Settings()
    validate_settings(settings)
    return settings
