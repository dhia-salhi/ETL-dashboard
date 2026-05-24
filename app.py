"""
app.py — Business Analytics Dashboard (Enhanced Edition)
=========================================================
Run with:  streamlit run app.py

Enhancements v3:
  - Vivid multi-stop gradient palette (violet → indigo → cyan → emerald)
  - Animated gradient mesh background
  - CSS counter animation on KPI values (fade + slide-up on load)
  - Glowing accent borders, shimmer effects on cards
  - Chart bars rendered with gradient colors via Plotly colorscales
  - Sidebar collapse bug fixed: toggle button always visible via forced CSS
  - Glassmorphism sidebar with backdrop-filter
  - Animated live-dot pulse in header badge
  - Smooth page-load stagger for all cards
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────── PAGE CONFIG ──────────────────────────────────────

st.set_page_config(
    page_title="BizAnalytics · Dashboard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── DESIGN TOKENS ────────────────────────────────────

# Core palette — vivid but tasteful
VIOLET      = "#7c3aed"
INDIGO      = "#6366f1"
INDIGO_DIM  = "#4f46e5"
CYAN        = "#06b6d4"
TEAL        = "#14b8a6"
EMERALD     = "#10b981"
ROSE        = "#f43f5e"
AMBER       = "#f59e0b"

# Surfaces (true dark, slight blue tint)
BG          = "#080810"
SURFACE_1   = "#0e0e1a"   # sidebar
SURFACE_2   = "#13131f"   # card bg
SURFACE_3   = "#1c1c2e"   # input / hover
SURFACE_4   = "#252540"   # active states

# Borders
BORDER      = "#252538"
BORDER_MID  = "#333355"
BORDER_HI   = "#4444aa"

# Text
TEXT_HI     = "#f0f0ff"
TEXT_MID    = "#9090c0"
TEXT_LO     = "#55556a"

# Chart palette list
CHART_COLORS = [INDIGO, CYAN, EMERALD, VIOLET, ROSE, AMBER, TEAL]

# Plotly base layout
PLOT_LAYOUT = dict(
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    font          = dict(family="DM Sans, sans-serif", color=TEXT_MID, size=12),
    margin        = dict(l=4, r=4, t=40, b=4),
    hoverlabel    = dict(
        bgcolor     = SURFACE_4,
        bordercolor = BORDER_HI,
        font_color  = TEXT_HI,
        font_size   = 13,
    ),
    title_font    = dict(size=14, color=TEXT_HI, family="DM Sans, sans-serif"),
    colorway      = CHART_COLORS,
)

LEGEND_STYLE = dict(
    orientation="h", yanchor="bottom", y=1.08,
    xanchor="right", x=1, font_size=11,
    bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
)

AXIS_STYLE = dict(
    showgrid   = True,
    gridcolor  = BORDER,
    gridwidth  = 1,
    zeroline   = False,
    linecolor  = BORDER,
    tickcolor  = BORDER_MID,
    tickfont   = dict(size=11, color=TEXT_MID),
)
AXIS_NOGRID = {**AXIS_STYLE, "showgrid": False}

# ─────────────────────────── GLOBAL CSS ───────────────────────────────────────

st.markdown(f"""
<style>
/* ── Fonts ────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset ────────────────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
}}

/* ── Animated gradient mesh background ────────────────────────────────────── */
.stApp {{
    background-color: {BG};
    background-image:
        radial-gradient(ellipse 80% 50% at 10% 0%,   rgba(99,102,241,.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 10%,  rgba(6,182,212,.12)  0%, transparent 55%),
        radial-gradient(ellipse 50% 60% at 50% 100%, rgba(16,185,129,.08) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 80% 60%,  rgba(124,58,237,.10) 0%, transparent 50%);
    color: {TEXT_HI};
    animation: bgShift 18s ease-in-out infinite alternate;
}}

@keyframes bgShift {{
    0%   {{ background-position: 0% 0%, 100% 0%, 50% 100%, 80% 60%; }}
    100% {{ background-position: 5% 5%,  95% 5%,  55%  95%, 75% 55%; }}
}}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {SURFACE_1} 0%, rgba(8,8,20,.97) 100%);
    border-right: 1px solid {BORDER_MID};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}}

section[data-testid="stSidebar"] > div {{
    padding-top: 0 !important;
}}

/* ── Hide Streamlit chrome ────────────────────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer     {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* Keep the header transparent — do NOT hide it or the sidebar toggle dies.  */
header[data-testid="stHeader"] {{
    background: transparent !important;
    border-bottom: none !important;
    height: 3.5rem !important;
}}

/* Style Streamlit's native sidebar toggle to look like our design system.   */
/* This button is rendered by Streamlit and always works — we just restyle it.*/
[data-testid="stSidebarCollapsedControl"] {{
    background: #1c1c2e !important;
    border: 1px solid #333355 !important;
    border-radius: 10px !important;
    width: 38px !important;
    height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(0,0,0,.5) !important;
    transition: background .2s, border-color .2s, box-shadow .2s !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
}}
[data-testid="stSidebarCollapsedControl"]:hover {{
    background: #252540 !important;
    border-color: #6366f1 !important;
    box-shadow: 0 0 18px rgba(99,102,241,.55) !important;
}}
[data-testid="stSidebarCollapsedControl"] svg {{
    fill: #f0f0ff !important;
    color: #f0f0ff !important;
    visibility: visible !important;
    opacity: 1 !important;
}}
/* Also handle the expand button inside sidebar (the >>> when open) */
[data-testid="stSidebar"] button[kind="header"],
[data-testid="stSidebar"] [data-testid="stBaseButton-header"] {{
    background: #1c1c2e !important;
    border: 1px solid #333355 !important;
    border-radius: 10px !important;
    color: #f0f0ff !important;
    visibility: visible !important;
    opacity: 1 !important;
}}

/* ── Page load animation ──────────────────────────────────────────────────── */
@keyframes fadeSlideUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}

/* ── KPI cards ────────────────────────────────────────────────────────────── */
.kpi-card {{
    background: linear-gradient(135deg, {SURFACE_2} 0%, rgba(19,19,35,.9) 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 22px 20px 20px;
    position: relative;
    overflow: hidden;
    cursor: default;
    animation: fadeSlideUp .55s cubic-bezier(.22,1,.36,1) both;
    transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
}}

/* staggered load delay per card */
.kpi-card:nth-child(1) {{ animation-delay: .05s; }}
.kpi-card:nth-child(2) {{ animation-delay: .10s; }}
.kpi-card:nth-child(3) {{ animation-delay: .15s; }}
.kpi-card:nth-child(4) {{ animation-delay: .20s; }}
.kpi-card:nth-child(5) {{ animation-delay: .25s; }}
.kpi-card:nth-child(6) {{ animation-delay: .30s; }}

/* Top accent line */
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent-line, linear-gradient(90deg, {INDIGO}, {CYAN}));
    opacity: 0;
    transition: opacity .3s ease;
}}

/* Shimmer sweep on hover */
.kpi-card::after {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(105deg,
        transparent 40%,
        rgba(255,255,255,.04) 50%,
        transparent 60%);
    transform: translateX(-100%);
    transition: transform .6s ease;
}}

.kpi-card:hover {{
    border-color: {BORDER_HI};
    box-shadow:
        0 0 0 1px rgba(99,102,241,.2),
        0 8px 32px rgba(0,0,0,.45),
        0 0 40px rgba(99,102,241,.08);
    transform: translateY(-3px);
}}
.kpi-card:hover::before {{ opacity: 1; }}
.kpi-card:hover::after  {{ transform: translateX(100%); }}

.kpi-icon {{
    font-size: 1.1rem;
    background: {SURFACE_3};
    border: 1px solid {BORDER_MID};
    border-radius: 10px;
    padding: 7px 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
    line-height: 1;
}}

.kpi-label {{
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: {TEXT_MID};
    margin: 0 0 8px;
}}

.kpi-value {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {TEXT_HI};
    line-height: 1.05;
    letter-spacing: -.03em;
    animation: fadeSlideUp .6s cubic-bezier(.22,1,.36,1) both;
}}

/* ── Section headers ──────────────────────────────────────────────────────── */
.section-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 36px 0 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid {BORDER};
    animation: fadeIn .5s ease both;
}}

.section-header-icon {{
    font-size: 0.95rem;
    background: linear-gradient(135deg, {SURFACE_3}, {SURFACE_4});
    border: 1px solid {BORDER_MID};
    border-radius: 9px;
    padding: 6px 8px;
    line-height: 1;
    box-shadow: 0 2px 8px rgba(0,0,0,.3);
}}

.section-header-text {{
    font-size: 1rem;
    font-weight: 700;
    color: {TEXT_HI};
    letter-spacing: -.02em;
}}

/* ── Page header ──────────────────────────────────────────────────────────── */
.page-header {{
    padding: 30px 0 22px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 4px;
    animation: fadeSlideUp .5s ease both;
}}

.page-title {{
    font-size: 2rem;
    font-weight: 800;
    color: {TEXT_HI};
    letter-spacing: -.04em;
    margin: 0;
    line-height: 1.1;
    background: linear-gradient(120deg, {TEXT_HI} 0%, #a5b4fc 60%, {CYAN} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.page-subtitle {{
    font-size: 0.9rem;
    color: {TEXT_MID};
    margin-top: 7px;
    line-height: 1.5;
}}

/* ── Animated live badge ──────────────────────────────────────────────────── */
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(99,102,241,.1);
    border: 1px solid rgba(99,102,241,.3);
    color: #a5b4fc;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 20px;
    padding: 4px 12px;
    letter-spacing: .03em;
    margin-top: 12px;
}}

.badge-dot {{
    width: 7px;
    height: 7px;
    background: {EMERALD};
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 6px {EMERALD};
    animation: pulseDot 2s ease infinite;
}}

@keyframes pulseDot {{
    0%, 100% {{ transform: scale(1);   box-shadow: 0 0 6px {EMERALD}; }}
    50%       {{ transform: scale(.7); box-shadow: 0 0 2px {EMERALD}; }}
}}

/* ── Sidebar brand ────────────────────────────────────────────────────────── */
.sidebar-brand {{
    padding: 24px 4px 20px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 4px;
}}

.sidebar-brand-logo {{
    font-size: 1.25rem;
    font-weight: 800;
    color: {TEXT_HI};
    letter-spacing: -.03em;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.sidebar-brand-tile {{
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, {VIOLET} 0%, {INDIGO} 50%, {CYAN} 100%);
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(99,102,241,.4);
    animation: glowPulse 3s ease infinite alternate;
}}

@keyframes glowPulse {{
    from {{ box-shadow: 0 4px 16px rgba(99,102,241,.4); }}
    to   {{ box-shadow: 0 4px 24px rgba(6,182,212,.5); }}
}}

.sidebar-brand-sub {{
    font-size: 0.73rem;
    color: {TEXT_LO};
    margin-top: 5px;
    padding-left: 42px;
    letter-spacing: .01em;
}}

/* ── Sidebar labels ───────────────────────────────────────────────────────── */
.sidebar-label {{
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
    color: {TEXT_LO};
    margin: 22px 0 8px;
    padding: 0 2px;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.sidebar-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: {BORDER};
}}

/* ── Sidebar footer ───────────────────────────────────────────────────────── */
.sidebar-footer {{
    font-size: 0.7rem;
    color: {TEXT_LO};
    text-align: center;
    padding: 16px 4px;
    border-top: 1px solid {BORDER};
    margin-top: 24px;
    line-height: 1.7;
}}

/* ── Streamlit widget overrides ───────────────────────────────────────────── */
div[data-testid="stMultiSelect"] > div > div {{
    background: {SURFACE_3} !important;
    border-color: {BORDER_MID} !important;
    border-radius: 10px !important;
    color: {TEXT_HI} !important;
    transition: border-color .2s !important;
}}
div[data-testid="stMultiSelect"] > div > div:focus-within {{
    border-color: {INDIGO} !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important;
}}

div[data-testid="stDateInput"] input {{
    background: {SURFACE_3} !important;
    border-color: {BORDER_MID} !important;
    border-radius: 10px !important;
    color: {TEXT_HI} !important;
}}

div[data-testid="stExpander"] {{
    background: {SURFACE_2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    overflow: hidden;
    transition: border-color .2s !important;
}}
div[data-testid="stExpander"]:hover {{
    border-color: {BORDER_MID} !important;
}}
div[data-testid="stExpander"] summary {{
    color: {TEXT_HI} !important;
    font-weight: 500 !important;
    padding: 14px 16px !important;
}}

.stDownloadButton > button {{
    background: {SURFACE_3} !important;
    border: 1px solid {BORDER_MID} !important;
    color: {TEXT_HI} !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 9px 18px !important;
    letter-spacing: .01em !important;
    transition: all .2s ease !important;
}}
.stDownloadButton > button:hover {{
    background: linear-gradient(135deg, {INDIGO_DIM}, {INDIGO}) !important;
    border-color: {INDIGO} !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(99,102,241,.35) !important;
    transform: translateY(-1px) !important;
}}

div[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {BORDER} !important;
}}

/* Warning */
div[data-testid="stAlert"] {{
    background: rgba(245,158,11,.07) !important;
    border: 1px solid rgba(245,158,11,.25) !important;
    border-radius: 12px !important;
    color: {AMBER} !important;
}}

/* HR */
hr {{
    border-color: {BORDER} !important;
    margin: 28px 0 !important;
}}

/* Slider thumb */
.stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {{
    background: {INDIGO} !important;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── DATA ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data():
    conn        = sqlite3.connect("data.db")
    df_products = pd.read_sql("SELECT * FROM products", conn)
    df_orders   = pd.read_sql("SELECT * FROM orders",   conn)
    conn.close()
    df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
    return df_products, df_orders

with st.spinner("Loading data…"):
    df_products, df_orders = load_data()

# ─────────────────────────── SIDEBAR ──────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <div class="sidebar-brand-logo">
        <span class="sidebar-brand-tile">◈</span> BizAnalytics
      </div>
      <div class="sidebar-brand-sub">Sales Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Category</div>', unsafe_allow_html=True)
    all_cats = sorted(df_orders["category"].dropna().unique().tolist())
    selected_categories = st.multiselect(
        label="Product Category",
        options=all_cats,
        default=all_cats,
        help="Filter by one or more product categories",
        placeholder="Choose categories…",
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-label">Date Range</div>', unsafe_allow_html=True)
    min_date = df_orders["order_date"].min().date()
    max_date = df_orders["order_date"].max().date()
    date_range = st.date_input(
        label="Order Date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-label">Quality Filter</div>', unsafe_allow_html=True)
    min_rating = st.slider(
        "Min Rating",
        min_value=1.0, max_value=5.0,
        value=1.0, step=0.1,
        label_visibility="collapsed",
    )

    st.markdown("""
    <div class="sidebar-footer">
        Data source · DummyJSON API<br>
        Updated on last ETL run
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────── GUARDS ───────────────────────────────────────────

if not selected_categories:
    st.warning("Select at least one category from the sidebar to load the dashboard.")
    st.stop()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0] if date_range else min_date

# ─────────────────────────── FILTER ───────────────────────────────────────────

filtered_orders = df_orders[
    (df_orders["category"].isin(selected_categories)) &
    (df_orders["order_date"].dt.date >= start_date) &
    (df_orders["order_date"].dt.date <= end_date)
]
filtered_products = df_products[df_products["avg_rating"] >= min_rating]

# ─────────────────────────── PAGE HEADER ──────────────────────────────────────

st.markdown(f"""
<div class="page-header">
  <h1 class="page-title">Business Analytics</h1>
  <p class="page-subtitle">
    Real-time sales overview &nbsp;·&nbsp;
    {start_date.strftime("%b %d, %Y")} – {end_date.strftime("%b %d, %Y")}
  </p>
  <div class="badge"><span class="badge-dot"></span> Live data</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────── KPI METRICS ──────────────────────────────────────

total_revenue    = filtered_orders["revenue"].sum()
total_profit     = filtered_orders["profit"].sum()
total_orders     = filtered_orders["order_id"].nunique()
total_units_sold = filtered_orders["quantity"].sum()
avg_rating       = filtered_products["avg_rating"].mean()
avg_discount     = filtered_products["discount_pct"].mean()

# Each card gets a unique accent-line gradient via CSS custom property
KPI_ACCENTS = [
    f"linear-gradient(90deg, {INDIGO}, {VIOLET})",
    f"linear-gradient(90deg, {EMERALD}, {CYAN})",
    f"linear-gradient(90deg, {CYAN}, {INDIGO})",
    f"linear-gradient(90deg, {VIOLET}, {ROSE})",
    f"linear-gradient(90deg, {AMBER}, {ROSE})",
    f"linear-gradient(90deg, {TEAL}, {EMERALD})",
]

def kpi_card(icon, label, value, accent):
    return f"""
    <div class="kpi-card" style="--accent-line:{accent}">
        <div class="kpi-icon">{icon}</div>
        <p class="kpi-label">{label}</p>
        <div class="kpi-value">{value}</div>
    </div>"""

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

kpi_data = [
    ("💰", "Total Revenue",  f"${total_revenue:,.0f}"),
    ("📈", "Est. Profit",    f"${total_profit:,.0f}"),
    ("🛒", "Total Orders",   f"{total_orders:,}"),
    ("📦", "Units Sold",     f"{total_units_sold:,}"),
    ("⭐", "Avg Rating",     f"{avg_rating:.2f} / 5"),
    ("🏷️", "Avg Discount",  f"{avg_discount:.1f}%"),
]

cols = st.columns(6, gap="small")
for col, (icon, label, value), accent in zip(cols, kpi_data, KPI_ACCENTS):
    with col:
        st.markdown(kpi_card(icon, label, value, accent), unsafe_allow_html=True)

# ─────────────────────────── HELPERS ──────────────────────────────────────────

def section_header(icon, title):
    st.markdown(f"""
    <div class="section-header">
      <span class="section-header-icon">{icon}</span>
      <span class="section-header-text">{title}</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────── REVENUE ANALYSIS ─────────────────────────────────

section_header("📊", "Revenue Analysis")

rev_col1, rev_col2 = st.columns([1, 1.65], gap="medium")

with rev_col1:
    cat_revenue = (
        filtered_orders
        .groupby("category")["revenue"].sum()
        .reset_index()
        .sort_values("revenue", ascending=True)
        .rename(columns={"revenue": "Revenue ($)", "category": "Category"})
    )
    n = len(cat_revenue)
    # gradient colorscale: violet → indigo → cyan
    bar_colors = [
        f"hsl({int(260 + 80 * i / max(n-1,1))}, 80%, {55 + 10 * i / max(n-1,1):.0f}%)"
        for i in range(n)
    ]

    fig_bar = go.Figure(go.Bar(
        x=cat_revenue["Revenue ($)"],
        y=cat_revenue["Category"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=cat_revenue["Revenue ($)"].apply(lambda v: f"${v/1e3:.1f}K"),
        textposition="inside",
        textfont=dict(color=TEXT_HI, size=11),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>",
    ))
    fig_bar.update_layout(**PLOT_LAYOUT, height=310, title_text="Revenue by Category")
    fig_bar.update_xaxes(**AXIS_STYLE)
    fig_bar.update_yaxes(**AXIS_NOGRID)
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

with rev_col2:
    daily = (
        filtered_orders
        .groupby(filtered_orders["order_date"].dt.date)["revenue"].sum()
        .reset_index()
        .rename(columns={"order_date": "Date", "revenue": "Daily Revenue ($)"})
    )
    daily["7-Day Avg"] = daily["Daily Revenue ($)"].rolling(7).mean()

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Daily Revenue ($)"],
        name="Daily", mode="lines",
        line=dict(color=f"rgba(99,102,241,.4)", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,.07)",
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig_line.add_trace(go.Scatter(
        x=daily["Date"], y=daily["7-Day Avg"],
        name="7-Day Avg", mode="lines",
        line=dict(color=CYAN, width=2.5),
        hovertemplate="<b>%{x}</b><br>7-Day Avg: $%{y:,.0f}<extra></extra>",
    ))
    fig_line.update_layout(**PLOT_LAYOUT, height=310,
                           title_text="Daily Revenue Trend", legend=LEGEND_STYLE)
    fig_line.update_xaxes(**AXIS_NOGRID)
    fig_line.update_yaxes(**AXIS_STYLE)
    st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────── PRODUCT INTELLIGENCE ─────────────────────────────

section_header("🏆", "Product Intelligence")

prod_col1, prod_col2 = st.columns([1.65, 1], gap="medium")

with prod_col1:
    top_products = (
        filtered_orders.groupby("product_name")["revenue"].sum()
        .reset_index().sort_values("revenue", ascending=False).head(10)
        .sort_values("revenue", ascending=True)
        .rename(columns={"revenue": "Revenue ($)", "product_name": "Product"})
    )
    n2 = len(top_products)
    top_colors = [
        f"hsl({int(170 + 60 * i / max(n2-1,1))}, 75%, {50 + 12 * i / max(n2-1,1):.0f}%)"
        for i in range(n2)
    ]
    fig_top = go.Figure(go.Bar(
        x=top_products["Revenue ($)"],
        y=top_products["Product"],
        orientation="h",
        marker=dict(color=top_colors, line=dict(width=0)),
        text=top_products["Revenue ($)"].apply(lambda v: f"${v/1e3:.1f}K"),
        textposition="inside",
        textfont=dict(color=TEXT_HI, size=11),
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
    ))
    fig_top.update_layout(**PLOT_LAYOUT, height=330, title_text="Top 10 Products by Revenue")
    fig_top.update_xaxes(**AXIS_STYLE)
    fig_top.update_yaxes(**AXIS_NOGRID)
    st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})

with prod_col2:
    fig_scatter = px.scatter(
        filtered_products,
        x="price_usd", y="avg_rating",
        color="category", size="units_in_stock",
        hover_name="product_name",
        title="Price vs. Rating",
        labels={"price_usd": "Price (USD)", "avg_rating": "Rating",
                "units_in_stock": "Stock", "category": ""},
        opacity=0.8,
        color_discrete_sequence=CHART_COLORS,
    )
    fig_scatter.update_layout(**PLOT_LAYOUT, height=330,
                              legend={**LEGEND_STYLE, "font_size": 10})
    fig_scatter.update_xaxes(**AXIS_STYLE)
    fig_scatter.update_yaxes(**AXIS_STYLE)
    fig_scatter.update_traces(
        marker=dict(line=dict(width=0)),
        hovertemplate="<b>%{hovertext}</b><br>$%{x:.0f} · ⭐ %{y:.1f}<extra></extra>",
    )
    st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────── MONTHLY & CATEGORY ───────────────────────────────

section_header("📅", "Monthly & Category Breakdown")

mon_col1, mon_col2 = st.columns([1.65, 1], gap="medium")

with mon_col1:
    monthly = filtered_orders.copy()
    monthly["Month"] = monthly["order_date"].dt.to_period("M").astype(str)
    monthly_summary = (
        monthly.groupby("Month")[["revenue", "profit"]].sum()
        .reset_index()
        .rename(columns={"revenue": "Revenue ($)", "profit": "Profit ($)"})
        .sort_values("Month")
    )
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly_summary["Month"], y=monthly_summary["Revenue ($)"],
        name="Revenue",
        marker=dict(
            color=monthly_summary["Revenue ($)"],
            colorscale=[[0, SURFACE_4], [1, INDIGO]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig_monthly.add_trace(go.Bar(
        x=monthly_summary["Month"], y=monthly_summary["Profit ($)"],
        name="Profit",
        marker=dict(
            color=monthly_summary["Profit ($)"],
            colorscale=[[0, "#0e3d38"], [1, TEAL]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>",
    ))
    fig_monthly.update_layout(
        **PLOT_LAYOUT, height=330,
        title_text="Monthly Performance",
        barmode="group", bargap=0.22, bargroupgap=0.06,
        legend=LEGEND_STYLE,
    )
    fig_monthly.update_xaxes(**AXIS_NOGRID, tickangle=-40)
    fig_monthly.update_yaxes(**AXIS_STYLE)
    st.plotly_chart(fig_monthly, use_container_width=True, config={"displayModeBar": False})

with mon_col2:
    cat_share = (
        filtered_orders.groupby("category")["revenue"].sum()
        .reset_index()
        .rename(columns={"revenue": "Revenue", "category": "Category"})
    )
    fig_donut = px.pie(
        cat_share, values="Revenue", names="Category",
        title="Category Share", hole=0.64,
        color_discrete_sequence=CHART_COLORS,
    )
    fig_donut.update_layout(
        **PLOT_LAYOUT, height=330,
        legend={**LEGEND_STYLE, "xanchor": "center", "x": 0.5, "font_size": 10},
    )
    fig_donut.update_traces(
        textinfo="percent",
        textfont_size=11,
        textfont_color=TEXT_HI,
        marker=dict(line=dict(color=BG, width=3)),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
        pull=[0.04] + [0] * (len(cat_share) - 1),  # slight pull on largest slice
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────── RAW DATA ─────────────────────────────────────────

section_header("🗂️", "Raw Order Data")

with st.expander("Explore filtered order records", expanded=False):
    display_cols = ["order_id", "order_date", "product_name", "category",
                    "brand", "quantity", "unit_price", "revenue", "profit"]
    display_cols = [c for c in display_cols if c in filtered_orders.columns]

    st.dataframe(
        filtered_orders[display_cols]
            .sort_values("order_date", ascending=False)
            .reset_index(drop=True),
        use_container_width=True,
        height=300,
    )
    csv_data = filtered_orders[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download filtered data as CSV",
        data=csv_data,
        file_name="filtered_orders.csv",
        mime="text/csv",
    )

# ─────────────────────────── FOOTER ───────────────────────────────────────────

st.markdown(f"""
<div style='text-align:center; color:{TEXT_LO}; font-size:0.78rem;
            margin-top:56px; padding:20px 0;
            border-top:1px solid {BORDER};
            animation: fadeIn .8s ease both;'>
    Powered by&nbsp;
    <span style='color:{TEXT_MID}; font-weight:600;'>Streamlit</span>
    &amp;
    <span style='color:{TEXT_MID}; font-weight:600;'>Plotly</span>
    &nbsp;·&nbsp; BizAnalytics
</div>
""", unsafe_allow_html=True)