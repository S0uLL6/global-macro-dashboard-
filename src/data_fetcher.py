import time
from pathlib import Path

from src.config import CACHE_DIR


def _cache_path(country: str, indicator: str) -> Path:
    """Return cache file path, e.g. data/cache/usa_gdp.csv."""
    return CACHE_DIR / f"{country.lower()}_{indicator.lower()}.csv"


import pandas as pd


def _cache_is_fresh(path: Path, max_age_hours: float) -> bool:
    """Return True if file exists and its mtime is within max_age_hours."""
    if not path.exists():
        return False
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < max_age_hours * 3600


def _save_to_cache(df: pd.DataFrame, path: Path) -> None:
    """Create parent dirs and save DataFrame to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
