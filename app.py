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
    page_title="PFEZ Master Plan & Revenue Analytics Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM ENTERPRISE & MOBILE-RESPONSIVE STYLING ---
st.markdown(
    """
    <style>
        .main { background-color: #0E1117; }
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; padding-left: 1.5rem; padding-right: 1.5rem; }
        h1, h2, h3 { color: #FAFAFA; }
        .stMetric {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 10px;
            border-radius: 6px;
        }
        
        /* Mobile Screen Responsiveness */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 100% !important;
                min-width: 100% !important;
                margin-bottom: 10px;
            }
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- TOP HEADER BANNER ---
st.markdown(
    """
    <div style="background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D; text-align: center; margin-bottom: 20px;">
        <h2 style="color: #58A6FF; margin: 0; font-size: 20px;">POLLOC FREEPORT AND ECONOMIC ZONE (PFEZ): MASTER PLAN & REVENUE FORECASTING DASHBOARD</h2>
        <p style="color: #8B949E; margin: 5px 0 0 0; font-size: 12px;">Data Source: Phase 3 SDPIP Report / Bangsamoro Economic Zone Authority (BEZA)</p>
    </div>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://img.icons8.com/color/96/port.png", width=50)
st.sidebar.title("PFEZ Navigation")
nav_selection = st.sidebar.radio(
    "Go to",
    [
        "Dashboard Home",
        "Revenue Analytics & Forecasting",
        "Investment Phasing",
        "Spatial Map Viewer",
        "M&E & Risk Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Project:** PFEZ Master Plan\n**Timeline:** 2026–2040\n**Total Budget:** PhP 5.3B\n**Zoning Layers:** Active Vector Layers"
)

# --- PROJECT AUTHOR & CONTACT INFO ---
st.sidebar.markdown("---")
st.sidebar.markdown("### Project Lead")

try:
    st.sidebar.image("AirSad.png", width=130)
except Exception:
    st.sidebar.image("https://img.icons8.com/fluency/96/user-male-circle.png", width=80)

st.sidebar.markdown(
    """
    <div style='font-size: 11px; color: #FFFFFF; font-weight: bold; margin-top: 8px; line-height: 1.3;'>
        ENGR. AIRSAD R. OLOMODIN, MBA, CBE
    </div>
    <div style='font-size: 11px; color: #C9D1D9; margin-top: 6px; line-height: 1.2;'>
        📱 0975-256-9055 / 0929-336-7787
    </div>
    <div style='font-size: 11px; color: #C9D1D9; margin-top: 4px; line-height: 1.2;'>
        ✉️ airsadolomodin@gmail.com
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

# --- PROFESSIONAL DISCLAIMER ---
st.sidebar.markdown(
    """
    <div style='font-size: 10px; color: #8B949E; line-height: 1.3;'>
    <b>Professional Disclaimer:</b><br>
    This dashboard is an interactive prototype developed for strategic evaluation and planning purposes. It utilizes Phase 3 SDPIP data and spatial layers from the Bangsamoro Economic Zone Authority (BEZA). All rights reserved.
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

# --- LOAD AND CLEAN REVENUE DATA ---
@st.cache_data
def load_revenue_data():
    file_path = "REVENUE.xlsx"
    if os.path.exists(file_path):
        df_raw = pd.read_excel(file_path, sheet_name=0)
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

# --- HELPER FUNCTION FOR FOLIUM MAP ---
def render_multi_layer_map(selected_files, height=450):
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

# --- 1. DASHBOARD HOME VIEW ---
if nav_selection == "Dashboard Home":
    st.markdown("### Key Performance Indicators (KPIs) - Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Estimated Cost", value="PhP 5.3 Billion", delta="95 PAPs Total")
    with kpi2:
        st.metric(label="Historical Collected Revenue", value=f"PhP {df_rev['Collected_Revenue'].sum()/1e6:.2f} M", delta="2024–2026 Historical")
    with kpi3:
        st.metric(label="Planning Horizon", value="2026 - 2040", delta="Long-term Master Plan")
    with kpi4:
        st.metric(label="Phase 1 Budget", value="PhP 264.4 M", delta="39 Initial PAPs")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_phase = px.bar(
            df_projects,
            x="Phase",
            y="Cost_PhP_M",
            color="Status",
            title="Investment Capital by Phase & Status (PhP Millions)",
            template="plotly_dark",
            height=320,
        )
        fig_phase.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_phase, use_container_width=True)

    with chart_col2:
        fig_pie = px.pie(
            df_projects,
            names="Project Name",
            values="Cost_PhP_M",
            title="Major Project Cost Distribution Share",
            hole=0.4,
            template="plotly_dark",
            height=320,
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

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
        st.markdown("### Summary Investment Program Table")
        st.dataframe(df_projects[["Project Name", "Phase", "Cost_PhP_M", "Status"]], height=260, use_container_width=True)

# --- 2. REVENUE ANALYTICS & FORECASTING VIEW ---
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & PAP Master Plan Forecasting")
    st.markdown("Time series evaluation of monthly historical revenue collection (2024–2026) and long-term revenue forecasting under the **PFEZ Master Plan PAPs (2026–2040)**.")

    st.markdown("### 1. Historical Revenue Collection Time Series (2024–2026)")
    
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Traditional"], mode='lines+markers', name='Traditional Revenue'))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Non_Traditional"], mode='lines+markers', name='Non-Traditional Revenue'))
    fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Collected_Revenue"], mode='lines+markers', name='Total Collected Revenue', line=dict(width=3, color='#58A6FF')))
    
    fig_hist.update_layout(
        template="plotly_dark",
        title="Monthly Revenue Collections Breakdown (PhP)",
        xaxis_title="Timeline",
        yaxis_title="Revenue (PhP)",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10)
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
        
        # Phase Multipliers driven by PAP deployment:
        # Phase 1: BOSS & Baseline (2026-2030)
        # Phase 2: Container Yard & Halal Hub (2029-2035)
        # Phase 3: Seawall & Reclamation (2032-2038)
        # Phase 4: IT Park & Eco-Tourism (2035-2040)
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
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_fore, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("2030 Expected Annual Revenue", f"PhP {df_forecast.loc[df_forecast['Year']==2030, 'Master Plan Integrated Forecast (PhP M)'].values[0]:.2f} M", "Phase 1 Impact")
    with c2:
        st.metric("2035 Expected Annual Revenue", f"PhP {df_forecast.loc[df_forecast['Year']==2035, 'Master Plan Integrated Forecast (PhP M)'].values[0]:.2f} M", "Phase 2 & 3 Online")
    with c3:
        st.metric("Total Master Plan Value Add", f"PhP {(df_forecast['Master Plan Integrated Forecast (PhP M)'].sum() - df_forecast['Baseline Projection (PhP M)'].sum()):.2f} M", "2026-2040 Cumulative Uplift")

# --- 3. INVESTMENT PHASING VIEW ---
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

# --- 4. SPATIAL MAP VIEWER & OPEN ZONE MAP ---
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.markdown("Interactive GIS viewer integrating local vector zoning layers and the **Open Zone Map** global economic zone repository.")

    map_type = st.radio("Select View Mode:", ["Local QGIS Zoning Layers (Folium)", "Global Open Zone Map (Embedded Iframe)"], horizontal=True)

    if map_type == "Global Open Zone Map (Embedded Iframe)":
        st.markdown("### Global Special Economic Zones (Open Zone Map)")
        st.write("Displaying Open Zone Map interactive portal via iframe.")
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
                    st.markdown("### 🗂️ Zoning Layers Legend")
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

# --- 5. M&E & RISK MATRIX VIEW ---
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
