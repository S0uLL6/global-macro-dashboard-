# Global Macro Dashboard

An interactive Streamlit dashboard for exploring macroeconomic indicators across five major economies: **USA, Germany, UK, Japan, and China**.

---

## What This Shows

| Tab | Purpose |
|-----|---------|
| **Overview** | Single-country time series for GDP growth, CPI inflation, unemployment, or central bank rate. Includes trend chart, summary statistics, and text insight. |
| **Country Comparison** | Overlay chart aligning up to 5 countries on the same axis. Resampled to quarterly frequency for clean comparison. |
| **Correlations** | Scatter plot with OLS trendline between any two series. Pearson r, observation count, and relationship direction displayed as metrics. |

### Economics framing

- **Business cycles** — track how GDP growth and unemployment move in sync or diverge across economies.
- **Monetary policy comparison** — compare central bank rates (Fed Funds, ECB, Bank of England, BoJ) against inflation to spot tightening/easing cycles.
- **Phillips curve exploration** — scatter unemployment (X) vs CPI inflation (Y) for a country to test the classic inverse relationship empirically.

---

## Setup

```bash
# 1. Clone
git clone https://github.com/S0uLL6/global-macro-dashboard.git
cd global-macro-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env with your FRED API key (free at https://fred.stlouisfed.org/docs/api/api_key.html)
cp .env.example .env
# Edit .env and set FRED_API_KEY=your_key_here

# 4. (Optional) Pre-fetch and cache all data
python scripts/prefetch_data.py

# 5. Run the app
streamlit run app.py
```

---

## Data Sources

### FRED Series (primary — updated live)

| Country | GDP | CPI | Unemployment | Central Bank Rate |
|---------|-----|-----|--------------|-------------------|
| USA | `A191RL1Q225SBEA` | `CPIAUCSL` | `UNRATE` | `FEDFUNDS` |
| Germany | `CLVMNACSCAB1GQDE` | `DEUCPIALLMINMEI` | `LMUNRRTTDEM156S` | `ECBDFR` |
| UK | `GBRGDPNQDSMEI` | `GBRCPIALLMINMEI` | `LMUNRRTTGBM156S` | `BOERUKM` |
| Japan | `JPNGDPNQDSMEI` | `JPNCPIALLMINMEI` | `LMUNRRTTJPM156S` | `IRSTCI01JPM156N` |
| China | — | — | — | — |

### World Bank (fallback for China)

| Indicator | World Bank Code |
|-----------|----------------|
| GDP growth | `NY.GDP.MKTP.KD.ZG` |
| CPI inflation | `FP.CPI.TOTL.ZG` |
| Unemployment | `SL.UEM.TOTL.ZS` |
| Interest rate | *(not available)* |

China's data is sourced exclusively from the World Bank since FRED does not carry Chinese macro series. Annual frequency is resampled to quarterly for comparison charts.

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Single data gateway** (`get_indicator`) | One function handles cache check → FRED/WB routing → validation → cache write. Consumers (app and tests) never call APIs directly. |
| **CSV cache with 24-hour TTL** | Avoids repeated API calls during a session. `force_refresh` flag and sidebar button allow manual invalidation. |
| **YoY at visualisation time** | CPI is stored as the raw index level. `compute_yoy()` is applied only in the app, not in the cache, so raw values remain available for other calculations. |
| **World Bank as fallback only** | FRED is the primary source for all non-China series due to higher update frequency and richer metadata. WB is used only when FRED series ID is `None`. |
| **Frequency alignment via resampling** | `resample_to_common_freq(df, "QS")` converts monthly/quarterly/annual series to a common quarterly grid before overlay charts and correlation analysis, preventing visual artefacts from mixed-frequency data. |

---

## Running Tests

```bash
pytest
```

All tests use `unittest.mock` — no live API calls are made.
