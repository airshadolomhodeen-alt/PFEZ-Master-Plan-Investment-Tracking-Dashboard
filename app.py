import os
import json
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
    page_title="PFEZ Master Plan & Technical Capacity Dashboard",
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

# --- TOP EXECUTIVE BANNER ---
st.markdown(
    """
    <div style="background-color: #161B22; padding: 18px 24px; border-radius: 8px; border: 1px solid #30363D; text-align: left; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="background-color: #238636; color: #FFFFFF; font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 12px; letter-spacing: 0.5px;">EXECUTIVE STRATEGY BRIEF</span>
            <h2 style="color: #58A6FF; margin: 6px 0 2px 0; font-size: 22px; font-weight: 700;">POLLOC FREEPORT AND ECONOMIC ZONE (PFEZ)</h2>
            <p style="color: #8B949E; margin: 0; font-size: 13px;">Master Development Plan Implementation & Infrastructure Manpower Expansion Framework</p>
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
        "Manpower & Infrastructure Justification",
        "Revenue Analytics & Forecasting",
        "Investment Phasing",
        "Spatial Map Viewer",
        "M&E & Risk Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Project:** PFEZ Master Plan\n\n**Planning Horizon:** 2026–2040\n\n**Total Capital Budget:** PhP 5.3 Billion\n\n**Phase 1 Deliverables:** 39 PAPs"
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

# --- LOAD PROJECT DATA ---
@st.cache_data
def load_project_data():
    data = {
        "Project Name": [
            "Institutional Setup & BOSS Establishment",
            "Baseline Studies & Master Plan Updating",
            "Port Operations Zone Expansion & Container Yard",
            "Halal Processing & Certification Hub",
            "Power Substation & Water Distribution System",
            "Wharf Extension & Seawall Construction",
            "Land Reclamation for Port Logistics",
            "IT Park & Ecotourism Development",
        ],
        "Phase": [
            "Phase 1 (2026-2030)",
            "Phase 1 (2026-2030)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 3 (2032-2038)",
            "Phase 3 (2032-2038)",
            "Phase 4 (2035-2040)",
        ],
        "Cost_PhP_M": [114.4, 150.0, 1200.0, 550.0, 250.0, 1800.0, 1200.0, 167.6],
        "Status": [
            "In Progress",
            "In Progress",
            "Planning",
            "Planning",
            "Not Started",
            "Not Started",
            "Not Started",
            "Not Started",
        ],
        "Risk_Level": ["Low", "Low", "Medium", "Low", "Medium", "High", "High", "Low"],
        "PAPs_Count": [20, 19, 18, 10, 4, 10, 6, 8],
    }
    return pd.DataFrame(data)

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

df_projects = load_project_data()
df_rev = load_revenue_data()

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
        """
        <div class="callout-box">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 24px;">🏗️</span>
                <div>
                    <h4 style="margin: 0 0 4px 0; color: #58A6FF; font-size: 15px;">STRATEGIC JUSTIFICATION FOR TECHNICAL MANPOWER EXPANSION</h4>
                    <p style="margin: 0; color: #C9D1D9; font-size: 12px; line-height: 1.5;">
                        The PFEZ Master Development Plan commits <b>PhP 5.3 Billion</b> across 95 Programs and Projects (PAPs). Executing <b>Phase 1 (39 Initial PAPs / PhP 264.4M)</b> requires immediate augmentation of key engineering positions: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>. Without this critical technical capacity, project execution delays threaten the foundational works and projected revenue trajectory.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- KEY EXECUTIVE METRICS ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Investment Capital", value="PhP 5.3 Billion", delta="95 PAPs Across 4 Phases")
    with kpi2:
        st.metric(label="Phase 1 Foundation Budget", value="PhP 264.4 Million", delta="39 Immediate Deliverables")
    with kpi3:
        st.metric(label="Engineering Position Request", value="4 Engineering Positions", delta="Engineer V, III, and two I")
    with kpi4:
        st.metric(label="Historical Revenue Collection", value=f"PhP {df_rev['Collected_Revenue'].sum()/1e6:.2f} M", delta="2024–2026 Baseline")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- CHARTS ROW 1 ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        fig_phase = px.bar(
            df_projects,
            x="Phase",
            y="Cost_PhP_M",
            color="Status",
            title="Capital Expenditure Allocation by Phase & Execution Status (PhP M)",
            template="plotly_dark",
            height=320,
            color_discrete_map={"In Progress": "#58A6FF", "Planning": "#F0883E", "Not Started": "#30363D"}
        )
        fig_phase.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_phase, use_container_width=True)

    with chart_col2:
        fig_pie = px.pie(
            df_projects,
            names="Project Name",
            values="Cost_PhP_M",
            title="Major Project Capital Share Distribution",
            hole=0.45,
            template="plotly_dark",
            height=320,
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_pie.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

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
        
        # Calculate Trend Line
        x_numeric = np.arange(len(df_rev))
        y_vals = df_rev["Collected_Revenue"].values
        slope, intercept = np.polyfit(x_numeric, y_vals, 1)
        trend_line = slope * x_numeric + intercept
        
        if slope > 0:
            trend_status = "📈 UPTREND (+PhP 3.34k/mo)"
            trend_color = "#238636"
        else:
            trend_status = "📉 DOWNTREND"
            trend_color = "#DA3633"

        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 11px; color: #8B949E;">Baseline Historical Collection Trend:</span><br>
                    <span style="font-size: 16px; font-weight: bold; color: {trend_color};">{trend_status}</span>
                </div>
                <div style="font-size: 11px; color: #C9D1D9; text-align: right;">
                    Monthly Avg: <b>PhP 1.93M</b><br>Cumulative: <b>PhP 57.80M</b>
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
# 2. MANPOWER & INFRASTRUCTURE JUSTIFICATION VIEW
# ==========================================
elif nav_selection == "Manpower & Infrastructure Justification":
    st.title("👷 Technical Engineering Manpower Justification")
    st.markdown("Detailed resource analysis justifying the operational necessity for **Engineer V, Engineer III, and two Engineer I** positions to execute the **PFEZ Master Development Plan**.")

    st.markdown(
        """
        <div class="callout-box">
            <h4 style="margin: 0 0 6px 0; color: #58A6FF;">Core Engineering Rationale</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.5;">
                Foundational works—such as the <b>Wharf Extension, Land Reclamation, Container Yard Expansion, and BOSS Infrastructure</b>—are complex, highly technical engineering projects. Establishing an active engineering unit composed of an <b>Engineer V (Division Chief/Lead), Engineer III (Senior Technical Lead), and two Engineer I (Project Supervision & Field Engineers)</b> guarantees quality compliance, timely execution, and risk mitigation across all 39 Phase 1 PAPs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Specific Engineering Position Requirements")
        
        staff_data = pd.DataFrame({
            "Engineering Position": [
                "Engineer V (Division Head / Strategic Lead)",
                "Engineer III (Senior Project / Technical Lead)",
                "Engineer I - Position A (Field & Construction Supervision)",
                "Engineer I - Position B (Spatial Data & QA/QC Engineer)"
            ],
            "Requested Positions": [1, 1, 1, 1]
        })
        
        fig_staff = go.Figure()
        fig_staff.add_trace(go.Bar(
            y=staff_data["Engineering Position"], 
            x=staff_data["Requested Positions"], 
            name="Requested Personnel", 
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
            xaxis=dict(dtick=1, range=[0, 2]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_staff, use_container_width=True)

    with col2:
        st.markdown("### Role Allocation & Responsibilities")
        
        risk_table = pd.DataFrame({
            "Position": ["Engineer V", "Engineer III", "Engineer I (Field)", "Engineer I (QA/QC & GIS)"],
            "Primary Functional Mandate": [
                "Strategic infrastructure leadership, division management, & inter-agency coordination",
                "Detailed engineering design review, contract monitoring, & procurement compliance",
                "On-site monitoring, project inspection, & civil works quality verification",
                "Geospatial layer integration, structural QA/QC documentation, & monitoring report generation"
            ]
        })
        st.dataframe(risk_table, use_container_width=True, height=340)

# ==========================================
# 3. REVENUE ANALYTICS & FORECASTING VIEW
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & Master Plan Forecasting")
    st.markdown("Time series evaluation of monthly historical revenue collection (2024–2026) and long-term revenue forecasting under the **PFEZ Master Plan PAPs (2026–2040)**.")

    st.markdown("### 1. Historical Revenue Collection Time Series (2024–2026)")
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Traditional"], mode='lines+markers', name='Traditional Revenue', line=dict(color='#A371F7')))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Non_Traditional"], mode='lines+markers', name='Non-Traditional Revenue', line=dict(color='#F0883E')))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Collected_Revenue"], mode='lines+markers', name='Total Collected Revenue', line=dict(width=3, color='#58A6FF')))
    
    fig_hist.update_layout(
        template="plotly_dark",
        title="Monthly Revenue Collections Breakdown (PhP)",
        xaxis_title="Timeline",
        yaxis_title="Revenue (PhP)",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    st.markdown("### 2. Master Plan PAP Implementation Revenue Forecast Model (2026–2040)")
    
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        base_annual_growth = st.slider("Baseline Organic Annual Growth Rate (%)", min_value=1.0, max_value=10.0, value=3.5, step=0.5)
    with col_param2:
        pap_efficiency_boost = st.slider("PAPs Implementation Multiplier", min_value=1.0, max_value=2.5, value=1.4, step=0.1)

    annual_2025_base = df_rev[df_rev["Date"].dt.year == 2025]["Collected_Revenue"].sum()
    
    years = list(range(2026, 2041))
    baseline_proj = []
    masterplan_proj = []
    
    for y in years:
        n = y - 2025
        b_val = annual_2025_base * ((1 + (base_annual_growth / 100)) ** n)
        baseline_proj.append(b_val)
        
        if y <= 2028:
            phase_multiplier = 1.20
        elif y <= 2031:
            phase_multiplier = 1.55
        elif y <= 2035:
            phase_multiplier = 2.00
        else:
            phase_multiplier = 2.40
            
        m_val = b_val * (1 + (phase_multiplier - 1) * pap_efficiency_boost)
        masterplan_proj.append(m_val)

    df_forecast = pd.DataFrame({
        "Year": years,
        "Baseline Projection (PhP M)": [v / 1e6 for v in baseline_proj],
        "Master Plan Integrated Forecast (PhP M)": [v / 1e6 for v in masterplan_proj]
    })

    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(
        x=df_forecast["Year"], 
        y=df_forecast["Baseline Projection (PhP M)"], 
        mode='lines+markers', 
        name='Business-As-Usual (Without PAPs)', 
        line=dict(dash='dash', color='#8B949E')
    ))
    fig_fore.add_trace(go.Scatter(
        x=df_forecast["Year"], 
        y=df_forecast["Master Plan Integrated Forecast (PhP M)"], 
        mode='lines+markers', 
        name='Master Plan Integrated Revenue', 
        line=dict(width=3, color='#238636')
    ))

    fig_fore.update_layout(
        template="plotly_dark",
        title="Projected Annual Revenue Trajectory (2026–2040) in PhP Millions",
        xaxis_title="Year",
        yaxis_title="Annual Revenue (PhP Millions)",
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_fore, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("2030 Expected Annual Revenue", f"PhP {df_forecast.loc[df_forecast['Year']==2030, 'Master Plan Integrated Forecast (PhP M)'].values[0]:.2f} M", "Phase 1 Impact")
    with c2:
        st.metric("2035 Expected Annual Revenue", f"PhP {df_forecast.loc[df_forecast['Year']==2035, 'Master Plan Integrated Forecast (PhP M)'].values[0]:.2f} M", "Phase 2 & 3 Online")
    with c3:
        st.metric("Total Master Plan Value Add", f"PhP {(df_forecast['Master Plan Integrated Forecast (PhP M)'].sum() - df_forecast['Baseline Projection (PhP M)'].sum()):.2f} M", "2026-2040 Cumulative Uplift")

# ==========================================
# 4. INVESTMENT PHASING VIEW
# ==========================================
elif nav_selection == "Investment Phasing":
    st.title("💰 Investment & Phasing Program (2026–2040)")
    st.markdown("Detailed breakdown of the **95 Programs and Projects (PAPs)** amounting to **PhP 5.3 Billion** across 4 distinct phases as outlined in the Phase 3 SDPIP Report.")
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Phase 1 (2026-2030)", "PhP 264.4 M", "39 PAPs")
    with col_p2:
        st.metric("Phase 2 (2029-2035)", "PhP 2.0 B", "32 PAPs")
    with col_p3:
        st.metric("Phase 3 (2032-2038)", "PhP 3.0 B", "16 PAPs")
    with col_p4:
        st.metric("Phase 4 (2035-2040)", "PhP 167.6 M", "8 PAPs")
        
    st.markdown("---")
    st.dataframe(df_projects, use_container_width=True)

# ==========================================
# 5. SPATIAL MAP VIEWER & OPEN ZONE MAP
# ==========================================
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.markdown("Interactive GIS viewer integrating local vector zoning layers and the **Open Zone Map** global economic zone repository.")

    map_type = st.radio("Select View Mode:", ["Local QGIS Zoning Layers (Folium)", "Global Open Zone Map (Embedded Iframe)"], horizontal=True)

    if map_type == "Global Open Zone Map (Embedded Iframe)":
        st.markdown("### Global Special Economic Zones (Open Zone Map)")
        components.iframe(src="https://www.openzonemap.com/map", height=650, scrolling=True)

    else:
        geojson_files = sorted([f for f in os.listdir(".") if f.endswith(".geojson")])
        
        if geojson_files:
            st.write("Select one or multiple QGIS vector layers to display on the master map:")
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
                    st.markdown("<p style='font-size: 12px; color: #8B949E;'>Active zones currently rendered:</p>", unsafe_allow_html=True)
                    
                    if legend_items:
                        for name, col in legend_items:
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; background-color: #161B22; border: 1px solid #30363D; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">
                                    <span style="width: 14px; height: 14px; background-color: {col}; border: 1px solid #ffffff; display: inline-block; margin-right: 10px; border-radius: 3px; flex-shrink: 0;"></span>
                                    <span style="font-size: 12px; color: #FAFAFA; font-weight: 500; word-break: break-word;">{name}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No active layers selected.")
            else:
                st.info("Select at least one layer above to render the map.")
        else:
            st.warning("No `.geojson` files found in the repository. Please ensure QGIS vector exports are placed in the app directory.")

# ==========================================
# 6. M&E & RISK MATRIX VIEW
# ==========================================
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    st.markdown("Tracking project risks, mitigation measures, and performance indicators across the PFEZ master development lifecycle.")
    
    risk_df = df_projects[["Project Name", "Phase", "Risk_Level", "Status"]].copy()
    risk_df["Mitigation Strategy"] = [
        "Early institutional alignment with BEZA and BARMM ministries",
        "Engage technical consultants for comprehensive baseline data",
        "Establish PPP frameworks and secure ODA co-financing",
        "Strict adherence to Halal accreditation standards and stakeholder engagement",
        "Coordinate with local power cooperatives and DPWH",
        "Phased marine engineering studies and environmental safeguards",
        "Rigorous geotechnical and hydrodynamic modeling for reclamation",
        "Incorporate green building standards and renewable energy components",
    ]
    st.dataframe(risk_df, use_container_width=True)
