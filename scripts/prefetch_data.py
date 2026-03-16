"""Prefetch / cache-warmer script.

Loops over all 5 countries × 4 indicators = 20 combinations.
Calls get_indicator(force_refresh=True) for each and reports results.
Exits with code 1 if any unexpected failures occur.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import COUNTRIES, INDICATORS
from src.data_fetcher import get_indicator

EXPECTED_UNAVAILABLE = {
    ("China", "interest_rate"),
}


def main() -> None:
    total = len(COUNTRIES) * len(INDICATORS)
    ok_count = 0
    fail_count = 0

    for country in COUNTRIES:
        for indicator in INDICATORS:
            if (country, indicator) in EXPECTED_UNAVAILABLE:
                print(f"[SKIP] {country}/{indicator} — no source available (expected)")
                continue
            try:
                df = get_indicator(country, indicator, force_refresh=True)
                n = len(df)
                print(f"[OK]   {country}/{indicator} — {n} rows")
                ok_count += 1
            except Exception as exc:
                print(f"[FAIL] {country}/{indicator} — {exc}")
                fail_count += 1

    expected_skips = len(EXPECTED_UNAVAILABLE)
    print(f"\nSummary: {ok_count} OK / {total - expected_skips} attempted "
          f"({expected_skips} skipped, {fail_count} failed)")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
