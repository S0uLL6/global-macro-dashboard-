from pathlib import Path

from src.config import CACHE_DIR


def _cache_path(country: str, indicator: str) -> Path:
    """Return cache file path, e.g. data/cache/usa_gdp.csv."""
    return CACHE_DIR / f"{country.lower()}_{indicator.lower()}.csv"
