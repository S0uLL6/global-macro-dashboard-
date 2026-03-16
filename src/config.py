from pathlib import Path

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_MAX_AGE_HOURS = 24

# FRED series IDs: country -> indicator -> series_id (None = World Bank only)
FRED_SERIES = {
    "USA": {
        "gdp": "A191RL1Q225SBEA",
        "cpi": "CPIAUCSL",
        "unemployment": "UNRATE",
        "interest_rate": "FEDFUNDS",
    },
    "Germany": {
        "gdp": "CLVMNACSCAB1GQDE",
        "cpi": "DEUCPIALLMINMEI",
        "unemployment": "LMUNRRTTDEM156S",
        "interest_rate": "ECBDFR",
    },
    "UK": {
        "gdp": "GBRGDPNQDSMEI",
        "cpi": "GBRCPIALLMINMEI",
        "unemployment": "LMUNRRTTGBM156S",
        "interest_rate": "BOERUKM",
    },
    "Japan": {
        "gdp": "JPNGDPNQDSMEI",
        "cpi": "JPNCPIALLMINMEI",
        "unemployment": "LMUNRRTTJPM156S",
        "interest_rate": "IRSTCI01JPM156N",
    },
    "China": {
        "gdp": None,
        "cpi": None,
        "unemployment": None,
        "interest_rate": None,
    },
}

# World Bank indicator codes (fallback for China and missing FRED series)
WORLD_BANK_SERIES = {
    "gdp": "NY.GDP.MKTP.KD.ZG",
    "cpi": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "interest_rate": None,  # Not available from World Bank
}

# World Bank ISO 2-letter country codes
WORLD_BANK_ISO = {
    "USA": "US",
    "Germany": "DE",
    "UK": "GB",
    "Japan": "JP",
    "China": "CN",
}

# Human-readable labels shown in the UI
INDICATOR_LABELS = {
    "gdp": "GDP Growth (%)",
    "cpi": "CPI Inflation",
    "unemployment": "Unemployment Rate (%)",
    "interest_rate": "Central Bank Rate (%)",
}

# Consistent hex colours per country across all charts
COUNTRY_COLORS = {
    "USA": "#1f77b4",
    "Germany": "#d62728",
    "UK": "#2ca02c",
    "Japan": "#ff7f0e",
    "China": "#9467bd",
}

# Indicators where the raw FRED series is already in % rate (no YoY needed)
ALREADY_RATE_INDICATORS = {"gdp", "unemployment", "interest_rate"}

# Indicators where FRED series is an index level (YoY % change needed)
INDEX_LEVEL_INDICATORS = {"cpi"}

# Countries whose GDP FRED series is an absolute level (not % change) → need YoY
# USA uses A191RL1Q225SBEA which is already QoQ %; others use volume level series
GDP_LEVEL_COUNTRIES = {"Germany", "UK", "Japan", "China"}

# Convenience lists for iteration
COUNTRIES = list(FRED_SERIES.keys())
INDICATORS = list(INDICATOR_LABELS.keys())
