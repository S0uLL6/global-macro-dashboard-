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
