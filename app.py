"""Global Macro Dashboard — Streamlit application."""
import shutil

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import src.analysis as analysis
from src.config import (
    ALREADY_RATE_INDICATORS,
    COUNTRIES,
    COUNTRY_COLORS,
    INDEX_LEVEL_INDICATORS,
    INDICATOR_LABELS,
    INDICATORS,
    CACHE_DIR,
)
from src.data_fetcher import get_indicator, get_multi_country

# ── page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Global Macro Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── session state ─────────────────────────────────────────────────────────────
if "data_cache" not in st.session_state:
    st.session_state.data_cache = {}

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Global Macro")
    st.markdown("---")

    selected_country = st.selectbox("Country", COUNTRIES, index=0)
    selected_indicator = st.selectbox(
        "Indicator",
        INDICATORS,
        format_func=lambda k: INDICATOR_LABELS[k],
        index=0,
    )

    start_year = st.number_input("Start year", min_value=1960, max_value=2023, value=2000)
    end_year = st.number_input("End year", min_value=1961, max_value=2030, value=2024)

    comparison_countries = st.multiselect(
        "Compare countries (Tab 2)",
        COUNTRIES,
        default=["USA", "Germany", "Japan"],
    )

    st.markdown("---")
    force_refresh = st.button("Force Refresh All Data")
    if force_refresh:
        st.session_state.data_cache = {}
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        st.rerun()

# ── data loader helper ────────────────────────────────────────────────────────

def _load_data(
    country: str,
    indicator: str,
    start: str = "2000-01-01",
    force: bool = False,
) -> pd.DataFrame | None:
    """Load data via session-state in-memory cache → get_indicator()."""
    key = f"{country}_{indicator}"
    if not force and key in st.session_state.data_cache:
        return st.session_state.data_cache[key]
    try:
        with st.spinner(f"Loading {country} {INDICATOR_LABELS[indicator]}…"):
            df = get_indicator(country, indicator, start=str(start_year) + "-01-01", force_refresh=force)
        st.session_state.data_cache[key] = df
        return df
    except Exception as exc:
        st.error(f"Could not load {country}/{indicator}: {exc}")
        return None


def _apply_yoy(df: pd.DataFrame, indicator: str) -> pd.Series:
    """Apply YoY transformation for index-level indicators (e.g. CPI)."""
    series = df.iloc[:, 0]
    if indicator in INDEX_LEVEL_INDICATORS:
        return analysis.compute_yoy(series)
    return series


def _filter_date(series: pd.Series) -> pd.Series:
    """Filter series to [start_year, end_year] range."""
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp(f"{end_year}-12-31")
    return series[(series.index >= start) & (series.index <= end)]


# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Overview", "Country Comparison", "Correlations"])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — single-country overview
# ════════════════════════════════════════════════════════════════════
with tab1:
    try:
        # Guard: China has no interest_rate data
        if selected_country == "China" and selected_indicator == "interest_rate":
            st.warning("Interest rate data is not available for China.")
            st.stop()

        df = _load_data(selected_country, selected_indicator)
        if df is None:
            st.stop()

        series = _apply_yoy(df, selected_indicator)
        series = _filter_date(series)

        if series.empty:
            st.warning("No data available for the selected date range.")
            st.stop()

        # ── label for y-axis ──────────────────────────────────────
        y_label = INDICATOR_LABELS[selected_indicator]
        if selected_indicator in INDEX_LEVEL_INDICATORS:
            y_label += " YoY %"

        # ── line chart ────────────────────────────────────────────
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=selected_country,
                line=dict(color=COUNTRY_COLORS[selected_country], width=2),
            )
        )
        fig.update_layout(
            title=f"{selected_country} — {y_label}",
            xaxis_title="Date",
            yaxis_title=y_label,
            hovermode="x unified",
            template="plotly_white",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── text insight ──────────────────────────────────────────
        st.info(analysis.generate_text_insight(series, selected_country, selected_indicator))

        # ── summary stats table ───────────────────────────────────
        stats = pd.DataFrame(
            {
                "Metric": ["Latest Value", "Mean", "Std Dev", "Min", "Max", "Observations"],
                "Value": [
                    f"{series.iloc[-1]:.2f}",
                    f"{series.mean():.2f}",
                    f"{series.std():.2f}",
                    f"{series.min():.2f}",
                    f"{series.max():.2f}",
                    str(len(series)),
                ],
            }
        )
        st.dataframe(stats, hide_index=True, use_container_width=True)

        # ── raw data expander ─────────────────────────────────────
        with st.expander("Show raw data"):
            raw = series.sort_index(ascending=False).to_frame(name=y_label)
            raw.index.name = "Date"
            st.dataframe(raw, use_container_width=True)

    except Exception as exc:
        st.error(f"An error occurred: {exc}")
        if st.button("Clear cache and retry", key="retry_tab1"):
            st.session_state.data_cache = {}
            st.rerun()

# ════════════════════════════════════════════════════════════════════
# TAB 2 — multi-country overlay
# ════════════════════════════════════════════════════════════════════
with tab2:
    try:
        if not comparison_countries:
            st.info("Select at least one country in the sidebar.")
            st.stop()

        y_label = INDICATOR_LABELS[selected_indicator]
        if selected_indicator in INDEX_LEVEL_INDICATORS:
            y_label += " YoY %"

        # ── load each country ─────────────────────────────────────
        series_dict: dict[str, pd.Series] = {}
        for country in comparison_countries:
            if country == "China" and selected_indicator == "interest_rate":
                st.warning(f"Interest rate not available for China — skipping.")
                continue
            df = _load_data(country, selected_indicator)
            if df is not None:
                s = _apply_yoy(df, selected_indicator)
                if not s.empty:
                    series_dict[country] = s

        if not series_dict:
            st.warning("No data loaded for any selected country.")
            st.stop()

        # ── align and filter ──────────────────────────────────────
        wide = pd.concat(series_dict, axis=1)
        wide = analysis.resample_to_common_freq(wide, "QS")
        start = pd.Timestamp(f"{start_year}-01-01")
        end = pd.Timestamp(f"{end_year}-12-31")
        wide = wide[(wide.index >= start) & (wide.index <= end)]

        if wide.empty:
            st.warning("No data available for the selected date range.")
            st.stop()

        # ── overlay chart ─────────────────────────────────────────
        fig2 = go.Figure()
        for country, col in zip(series_dict.keys(), wide.columns):
            fig2.add_trace(
                go.Scatter(
                    x=wide.index,
                    y=wide[col],
                    mode="lines",
                    name=country,
                    line=dict(color=COUNTRY_COLORS.get(country, "#888"), width=2),
                )
            )
        fig2.update_layout(
            title=f"Country Comparison — {y_label}",
            xaxis_title="Date",
            yaxis_title=y_label,
            hovermode="x unified",
            template="plotly_white",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ── cross-country stats table ─────────────────────────────
        rows = []
        for country in series_dict:
            s = _filter_date(series_dict[country])
            if s.empty:
                continue
            rows.append(
                {
                    "Country": country,
                    "Latest": f"{s.iloc[-1]:.2f}",
                    "Latest Date": s.index[-1].strftime("%b %Y"),
                    "Mean": f"{s.mean():.2f}",
                    "Std Dev": f"{s.std():.2f}",
                    "Min": f"{s.min():.2f}",
                    "Max": f"{s.max():.2f}",
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    except Exception as exc:
        st.error(f"An error occurred: {exc}")
        if st.button("Clear cache and retry", key="retry_tab2"):
            st.session_state.data_cache = {}
            st.rerun()

# ════════════════════════════════════════════════════════════════════
# TAB 3 — correlations scatter
# ════════════════════════════════════════════════════════════════════
with tab3:
    try:
        col_x, col_y = st.columns(2)
        with col_x:
            st.subheader("X-axis")
            x_indicator = st.selectbox(
                "Indicator (X)", INDICATORS, format_func=lambda k: INDICATOR_LABELS[k],
                index=0, key="x_ind"
            )
            x_country = st.selectbox("Country (X)", COUNTRIES, index=0, key="x_ctr")
        with col_y:
            st.subheader("Y-axis")
            y_indicator = st.selectbox(
                "Indicator (Y)", INDICATORS, format_func=lambda k: INDICATOR_LABELS[k],
                index=2, key="y_ind"
            )
            y_country = st.selectbox("Country (Y)", COUNTRIES, index=0, key="y_ctr")

        # ── guard: China interest rate ────────────────────────────
        for ctr, ind, axis in [(x_country, x_indicator, "X"), (y_country, y_indicator, "Y")]:
            if ctr == "China" and ind == "interest_rate":
                st.warning(f"Interest rate not available for China ({axis}-axis).")
                st.stop()

        # ── load both series ──────────────────────────────────────
        df_x = _load_data(x_country, x_indicator)
        df_y = _load_data(y_country, y_indicator)
        if df_x is None or df_y is None:
            st.stop()

        sx = _apply_yoy(df_x, x_indicator)
        sy = _apply_yoy(df_y, y_indicator)
        sx = _filter_date(sx)
        sy = _filter_date(sy)

        # ── inner-join alignment ──────────────────────────────────
        aligned = pd.concat(
            {"x": sx, "y": sy}, axis=1, join="inner"
        ).dropna()

        if len(aligned) < 5:
            st.warning(
                f"Not enough overlapping observations ({len(aligned)}) to compute correlation. "
                "Try a wider date range or different series."
            )
            st.stop()

        # ── scatter chart ─────────────────────────────────────────
        scatter_df = aligned.reset_index()
        scatter_df.columns = ["date", "x", "y"]
        scatter_df["date_str"] = scatter_df["date"].dt.strftime("%b %Y")

        fig3 = px.scatter(
            scatter_df,
            x="x",
            y="y",
            hover_data={"date_str": True, "x": ":.2f", "y": ":.2f", "date": False},
            trendline="ols",
            labels={
                "x": f"{x_country} {INDICATOR_LABELS[x_indicator]}",
                "y": f"{y_country} {INDICATOR_LABELS[y_indicator]}",
            },
            template="plotly_white",
            height=450,
        )
        st.plotly_chart(fig3, use_container_width=True)

        # ── correlation metrics ───────────────────────────────────
        r = analysis.compute_correlation(aligned["x"], aligned["y"])
        n = len(aligned)
        if abs(r) < 0.2:
            direction = "Weak / No relationship"
        elif r > 0:
            direction = "Positive"
        else:
            direction = "Negative"

        m1, m2, m3 = st.columns(3)
        m1.metric("Pearson r", f"{r:.3f}")
        m2.metric("Observations", str(n))
        m3.metric("Relationship", direction)

        st.caption(
            "Correlation does not imply causation. "
            "These are statistical associations only."
        )

    except Exception as exc:
        st.error(f"An error occurred: {exc}")
        if st.button("Clear cache and retry", key="retry_tab3"):
            st.session_state.data_cache = {}
            st.rerun()
