import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

from src.config import CACHE_DIR

_fred_client: "Fred | None" = None


def _get_fred_client() -> "Fred":
    """Lazy-initialise FRED client using FRED_API_KEY from .env."""
    global _fred_client
    if _fred_client is None:
        load_dotenv()
        api_key = os.environ.get("FRED_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "FRED_API_KEY is not set. Add it to your .env file."
            )
        _fred_client = Fred(api_key=api_key)
    return _fred_client


def _cache_path(country: str, indicator: str) -> Path:
    """Return cache file path, e.g. data/cache/usa_gdp.csv."""
    return CACHE_DIR / f"{country.lower()}_{indicator.lower()}.csv"


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


def _load_from_cache(path: Path) -> pd.DataFrame:
    """Load CSV from cache with DatetimeIndex."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.DatetimeIndex(df.index)
    return df
