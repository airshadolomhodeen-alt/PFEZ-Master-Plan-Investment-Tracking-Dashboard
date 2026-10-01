import colorsys
import json
import os
import re
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PFEZ Master Development Plan & Technical Capacity Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXCEL_FILE = "REVENUE.xlsx"

# --- CUSTOM EXECUTIVE DARK STYLING ---
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


# --- LOAD CSV DATA DYNAMICALLY ---
@st.cache_data
def load_masterplan_data():
    file_path = "MASTERPLAN PROJECTS.csv"
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding="latin1")
        except Exception:
            df = pd.read_csv(file_path, encoding="cp1252")

        df.columns = [c.strip() for c in df.columns]
        df["SECTOR"] = df["SECTOR"].str.strip()
        df["CATEGORY"] = df["CATEGORY"].str.strip()

        def parse_amount(val):
            if pd.isna(val):
                return 0.0
            s = str(val).replace("PhP", "").strip()
            parts = s.split(".")
            if len(parts) > 2:
                s = parts[0] + "." + "".join(parts[1:])
            s = s.replace(",", "").strip()
            try:
                return float(s)
            except Exception:
                return 0.0

        df["Cost_PhP"] = df["ESTIMATE AMOUNT"].apply(parse_amount)
        df["Cost_PhP_B"] = df["Cost_PhP"] / 1e9

        def assign_phase(p_no):
            if p_no <= 39:
                return "Phase 1 (2026–2030)"
            elif p_no <= 71:
                return "Phase 2 (2029–2035)"
            elif p_no <= 87:
                return "Phase 3 (2032–2038)"
            else:
                return "Phase 4 (2035–2040)"

        df["Phase"] = df["PROJECT NO."].apply(assign_phase)
        return df
    else:
        p_list = list(range(1, 96))
        phases = (
            ["Phase 1 (2026–2030)"] * 39
            + ["Phase 2 (2029–2035)"] * 32
            + ["Phase 3 (2032–2038)"] * 16
            + ["Phase 4 (2035–2040)"] * 8
        )
        return pd.DataFrame({
            "PROJECT NO.": p_list,
            "PROJECT TITLE": [f"Sample Master Plan PAP {i}" for i in p_list],
            "SECTOR": (
                ["Infrastructure"] * 21
                + ["Institutional"] * 24
                + ["Economic"] * 25
                + ["Social"] * 13
                + ["Environmental"] * 12
            ),
            "CATEGORY": ["Infrastructure Preparation"] * 95,
            "Cost_PhP": [89724294.0] * 95,
            "Cost_PhP_B": [0.0897] * 95,
            "Phase": phases,
        })


# --- LOAD REVENUE DATA PRESERVING EXACT EXCEL STRUCTURE ---
def load_revenue_data():
    if os.path.exists(EXCEL_FILE):
        try:
            return pd.read_excel(EXCEL_FILE)
        except Exception:
            pass

    return pd.DataFrame({
        "Month/Year": ["January (2026)", "February (2026)", "March (2026)"],
        "COLLECTED REVENUE": [1500000.0, 1800000.0, 2100000.0],
    })


def prepare_clean_time_series(df):
    """Filters out headers and non-data months (e.g. July 2026 - Dec 2026 without data)."""
    clean_records = []
    month_col = df.columns[0]

    target_col = None
    for col in df.columns:
        col_str = str(col).upper()
        if any(
            k in col_str
            for k in ["COLLECTED REVENUE", "REVENUE", "TOTAL", "COLLECTED"]
        ):
            target_col = col
            break

    if target_col is None:
        target_col = df.columns[-1]

    for idx, row in df.iterrows():
        month_val = str(row[month_col]).strip()
        raw_rev = row[target_col]

        # Filter out rows with no actual revenue entries (NaN, Empty, 0, or dashes)
        if pd.isna(raw_rev) or str(raw_rev).strip().lower() in [
            "",
            "nan",
            "none",
            "-",
        ]:
            continue

        rev_str = (
            str(raw_rev)
            .replace("PhP", "")
            .replace(",", "")
            .replace("₱", "")
            .strip()
        )

        try:
            val = float(rev_str)
            if val > 0 and month_val.upper() not in [
                "MONTH",
                "NONE",
                "NAN",
                "COLLECTED REVENUE",
            ]:
                clean_records.append({"Month": month_val, "Revenue": val})
        except ValueError:
            continue

    return pd.DataFrame(clean_records)


def get_total_revenue_value(df):
    """Calculates total revenue without altering original columns."""
    clean_df = prepare_clean_time_series(df)
    if not clean_df.empty:
        return clean_df["Revenue"].sum()
    return 0.0


df_master = load_masterplan_data()
df_rev = load_revenue_data()

# --- TOP EXECUTIVE BANNER ---
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

# --- SIDEBAR NAVIGATION ---
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

# --- SIDEBAR AUTHOR BRANDING ---
st.sidebar.markdown("---")
st.sidebar.markdown("### Project Lead & Author")

try:
    st.sidebar.image("AirSad.png", width=120)
except Exception:
    st.sidebar.image(
        "https://img.icons8.com/fluency/96/user-male-circle.png", width=75
    )

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


# --- MAP RENDERER HELPER ---
def render_multi_layer_map(selected_files, height=310):
    all_gdfs = []
    legend_items = []
    total_files = max(len(selected_files), 1)

    m = folium.Map(
        location=[7.34, 124.28], zoom_start=14.5, bearing=85, tiles=None
    )
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
            display_name = (
                file_name.replace(".geojson", "").replace("_", " ").title()
            )

            hue = idx / total_files
            rgb_float = colorsys.hls_to_rgb(hue, 0.55, 0.85)
            hex_color = "#%02x%02x%02x" % (
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
                        "fillColor": color,
                        "color": "#333333",
                        "weight": 1.5,
                        "fillOpacity": 0.75,
                    },
                ).add_to(m)
        except Exception:
            pass

    if all_gdfs:
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)
        centroid = combined_gdf.geometry.unary_union.centroid
        m.location = [centroid.y, centroid.x]
        m.options["zoom"] = 14.5
        m.options["bearing"] = 85

    st_folium(m, width="100%", height=height)
    return legend_items


# ==========================================
# 1. DASHBOARD HOME VIEW
# ==========================================
if nav_selection == "Dashboard Home":

    st.markdown(
        f"""
        <div class="callout-box">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🏗</span>
                <div>
                    <h4 style="margin: 0 0 4px 0; color: #58A6FF; font-size: 15px;">STRATEGIC JUSTIFICATION FOR TECHNICAL ENGINEERING MANPOWER EXPANSION</h4>
                    <p style="margin: 0; color: #C9D1D9; font-size: 12px; line-height: 1.5;">
                        The PFEZ Master Development Plan commits <b>PhP {df_master['Cost_PhP_B'].sum():.3f} Billion</b> across <b>{len(df_master)} Programs and Projects (PAPs)</b> structured into <b>4 Implementation Phases (2026–2040)</b>. Executing <b>Phase 1 (39 Immediate PAPs)</b> requires technical reinforcement: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="Total Capital Budget",
            value=f"PhP {df_master['Cost_PhP_B'].sum():.3f} Billion",
            delta=f"{len(df_master)} Official PAPs Across 4 Phases",
        )
    with k2:
        p1_cost_b = df_master[df_master["Phase"] == "Phase 1 (2026–2030)"][
            "Cost_PhP_B"
        ].sum()
        st.metric(
            label="Phase 1 Immediate Budget",
            value=f"PhP {p1_cost_b:.3f} Billion",
            delta="39 Immediate Deliverables",
        )
    with k3:
        st.metric(
            label="Engineering Request",
            value="4 Positions",
            delta="Engineer V, III, and two I",
        )
    with k4:
        total_rev_val = get_total_revenue_value(df_rev)
        st.metric(
            label="Historical Revenue Baseline",
            value=f"PhP {total_rev_val/1e6:.2f} Million",
            delta="Collection Total",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "### 🎯 Evaluator Bull's Eye View: Phase 1 to Phase 4 Implementation Roadmap"
    )

    phase_summary = (
        df_master.groupby("Phase")
        .agg(
            PAPs_Count=("PROJECT NO.", "count"),
            Total_Budget_B=("Cost_PhP_B", "sum"),
        )
        .reset_index()
    )

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    with p_col1:
        p1_m = phase_summary[phase_summary["Phase"].str.contains("Phase 1")]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #58A6FF;">
                <span style="background-color: #1F6FE5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 1 (2026–2030)</span>
                <h3 style="color: #58A6FF; margin: 8px 0 2px 0; font-size: 18px;">PhP {p1_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p1_m['PAPs_Count'].values[0]} PAPs</b> | Institutional Setup & Baselines</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_col2:
        p2_m = phase_summary[phase_summary["Phase"].str.contains("Phase 2")]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #F0883E;">
                <span style="background-color: #D25D11; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 2 (2029–2035)</span>
                <h3 style="color: #F0883E; margin: 8px 0 2px 0; font-size: 18px;">PhP {p2_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p2_m['PAPs_Count'].values[0]} PAPs</b> | Container Yard & Halal Hub</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_col3:
        p3_m = phase_summary[phase_summary["Phase"].str.contains("Phase 3")]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #A371F7;">
                <span style="background-color: #8957E5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 3 (2032–2038)</span>
                <h3 style="color: #A371F7; margin: 8px 0 2px 0; font-size: 18px;">PhP {p3_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p3_m['PAPs_Count'].values[0]} PAPs</b> | Wharf Extension & Reclamation</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p_col4:
        p4_m = phase_summary[phase_summary["Phase"].str.contains("Phase 4")]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #238636;">
                <span style="background-color: #238636; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 4 (2035–2040)</span>
                <h3 style="color: #2EA043; margin: 8px 0 2px 0; font-size: 18px;">PhP {p4_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p4_m['PAPs_Count'].values[0]} PAPs</b> | IT Park & Eco-Tourism</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    c_col1, c_col2 = st.columns(2)

    with c_col1:
        fig_phase = px.bar(
            phase_summary,
            x="Phase",
            y="Total_Budget_B",
            text_auto=".3f",
            title="Capital Expenditure Allocation by Phase (PhP Billion)",
            template="plotly_dark",
            height=330,
            color="Phase",
            color_discrete_sequence=[
                "#58A6FF",
                "#F0883E",
                "#A371F7",
                "#238636",
            ],
        )
        fig_phase.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="PhP Billion",
            showlegend=False,
        )
        st.plotly_chart(fig_phase, use_container_width=True)

    with c_col2:
        sector_agg = (
            df_master.groupby("SECTOR")["Cost_PhP_B"].sum().reset_index()
        )
        fig_sec = px.pie(
            sector_agg,
            names="SECTOR",
            values="Cost_PhP_B",
            title="Capital Budget Distribution across Sectors",
            hole=0.45,
            template="plotly_dark",
            height=330,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_sec.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    bot_col1, bot_col2 = st.columns(2)

    with bot_col1:
        st.markdown("### Spatial Zoning Quick Viewer")
        geojson_files = sorted(
            [f for f in os.listdir(".") if f.endswith(".geojson")]
        )
        if geojson_files:
            selected_home_zone = st.selectbox(
                "Select Zone Layer",
                geojson_files,
                format_func=lambda x: x.replace(".geojson", "")
                .replace("_", " ")
                .title(),
                key="home_zone",
            )
            try:
                render_multi_layer_map([selected_home_zone], height=310)
            except Exception as e:
                st.error(f"Error reading layer: {e}")
        else:
            st.warning("No geojson files found in directory.")

    with bot_col2:
        st.markdown("### Historical Revenue Time Series & Trend Analysis")

        clean_ts_df = prepare_clean_time_series(df_rev)

        if not clean_ts_df.empty:
            fig_ts = px.line(
                clean_ts_df,
                x="Month",
                y="Revenue",
                title="Monthly Revenue Collections with Linear Trendline (PhP)",
                markers=True,
            )

            y_vals = clean_ts_df["Revenue"].values
            x_vals = np.arange(len(y_vals))

            if len(y_vals) > 1:
                m, c = np.polyfit(x_vals, y_vals, 1)
                trendline_y = m * x_vals + c

                fig_ts.add_trace(
                    go.Scatter(
                        x=clean_ts_df["Month"],
                        y=trendline_y,
                        mode="lines",
                        name="Linear Trendline",
                        line=dict(color="#FF4B4B", width=2, dash="dash"),
                    )
                )

            fig_ts.update_traces(
                selector=dict(mode="lines+markers"),
                line_color="#58A6FF",
                marker=dict(size=6, color="#58A6FF"),
            )
            fig_ts.update_layout(
                template="plotly_dark",
                height=270,
                margin=dict(l=10, r=10, t=35, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Month",
                yaxis_title="Revenue (PhP)",
                xaxis=dict(
                    tickangle=-45,
                    tickfont=dict(size=9),
                    type="category",
                ),
                yaxis=dict(gridcolor="#30363D"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("No numerical revenue data available to render trendline.")

        with st.expander("➕ Add Value / New Entry", expanded=True):
            with st.form("add_revenue_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    new_period = st.text_input(
                        "Period / Month", placeholder="e.g. Month 39 or Jan 2027"
                    )
                with c2:
                    new_val = st.number_input(
                        "Revenue Amount (PhP)", min_value=0.0, step=10000.0
                    )

                submit_btn = st.form_submit_button("➕ Add Entry to Excel")

                if submit_btn:
                    if new_period.strip():
                        time_col = df_rev.columns[0]
                        val_col = df_rev.columns[-1]

                        new_row = {col: None for col in df_rev.columns}
                        new_row[time_col] = new_period
                        new_row[val_col] = new_val

                        updated_df = pd.concat(
                            [df_rev, pd.DataFrame([new_row])], ignore_index=True
                        )
                        try:
                            updated_df.to_excel(EXCEL_FILE, index=False)
                            st.success(f"Added {new_period}: PhP {new_val:,.2f}")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error updating file: {err}")
                    else:
                        st.warning("Please enter a valid period name.")

# ==========================================
# 2. INVESTMENT PHASING VIEW (PHASES 1 TO 4)
# ==========================================
elif nav_selection == "Investment Phasing (Phases 1–4)":
    st.title("💰 Investment & Phasing Program (2026–2040)")
    st.markdown(
        "Detailed evaluator breakdown of the **95 Programs and Projects (PAPs)** amounting to **PhP 8.524 Billion** across 4 implementation phases."
    )

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Phase 1 (2026–2030)", "PhP 0.284 Billion", "39 Initial PAPs")
    with col_p2:
        st.metric("Phase 2 (2029–2035)", "PhP 1.949 Billion", "32 Core PAPs")
    with col_p3:
        st.metric(
            "Phase 3 (2032–2038)", "PhP 6.124 Billion", "16 Major Capital PAPs"
        )
    with col_p4:
        st.metric("Phase 4 (2035–2040)", "PhP 0.168 Billion", "8 Finalizing PAPs")

    st.markdown("---")

    selected_phase = st.selectbox(
        "Select Phase to Inspect Projects:",
        options=[
            "All Phases",
            "Phase 1 (2026–2030)",
            "Phase 2 (2029–2035)",
            "Phase 3 (2032–2038)",
            "Phase 4 (2035–2040)",
        ],
    )

    if selected_phase == "All Phases":
        df_phase_view = df_master
    else:
        df_phase_view = df_master[df_master["Phase"] == selected_phase]

    st.markdown(
        f"**Displaying {len(df_phase_view)} PAPs | Total Budget: PhP {df_phase_view['Cost_PhP_B'].sum():,.3f} Billion**"
    )
    st.dataframe(
        df_phase_view[[
            "PROJECT NO.",
            "PROJECT TITLE",
            "SECTOR",
            "CATEGORY",
            "Phase",
            "ESTIMATE AMOUNT",
        ]],
        use_container_width=True,
        height=450,
    )

# ==========================================
# 3. MASTER PLAN PROJECTS DIRECTORY VIEW
# ==========================================
elif nav_selection == "Master Plan Projects Directory":
    st.title("📋 Master Plan Programs & Projects (PAPs) Directory")
    st.markdown(
        f"Complete searchable database of **{len(df_master)} PAPs** totaling **PhP {df_master['Cost_PhP_B'].sum():,.3f} Billion**."
    )

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        selected_phases = st.multiselect(
            "Filter by Phase:",
            options=sorted(df_master["Phase"].unique()),
            default=sorted(df_master["Phase"].unique()),
        )
    with col_filter2:
        selected_sectors = st.multiselect(
            "Filter by Sector:",
            options=sorted(df_master["SECTOR"].unique()),
            default=sorted(df_master["SECTOR"].unique()),
        )
    with col_filter3:
        selected_cats = st.multiselect(
            "Filter by Category:",
            options=sorted(df_master["CATEGORY"].unique()),
            default=sorted(df_master["CATEGORY"].unique()),
        )

    df_filtered = df_master[
        (df_master["Phase"].isin(selected_phases))
        & (df_master["SECTOR"].isin(selected_sectors))
        & (df_master["CATEGORY"].isin(selected_cats))
    ]

    st.markdown(
        f"**Showing {len(df_filtered)} of {len(df_master)} Projects | Subtotal: PhP {df_filtered['Cost_PhP_B'].sum():,.3f} Billion**"
    )

    st.dataframe(
        df_filtered[[
            "PROJECT NO.",
            "PROJECT TITLE",
            "SECTOR",
            "CATEGORY",
            "Phase",
            "ESTIMATE AMOUNT",
        ]],
        use_container_width=True,
        height=480,
    )

# ==========================================
# 4. MANPOWER & INFRASTRUCTURE JUSTIFICATION VIEW
# ==========================================
elif nav_selection == "Manpower Justification":
    st.title("👷 Technical Engineering Manpower Justification")
    st.markdown(
        "Operational necessity analysis justifying the direct appointment of **Engineer V, Engineer III, and two Engineer I** positions."
    )

    st.markdown(
        """
        <div class="callout-box">
            <h4 style="margin: 0 0 6px 0; color: #58A6FF;">Core Technical Rationale for Evaluators</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.5;">
                Executing complex infrastructure across Phase 1 through Phase 4 requires an agile technical workforce. Approving the requested headcount—<b>Engineer V, Engineer III, and two Engineer I positions</b>—ensures robust project supervision, procurement, and execution across all 95 PAPs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Requested Engineering Headcount")

        staff_data = pd.DataFrame({
            "Engineering Position": [
                "Engineer V (Division Chief)",
                "Engineer III (Senior Lead)",
                "Engineer I - Position A (Field Supervision)",
                "Engineer I - Position B (QA/QC & GIS)",
            ],
            "Requested Positions": [1, 1, 1, 1],
        })

        fig_staff = go.Figure()
        fig_staff.add_trace(
            go.Bar(
                y=staff_data["Engineering Position"],
                x=staff_data["Requested Positions"],
                name="Personnel Headcount",
                orientation="h",
                marker_color="#58A6FF",
                text=staff_data["Requested Positions"],
                textposition="auto",
            )
        )

        fig_staff.update_layout(
            template="plotly_dark",
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(dtick=1, range=[0, 2]),
        )
        st.plotly_chart(fig_staff, use_container_width=True)

    with col2:
        st.markdown("### Functional Mandate Breakdown")

        roles_table = pd.DataFrame({
            "Position Title": [
                "Engineer V",
                "Engineer III",
                "Engineer I (Field)",
                "Engineer I (QA/QC)",
            ],
            "Primary Responsibilities": [
                (
                    "Division management, strategic program alignment, and"
                    " governance"
                ),
                (
                    "Detailed engineering design review, technical"
                    " specifications, procurement"
                ),
                (
                    "On-site project inspection, contractor compliance, civil"
                    " works"
                ),
                (
                    "Quality assurance, structural monitoring, and GIS"
                    " integration"
                ),
            ],
        })
        st.dataframe(roles_table, use_container_width=True, height=340)

# ==========================================
# 5. REVENUE ANALYTICS & FORECASTING VIEW
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & Master Plan Forecasting")
    st.markdown(
        "Comprehensive revenue breakdown across **Traditional Port Revenues**, **Non-Traditional Economic Revenues**, and **Integrated Master Plan Projections**."
    )

    # --- TABS RESTORED ---
    rev_tab1, rev_tab2, rev_tab3, rev_tab4 = st.tabs([
        "📊 Historical Revenue Analytics",
        "⚓ Traditional Revenue Streams",
        "🏢 Non-Traditional Revenue Streams",
        "🚀 Integrated Master Plan Forecast",
    ])

    # TAB 1: HISTORICAL REVENUE ANALYTICS
    with rev_tab1:
        st.markdown("### 1. Historical Revenue Collections & Trend Analysis")

        clean_ts_df = prepare_clean_time_series(df_rev)

        if not clean_ts_df.empty:
            fig_hist = px.line(
                clean_ts_df,
                x="Month",
                y="Revenue",
                title="Monthly Revenue Collections with Linear OLS Trendline (PhP)",
                markers=True,
            )

            y_vals = clean_ts_df["Revenue"].values
            x_vals = np.arange(len(y_vals))

            if len(y_vals) > 1:
                m, c = np.polyfit(x_vals, y_vals, 1)
                trendline_y = m * x_vals + c

                fig_hist.add_trace(
                    go.Scatter(
                        x=clean_ts_df["Month"],
                        y=trendline_y,
                        mode="lines",
                        name="Linear Trendline",
                        line=dict(color="#FF4B4B", width=2, dash="dash"),
                    )
                )

            fig_hist.update_traces(
                selector=dict(mode="lines+markers"),
                line_color="#58A6FF",
                marker=dict(size=7, color="#58A6FF"),
            )
            fig_hist.update_layout(
                template="plotly_dark",
                height=400,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Month",
                yaxis_title="Revenue (PhP)",
                xaxis=dict(tickangle=-45, type="category"),
                yaxis=dict(gridcolor="#30363D"),
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No numerical revenue records found in Excel dataset.")

        st.markdown("### Raw Excel Revenue Dataset")
        st.dataframe(df_rev, use_container_width=True, height=250)

    # TAB 2: TRADITIONAL REVENUE STREAMS
    with rev_tab2:
        st.markdown(
            "### ⚓ Traditional Port & Maritime Revenue Streams (Core Port Services)"
        )
        st.markdown(
            "Traditional revenue generated directly from vessel operations, cargo handling, and port tariff collections."
        )

        trad_col1, trad_col2 = st.columns(2)

        with trad_col1:
            trad_df = pd.DataFrame({
                "Revenue Category": [
                    "Wharfage Dues",
                    "Dockage & Berthing Fees",
                    "Port Dues & Harbor Fees",
                    "Cargo Handling / Arrastre & Stevedoring Share",
                    "Storage & Demurrage Fees",
                ],
                "Annual Estimate (PhP)": [
                    15000000.0,
                    12000000.0,
                    8000000.0,
                    25000000.0,
                    6000000.0,
                ],
            })

            fig_trad = px.bar(
                trad_df,
                x="Annual Estimate (PhP)",
                y="Revenue Category",
                orientation="h",
                title="Traditional Port Revenue Streams",
                template="plotly_dark",
                color="Annual Estimate (PhP)",
                color_continuous_scale="Blues",
            )
            fig_trad.update_layout(
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_trad, use_container_width=True)

        with trad_col2:
            st.markdown("#### Strategic Details - Traditional Revenues")
            st.dataframe(trad_df, use_container_width=True, height=350)

    # TAB 3: NON-TRADITIONAL REVENUE STREAMS
    with rev_tab3:
        st.markdown(
            "### 🏢 Non-Traditional Economic Zone & Commercial Revenue Streams"
        )
        st.markdown(
            "Diversified income generated from land leases, commercial permits, processing fees, and utility surcharges."
        )

        nontrad_col1, nontrad_col2 = st.columns(2)

        with nontrad_col1:
            nontrad_df = pd.DataFrame({
                "Revenue Category": [
                    "Industrial Land Lease & Ground Rent",
                    "Ecozone Enterprise Registration Fees",
                    "Commercial Building Leases",
                    "Utility & Infrastructure Surcharges",
                    "Permits, Licenses & Environmental Fees",
                ],
                "Annual Estimate (PhP)": [
                    35000000.0,
                    10000000.0,
                    18000000.0,
                    12000000.0,
                    7000000.0,
                ],
            })

            fig_nontrad = px.bar(
                nontrad_df,
                x="Annual Estimate (PhP)",
                y="Revenue Category",
                orientation="h",
                title="Non-Traditional Revenue Streams",
                template="plotly_dark",
                color="Annual Estimate (PhP)",
                color_continuous_scale="Oranges",
            )
            fig_nontrad.update_layout(
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_nontrad, use_container_width=True)

        with nontrad_col2:
            st.markdown("#### Strategic Details - Non-Traditional Revenues")
            st.dataframe(nontrad_df, use_container_width=True, height=350)

    # TAB 4: INTEGRATED MASTER PLAN FORECAST
    with rev_tab4:
        st.markdown(
            "### 🚀 Integrated Master Plan Revenue Forecast (2026–2040)"
        )
        st.markdown(
            "Long-term projected revenues post-completion of Phase 1 through Phase 4 master plan capital projects."
        )

        forecast_years = [
            "2026 (Phase 1 Start)",
            "2028",
            "2030 (Phase 1 End)",
            "2033 (Phase 2)",
            "2036 (Phase 3)",
            "2040 (Phase 4 Target)",
        ]
        trad_forecast = [66.0, 85.0, 120.0, 180.0, 260.0, 380.0]  # Million PhP
        nontrad_forecast = [
            82.0,
            110.0,
            160.0,
            250.0,
            410.0,
            620.0,
        ]  # Million PhP

        forecast_df = pd.DataFrame({
            "Year/Phase": forecast_years,
            "Traditional Revenue (M PhP)": trad_forecast,
            "Non-Traditional Revenue (M PhP)": nontrad_forecast,
        })
        forecast_df["Total Master Plan Revenue (M PhP)"] = (
            forecast_df["Traditional Revenue (M PhP)"]
            + forecast_df["Non-Traditional Revenue (M PhP)"]
        )

        fig_forecast = go.Figure()
        fig_forecast.add_trace(
            go.Bar(
                x=forecast_df["Year/Phase"],
                y=forecast_df["Traditional Revenue (M PhP)"],
                name="Traditional Port Revenues",
                marker_color="#58A6FF",
            )
        )
        fig_forecast.add_trace(
            go.Bar(
                x=forecast_df["Year/Phase"],
                y=forecast_df["Non-Traditional Revenue (M PhP)"],
                name="Non-Traditional Ecozone Revenues",
                marker_color="#F0883E",
            )
        )

        fig_forecast.update_layout(
            barmode="stack",
            title="Integrated Revenue Growth Forecast (Millions PhP)",
            template="plotly_dark",
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Timeline / Phase Horizon",
            yaxis_title="Revenue (Million PhP)",
        )

        st.plotly_chart(fig_forecast, use_container_width=True)

        st.markdown("#### Forecast Summary Table")
        st.dataframe(forecast_df, use_container_width=True)

# ==========================================
# 6. SPATIAL MAP VIEWER & OPEN ZONE MAP
# ==========================================
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺 Spatial Development & Land Use Map Viewer")

    map_type = st.radio(
        "Select View Mode:",
        [
            "Local QGIS Zoning Layers (Folium)",
            "Global Open Zone Map (Embedded Iframe)",
        ],
        horizontal=True,
    )

    if map_type == "Global Open Zone Map (Embedded Iframe)":
        components.iframe(
            src="https://www.openzonemap.com/map", height=650, scrolling=True
        )
    else:
        geojson_files = sorted(
            [f for f in os.listdir(".") if f.endswith(".geojson")]
        )
        if geojson_files:
            selected_layers = st.multiselect(
                "Active Zoning Layers",
                geojson_files,
                default=geojson_files,
                format_func=lambda x: x.replace(".geojson", "")
                .replace("_", " ")
                .title(),
            )
            if selected_layers:
                render_multi_layer_map(selected_layers, height=560)

# ==========================================
# 7. M&E & RISK MATRIX VIEW
# ==========================================
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")

    risk_summary = (
        df_master.groupby("Phase")
        .agg(
            Total_Projects=("PROJECT NO.", "count"),
            Total_Cost_B=("Cost_PhP_B", "sum"),
        )
        .reset_index()
    )

    risk_summary["Risk Rating"] = [
        "Low Risk",
        "Medium Risk",
        "High Risk",
        "Low Risk",
    ]
    st.dataframe(risk_summary, use_container_width=True, height=300)
