import os
import time
import warnings
from pathlib import Path

import pandas as pd
import wbgapi
from dotenv import load_dotenv
from fredapi import Fred

from src.config import (
    CACHE_DIR,
    CACHE_MAX_AGE_HOURS,
    COUNTRIES,
    FRED_SERIES,
    WORLD_BANK_ISO,
    WORLD_BANK_SERIES,
)

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


def fetch_fred_series(series_id: str, start: str = "2000-01-01") -> pd.Series:
    """Fetch a FRED series, return as a named Series with DatetimeIndex, NaN dropped."""
    fred = _get_fred_client()
    data = fred.get_series(series_id, observation_start=start)
    data.index = pd.DatetimeIndex(data.index)
    data.name = series_id
    return data.dropna()


def fetch_world_bank(country_iso: str, wb_indicator: str) -> pd.Series:
    """Fetch a World Bank indicator for one country.

    Returns a pd.Series with DatetimeIndex (Jan 1 of each year), sorted, NaN dropped.
    """
    df = wbgapi.data.DataFrame(wb_indicator, economy=country_iso)
    # df columns are year strings like "YR2020"; rows are economies
    row = df.loc[country_iso] if country_iso in df.index else df.iloc[0]
    # Convert year labels "YR2020" → Timestamp("2020-01-01")
    index = pd.to_datetime(
        [str(col).replace("YR", "") for col in row.index], format="%Y"
    )
    series = pd.Series(row.values, index=index, name=wb_indicator, dtype=float)
    series = series.sort_index().dropna()
    return series


def _validate_dataframe(df: pd.DataFrame, country: str, indicator: str) -> pd.DataFrame:
    """Validate fetched DataFrame; raise on empty, warn on >50% NaN, ensure DatetimeIndex."""
    if df.empty:
        raise ValueError(f"Empty DataFrame returned for {country}/{indicator}")
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.DatetimeIndex(df.index)
    nan_ratio = df.iloc[:, 0].isna().mean()
    if nan_ratio > 0.5:
        warnings.warn(
            f"{country}/{indicator}: {nan_ratio:.0%} of values are NaN",
            UserWarning,
            stacklevel=3,
        )
    return df


def get_indicator(
    country: str,
    indicator: str,
    start: str = "2000-01-01",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Unified router: return single-column DataFrame for country/indicator.

    Checks CSV cache first (unless force_refresh=True). Routes to FRED or
    World Bank depending on config. Saves result to cache.
    """
    path = _cache_path(country, indicator)

    if not force_refresh and _cache_is_fresh(path, CACHE_MAX_AGE_HOURS):
        return _load_from_cache(path)

    fred_id = FRED_SERIES.get(country, {}).get(indicator)
    wb_code = WORLD_BANK_SERIES.get(indicator)
    iso = WORLD_BANK_ISO.get(country)

    if fred_id is not None:
        series = fetch_fred_series(fred_id, start=start)
    elif wb_code is not None and iso is not None:
        series = fetch_world_bank(iso, wb_code)
    else:
        raise ValueError(
            f"No data source available for {country}/{indicator}. "
            "Neither FRED series ID nor World Bank code is configured."
        )

    col_name = f"{country}_{indicator}"
    df = series.to_frame(name=col_name)
    df = _validate_dataframe(df, country, indicator)
    _save_to_cache(df, path)
    return df


def get_multi_country(
    countries: list,
    indicator: str,
    start: str = "2000-01-01",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Fetch indicator for multiple countries; return wide DataFrame.

    Skips countries that fail with a warning. Raises ValueError if all fail.
    """
    frames = []
    for country in countries:
        try:
            df = get_indicator(country, indicator, start=start, force_refresh=force_refresh)
            frames.append(df)
        except Exception as exc:
            warnings.warn(f"Skipping {country}/{indicator}: {exc}", UserWarning, stacklevel=2)

    if not frames:
        raise ValueError(f"All countries failed for indicator '{indicator}'")

    return pd.concat(frames, axis=1, join="outer")
