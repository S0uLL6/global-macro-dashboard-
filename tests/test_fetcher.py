"""Unit tests for src/data_fetcher.py."""
import time
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data_fetcher import (
    _cache_is_fresh,
    _cache_path,
    _load_from_cache,
    _save_to_cache,
    get_indicator,
    get_multi_country,
)


# ── cache helpers ─────────────────────────────────────────────────────────────

def test_cache_path_format():
    path = _cache_path("USA", "GDP")
    assert path.name == "usa_gdp.csv"


def test_cache_is_fresh_missing_file(tmp_path):
    assert not _cache_is_fresh(tmp_path / "nonexistent.csv", max_age_hours=24)


def test_cache_is_fresh_new_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("test")
    assert _cache_is_fresh(p, max_age_hours=24)


def test_cache_is_stale_old_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("test")
    # Backdate mtime by 25 hours
    stale_time = time.time() - 25 * 3600
    import os
    os.utime(p, (stale_time, stale_time))
    assert not _cache_is_fresh(p, max_age_hours=24)


def test_save_and_load_cache(tmp_path):
    df = pd.DataFrame({"val": [1.0, 2.0]}, index=pd.date_range("2020-01-01", periods=2, freq="MS"))
    p = tmp_path / "cache" / "test.csv"
    _save_to_cache(df, p)
    loaded = _load_from_cache(p)
    assert isinstance(loaded.index, pd.DatetimeIndex)
    assert list(loaded["val"]) == [1.0, 2.0]


# ── get_indicator routing ─────────────────────────────────────────────────────

def _make_fred_series(series_id: str) -> pd.Series:
    idx = pd.date_range("2020-01-01", periods=5, freq="QS")
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx, name=series_id)


def test_get_indicator_routes_usa_gdp_to_fred(tmp_path):
    """USA/gdp should call fetch_fred_series with A191RL1Q225SBEA."""
    fred_data = _make_fred_series("A191RL1Q225SBEA")
    with (
        patch("src.data_fetcher.fetch_fred_series", return_value=fred_data) as mock_fred,
        patch("src.data_fetcher.CACHE_DIR", tmp_path),
        patch("src.data_fetcher._cache_is_fresh", return_value=False),
    ):
        result = get_indicator("USA", "gdp")
        mock_fred.assert_called_once()
        call_args = mock_fred.call_args[0]
        assert call_args[0] == "A191RL1Q225SBEA"
        assert isinstance(result, pd.DataFrame)
        assert "USA_gdp" in result.columns


def test_get_indicator_routes_china_gdp_to_world_bank(tmp_path):
    """China/gdp has no FRED series → should call fetch_world_bank."""
    wb_data = pd.Series(
        [6.0, 7.0, 8.0, 5.0, 2.0],
        index=pd.date_range("2015-01-01", periods=5, freq="YS"),
        name="NY.GDP.MKTP.KD.ZG",
    )
    with (
        patch("src.data_fetcher.fetch_world_bank", return_value=wb_data) as mock_wb,
        patch("src.data_fetcher.CACHE_DIR", tmp_path),
        patch("src.data_fetcher._cache_is_fresh", return_value=False),
    ):
        result = get_indicator("China", "gdp")
        mock_wb.assert_called_once()
        assert isinstance(result, pd.DataFrame)
        assert "China_gdp" in result.columns


# ── get_multi_country ─────────────────────────────────────────────────────────

def test_get_multi_country_skips_failed_countries(tmp_path):
    """One failing country should be skipped; partial result returned."""
    good_data = pd.DataFrame(
        {"USA_gdp": [1.0, 2.0, 3.0]},
        index=pd.date_range("2020-01-01", periods=3, freq="QS"),
    )

    def fake_get_indicator(country, indicator, **kwargs):
        if country == "Germany":
            raise RuntimeError("API error")
        return good_data

    with (
        patch("src.data_fetcher.get_indicator", side_effect=fake_get_indicator),
    ):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_multi_country(["USA", "Germany"], "gdp")
            assert any("Germany" in str(warning.message) for warning in w)

    assert "USA_gdp" in result.columns
    assert result.shape[1] == 1


def test_get_multi_country_raises_when_all_fail():
    def always_fail(country, indicator, **kwargs):
        raise RuntimeError("fail")

    with patch("src.data_fetcher.get_indicator", side_effect=always_fail):
        with pytest.raises(ValueError, match="All countries failed"):
            get_multi_country(["USA", "Germany"], "gdp")
