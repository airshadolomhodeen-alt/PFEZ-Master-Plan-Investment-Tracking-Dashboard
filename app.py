import os
import json
import re
import colorsys
import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & EXECUTIVE STYLING
# ==========================================
st.set_page_config(
    page_title="PFEZ Master Development Plan & Technical Capacity Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        /* Base Backgrounds */
        .main { background-color: #0D1117; }
        .block-container { padding-top: 0.8rem; padding-bottom: 1.5rem; padding-left: 1.5rem; padding-right: 1.5rem; }
        h1, h2, h3, h4 { color: #F0F6FC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        
        /* Metric Styling */
        div[data-testid="stMetric"] {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 14px 18px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        div[data-testid="stMetric"] label {
            color: #8B949E !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #58A6FF !important;
            font-size: 22px !important;
            font-weight: 700 !important;
        }

        /* Callout Box */
        .callout-box {
            background: linear-gradient(135deg, #161B22 0%, #1F242C 100%);
            border-left: 4px solid #58A6FF;
            border-top: 1px solid #30363D;
            border-right: 1px solid #30363D;
            border-bottom: 1px solid #30363D;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        /* Phase Card Box */
        .phase-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
        }

        /* Mobile Screen Responsiveness */
        @media (max-width: 768px) {
            .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
            div[data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; margin-bottom: 10px; }
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. EXECUTIVE VISUAL DESIGN SYSTEM & HELPERS
# ==========================================
EXECUTIVE_THEME = {
    "template": "plotly_dark",
    "paper_bgcolor": "#0B0E14",
    "plot_bgcolor": "#0F141D",
    "grid_color": "#2B3245",
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    "color_actual": "#38BDF8",
    "color_ols": "#10B981",
    "color_ma": "#F59E0B",
    "color_target": "#EF4444",
    "color_trad": "#A855F7",
    "color_nontrad": "#F97316",
    "color_bau": "#94A3B8",
    "color_integrated": "#10B981",
    "color_fill_gap": "rgba(16, 185, 129, 0.12)",
    "color_stat_band": "rgba(59, 130, 246, 0.08)",
    "color_stat_line": "rgba(96, 165, 250, 0.4)",
}

def apply_executive_theme(fig, title_text="", subtitle_text="", height=480):
    full_title = f"<b>{title_text}</b>"
    if subtitle_text:
        full_title += f"<br><sup style='color:#8B949E; font-size:12px;'>{subtitle_text}</sup>"

    fig.update_layout(
        template=EXECUTIVE_THEME["template"],
        height=height,
        paper_bgcolor=EXECUTIVE_THEME["paper_bgcolor"],
        plot_bgcolor=EXECUTIVE_THEME["plot_bgcolor"],
        font=dict(family=EXECUTIVE_THEME["font_family"], color="#F0F6FC", size=12),
        title=dict(text=full_title, font=dict(size=18), x=0.0, xanchor="left"),
        margin=dict(l=60, r=200, t=80, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor=EXECUTIVE_THEME["grid_color"],
            gridwidth=0.5,
            tickfont=dict(size=11, color="#8B949E"),
            title_font=dict(size=12, color="#C9D1D9"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=EXECUTIVE_THEME["grid_color"],
            gridwidth=0.5,
            tickfont=dict(size=11, color="#8B949E"),
            title_font=dict(size=12, color="#C9D1D9"),
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            font=dict(size=11, color="#C9D1D9"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig

def configure_modebar():
    return {"displayModeBar": "hover", "responsive": True}

# ==========================================
# 3. DATA LOADERS & DATA PIPELINE
# ==========================================
@st.cache_data
def load_masterplan_data():
    file_path = "MASTERPLAN PROJECTS.csv"
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding="latin1")
        except Exception:
            df = pd.read_csv(file_path, encoding="cp1252")
            
        df.columns = [c.strip() for c in df.columns]
        df['SECTOR'] = df['SECTOR'].str.strip()
        df['CATEGORY'] = df['CATEGORY'].str.strip()
        
        def parse_amount(val):
            if pd.isna(val):
                return 0.0
            s = str(val).replace("PhP", "").strip()
            parts = s.split('.')
            if len(parts) > 2:
                s = parts[0] + '.' + ''.join(parts[1:])
            s = s.replace(",", "").strip()
            try:
                return float(s)
            except:
                return 0.0

        df['Cost_PhP'] = df['ESTIMATE AMOUNT'].apply(parse_amount)
        df['Cost_PhP_B'] = df['Cost_PhP'] / 1e9

        def assign_phase(p_no):
            if p_no <= 39:
                return "Phase 1 (2026–2030)"
            elif p_no <= 71:
                return "Phase 2 (2029–2035)"
            elif p_no <= 87:
                return "Phase 3 (2032–2038)"
            else:
                return "Phase 4 (2035–2040)"

        def assign_pcm_stage(p_no):
            if p_no <= 39:
                return "5. Implementation & Monitoring"
            elif p_no <= 71:
                return "3. Formulation & Design"
            elif p_no <= 87:
                return "2. Identification"
            else:
                return "1. Programming"

        df['Phase'] = df['PROJECT NO.'].apply(assign_phase)
        df['PCM Stage'] = df['PROJECT NO.'].apply(assign_pcm_stage)
        return df
    else:
        p_list = list(range(1, 96))
        phases = ["Phase 1 (2026–2030)"]*39 + ["Phase 2 (2029–2035)"]*32 + ["Phase 3 (2032–2038)"]*16 + ["Phase 4 (2035–2040)"]*8
        pcm_stages = ["5. Implementation & Monitoring"]*39 + ["3. Formulation & Design"]*32 + ["2. Identification"]*16 + ["1. Programming"]*8
        return pd.DataFrame({
            "PROJECT NO.": p_list,
            "PROJECT TITLE": [f"Sample Master Plan PAP {i}" for i in p_list],
            "SECTOR": ["Infrastructure"] * 21 + ["Institutional"] * 24 + ["Economic"] * 25 + ["Social"] * 13 + ["Environmental"] * 12,
            "CATEGORY": ["Infrastructure Preparation"] * 95,
            "Cost_PhP": [89724294.0] * 95,
            "Cost_PhP_B": [0.0897] * 95,
            "Phase": phases,
            "PCM Stage": pcm_stages
        })

@st.cache_data
def load_revenue_data():
    file_path = "REVENUE.xlsx"
    if os.path.exists(file_path):
        try:
            df_raw = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
            clean_rows = []
            for idx in range(2, 32):
                if idx >= len(df_raw):
                    break
                row = df_raw.iloc[idx]
                m_str = str(row.iloc[0]).strip()
                
                def parse_num(val):
                    if pd.isna(val):
                        return 0.0
                    s = str(val).replace("₱", "").replace(",", "").replace("\n", "").strip()
                    try:
                        return float(s)
                    except:
                        return 0.0

                trad = parse_num(row.iloc[2]) if len(row) > 2 else 0.0
                non_trad = parse_num(row.iloc[4]) if len(row) > 4 else 0.0
                bto = parse_num(row.iloc[6]) if len(row) > 6 else 0.0
                bir = parse_num(row.iloc[8]) if len(row) > 8 else 0.0
                collected = parse_num(row.iloc[10]) if len(row) > 10 else (trad + non_trad)
                
                clean_rows.append({
                    "Month_Raw": m_str,
                    "Traditional": trad,
                    "Non_Traditional": non_trad,
                    "BTO_Remittance": bto,
                    "BIR_Remittance": bir,
                    "Collected_Revenue": collected
                })
            
            df_clean = pd.DataFrame(clean_rows)
            date_list = pd.date_range(start="2024-01-01", periods=len(df_clean), freq="MS")
            df_clean["Date"] = date_list
            return df_clean
        except Exception:
            pass

    dates = pd.date_range(start="2024-01-01", periods=30, freq="MS")
    return pd.DataFrame({
        "Date": dates,
        "Traditional": [1200000 + i*15000 for i in range(30)],
        "Non_Traditional": [850000 + i*12000 for i in range(30)],
        "BTO_Remittance": [2000000]*30,
        "BIR_Remittance": [200000]*30,
        "Collected_Revenue": [(1200000 + i*15000) + (850000 + i*12000) for i in range(30)]
    })

@st.cache_data
def load_forecast_data():
    years = list(range(2026, 2041))
    bau_billion = [0.035 + (i * 0.003) for i in range(len(years))]
    integrated_billion = [0.035 + (i * 0.025) for i in range(len(years))]
    return pd.DataFrame({
        "Year": years,
        "Baseline (PhP Billion)": bau_billion,
        "Master Plan Integrated (PhP Billion)": integrated_billion
    })

df_master = load_masterplan_data()
df_rev = load_revenue_data()
df_forecast = load_forecast_data()

# ==========================================
# 4. REFACTORED VISUALIZATION COMPONENTS
# ==========================================

def render_component_1_historical_revenue(df_rev_input):
    if df_rev_input is None or df_rev_input.empty:
        st.warning("Revenue visualization unavailable: required revenue fields are missing.")
        return

    df_plot = df_rev_input.copy()
    req_cols = ["Date", "Collected_Revenue"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue visualization unavailable: missing column '{col}'.")
            return

    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    df_plot["Collected_Revenue"] = pd.to_numeric(df_plot["Collected_Revenue"], errors="coerce")
    df_plot = df_plot.dropna(subset=["Date", "Collected_Revenue"]).sort_values("Date").reset_index(drop=True)

    if df_plot.empty:
        st.warning("Revenue visualization unavailable: no valid numerical observations.")
        return

    revenue_m = df_plot["Collected_Revenue"] / 1e6
    mean_rev = revenue_m.mean()
    std_rev = revenue_m.std()
    upper_band = mean_rev + std_rev
    lower_band = max(0.0, mean_rev - std_rev)

    df_plot["MA_3M"] = revenue_m.rolling(window=3, min_periods=3).mean()

    x_idx = np.arange(len(df_plot))
    slope, intercept = np.polyfit(x_idx, revenue_m.values, 1)
    ols_trend = slope * x_idx + intercept

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=pd.concat([df_plot["Date"], df_plot["Date"][::-1]]),
            y=np.concatenate([np.full(len(df_plot), upper_band), np.full(len(df_plot), lower_band)]),
            fill="todense",
            fillcolor=EXECUTIVE_THEME["color_stat_band"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Historical Mean ± 1σ",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=np.full(len(df_plot), upper_band),
            mode="lines",
            line=dict(color=EXECUTIVE_THEME["color_stat_line"], width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=np.full(len(df_plot), lower_band),
            mode="lines",
            line=dict(color=EXECUTIVE_THEME["color_stat_line"], width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=ols_trend,
            mode="lines",
            name="OLS Trend",
            line=dict(color=EXECUTIVE_THEME["color_ols"], width=1.8),
            hovertemplate="<b>OLS Trend</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=df_plot["MA_3M"],
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color=EXECUTIVE_THEME["color_ma"], width=2.2),
            hovertemplate="<b>3M Moving Avg</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=revenue_m,
            mode="lines+markers",
            name="Actual Revenue",
            line=dict(color=EXECUTIVE_THEME["color_actual"], width=2.5),
            marker=dict(size=6, symbol="circle"),
            hovertemplate="<b>Month</b>: %{x|%B %Y}<br><b>Actual Revenue</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    fig.add_hline(
        y=2.50,
        line_dash="dash",
        line_color=EXECUTIVE_THEME["color_target"],
        line_width=1.5,
        annotation_text="Monthly Target — PhP 2.50M",
        annotation_position="top right",
        annotation_font=dict(size=10, color=EXECUTIVE_THEME["color_target"]),
    )

    apply_executive_theme(
        fig,
        title_text="Historical Revenue Performance & Statistical Momentum",
        subtitle_text="Actual monthly revenue collections vs. OLS trend, 3M moving average, and target baseline",
        height=450,
    )
    fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
    fig.update_xaxes(title_text="Timeline")

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())


def render_component_2_revenue_breakdown(df_rev_input):
    if df_rev_input is None or df_rev_input.empty:
        st.warning("Revenue breakdown unavailable: required revenue fields are missing.")
        return

    df_plot = df_rev_input.copy().reset_index(drop=True)
    req_cols = ["Date", "Traditional", "Non_Traditional"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue breakdown unavailable: missing column '{col}'.")
            return

    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    df_plot["Traditional"] = pd.to_numeric(df_plot["Traditional"], errors="coerce").fillna(0.0)
    df_plot["Non_Traditional"] = pd.to_numeric(df_plot["Non_Traditional"], errors="coerce").fillna(0.0)
    df_plot = df_plot.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    df_plot["Trad_M"] = df_plot["Traditional"] / 1e6
    df_plot["NonTrad_M"] = df_plot["Non_Traditional"] / 1e6
    df_plot["Total_M"] = df_plot["Trad_M"] + df_plot["NonTrad_M"]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=df_plot["Trad_M"],
            name="Traditional Revenue",
            marker_color=EXECUTIVE_THEME["color_trad"],
            customdata=np.stack((df_plot["NonTrad_M"], df_plot["Total_M"]), axis=-1),
            hovertemplate=(
                "<b>Month</b>: %{x|%B %Y}<br>"
                "Traditional: PhP %{y:.2f}M<br>"
                "Non-Traditional: PhP %{customdata[0]:.2f}M<br>"
                "<b>Total Revenue</b>: PhP %{customdata[1]:.2f}M<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=df_plot["NonTrad_M"],
            name="Non-Traditional Revenue",
            marker_color=EXECUTIVE_THEME["color_nontrad"],
            customdata=np.stack((df_plot["Trad_M"], df_plot["Total_M"]), axis=-1),
            hovertemplate=(
                "<b>Month</b>: %{x|%B %Y}<br>"
                "Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Non-Traditional: PhP %{y:.2f}M<br>"
                "<b>Total Revenue</b>: PhP %{customdata[1]:.2f}M<extra></extra>"
            ),
        )
    )

    apply_executive_theme(
        fig,
        title_text="Historical Revenue Composition by Stream",
        subtitle_text="Monthly breakdown between Traditional (Maritime/Ship Calls) and Non-Traditional (Ecozone Leases)",
        height=420,
    )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
    fig.update_xaxes(title_text="Timeline")

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())


def render_component_3_integrated_forecast(df_forecast_input):
    if df_forecast_input is None or df_forecast_input.empty:
        st.warning("Revenue forecast model unavailable: required projection data is missing.")
        return

    df_plot = df_forecast_input.copy().reset_index(drop=True)
    req_cols = ["Year", "Baseline (PhP Billion)", "Master Plan Integrated (PhP Billion)"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue forecast model unavailable: missing column '{col}'.")
            return

    df_plot["Year"] = pd.to_numeric(df_plot["Year"], errors="coerce")
    df_plot["BAU_M"] = pd.to_numeric(df_plot["Baseline (PhP Billion)"], errors="coerce") * 1000.0
    df_plot["Integrated_M"] = pd.to_numeric(df_plot["Master Plan Integrated (PhP Billion)"], errors="coerce") * 1000.0
    df_plot = df_plot.dropna(subset=["Year", "BAU_M", "Integrated_M"]).sort_values("Year").reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=pd.concat([df_plot["Year"], df_plot["Year"][::-1]]),
            y=pd.concat([df_plot["Integrated_M"], df_plot["BAU_M"][::-1]]),
            fill="tonext",
            fillcolor=EXECUTIVE_THEME["color_fill_gap"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Incremental Revenue Potential",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["BAU_M"],
            mode="lines+markers",
            name="Business-As-Usual (BAU)",
            line=dict(color=EXECUTIVE_THEME["color_bau"], width=2, dash="dash"),
            marker=dict(size=5),
            hovertemplate="<b>Year</b>: %{x}<br><b>BAU Revenue</b>: PhP %{y:,.1f}M<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["Integrated_M"],
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color=EXECUTIVE_THEME["color_integrated"], width=2.8),
            marker=dict(size=6, symbol="circle"),
            hovertemplate="<b>Year</b>: %{x}<br><b>Integrated Revenue</b>: PhP %{y:,.1f}M<extra></extra>",
        )
    )

    if 2028 in df_plot["Year"].values:
        val_2028 = df_plot.loc[df_plot["Year"] == 2028, "Integrated_M"].values[0]
        fig.add_annotation(
            x=2028,
            y=val_2028,
            text="Phase I PAPs Online",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#10B981",
            arrowsize=1,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            font=dict(size=10, color="#10B981"),
            bgcolor="#0F141D",
            bordercolor="#10B981",
            borderwidth=1,
            borderpad=4,
        )

    if 2035 in df_plot["Year"].values:
        val_2035 = df_plot.loc[df_plot["Year"] == 2035, "Integrated_M"].values[0]
        fig.add_annotation(
            x=2035,
            y=val_2035,
            text="Full Ecozone Logistics Integration",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#10B981",
            arrowsize=1,
            arrowwidth=1.5,
            ax=-40,
            ay=-35,
            font=dict(size=10, color="#10B981"),
            bgcolor="#0F141D",
            bordercolor="#10B981",
            borderwidth=1,
            borderpad=4,
        )

    apply_executive_theme(
        fig,
        title_text="Projected Long-Term Annual Revenue Trajectory (2026–2040)",
        subtitle_text="Comparative trajectory between Baseline BAU and Master Plan Integrated Development Scenarios",
        height=480,
    )
    fig.update_yaxes(title_text="Annual Revenue (PhP Millions)", tickprefix="PhP ", tickformat=",d", ticksuffix="M")
    fig.update_xaxes(title_text="Year", dtick=2)

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())

# ==========================================
# 5. TOP EXECUTIVE BANNER
# ==========================================
st.markdown(
    """
    <div style="background-color: #161B22; padding: 18px 24px; border-radius: 8px; border: 1px solid #30363D; text-align: left; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="background-color: #238636; color: #FFFFFF; font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 12px; letter-spacing: 0.5px;">EXECUTIVE STRATEGY BRIEF FOR EVALUATORS</span>
            <h2 style="color: #58A6FF; margin: 6px 0 2px 0; font-size: 22px; font-weight: 700;">POLLOC FREEPORT AND ECONOMIC ZONE (PFEZ)</h2>
            <p style="color: #8B949E; margin: 0; font-size: 13px;">Master Development Plan Implementation & Technical Infrastructure Manpower Framework</p>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 11px; color: #8B949E;">Authority:</span><br>
            <span style="font-size: 12px; color: #C9D1D9; font-weight: 600;">Bangsamoro Economic Zone Authority (BEZA)</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 6. SIDEBAR NAVIGATION & BRANDING
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/port.png", width=45)
st.sidebar.title("PFEZ Navigation")
nav_selection = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard Home",
        "Investment Phasing (Phases 1–4)",
        "Master Plan Projects Directory",
        "Manpower Justification",
        "Revenue Analytics & Forecasting",
        "Spatial Map Viewer",
        "M&E & Risk Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"**Project Portfolio:** PFEZ Master Plan\n\n**Total PAPs:** {len(df_master)} Projects\n\n**Total Estimated Capital:** PhP {df_master['Cost_PhP_B'].sum():.3f} Billion\n\n**Target Horizon:** 2026–2040 (4 Phases)"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Project Lead & Author")

try:
    st.sidebar.image("AirSad.png", width=120)
except Exception:
    st.sidebar.image("https://img.icons8.com/fluency/96/user-male-circle.png", width=75)

st.sidebar.markdown(
    """
    <div style='font-size: 11px; color: #FFFFFF; font-weight: bold; margin-top: 8px;'>
        ENGR. AIRSAD R. OLOMODIN, MBA, CBE
    </div>
    <div style='font-size: 11px; color: #8B949E; margin-top: 4px; line-height: 1.3;'>
        📱 0975-256-9055 / 0929-336-7787<br>
        ✉ airsadolomodin@gmail.com
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='font-size: 10px; color: #8B949E; line-height: 1.3;'>
    <b>Disclaimer:</b> Strategic decision-support tool built for BEZA infrastructure resource allocation and workforce expansion evaluation.
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 7. MAP RENDERER HELPER
# ==========================================
def render_multi_layer_map(selected_files, height=310):
    all_gdfs = []
    legend_items = []
    total_files = max(len(selected_files), 1)
    
    m = folium.Map(location=[7.34, 124.28], zoom_start=14.5, bearing=85, tiles=None)
    esri_tile_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
    
    folium.TileLayer(
        tiles=esri_tile_url,
        attr="Esri",
        name="esriworldstreetmap",
        control=True,
        max_zoom=19,
    ).add_to(m)
    
    for idx, file_name in enumerate(selected_files):
        try:
            gdf = gpd.read_file(file_name)
            display_name = file_name.replace(".geojson", "").replace("_", " ").title()
            
            hue = idx / total_files
            rgb_float = colorsys.hls_to_rgb(hue, 0.55, 0.85)
            hex_color = '#%02x%02x%02x' % (
                int(rgb_float[0] * 255),
                int(rgb_float[1] * 255),
                int(rgb_float[2] * 255),
            )
            rgb_css = f"rgba({int(rgb_float[0]*255)}, {int(rgb_float[1]*255)}, {int(rgb_float[2]*255)}, 0.85)"
            legend_items.append((display_name, rgb_css))
            
            if not gdf.empty:
                if gdf.crs is not None and gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs(epsg=4326)
                all_gdfs.append(gdf)
                
                folium.GeoJson(
                    gdf,
                    name=display_name,
                    style_function=lambda x, color=hex_color: {
                        'fillColor': color,
                        'color': '#333333',
                        'weight': 1.5,
                        'fillOpacity': 0.75,
                    },
                ).add_to(m)
        except Exception:
            pass

    if all_gdfs:
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)
        centroid = combined_gdf.geometry.unary_union.centroid
        m.location = [centroid.y, centroid.x]
        m.options['zoom'] = 14.5
        m.options['bearing'] = 85
        
    st_folium(m, width="100%", height=height)
    return legend_items

# ==========================================
# MODULE ROUTING
# ==========================================

# ------------------------------------------
# MODULE 1: DASHBOARD HOME VIEW
# ------------------------------------------
if nav_selection == "Dashboard Home":

    st.markdown(
        f"""
        <div class="callout-box">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🏗</span>
                <div>
                    <h4 style="margin: 0 0 4px 0; color: #58A6FF; font-size: 15px;">STRATEGIC JUSTIFICATION FOR TECHNICAL ENGINEERING MANPOWER EXPANSION</h4>
                    <p style="margin: 0; color: #C9D1D9; font-size: 12px; line-height: 1.5;">
                        The PFEZ Master Development Plan commits <b>PhP {df_master['Cost_PhP_B'].sum():.3f} Billion</b> across <b>{len(df_master)} Programs and Projects (PAPs)</b> structured into <b>4 Implementation Phases (2026–2040)</b>. Executing <b>Phase 1 (39 Immediate PAPs)</b> requires technical reinforcement: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>. Without direct engineering oversight, project execution delays threaten the foundational works and projected revenue trajectory.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(label="Total Capital Budget", value=f"PhP {df_master['Cost_PhP_B'].sum():.3f} Billion", delta=f"{len(df_master)} Official PAPs Across 4 Phases")
    with k2:
        p1_cost_b = df_master[df_master['Phase'] == 'Phase 1 (2026–2030)']['Cost_PhP_B'].sum()
        st.metric(label="Phase 1 Immediate Budget", value=f"PhP {p1_cost_b:.3f} Billion", delta="39 Immediate Deliverables")
    with k3:
        st.metric(label="Engineering Request", value="4 Positions", delta="Engineer V, III, and two I")
    with k4:
        st.metric(label="Historical Revenue Baseline", value=f"PhP {df_rev['Collected_Revenue'].sum()/1e9:.3f} Billion", delta="2024–2026 Collection")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🎯 Evaluator Bull's Eye View: Phase 1 to Phase 4 Implementation Roadmap")
    
    phase_summary = df_master.groupby('Phase').agg(
        PAPs_Count=('PROJECT NO.', 'count'),
        Total_Budget_B=('Cost_PhP_B', 'sum')
    ).reset_index()

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    
    with p_col1:
        p1_m = phase_summary[phase_summary['Phase'].str.contains('Phase 1')]
        val_b = p1_m['Total_Budget_B'].values[0] if not p1_m.empty else 0.0
        val_c = p1_m['PAPs_Count'].values[0] if not p1_m.empty else 0
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #58A6FF;">
                <span style="background-color: #1F6FE5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 1 (2026–2030)</span>
                <h3 style="color: #58A6FF; margin: 8px 0 2px 0; font-size: 18px;">PhP {val_b:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{val_c} PAPs</b> | Institutional Setup, BOSS & Baselines</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col2:
        p2_m = phase_summary[phase_summary['Phase'].str.contains('Phase 2')]
        val_b = p2_m['Total_Budget_B'].values[0] if not p2_m.empty else 0.0
        val_c = p2_m['PAPs_Count'].values[0] if not p2_m.empty else 0
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #F0883E;">
                <span style="background-color: #D25D11; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 2 (2029–2035)</span>
                <h3 style="color: #F0883E; margin: 8px 0 2px 0; font-size: 18px;">PhP {val_b:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{val_c} PAPs</b> | Container Yard & Halal Processing Hub</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col3:
        p3_m = phase_summary[phase_summary['Phase'].str.contains('Phase 3')]
        val_b = p3_m['Total_Budget_B'].values[0] if not p3_m.empty else 0.0
        val_c = p3_m['PAPs_Count'].values[0] if not p3_m.empty else 0
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #A371F7;">
                <span style="background-color: #8957E5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 3 (2032–2038)</span>
                <h3 style="color: #A371F7; margin: 8px 0 2px 0; font-size: 18px;">PhP {val_b:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{val_c} PAPs</b> | Wharf Extension & Land Reclamation</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col4:
        p4_m = phase_summary[phase_summary['Phase'].str.contains('Phase 4')]
        val_b = p4_m['Total_Budget_B'].values[0] if not p4_m.empty else 0.0
        val_c = p4_m['PAPs_Count'].values[0] if not p4_m.empty else 0
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #238636;">
                <span style="background-color: #238636; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 4 (2035–2040)</span>
                <h3 style="color: #238636; margin: 8px 0 2px 0; font-size: 18px;">PhP {val_b:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{val_c} PAPs</b> | Smart Logistics & Full Ecozone Maturity</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c_left, c_right = st.columns(2)

    with c_left:
        fig_phase = px.bar(
            phase_summary,
            x="Phase",
            y="Total_Budget_B",
            text="Total_Budget_B",
            labels={"Total_Budget_B": "Capital Budget (PhP Billions)", "Phase": "Implementation Phase"},
            color="Phase",
            color_discrete_sequence=["#58A6FF", "#F0883E", "#A371F7", "#238636"]
        )
        fig_phase.update_traces(texttemplate="PhP %{text:.2f}B", textposition="outside")
        apply_executive_theme(
            fig_phase,
            title_text="Capital Allocation by Implementation Phase",
            subtitle_text="Distribution of estimated project budgets across investment horizons",
            height=380
        )
        st.plotly_chart(fig_phase, use_container_width=True, config=configure_modebar())

    with c_right:
        sector_summary = df_master.groupby('SECTOR')['Cost_PhP_B'].sum().reset_index()
        fig_sector = px.pie(
            sector_summary,
            names="SECTOR",
            values="Cost_PhP_B",
            hole=0.4,
            color_discrete_sequence=["#38BDF8", "#10B981", "#F59E0B", "#A855F7", "#F97316"]
        )
        apply_executive_theme(
            fig_sector,
            title_text="Investment Breakdown by Key Sector",
            subtitle_text="Sectoral percentage share of overall master plan budget",
            height=380
        )
        st.plotly_chart(fig_sector, use_container_width=True, config=configure_modebar())

# ------------------------------------------
# MODULE 2: INVESTMENT PHASING (PHASES 1–4)
# ------------------------------------------
elif nav_selection == "Investment Phasing (Phases 1–4)":
    st.markdown("## 📅 Capital Investment Phasing Framework (2026–2040)")
    st.markdown("Explore project portfolios and investment allocations distributed across implementation phases.")

    selected_phase = st.selectbox(
        "Filter by Implementation Phase:",
        ["All Phases"] + list(df_master['Phase'].unique())
    )

    df_filtered = df_master.copy()
    if selected_phase != "All Phases":
        df_filtered = df_filtered[df_filtered['Phase'] == selected_phase]

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Phase Portfolio Budget", f"PhP {df_filtered['Cost_PhP_B'].sum():.3f} Billion")
    with m2:
        st.metric("Total Active PAPs", f"{len(df_filtered)} Projects")
    with m3:
        st.metric("Primary Sector Share", df_filtered['SECTOR'].mode()[0] if not df_filtered.empty else "N/A")

    st.markdown("---")
    
    fig_bar = px.bar(
        df_filtered,
        x="PROJECT NO.",
        y="Cost_PhP_B",
        color="SECTOR",
        hover_data=["PROJECT TITLE", "CATEGORY", "Phase"],
        labels={"Cost_PhP_B": "Cost (PhP Billions)", "PROJECT NO.": "Project Number"},
        color_discrete_sequence=["#38BDF8", "#10B981", "#F59E0B", "#A855F7", "#F97316"]
    )
    apply_executive_theme(
        fig_bar,
        title_text="Project-Level Capital Distribution",
        subtitle_text="Individual project budgets categorized by sector",
        height=420
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=configure_modebar())

    st.markdown("### Selected Phase Projects List")
    st.dataframe(
        df_filtered[["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "Cost_PhP_B", "Phase", "PCM Stage"]],
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------
# MODULE 3: MASTER PLAN PROJECTS DIRECTORY
# ------------------------------------------
elif nav_selection == "Master Plan Projects Directory":
    st.markdown("## 📋 Comprehensive Master Plan Projects Directory")
    st.markdown("Filter, search, and audit all 95 Programs and Projects (PAPs) under the PFEZ Master Plan.")

    c1, c2, c3 = st.columns(3)
    with c1:
        sector_filter = st.multiselect("Filter by Sector:", options=df_master['SECTOR'].unique(), default=df_master['SECTOR'].unique())
    with c2:
        phase_filter = st.multiselect("Filter by Phase:", options=df_master['Phase'].unique(), default=df_master['Phase'].unique())
    with c3:
        search_kw = st.text_input("Search Project Title:", "")

    df_dir = df_master[
        (df_master['SECTOR'].isin(sector_filter)) &
        (df_master['Phase'].isin(phase_filter))
    ]

    if search_kw:
        df_dir = df_dir[df_dir['PROJECT TITLE'].str.contains(search_kw, case=False, na=False)]

    st.markdown(f"**Showing {len(df_dir)} out of {len(df_master)} Projects** | Total Filtered Capital: **PhP {df_dir['Cost_PhP_B'].sum():.3f} Billion**")

    st.dataframe(
        df_dir[["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "ESTIMATE AMOUNT", "Cost_PhP_B", "Phase", "PCM Stage"]],
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------
# MODULE 4: MANPOWER JUSTIFICATION
# ------------------------------------------
elif nav_selection == "Manpower Justification":
    st.markdown("## 👷 Technical Engineering Manpower Expansion Justification")
    st.markdown("Strategic rationale for expanding the BEZA Technical Infrastructure Division to oversee Phase 1 master plan deliverables.")

    st.markdown(
        """
        <div class="callout-box">
            <h4 style="margin: 0 0 8px 0; color: #58A6FF;">PROPOSED TECHNICAL PERSONNEL EXPANSION</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.6;">
                To guarantee sound engineering management, strict structural compliance, and timely project delivery across <b>PhP 3.518 Billion</b> in Phase 1 projects, BEZA urgently requires four (4) core technical positions:
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            ### Required Technical Staffing
            1. **Engineer V (Division Head / Lead Engineer)**
               - *Role:* Strategic engineering management, master plan alignment, inter-agency coordination.
            2. **Engineer III (Senior Project Manager)**
               - *Role:* Procurement specification, contract management, structural quality assurance.
            3. **Engineer I (Field Inspection & Monitoring - 2 Positions)**
               - *Role:* On-site supervision, quantity surveying, contractor compliance verification.
            """
        )

    with col2:
        st.markdown(
            """
            ### Operational Risk Without Reinforcement
            - ⚠️ **Execution Bottlenecks:** Delayed review of detailed engineering designs (DED).
            - ⚠️ **Quality Assurance Deficits:** Inadequate field inspection leading to sub-standard works.
            - ⚠️ **Fiscal Slippage:** Risk of cost overruns and unbilled implementation delays.
            - ⚠️ **Revenue Lag:** Deferred completion directly postpones tenant leasing revenues.
            """
        )

# ------------------------------------------
# MODULE 5: REVENUE ANALYTICS & FORECASTING
# ------------------------------------------
elif nav_selection == "Revenue Analytics & Forecasting":
    st.markdown("## 📈 Revenue Analytics & Long-Term Financial Forecasting")
    st.markdown("Historical collections analysis and long-term revenue projections under Master Plan implementation.")

    st.markdown("### 1. Historical Revenue & Momentum Analysis")
    render_component_1_historical_revenue(df_rev)

    st.markdown("---")
    st.markdown("### 2. Historical Revenue Stream Composition")
    render_component_2_revenue_breakdown(df_rev)

    st.markdown("---")
    st.markdown("### 3. Projected Long-Term Revenue Trajectory (2026–2040)")
    render_component_3_integrated_forecast(df_forecast)

# ------------------------------------------
# MODULE 6: SPATIAL MAP VIEWER & OPENZONEMAP
# ------------------------------------------
elif nav_selection == "Spatial Map Viewer":
    st.markdown("## 🗺️ Spatial Map Viewer & Global SEZs")
    st.markdown("Interactive GIS map visualization for local PFEZ layers and the Global OpenZoneMap.")

    # Toggle switch between OpenZoneMap iframe and local GeoJSON layer viewer
    map_mode = st.radio(
        "Select Map Source:",
        ["Global OpenZoneMap (Live Web Map)", "Local PFEZ GeoJSON Layers"],
        horizontal=True
    )

    if map_mode == "Global OpenZoneMap (Live Web Map)":
        st.markdown("### 🌐 Global Open Zone Map Integration")
        st.write("Displaying the Open Zone Map inside Streamlit.")
        components.iframe(
            src="https://www.openzonemap.com/map",
            height=700,
            scrolling=True
        )
    else:
        st.markdown("### 🗺️ Local PFEZ Spatial Map & Zone Layout")
        available_layers = [f for f in os.listdir(".") if f.endswith(".geojson")]
        
        if available_layers:
            selected_layers = st.multiselect("Select Spatial Layers to Display:", options=available_layers, default=available_layers[:1])
            if selected_layers:
                legend = render_multi_layer_map(selected_layers, height=500)
                if legend:
                    st.markdown("#### Layer Legend")
                    leg_cols = st.columns(min(len(legend), 4))
                    for idx, (lname, color_css) in enumerate(legend):
                        with leg_cols[idx % 4]:
                            st.markdown(
                                f"<div style='display:flex; align-items:center; gap:8px;'><div style='width:16px; height:16px; background-color:{color_css}; border-radius:3px;'></div><span style='font-size:12px;'>{lname}</span></div>",
                                unsafe_allow_html=True
                            )
            else:
                st.info("Please select at least one layer to view the spatial map.")
        else:
            st.warning("No `.geojson` map layers found in the current root directory. Base spatial viewer loaded.")
            m = folium.Map(location=[7.34, 124.28], zoom_start=14, tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            st_folium(m, width="100%", height=450)

# ------------------------------------------
# MODULE 7: M&E & RISK MATRIX
# ------------------------------------------
elif nav_selection == "M&E & Risk Matrix":
    st.markdown("## 🛡️ Monitoring & Evaluation (M&E) & Risk Mitigation Framework")
    st.markdown("Project Cycle Management (PCM) stage gates, logical framework, and institutional risk matrix.")

    tab1, tab2 = st.tabs(["PCM Stage Gate Framework", "Institutional Risk Matrix"])

    with tab1:
        st.markdown("### Project Cycle Management (PCM) Distribution")
        pcm_counts = df_master['PCM Stage'].value_counts().reset_index()
        pcm_counts.columns = ['PCM Stage', 'Count']
        
        fig_pcm = px.bar(
            pcm_counts,
            x="PCM Stage",
            y="Count",
            color="PCM Stage",
            color_discrete_sequence=["#38BDF8", "#10B981", "#F59E0B", "#A855F7"]
        )
        apply_executive_theme(
            fig_pcm,
            title_text="PAPs by Project Cycle Management Stage",
            subtitle_text="Current distribution across stage gates",
            height=380
        )
        st.plotly_chart(fig_pcm, use_container_width=True, config=configure_modebar())

    with tab2:
        st.markdown("### Institutional Risk Mitigation Matrix")
        risk_data = pd.DataFrame([
            {"Risk Category": "Technical / Engineering", "Identified Risk": "Delay in detailed engineering designs (DED) and contractor procurement", "Severity": "High", "Mitigation Strategy": "Recruit dedicated technical staff (Engineer V & III) to fast-track terms of reference and review processes."},
            {"Risk Category": "Financial / Fiscal", "Identified Risk": "Budgetary constraints and delays in capital disbursements", "Severity": "Medium", "Mitigation Strategy": "Establish phased capital allocation aligned with revenue milestones and explore PPP options."},
            {"Risk Category": "Operational / Logistics", "Identified Risk": "Port congestion and insufficient container storage during early phases", "Severity": "Medium", "Mitigation Strategy": "Prioritize Phase 1 container yard expansion and off-dock logistics facilities."},
            {"Risk Category": "Institutional / Legal", "Identified Risk": "Jurisdictional overlaps and slow regulatory permitting", "Severity": "High", "Mitigation Strategy": "Operationalize Business Permits and Licensing System (BPLS) and One-Stop Shop (BOSS) under BEZA."}
        ])
        
        st.dataframe(risk_data, use_container_width=True, hide_index=True)
