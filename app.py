from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Northstar | Analytics",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = {
    "accent": "#6E8BFF",
    "accent_2": "#39C6A5",
    "warning": "#E3A84B",
    "danger": "#E06C75",
}


def build_sample_data() -> dict[str, pd.DataFrame]:
    """Create deterministic, monthly sample datasets with a shared core schema."""
    rng = np.random.default_rng(23)
    months = pd.date_range("2025-01-01", periods=20, freq="MS")

    retail_rows: list[dict[str, Any]] = []
    categories = ["Home", "Beauty", "Electronics", "Apparel"]
    retail_channels = ["Direct", "Paid Search", "Email", "Social"]
    category_base = {"Home": 0.95, "Beauty": 0.72, "Electronics": 1.35, "Apparel": 1.08}
    channel_base = {"Direct": 1.25, "Paid Search": 1.08, "Email": 1.16, "Social": 0.82}
    for month_index, month in enumerate(months):
        season = 1 + 0.14 * np.sin((month_index - 2) * np.pi / 6)
        for category in categories:
            for channel in retail_channels:
                orders = max(
                    18,
                    int(
                        (72 + month_index * 2.2)
                        * category_base[category]
                        * channel_base[channel]
                        * season
                        * rng.normal(1, 0.075)
                    ),
                )
                conversion_rate = {
                    "Direct": 0.047,
                    "Paid Search": 0.036,
                    "Email": 0.064,
                    "Social": 0.022,
                }[channel] * rng.normal(1, 0.045)
                revenue = orders * {
                    "Home": 78,
                    "Beauty": 44,
                    "Electronics": 164,
                    "Apparel": 61,
                }[category] * rng.normal(1, 0.055)
                sessions = int(orders / conversion_rate)
                retail_rows.append(
                    {
                        "date": month,
                        "category": category,
                        "channel": channel,
                        "revenue": round(revenue, 2),
                        "orders": orders,
                        "sessions": sessions,
                        "ad_spend": round(
                            sessions
                            * {
                                "Direct": 0.08,
                                "Paid Search": 0.72,
                                "Email": 0.12,
                                "Social": 0.48,
                            }[channel],
                            2,
                        ),
                        "units_sold": int(orders * rng.uniform(1.15, 1.55)),
                    }
                )

    marketing_rows: list[dict[str, Any]] = []
    campaigns = ["Brand awareness", "Spring launch", "Retargeting", "Creator series"]
    marketing_channels = ["Search", "Social", "Email", "Display", "Affiliate"]
    channel_spend = {"Search": 520, "Social": 360, "Email": 100, "Display": 290, "Affiliate": 210}
    channel_ctr = {"Search": 0.038, "Social": 0.024, "Email": 0.092, "Display": 0.011, "Affiliate": 0.031}
    channel_conversion = {"Search": 0.061, "Social": 0.025, "Email": 0.071, "Display": 0.013, "Affiliate": 0.046}
    for month_index, month in enumerate(months):
        for campaign_index, campaign in enumerate(campaigns):
            for channel_index, channel in enumerate(marketing_channels):
                impressions = int(
                    (17500 + month_index * 520)
                    * (1 + campaign_index * 0.08)
                    * rng.normal(1, 0.1)
                )
                clicks = max(8, int(impressions * channel_ctr[channel] * rng.normal(1, 0.1)))
                conversions = max(
                    1,
                    int(clicks * channel_conversion[channel] * rng.normal(1, 0.12)),
                )
                spend = clicks * channel_spend[channel] / 100
                order_value = 58 + campaign_index * 7 + (month_index % 4) * 2
                marketing_rows.append(
                    {
                        "date": month,
                        "category": campaign,
                        "channel": channel,
                        "revenue": round(conversions * order_value * rng.normal(1, 0.06), 2),
                        "orders": conversions,
                        "sessions": clicks,
                        "ad_spend": round(spend, 2),
                        "impressions": impressions,
                        "clicks": clicks,
                    }
                )

    saas_rows: list[dict[str, Any]] = []
    plans = {"Starter": 19, "Growth": 59, "Scale": 149}
    acquisition_channels = ["Organic", "Paid Search", "Partner", "Content"]
    channel_mix = {"Organic": 1.22, "Paid Search": 1.0, "Partner": 0.73, "Content": 0.85}
    for month_index, month in enumerate(months):
        for plan_index, (plan, monthly_price) in enumerate(plans.items()):
            for channel in acquisition_channels:
                churn_rate = 0.027 + plan_index * 0.004 + (0.012 if channel == "Paid Search" else 0)
                new_subscriptions = max(
                    2,
                    int(
                        (18 + month_index * 0.9)
                        * channel_mix[channel]
                        * (1 + plan_index * 0.2)
                        * rng.normal(1, 0.12)
                    ),
                )
                active_customers = int(
                    new_subscriptions
                    * (7.2 + month_index * 0.23)
                    * (1 - churn_rate * 2)
                )
                visits = int(new_subscriptions / (0.055 if channel in ["Organic", "Content"] else 0.035))
                saas_rows.append(
                    {
                        "date": month,
                        "category": plan,
                        "channel": channel,
                        "revenue": round(active_customers * monthly_price, 2),
                        "orders": new_subscriptions,
                        "sessions": visits,
                        "ad_spend": round(
                            visits * (0.32 if channel == "Paid Search" else 0.07 if channel == "Partner" else 0.04),
                            2,
                        ),
                        "active_subscribers": active_customers,
                        "churned_subscribers": int(active_customers * churn_rate),
                        "churn_rate": round(churn_rate * 100, 2),
                    }
                )

    return {
        "Retail sales": pd.DataFrame(retail_rows),
        "Marketing campaigns": pd.DataFrame(marketing_rows),
        "SaaS subscriptions": pd.DataFrame(saas_rows),
    }


ALIASES = {
    "date": ["date", "day", "month", "timestamp", "created_at", "order_date", "period"],
    "revenue": ["revenue", "sales", "amount", "gmv", "mrr", "total_sales", "net_sales"],
    "orders": [
        "orders",
        "order_count",
        "transactions",
        "purchases",
        "conversions",
        "signups",
        "subscriptions",
        "new_customers",
    ],
    "sessions": ["sessions", "visits", "website_visits", "traffic", "clicks", "impressions"],
    "category": ["category", "product", "segment", "campaign", "plan", "tier", "group"],
    "channel": ["channel", "source", "medium", "platform", "acquisition_channel"],
    "ad_spend": ["ad_spend", "marketing_spend", "spend", "cost", "advertising_cost"],
    "conversion_rate": ["conversion_rate", "conversion_pct", "conversion_percent", "cr"],
}


def key_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def find_column(frame: pd.DataFrame, aliases: list[str]) -> Any | None:
    normalized = {key_name(column): column for column in frame.columns}
    for alias in aliases:
        if key_name(alias) in normalized:
            return normalized[key_name(alias)]
    for column in frame.columns:
        normalized_column = key_name(column)
        if any(key_name(alias) in normalized_column for alias in aliases):
            return column
    return None


def resolve_columns(frame: pd.DataFrame) -> dict[str, Any | None]:
    found = {name: find_column(frame, aliases) for name, aliases in ALIASES.items()}
    if found["date"] is None:
        for column in frame.columns:
            parsed = pd.to_datetime(frame[column], errors="coerce")
            if parsed.notna().mean() >= 0.75:
                found["date"] = column
                break
    return found


def numeric_series(frame: pd.DataFrame, column: Any | None) -> pd.Series | None:
    if column is None:
        return None
    return pd.to_numeric(
        frame[column].astype(str).str.replace(r"[$,%\s,]", "", regex=True),
        errors="coerce",
    )


def prepare_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any | None]]:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    columns = resolve_columns(frame)
    if columns["date"] is not None:
        frame["_date"] = pd.to_datetime(frame[columns["date"]], errors="coerce")
    if columns["revenue"] is not None:
        frame["_revenue"] = numeric_series(frame, columns["revenue"])
    if columns["orders"] is not None:
        frame["_orders"] = numeric_series(frame, columns["orders"])
    if columns["sessions"] is not None:
        frame["_sessions"] = numeric_series(frame, columns["sessions"])
    if columns["ad_spend"] is not None:
        frame["_ad_spend"] = numeric_series(frame, columns["ad_spend"])
    if columns["conversion_rate"] is not None:
        rate = numeric_series(frame, columns["conversion_rate"])
        if rate is not None and rate.dropna().median() > 1:
            rate = rate / 100
        frame["_conversion_rate"] = rate
    return frame, columns


def fmt_money(value: float | int) -> str:
    if pd.isna(value):
        return "—"
    absolute = abs(float(value))
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    if absolute >= 10_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def fmt_number(value: float | int) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def theme_css(mode: str) -> str:
    if mode == "Light":
        surface = "#FFFFFF"
        background = "#F4F7FB"
        text = "#172238"
        muted = "#71809A"
        border = "#E3E9F2"
        shadow = "0 8px 30px rgba(25, 45, 85, .06)"
        control = "#F1F4F9"
    else:
        surface = "#151E2D"
        background = "#0D1420"
        text = "#E8EEF9"
        muted = "#94A4BB"
        border = "#273449"
        shadow = "0 12px 35px rgba(0, 0, 0, .18)"
        control = "#1B2638"
    return f"""
    <style>
    :root {{
      --surface: {surface};
      --background: {background};
      --text: {text};
      --muted: {muted};
      --border: {border};
      --shadow: {shadow};
      --control: {control};
      --accent: {PALETTE["accent"]};
      --mint: {PALETTE["accent_2"]};
      --amber: {PALETTE["warning"]};
      --red: {PALETTE["danger"]};
    }}
    html, body, [data-testid="stAppViewContainer"] {{
      background: var(--background);
      color: var(--text);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{
      background: var(--surface);
      border-right: 1px solid var(--border);
    }}
    [data-testid="stSidebar"] * {{ color: var(--text); }}
    [data-testid="stMainBlockContainer"] {{
      max-width: 1500px;
      padding-top: 1.8rem;
      padding-bottom: 3.5rem;
    }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {{ color: var(--muted); }}
    h1, h2, h3, h4, [data-testid="stMetricLabel"] {{
      color: var(--text) !important;
    }}
    [data-testid="stMetric"] {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 19px 21px;
      box-shadow: var(--shadow);
      min-height: 118px;
    }}
    [data-testid="stMetricLabel"] {{
      font-size: .82rem;
      font-weight: 600;
      letter-spacing: .025em;
    }}
    [data-testid="stMetricValue"] {{
      font-size: 1.75rem;
      font-weight: 720;
      color: var(--text) !important;
    }}
    [data-testid="stMetricDelta"] {{ font-size: .78rem; }}
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
      background: var(--surface);
      border-color: var(--border) !important;
      border-radius: 18px;
      box-shadow: var(--shadow);
    }}
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stDateInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stFileUploader"] section {{
      background: var(--control);
      border-color: var(--border);
      border-radius: 10px;
      color: var(--text);
    }}
    [data-testid="stButton"] button {{
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--control);
      color: var(--text);
      transition: transform .16s ease, border-color .16s ease;
    }}
    [data-testid="stButton"] button:hover {{
      transform: translateY(-1px);
      border-color: var(--accent);
      color: var(--accent);
    }}
    [data-testid="stFileUploader"] {{ border-radius: 12px; }}
    [data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: 12px; }}
    [data-testid="stAlert"] {{ border-radius: 12px; }}
    .hero-kicker {{
      font-size: .75rem;
      font-weight: 700;
      letter-spacing: .15em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: .4rem;
    }}
    .hero-title {{
      color: var(--text);
      font-size: clamp(2rem, 4vw, 2.7rem);
      line-height: 1.06;
      font-weight: 760;
      letter-spacing: -.045em;
      margin: 0;
    }}
    .hero-subtitle {{
      color: var(--muted);
      margin: .6rem 0 0;
      font-size: .98rem;
    }}
    .section-label {{
      color: var(--muted);
      font-size: .73rem;
      font-weight: 700;
      letter-spacing: .13em;
      text-transform: uppercase;
      margin-bottom: .65rem;
    }}
    .insight {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-left: 3px solid var(--accent);
      border-radius: 13px;
      padding: 15px 16px;
      margin-bottom: 10px;
      box-shadow: var(--shadow);
    }}
    .insight.warning {{ border-left-color: var(--amber); }}
    .insight.positive {{ border-left-color: var(--mint); }}
    .insight-title {{ color: var(--text); font-weight: 680; margin-bottom: 3px; }}
    .insight-copy {{ color: var(--muted); font-size: .9rem; line-height: 1.5; }}
    .data-note {{ color: var(--muted); font-size: .82rem; }}
    .source-chip {{
      display: inline-block;
      background: var(--control);
      border: 1px solid var(--border);
      border-radius: 99px;
      padding: 5px 10px;
      color: var(--muted);
      font-size: .76rem;
    }}
    div[data-testid="stHorizontalBlock"] {{ gap: 1rem; }}
    @media (max-width: 760px) {{
      [data-testid="stMainBlockContainer"] {{ padding: 1rem 1rem 2rem; }}
      [data-testid="stMetric"] {{ padding: 14px 15px; min-height: 98px; }}
      [data-testid="stMetricValue"] {{ font-size: 1.42rem; }}
    }}
    </style>
    """


def chart_layout(mode: str, title: str) -> dict[str, Any]:
    dark = mode == "Dark"
    foreground = "#E8EEF9" if dark else "#26354C"
    muted = "#94A4BB" if dark else "#77869C"
    grid = "#273449" if dark else "#E8EDF4"
    return {
        "title": {"text": title, "font": {"size": 15, "color": foreground}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, ui-sans-serif, system-ui", "color": muted, "size": 11},
        "margin": {"l": 10, "r": 18, "t": 46, "b": 10},
        "xaxis": {"gridcolor": grid, "zerolinecolor": grid},
        "yaxis": {"gridcolor": grid, "zerolinecolor": grid},
        "legend": {"orientation": "h", "y": -0.2},
        "hoverlabel": {"bgcolor": "#172238", "font": {"color": "#FFFFFF"}},
    }


def insight_card(title: str, message: str, kind: str = "") -> None:
    st.markdown(
        f'<div class="insight {kind}"><div class="insight-title">{title}</div>'
        f'<div class="insight-copy">{message}</div></div>',
        unsafe_allow_html=True,
    )


def make_insights(data: pd.DataFrame, columns: dict[str, Any | None]) -> list[tuple[str, str, str]]:
    insights: list[tuple[str, str, str]] = []
    if "_revenue" in data and data["_revenue"].notna().any():
        revenue = data["_revenue"].fillna(0)
        for column_name, label in [("_category", "segment"), ("_channel", "channel")]:
            if column_name not in data or data[column_name].nunique(dropna=True) < 2:
                continue
            grouped = data.assign(_revenue_for_insight=revenue).groupby(column_name, dropna=True)[
                "_revenue_for_insight"
            ].sum().sort_values(ascending=False)
            if not grouped.empty:
                leader = str(grouped.index[0])
                leader_value = float(grouped.iloc[0])
                share = leader_value / max(float(grouped.sum()), 1)
                insights.append(
                    (
                        "Top-performing " + label,
                        f"{leader} contributes {share:.0%} of filtered revenue ({fmt_money(leader_value)}). "
                        "Review what is driving its results before scaling similar activity.",
                        "positive",
                    )
                )

        if "_ad_spend" in data and data["_ad_spend"].fillna(0).sum() > 0 and "_channel" in data:
            channel_summary = data.groupby("_channel", dropna=True).agg(
                revenue=("_revenue", "sum"), spend=("_ad_spend", "sum")
            )
            channel_summary = channel_summary[channel_summary["spend"] > 0]
            if len(channel_summary) >= 2:
                channel_summary["roas"] = channel_summary["revenue"] / channel_summary["spend"]
                weakest = channel_summary["roas"].idxmin()
                strongest = channel_summary["roas"].idxmax()
                if channel_summary.loc[weakest, "roas"] < channel_summary["roas"].median():
                    insights.append(
                        (
                            "Review paid efficiency",
                            f"{weakest} has the lowest revenue-to-spend ratio "
                            f"({channel_summary.loc[weakest, 'roas']:.2f}×), while {strongest} leads at "
                            f"{channel_summary.loc[strongest, 'roas']:.2f}×. Check targeting and budget allocation.",
                            "warning",
                        )
                    )

    if "_orders" in data and "_sessions" in data:
        sessions = data["_sessions"].fillna(0).sum()
        orders = data["_orders"].fillna(0).sum()
        rate = orders / sessions if sessions > 0 else 0
        if sessions > 0:
            if rate < 0.02:
                insights.append(
                    (
                        "Conversion opportunity",
                        f"The overall conversion rate is {rate:.1%}. Review landing-page relevance and the steps "
                        "between discovery and purchase.",
                        "warning",
                    )
                )
            elif rate >= 0.05:
                insights.append(
                    (
                        "Strong conversion",
                        f"The overall conversion rate is {rate:.1%}. Identify the best-performing journeys and "
                        "apply those patterns to lower-converting segments.",
                        "positive",
                    )
                )

    if "_date" in data and "_revenue" in data:
        monthly = data.dropna(subset=["_date"]).copy()
        monthly["_month"] = monthly["_date"].dt.to_period("M")
        totals = monthly.groupby("_month")["_revenue"].sum().sort_index()
        if len(totals) >= 2 and totals.iloc[-2] != 0:
            growth = (totals.iloc[-1] / totals.iloc[-2]) - 1
            if growth <= -0.05:
                insights.append(
                    (
                        "Revenue trend needs attention",
                        f"Revenue fell {abs(growth):.1%} from {totals.index[-2]} to {totals.index[-1]}. "
                        "Compare recent mix, channel results, and any changes in demand.",
                        "warning",
                    )
                )
            elif growth >= 0.1:
                insights.append(
                    (
                        "Revenue momentum",
                        f"Revenue increased {growth:.1%} from {totals.index[-2]} to {totals.index[-1]}. "
                        "Check whether the increase is broad-based or concentrated in one segment.",
                        "positive",
                    )
                )

    if not insights:
        insights.append(
            (
                "More data, clearer recommendations",
                "Add date, revenue, and category or channel fields to surface specific performance patterns.",
                "",
            )
        )
    return insights[:5]


def main() -> None:
    if "theme" not in st.session_state:
        st.session_state.theme = "Dark"

    st.markdown(theme_css(st.session_state.theme), unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### NORTHSTAR")
        st.caption("Data analytics & strategic insights")
        st.divider()
        st.markdown("#### Choose your data")
        source_mode = st.radio(
            "Data source",
            ["Sample dataset", "Upload CSV"],
            horizontal=False,
            label_visibility="collapsed",
        )
        sample_name = "Retail sales"
        uploaded_file = None
        if source_mode == "Sample dataset":
            sample_name = st.selectbox(
                "Sample dataset",
                ["Retail sales", "Marketing campaigns", "SaaS subscriptions"],
            )
            samples = build_sample_data()
            raw_data = samples[sample_name].copy()
            st.caption(
                {
                    "Retail sales": "Orders, revenue, products, and acquisition channels.",
                    "Marketing campaigns": "Campaign reach, clicks, conversions, spend, and revenue.",
                    "SaaS subscriptions": "Plan performance, acquisition, subscribers, and recurring revenue.",
                }[sample_name]
            )
        else:
            uploaded_file = st.file_uploader("Upload a .csv file", type=["csv"])
            raw_data = pd.DataFrame()
            if uploaded_file is not None:
                try:
                    raw_data = pd.read_csv(uploaded_file)
                except Exception as error:
                    st.error(f"Could not read this CSV: {error}")
                    st.stop()
            else:
                st.info("Upload a CSV to explore your own data.")

        st.divider()
        st.markdown("#### Display")
        light_mode = st.toggle("Light mode", value=st.session_state.theme == "Light")
        selected_theme = "Light" if light_mode else "Dark"
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
        st.caption("CSV files are analyzed in this session and are not saved.")

    title = "Your data, in focus."
    subtitle = "A clear view of performance, momentum, and where to act next."
    left, right = st.columns([5, 1.25], vertical_alignment="center")
    with left:
        st.markdown(
            f'<div class="hero-kicker">NORTHSTAR / STRATEGY OVERVIEW</div>'
            f'<h1 class="hero-title">{title}</h1>'
            f'<p class="hero-subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div style="text-align:right;padding-top:12px">'
            f'<span class="source-chip">{source_mode}: {sample_name if source_mode == "Sample dataset" else uploaded_file.name if uploaded_file else "Waiting for file"}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if raw_data.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Choose a sample dataset or upload a CSV to start exploring.")
        return

    if len(raw_data) == 0 or len(raw_data.columns) == 0:
        st.warning("This CSV has no data rows. Please upload a file with a header and at least one row.")
        return

    data, columns = prepare_data(raw_data)
    st.markdown(
        f'<p class="data-note">{len(data):,} rows · {len(raw_data.columns)} columns</p>',
        unsafe_allow_html=True,
    )
    if columns["revenue"] is None:
        st.warning(
            "A revenue field was not detected. Add a column named revenue, sales, amount, or MRR "
            "to enable revenue KPIs and trend charts."
        )

    if "_date" in data:
        data = data.dropna(subset=["_date"])
        if data.empty:
            st.error("No valid dates were found in the selected date column.")
            return

    filter_columns = st.columns([1.4, 1.4, 1.2], vertical_alignment="bottom")
    filtered = data.copy()
    with filter_columns[0]:
        if "_date" in filtered:
            min_date = filtered["_date"].min().date()
            max_date = filtered["_date"].max().date()
            selected_dates = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                filtered = filtered[
                    (filtered["_date"].dt.date >= selected_dates[0])
                    & (filtered["_date"].dt.date <= selected_dates[1])
                ]
        else:
            st.caption("No date field detected")
    with filter_columns[1]:
        category_col = columns["category"]
        if category_col is not None and filtered[category_col].nunique(dropna=True) > 1:
            options = sorted(filtered[category_col].dropna().astype(str).unique().tolist())
            selected_categories = st.multiselect("Segment", options, default=options)
            filtered = filtered[filtered[category_col].astype(str).isin(selected_categories)]
            filtered["_category"] = filtered[category_col].astype(str)
        elif category_col is not None:
            filtered["_category"] = filtered[category_col].astype(str)
            st.caption(f"Segment: {filtered[category_col].iloc[0]}")
        else:
            st.caption("No segment field detected")
    with filter_columns[2]:
        channel_col = columns["channel"]
        if channel_col is not None and filtered[channel_col].nunique(dropna=True) > 1:
            options = sorted(filtered[channel_col].dropna().astype(str).unique().tolist())
            selected_channels = st.multiselect("Channel", options, default=options)
            filtered = filtered[filtered[channel_col].astype(str).isin(selected_channels)]
            filtered["_channel"] = filtered[channel_col].astype(str)
        elif channel_col is not None:
            filtered["_channel"] = filtered[channel_col].astype(str)
            st.caption(f"Channel: {filtered[channel_col].iloc[0]}")
        else:
            st.caption("No channel field detected")

    if category_col is not None and "_category" not in filtered:
        filtered["_category"] = filtered[category_col].astype(str)
    if channel_col is not None and "_channel" not in filtered:
        filtered["_channel"] = filtered[channel_col].astype(str)

    if filtered.empty:
        st.info("No rows match the selected filters. Adjust the filters to see your data.")
        return

    revenue_total = filtered["_revenue"].fillna(0).sum() if "_revenue" in filtered else np.nan
    orders_total = filtered["_orders"].fillna(0).sum() if "_orders" in filtered else np.nan
    sessions_total = filtered["_sessions"].fillna(0).sum() if "_sessions" in filtered else np.nan
    aov = revenue_total / orders_total if orders_total and not pd.isna(revenue_total) else np.nan
    conversion = orders_total / sessions_total if sessions_total and not pd.isna(orders_total) else np.nan
    if pd.isna(conversion) and "_conversion_rate" in filtered:
        conversion_values = filtered["_conversion_rate"].dropna()
        if not conversion_values.empty:
            conversion = float(conversion_values.mean())

    growth = np.nan
    growth_note = "Needs two months of data"
    if "_date" in filtered and "_revenue" in filtered:
        monthly = filtered.dropna(subset=["_date"]).copy()
        monthly["_month"] = monthly["_date"].dt.to_period("M")
        revenue_by_month = monthly.groupby("_month")["_revenue"].sum().sort_index()
        if len(revenue_by_month) >= 2 and revenue_by_month.iloc[-2] != 0:
            growth = revenue_by_month.iloc[-1] / revenue_by_month.iloc[-2] - 1
            growth_note = f"vs. {revenue_by_month.index[-2]}"

    st.markdown('<div class="section-label">Performance snapshot</div>', unsafe_allow_html=True)
    kpis = st.columns(4)
    kpis[0].metric("Total revenue", fmt_money(revenue_total), help="Sum of the detected revenue field in the filtered data.")
    kpis[1].metric("Average order value", fmt_money(aov), help="Total revenue divided by detected orders or conversions.")
    kpis[2].metric(
        "Conversion rate",
        f"{conversion:.1%}" if not pd.isna(conversion) else "—",
        help="Detected orders or conversions divided by sessions, visits, clicks, or traffic.",
    )
    kpis[3].metric(
        "Month-over-month growth",
        f"{growth:+.1%}" if not pd.isna(growth) else "—",
        delta=growth_note if not pd.isna(growth) else None,
        delta_color="normal",
        help="Revenue change between the two most recent months in the filtered date range.",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Explore performance</div>', unsafe_allow_html=True)
    chart_columns = st.columns([1.45, 1, 1])

    if "_date" in filtered and "_revenue" in filtered:
        trend = filtered.dropna(subset=["_date"]).copy()
        trend["_month"] = trend["_date"].dt.to_period("M").dt.to_timestamp()
        if "_category" in trend:
            trend_grouped = trend.groupby(["_month", "_category"], as_index=False)["_revenue"].sum()
            trend_fig = px.line(
                trend_grouped,
                x="_month",
                y="_revenue",
                color="_category",
                markers=True,
                color_discrete_sequence=[PALETTE["accent"], PALETTE["accent_2"], "#D28CE5", PALETTE["warning"]],
            )
        else:
            trend_grouped = trend.groupby("_month", as_index=False)["_revenue"].sum()
            trend_fig = px.line(trend_grouped, x="_month", y="_revenue", markers=True)
        trend_fig.update_layout(**chart_layout(st.session_state.theme, "Revenue over time"))
        trend_fig.update_yaxes(title=None, tickprefix="$", separatethousands=True)
        trend_fig.update_xaxes(title=None)
        with chart_columns[0]:
            st.plotly_chart(trend_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        with chart_columns[0]:
            st.info("A valid date and revenue field are needed for the trend chart.")

    if "_category" in filtered and "_revenue" in filtered:
        category_totals = (
            filtered.groupby("_category", as_index=False)["_revenue"]
            .sum()
            .sort_values("_revenue", ascending=True)
        )
        category_fig = px.bar(
            category_totals,
            x="_revenue",
            y="_category",
            orientation="h",
            color="_revenue",
            color_continuous_scale=[PALETTE["accent"], PALETTE["accent_2"]],
        )
        category_fig.update_layout(**chart_layout(st.session_state.theme, "Revenue by segment"))
        category_fig.update_layout(coloraxis_showscale=False)
        category_fig.update_xaxes(title=None, tickprefix="$")
        category_fig.update_yaxes(title=None)
        with chart_columns[1]:
            st.plotly_chart(category_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        with chart_columns[1]:
            st.info("Add a category, product, segment, plan, or campaign field for a breakdown.")

    x_metric = "_ad_spend" if "_ad_spend" in filtered and filtered["_ad_spend"].notna().any() else "_sessions"
    x_label = "Ad spend" if x_metric == "_ad_spend" else "Traffic"
    y_metric = "_revenue" if "_revenue" in filtered else "_orders" if "_orders" in filtered else None
    if y_metric is not None and x_metric in filtered and filtered[x_metric].notna().any():
        scatter_data = filtered.dropna(subset=[x_metric, y_metric]).copy()
        color_arg = "_channel" if "_channel" in scatter_data else None
        scatter_fig = px.scatter(
            scatter_data,
            x=x_metric,
            y=y_metric,
            color=color_arg,
            size="_orders" if "_orders" in scatter_data and y_metric != "_orders" else None,
            hover_name="_category" if "_category" in scatter_data else None,
            color_discrete_sequence=[PALETTE["accent"], PALETTE["accent_2"], "#D28CE5", PALETTE["warning"]],
            opacity=0.78,
        )
        scatter_fig.update_layout(**chart_layout(st.session_state.theme, "Spend & performance correlation"))
        scatter_fig.update_xaxes(title=x_label, tickprefix="$" if x_metric == "_ad_spend" else "")
        scatter_fig.update_yaxes(
            title="Revenue" if y_metric == "_revenue" else "Orders / conversions",
            tickprefix="$" if y_metric == "_revenue" else "",
        )
        with chart_columns[2]:
            st.plotly_chart(scatter_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        with chart_columns[2]:
            st.info("Add traffic and performance metrics to explore their relationship.")

    st.markdown("<br>", unsafe_allow_html=True)
    insights_col, data_col = st.columns([1, 1.35])
    with insights_col:
        st.markdown('<div class="section-label">Strategic insights</div>', unsafe_allow_html=True)
        for title_text, message, kind in make_insights(filtered, columns):
            insight_card(title_text, message, kind)

    with data_col:
        st.markdown('<div class="section-label">Data preview</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("First 8 rows after filters")
            st.dataframe(
                filtered.drop(columns=["_date", "_revenue", "_orders", "_sessions", "_ad_spend"], errors="ignore")
                .head(8),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("How these metrics are calculated"):
                st.markdown(
                    """
                    - **Revenue:** sum of the detected revenue, sales, amount, or MRR column.
                    - **Average order value:** revenue divided by orders, transactions, or conversions.
                    - **Conversion rate:** orders or conversions divided by sessions, visits, clicks, or traffic.
                    - **Month-over-month growth:** latest month’s revenue compared with the prior available month.
                    - **Strategic insights:** rule-based signals from filtered segment performance, revenue trends, and spend efficiency.
                    """
                )


if __name__ == "__main__":
    main()
