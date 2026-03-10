"""Smoke test / cache warmer: verify fetch_fred_series() returns live data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import fetch_fred_series

if __name__ == "__main__":
    series = fetch_fred_series("UNRATE", start="2000-01-01")
    assert not series.empty, "Series is empty — check FRED_API_KEY"
    print(f"UNRATE: {len(series)} observations, {series.index[0].date()} → {series.index[-1].date()}")
    print(series.tail(3))
    print("Smoke test passed.")
