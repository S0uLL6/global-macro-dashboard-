"""Unit tests for src/analysis.py."""
import math

import pandas as pd
import pytest

from src.analysis import (
    compute_correlation,
    compute_yoy,
    generate_text_insight,
    resample_to_common_freq,
)


# ── TestComputeYoY ────────────────────────────────────────────────────────────

class TestComputeYoY:
    def _monthly_series(self, values, start="2010-01-01"):
        idx = pd.date_range(start, periods=len(values), freq="MS")
        return pd.Series(values, index=idx)

    def test_monthly_100_to_105_is_5_pct(self):
        """13 months: values[12]/values[0] - 1 = 5%."""
        values = [100.0] * 12 + [105.0]
        series = self._monthly_series(values)
        result = compute_yoy(series)
        assert not result.empty
        assert abs(result.iloc[-1] - 5.0) < 0.01

    def test_empty_series_returns_empty(self):
        result = compute_yoy(pd.Series(dtype=float))
        assert result.empty

    def test_too_short_returns_empty(self):
        """Series with only 5 monthly values → fewer than 12 periods needed."""
        series = self._monthly_series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = compute_yoy(series)
        assert result.empty

    def test_quarterly_series(self):
        """5 quarterly values → 1 YoY result (periods=4)."""
        idx = pd.date_range("2010-01-01", periods=5, freq="QS")
        series = pd.Series([100.0, 102.0, 103.0, 101.0, 106.0], index=idx)
        result = compute_yoy(series)
        assert len(result) == 1
        assert abs(result.iloc[-1] - 6.0) < 0.01

    def test_annual_series(self):
        """Annual: YoY with periods=1 → simple pct change."""
        idx = pd.date_range("2010-01-01", periods=3, freq="YS")
        series = pd.Series([100.0, 110.0, 121.0], index=idx)
        result = compute_yoy(series)
        assert len(result) == 2
        assert abs(result.iloc[0] - 10.0) < 0.01


# ── TestComputeCorrelation ────────────────────────────────────────────────────

class TestComputeCorrelation:
    def _series(self, values, start="2010-01-01", freq="MS"):
        idx = pd.date_range(start, periods=len(values), freq=freq)
        return pd.Series(values, index=idx)

    def test_perfect_positive_correlation(self):
        a = self._series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = self._series([2.0, 4.0, 6.0, 8.0, 10.0])
        r = compute_correlation(a, b)
        assert abs(r - 1.0) < 1e-9

    def test_perfect_negative_correlation(self):
        a = self._series([1.0, 2.0, 3.0, 4.0, 5.0])
        b = self._series([5.0, 4.0, 3.0, 2.0, 1.0])
        r = compute_correlation(a, b)
        assert abs(r + 1.0) < 1e-9

    def test_insufficient_overlap_returns_nan(self):
        """Only 3 overlapping points → NaN."""
        idx_a = pd.date_range("2010-01-01", periods=3, freq="MS")
        idx_b = pd.date_range("2010-01-01", periods=3, freq="MS")
        a = pd.Series([1.0, 2.0, 3.0], index=idx_a)
        b = pd.Series([1.0, 2.0, 3.0], index=idx_b)
        r = compute_correlation(a, b)
        assert math.isnan(r)

    def test_no_overlap_returns_nan(self):
        a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0],
                      index=pd.date_range("2010-01-01", periods=5, freq="MS"))
        b = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0],
                      index=pd.date_range("2020-01-01", periods=5, freq="MS"))
        r = compute_correlation(a, b)
        assert math.isnan(r)


# ── TestGenerateTextInsight ───────────────────────────────────────────────────

class TestGenerateTextInsight:
    def _series(self, n=24, freq="MS", start="2010-01-01"):
        idx = pd.date_range(start, periods=n, freq=freq)
        return pd.Series(range(n, 0, -1), index=idx, dtype=float)

    def test_returns_nonempty_string(self):
        result = generate_text_insight(self._series(), "USA", "gdp")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_country_name(self):
        result = generate_text_insight(self._series(), "Japan", "cpi")
        assert "Japan" in result

    def test_empty_series_returns_message(self):
        result = generate_text_insight(pd.Series(dtype=float), "UK", "unemployment")
        assert "No data" in result


# ── TestResample ──────────────────────────────────────────────────────────────

class TestResample:
    def test_monthly_to_quarterly(self):
        idx = pd.date_range("2020-01-01", periods=12, freq="MS")
        df = pd.DataFrame({"a": range(1, 13)}, index=idx, dtype=float)
        result = resample_to_common_freq(df, "QS", method="last")
        assert len(result) == 4  # 4 quarters
        # Q1 last = March (index 2) = 3.0
        assert result.iloc[0]["a"] == 3.0

    def test_index_is_datetimeindex(self):
        idx = pd.date_range("2020-01-01", periods=12, freq="MS")
        df = pd.DataFrame({"a": range(12)}, index=idx, dtype=float)
        result = resample_to_common_freq(df, "QS")
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_mean_method(self):
        idx = pd.date_range("2020-01-01", periods=3, freq="MS")
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0]}, index=idx)
        result = resample_to_common_freq(df, "QS", method="mean")
        assert abs(result.iloc[0]["a"] - 2.0) < 1e-9
