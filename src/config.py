from pathlib import Path

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
