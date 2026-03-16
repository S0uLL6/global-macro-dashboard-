"""analysis.py — statistical helpers for the Global Macro Dashboard."""
import pandas as pd


def compute_yoy(series: pd.Series, freq: str = "infer") -> pd.Series:
    """Return year-over-year % change for a time series.

    Detects frequency automatically; falls back to median-gap heuristic.
    Returns empty Series if input is too short.
    """
    if series.empty or len(series) < 2:
        return pd.Series(dtype=float)

    if freq == "infer":
        detected = pd.infer_freq(series.index)
        if detected is not None:
            freq = detected
        else:
            # Fallback: median gap in days → approximate periods per year
            gaps = series.index.to_series().diff().dt.days.dropna()
            median_gap = gaps.median()
            if median_gap <= 35:
                freq = "MS"   # monthly-ish
            elif median_gap <= 100:
                freq = "QS"   # quarterly-ish
            else:
                freq = "AS"   # annual-ish

    freq_upper = str(freq).upper()
    if freq_upper.startswith("M"):
        periods = 12
    elif freq_upper.startswith("Q"):
        periods = 4
    else:
        periods = 1

    if len(series) <= periods:
        return pd.Series(dtype=float)

    return series.pct_change(periods=periods).mul(100).dropna()
