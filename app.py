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

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PFEZ Master Development Plan & Capacity Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        df['Cost_PhP_M'] = df['Cost_PhP'] / 1e6
        return df
    else:
        # Fallback dataset if file is missing
        return pd.DataFrame({
            "PROJECT NO.": range(1, 96),
            "PROJECT TITLE": [f"Sample Master Plan PAP {i}" for i in range(1, 96)],
            "SECTOR": ["Infrastructure"] * 21 + ["Institutional"] * 24 + ["Economic"] * 25 + ["Social"] * 13 + ["Environmental"] * 12,
            "CATEGORY": ["Infrastructure Preparation"] * 95,
            "Cost_PhP": [89724294.0] * 95,
            "Cost_PhP_M": [89.72] * 95
        })

# --- LOAD REVENUE DATA ---
@st.cache_data
def load_revenue_data():
    file_path = "REVENUE.xlsx"
    if os.path.exists(file_path):
        df_raw = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
        clean_rows = []
        for idx in range(2, 32):
            row = df_raw.iloc[idx]
            m_str = str(row["Unnamed: 0"]).strip()
            
            def parse_num(val):
                if pd.isna(val):
                    return 0.0
                s = str(val).replace("₱", "").replace(",", "").replace("\n", "").strip()
                try:
                    return float(s)
                except:
                    return 0.0

            trad = parse_num(row["Unnamed: 2"])
            non_trad = parse_num(row["Unnamed: 4"])
            bto = parse_num(row["Unnamed: 6"])
            bir = parse_num(row["Unnamed: 8"])
            collected = parse_num(row["Unnamed: 10"])
            
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
    else:
        dates = pd.date_range(start="2024-01-01", periods=30, freq="MS")
        return pd.DataFrame({
            "Date": dates,
            "Traditional": 1e6,
            "Non_Traditional": 1e6,
            "BTO_Remittance": 2e6,
            "BIR_Remittance": 2e5,
            "Collected_Revenue": 2.2e6
        })

df_master = load_masterplan_data()
df_rev = load_revenue_data()

# --- TOP EXECUTIVE BANNER ---
st.markdown(
    """
    <div style="background-color: #161B22; padding: 18px 24px; border-radius: 8px; border: 1px solid #30363D; text-align: left; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="background-color: #238636; color: #FFFFFF; font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 12px; letter-spacing: 0.5px;">EXECUTIVE STRATEGY BRIEF</span>
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
        "Master Plan Projects Directory",
        "Manpower Justification",
        "Revenue Analytics & Forecasting",
        "Spatial Map Viewer",
        "M&E & Risk Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"**Project Portfolio:** PFEZ Master Plan\n\n**Total PAPs:** {len(df_master)} Projects\n\n**Total Estimated Capital:** PhP {df_master['Cost_PhP_M'].sum()/1e3:.2f} Billion\n\n**Target Horizon:** 2026–2040"
)

# --- SIDEBAR AUTHOR BRANDING ---
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
        ✉️ airsadolomodin@gmail.com
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

# --- MAP RENDERER HELPER ---
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
# 1. DASHBOARD HOME VIEW
# ==========================================
if nav_selection == "Dashboard Home":

    # --- STRATEGIC THESIS CALLOUT BANNER ---
    st.markdown(
        f"""
        <div class="callout-box">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🏗️️</span>
                <div>
                    <h4 style="margin: 0 0 4px 0; color: #58A6FF; font-size: 15px;">STRATEGIC JUSTIFICATION FOR TECHNICAL ENGINEERING MANPOWER EXPANSION</h4>
                    <p style="margin: 0; color: #C9D1D9; font-size: 12px; line-height: 1.5;">
                        The PFEZ Master Development Plan commits <b>PhP {df_master['Cost_PhP_M'].sum()/1e3:.2f} Billion</b> across <b>{len(df_master)} Programs and Projects (PAPs)</b>. To successfully execute this multi-sectoral capital program, BEZA urgently requires technical reinforcement: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>. Without dedicated engineering oversight, procurement bottlenecks and project management delays will jeopardize implementation timelines.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- KEY EXECUTIVE METRICS ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(label="Total Capital Budget", value=f"PhP {df_master['Cost_PhP_M'].sum()/1e3:.2f} Billion", delta=f"{len(df_master)} Official PAPs")
    with k2:
        infra_cost = df_master[df_master['SECTOR'] == 'Infrastructure']['Cost_PhP_M'].sum()
        st.metric(label="Infrastructure Allocation", value=f"PhP {infra_cost:.2f} Million", delta=f"{len(df_master[df_master['SECTOR'] == 'Infrastructure'])} Major Works")
    with k3:
        st.metric(label="Requested Personnel", value="4 Positions", delta="Engineer V, III, and two I")
    with k4:
        st.metric(label="Historical Revenue Collection", value=f"PhP {df_rev['Collected_Revenue'].sum()/1e6:.2f} M", delta="2024–2026 Baseline")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- CHARTS ROW 1 ---
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        sector_agg = df_master.groupby('SECTOR')['Cost_PhP_M'].sum().reset_index()
        fig_sec = px.bar(
            sector_agg,
            x="SECTOR",
            y="Cost_PhP_M",
            text_auto=".1f",
            title="Capital Budget Allocation by Sector (PhP Millions)",
            template="plotly_dark",
            height=320,
            color="SECTOR",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_sec.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    with c_col2:
        cat_agg = df_master.groupby('CATEGORY')['Cost_PhP_M'].sum().reset_index().sort_values('Cost_PhP_M', ascending=False)
        fig_cat = px.pie(
            cat_agg.head(8),
            names="CATEGORY",
            values="Cost_PhP_M",
            title="Top 8 Investment Categories by Capital Share",
            hole=0.45,
            template="plotly_dark",
            height=320,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_cat.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- CHARTS ROW 2 ---
    bot_col1, bot_col2 = st.columns(2)
    
    with bot_col1:
        st.markdown("### Spatial Zoning Quick Viewer")
        geojson_files = sorted([f for f in os.listdir(".") if f.endswith(".geojson")])
        if geojson_files:
            selected_home_zone = st.selectbox(
                "Select Zone Layer",
                geojson_files,
                format_func=lambda x: x.replace(".geojson", "").replace("_", " ").title(),
                key="home_zone",
            )
            try:
                render_multi_layer_map([selected_home_zone], height=260)
            except Exception as e:
                st.error(f"Error reading layer: {e}")
        else:
            st.warning("No geojson files found in directory.")

    with bot_col2:
        st.markdown("### Historical Revenue Time Series & Trend Analysis")
        
        x_numeric = np.arange(len(df_rev))
        y_vals = df_rev["Collected_Revenue"].values
        slope, intercept = np.polyfit(x_numeric, y_vals, 1)
        trend_line = slope * x_numeric + intercept
        
        trend_status = "📈 UPTREND (+PhP 3.34k/mo)" if slope > 0 else "📉 DOWNTREND"
        trend_color = "#238636" if slope > 0 else "#DA3633"

        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 11px; color: #8B949E;">Baseline Historical Collection Trend:</span><br>
                    <span style="font-size: 16px; font-weight: bold; color: {trend_color};">{trend_status}</span>
                </div>
                <div style="font-size: 11px; color: #C9D1D9; text-align: right;">
                    Monthly Avg: <b>PhP {df_rev['Collected_Revenue'].mean()/1e6:.2f}M</b><br>Cumulative: <b>PhP {df_rev['Collected_Revenue'].sum()/1e6:.2f}M</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_ts = go.Figure()
        fig_ts.add_trace(
            go.Scatter(
                x=df_rev["Date"],
                y=df_rev["Collected_Revenue"],
                mode="lines+markers",
                name="Monthly Collection",
                line=dict(color="#58A6FF", width=2),
                marker=dict(size=4),
            )
        )
        fig_ts.add_trace(
            go.Scatter(
                x=df_rev["Date"],
                y=trend_line,
                mode="lines",
                name="Trendline (OLS)",
                line=dict(color=trend_color, width=2, dash="dash"),
            )
        )

        fig_ts.update_layout(
            template="plotly_dark",
            height=210,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="PhP",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_ts, use_container_width=True)

# ==========================================
# 2. MASTER PLAN PROJECTS DIRECTORY VIEW
# ==========================================
elif nav_selection == "Master Plan Projects Directory":
    st.title("📋 Master Plan Programs & Projects (PAPs) Directory")
    st.markdown(f"Complete database of **{len(df_master)} PAPs** totaling **PhP {df_master['Cost_PhP_M'].sum():,.2f} Million**.")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_sectors = st.multiselect("Filter by Sector:", options=sorted(df_master['SECTOR'].unique()), default=sorted(df_master['SECTOR'].unique()))
    with col_filter2:
        selected_cats = st.multiselect("Filter by Category:", options=sorted(df_master['CATEGORY'].unique()), default=sorted(df_master['CATEGORY'].unique()))

    df_filtered = df_master[(df_master['SECTOR'].isin(selected_sectors)) & (df_master['CATEGORY'].isin(selected_cats))]

    st.markdown(f"**Showing {len(df_filtered)} of {len(df_master)} Projects | Subtotal: PhP {df_filtered['Cost_PhP_M'].sum():,.2f} Million**")

    st.dataframe(
        df_filtered[["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "ESTIMATE AMOUNT"]],
        use_container_width=True,
        height=500
    )

# ==========================================
# 3. MANPOWER & INFRASTRUCTURE JUSTIFICATION VIEW
# ==========================================
elif nav_selection == "Manpower Justification":
    st.title("👷 Technical Engineering Manpower Justification")
    st.markdown("Operational necessity analysis justifying the direct appointment of **Engineer V, Engineer III, and two Engineer I** positions.")

    st.markdown(
        """
        <div class="callout-box">
            <h4 style="margin: 0 0 6px 0; color: #58A6FF;">Core Technical Rationale</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.5;">
                Executing complex infrastructure, port extension, environmental baselines, and institutional development requires an agile, certified technical workforce. Approving the requested headcount—<b>Engineer V (Division Lead), Engineer III (Senior Technical Lead), and two Engineer I positions (Field & QA/QC Engineers)</b>—ensures robust project supervision, timely procurement, and high-quality civil engineering execution across all 95 PAPs.
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
                "Engineer V (Division Chief / Strategic Lead)",
                "Engineer III (Senior Project / Technical Lead)",
                "Engineer I - Position A (Field & Civil Works Supervision)",
                "Engineer I - Position B (QA/QC & Spatial Data Engineer)"
            ],
            "Requested Positions": [1, 1, 1, 1]
        })
        
        fig_staff = go.Figure()
        fig_staff.add_trace(go.Bar(
            y=staff_data["Engineering Position"], 
            x=staff_data["Requested Positions"], 
            name="Personnel Headcount", 
            orientation='h', 
            marker_color='#58A6FF',
            text=staff_data["Requested Positions"],
            textposition='auto'
        ))
        
        fig_staff.update_layout(
            template="plotly_dark",
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(dtick=1, range=[0, 2])
        )
        st.plotly_chart(fig_staff, use_container_width=True)

    with col2:
        st.markdown("### Functional Mandate Breakdown")
        
        roles_table = pd.DataFrame({
            "Position Title": ["Engineer V", "Engineer III", "Engineer I (Field)", "Engineer I (QA/QC & GIS)"],
            "Primary Responsibilities": [
                "Division management, strategic program alignment, and multi-agency infrastructure governance",
                "Detailed engineering design review, technical specifications, and procurement oversight",
                "On-site project inspection, contractor compliance, and civil works measurement",
                "Quality assurance, structural monitoring documentation, and GIS layer integration"
            ]
        })
        st.dataframe(roles_table, use_container_width=True, height=340)

# ==========================================
# 4. REVENUE ANALYTICS & FORECASTING VIEW
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & Master Plan Forecasting")
    st.markdown("Historical revenue analysis (2024–2026) and long-term financial modeling under the **PFEZ Master Plan PAPs (2026–2040)**.")

    st.markdown("### 1. Historical Revenue Breakdown")
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Traditional"], mode='lines+markers', name='Traditional Revenue', line=dict(color='#A371F7')))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Non_Traditional"], mode='lines+markers', name='Non-Traditional Revenue', line=dict(color='#F0883E')))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Collected_Revenue"], mode='lines+markers', name='Total Revenue Collected', line=dict(width=3, color='#58A6FF')))
    
    fig_hist.update_layout(
        template="plotly_dark",
        title="Monthly Revenue Collections (PhP)",
        xaxis_title="Timeline",
        yaxis_title="Revenue (PhP)",
        height=360,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    st.markdown("### 2. Integrated Revenue Forecast Model (2026–2040)")
    
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        base_growth = st.slider("Organic Baseline Annual Growth (%)", min_value=1.0, max_value=10.0, value=3.5, step=0.5)
    with col_param2:
        pap_multiplier = st.slider("PAPs Implementation Multiplier", min_value=1.0, max_value=2.5, value=1.4, step=0.1)

    annual_2025_base = df_rev[df_rev["Date"].dt.year == 2025]["Collected_Revenue"].sum()
    years = list(range(2026, 2041))
    
    baseline_proj = []
    masterplan_proj = []
    
    for y in years:
        n = y - 2025
        b_val = annual_2025_base * ((1 + (base_growth / 100)) ** n)
        baseline_proj.append(b_val)
        
        phase_mult = 1.20 if y <= 2028 else (1.55 if y <= 2031 else (2.00 if y <= 2035 else 2.40))
        m_val = b_val * (1 + (phase_mult - 1) * pap_multiplier)
        masterplan_proj.append(m_val)

    df_forecast = pd.DataFrame({
        "Year": years,
        "Baseline (PhP M)": [v / 1e6 for v in baseline_proj],
        "Master Plan Integrated (PhP M)": [v / 1e6 for v in masterplan_proj]
    })

    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(x=df_forecast["Year"], y=df_forecast["Baseline (PhP M)"], mode='lines+markers', name='Business-As-Usual', line=dict(dash='dash', color='#8B949E')))
    fig_fore.add_trace(go.Scatter(x=df_forecast["Year"], y=df_forecast["Master Plan Integrated (PhP M)"], mode='lines+markers', name='Master Plan Integrated Revenue', line=dict(width=3, color='#238636')))

    fig_fore.update_layout(
        template="plotly_dark",
        title="Projected Annual Revenue Trajectory (PhP Millions)",
        xaxis_title="Year",
        yaxis_title="Annual Revenue (PhP Millions)",
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_fore, use_container_width=True)

# ==========================================
# 5. SPATIAL MAP VIEWER & OPEN ZONE MAP
# ==========================================
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.markdown("Interactive GIS viewer integrating local vector zoning layers and the global economic zone repository.")

    map_type = st.radio("Select View Mode:", ["Local QGIS Zoning Layers (Folium)", "Global Open Zone Map (Embedded Iframe)"], horizontal=True)

    if map_type == "Global Open Zone Map (Embedded Iframe)":
        st.markdown("### Global Special Economic Zones (Open Zone Map)")
        components.iframe(src="https://www.openzonemap.com/map", height=650, scrolling=True)

    else:
        geojson_files = sorted([f for f in os.listdir(".") if f.endswith(".geojson")])
        
        if geojson_files:
            st.write("Select vector layers to display on the master map:")
            selected_layers = st.multiselect(
                "Active Zoning Layers",
                geojson_files,
                default=geojson_files,
                format_func=lambda x: x.replace(".geojson", "").replace("_", " ").title(),
            )
            
            if selected_layers:
                map_col, legend_col = st.columns([3, 1])
                
                with map_col:
                    legend_items = render_multi_layer_map(selected_layers, height=560)
                    
                with legend_col:
                    st.markdown("### 🗂 Zoning Layers Legend")
                    if legend_items:
                        for name, col in legend_items:
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; background-color: #161B22; border: 1px solid #30363D; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">
                                    <span style="width: 14px; height: 14px; background-color: {col}; border: 1px solid #ffffff; display: inline-block; margin-right: 10px; border-radius: 3px; flex-shrink: 0;"></span>
                                    <span style="font-size: 12px; color: #FAFAFA; font-weight: 500;">{name}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No active layers selected.")
            else:
                st.info("Select at least one layer above to render the map.")
        else:
            st.warning("No `.geojson` files found in the directory.")

# ==========================================
# 6. M&E & RISK MATRIX VIEW
# ==========================================
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    st.markdown("Tracking strategic risks, mitigation frameworks, and performance indicators across the Master Plan lifecycle.")
    
    risk_summary = df_master.groupby('SECTOR').agg(
        Total_Projects=('PROJECT NO.', 'count'),
        Total_Cost_M=('Cost_PhP_M', 'sum')
    ).reset_index()

    risk_summary['Risk Rating'] = ['Low', 'Low', 'High', 'Medium', 'Low']
    risk_summary['Primary Mitigation Strategy'] = [
        "Incentive package design & targeted investor roadshows",
        "Comprehensive EIA baseline surveys & regulatory compliance",
        "Dedicated engineering division (Engineer V, III, I) for direct field supervision & QA/QC",
        "Capacity development & inter-agency administrative alignment",
        "Community stakeholder consultations & social development planning"
    ]

    st.dataframe(risk_summary, use_container_width=True, height=300)
