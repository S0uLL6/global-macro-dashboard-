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


def compute_correlation(
    a: pd.Series, b: pd.Series, method: str = "pearson"
) -> float:
    """Compute correlation between two series aligned on their inner index.

    Returns NaN if fewer than 5 observations overlap.
    """
    combined = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(combined) < 5:
        return float("nan")
    return combined.iloc[:, 0].corr(combined.iloc[:, 1], method=method)


def generate_text_insight(series: pd.Series, country: str, indicator: str) -> str:
    """Return a human-readable insight string for a time series.

    Includes: latest value, 1-year delta direction, 5-year range.
    Handles empty series and short windows gracefully.
    """
    if series.empty:
        return f"No data available for {country} — {indicator}."

    latest_val = series.iloc[-1]
    latest_date = series.index[-1]

    # 1-year delta
    one_year_ago = latest_date - pd.DateOffset(years=1)
    past_year = series[series.index <= one_year_ago]
    if not past_year.empty:
        delta = latest_val - past_year.iloc[-1]
        direction = "up" if delta > 0 else ("down" if delta < 0 else "unchanged")
        delta_str = f", {direction} {abs(delta):.2f} vs a year ago"
    else:
        delta_str = ""

    # 5-year range
    five_years_ago = latest_date - pd.DateOffset(years=5)
    window = series[series.index >= five_years_ago]
    if len(window) >= 2:
        range_str = f" 5-year range: {window.min():.2f} – {window.max():.2f}."
    else:
        range_str = ""

    return (
        f"{country} — {indicator}: latest {latest_val:.2f} "
        f"({latest_date.strftime('%b %Y')}){delta_str}.{range_str}"
    )


def resample_to_common_freq(
    df: pd.DataFrame, target_freq: str = "QS", method: str = "last"
) -> pd.DataFrame:
    """Resample a DataFrame to a common frequency.

    Uses the specified aggregation method (default: last observed value).
    """
    resampler = df.resample(target_freq)
    if method == "last":
        return resampler.last()
    elif method == "mean":
        return resampler.mean()
    elif method == "first":
        return resampler.first()
    else:
        return resampler.last()
