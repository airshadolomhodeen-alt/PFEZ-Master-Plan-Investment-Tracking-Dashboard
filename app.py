import os
import json
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import plotly.express as px
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PFEZ Master Plan & Investment Tracking Dashboard",
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
        <h2 style="color: #58A6FF; margin: 0; font-size: 20px;">POLLOC FREEDOM AND ECONOMIC ZONE (PFEZ): MASTER PLAN & INVESTMENT TRACKING DASHBOARD</h2>
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
        "Investment Phasing",
        "Spatial Map Viewer",
        "M&E & Risk Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Project:** PFEZ Master Plan\n**Timeline:** 2026–2040\n**Total Budget:** PhP 5.3B\n**Zoning Layers:** 12 Active Files"
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
    unsafe_allow_html=True
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
    unsafe_allow_html=True
)

# --- REAL PROJECT & PHASING DATA (Phase 3 SDPIP / BEZA) ---
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
            "IT Park & Ecotourism Development"
        ],
        "Phase": [
            "Phase 1 (2026-2030)",
            "Phase 1 (2026-2030)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 3 (2032-2038)",
            "Phase 3 (2032-2038)",
            "Phase 4 (2035-2040)"
        ],
        "Cost_PhP_M": [114.4, 150.0, 1200.0, 550.0, 250.0, 1800.0, 1200.0, 167.6],
        "Status": ["In Progress", "In Progress", "Planning", "Planning", "Not Started", "Not Started", "Not Started", "Not Started"],
        "Risk_Level": ["Low", "Low", "Medium", "Low", "Medium", "High", "High", "Low"],
        "PAPs_Count": [20, 19, 18, 10, 4, 10, 6, 8]
    }
    return pd.DataFrame(data)

df_projects = load_project_data()

# --- HELPER FUNCTION FOR SMART MAP RENDERING ---
def render_multi_layer_map(selected_files, height=400):
    layers = []
    all_gdfs = []
    
    color_palette = [
        [88, 166, 255, 120],   # Transparent Blue fill
        [46, 160, 67, 120],    # Transparent Green fill
        [210, 153, 34, 120],   # Transparent Yellow fill
        [248, 81, 73, 120],    # Transparent Red fill
        [137, 87, 229, 120],   # Transparent Purple fill
        [57, 211, 83, 120],    # Transparent Neon Green fill
    ]
    
    for idx, file_name in enumerate(selected_files):
        try:
            gdf = gpd.read_file(file_name)
            if not gdf.empty:
                if gdf.crs is not None and gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs(epsg=4326)
                all_gdfs.append(gdf)
                
                if "PFEZ Boundaries" in file_name or "boundary" in file_name.lower():
                    layer = pdk.Layer(
                        "GeoJsonLayer",
                        json.loads(gdf.to_json()),
                        pickable=True,
                        stroked=True,
                        filled=False,
                        get_line_color=[255, 255, 255, 255],
                        get_line_width=45,
                        line_width_min_pixels=3,
                    )
                else:
                    color = color_palette[idx % len(color_palette)]
                    layer = pdk.Layer(
                        "GeoJsonLayer",
                        json.loads(gdf.to_json()),
                        pickable=True,
                        stroked=True,
                        filled=True,
                        get_fill_color=color,
                        get_line_color=[255, 255, 255, 200],
                        get_line_width=20,
                    )
                layers.append(layer)
        except Exception:
            pass

    if all_gdfs:
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)
        centroid = combined_gdf.geometry.unary_union.centroid
        
        view_state = pdk.ViewState(
            latitude=centroid.y,
            longitude=centroid.x,
            zoom=13,
            pitch=0,
        )
        
        r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style="dark",
            tooltip={"text": "Zoning Layer Feature: {name}" if "name" in combined_gdf.columns else "Zoning Layer Feature"}
        )
        st.pydeck_chart(r, use_container_width=True, height=height)
    else:
        st.warning("Select at least one valid layer to display on the map.")

# --- 1. DASHBOARD HOME VIEW ---
if nav_selection == "Dashboard Home":
    
    st.markdown("### Key Performance Indicators (KPIs) - Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Estimated Cost", value="PhP 5.3 Billion", delta="95 PAPs Total")
    with kpi2:
        st.metric(label="Total Programs & Projects", value="95 PAPs", delta="4 Implementation Phases")
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
                key="home_zone"
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

# --- 2. INVESTMENT PHASING VIEW ---
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

# --- 3. SPATIAL MAP VIEWER ---
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.markdown("Interactive multi-layer GIS viewer integrating QGIS vector layers for the Polloc Freeport and Economic Zone.")
    geojson_files = sorted([f for f in os.listdir(".") if f.endswith(".geojson")])
    
    if geojson_files:
        st.write("Select one or multiple QGIS vector layers to display on the master map:")
        selected_layers = st.multiselect(
            "Active Zoning Layers", 
            geojson_files, 
            default=geojson_files[:min(3, len(geojson_files))],
            format_func=lambda x: x.replace(".geojson", "").replace("_", " ").title()
        )
        
        if selected_layers:
            render_multi_layer_map(selected_layers, height=550)
        else:
            st.info("Select at least one layer above to render the map.")
    else:
        st.warning("No `.geojson` files found in the repository. Please ensure QGIS vector exports are placed in the app directory.")

# --- 4. M&E & RISK MATRIX VIEW ---
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
        "Incorporate green building standards and renewable energy components"
    ]
    st.dataframe(risk_df, use_container_width=True)
