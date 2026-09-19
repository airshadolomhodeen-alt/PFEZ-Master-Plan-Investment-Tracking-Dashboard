import os
import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PFEZ Master Plan & Investment Tracking Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM ENTERPRISE STYLING ---
st.markdown(
    """
    <style>
        .main { background-color: #0E1117; }
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; }
        h1, h2, h3 { color: #FAFAFA; }
        .stMetric {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 10px;
            border-radius: 6px;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- TOP HEADER BANNER ---
st.markdown(
    """
    <div style="background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D; text-align: center; margin-bottom: 20px;">
        <h2 style="color: #58A6FF; margin: 0; font-size: 22px;">POLLOC FREEDOM AND ECONOMIC ZONE (PFEZ): MASTER PLAN & INVESTMENT TRACKING DASHBOARD</h2>
        <p style="color: #8B949E; margin: 5px 0 0 0; font-size: 13px;">Data Source: Phase 3 SDPIP Report / Bangsamoro Economic Zone Authority (BEZA)[cite: 1]</p>
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
    "**Project:** PFEZ Master Plan\n**Timeline:** 2026–2040[cite: 1]\n**Total Budget:** PhP 5.3B[cite: 1]"
)

# --- MOCK PROJECT DATA ---
@st.cache_data
def load_project_data():
    data = {
        "Project Name": [
            "New Container Terminal Construction",
            "Access Road & Bridge Upgrading",
            "Halal Processing Hub Facility",
            "Mangrove Ecopark Development",
            "Power Substation & Utilities",
        ],
        "Phase": [
            "Phase 1 (2026-2030)",
            "Phase 1 (2026-2030)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 3 (2032-2038)",
        ],
        "Cost_PhP_M": [1800, 650, 900, 250, 750],
        "Status": ["In Progress", "Completed", "Planning", "Not Started", "Planning"],
        "Risk_Level": ["Low", "Low", "Medium", "Low", "High"],
    }
    return pd.DataFrame(data)

df_projects = load_project_data()

# --- 1. DASHBOARD HOME VIEW ---
if nav_selection == "Dashboard Home":
    
    # KPI METRICS ROW
    st.markdown("### Key Performance Indicators (KPIs) - Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Estimated Cost", value="PhP 5.3 Billion", delta="95 PAPs")
    with kpi2:
        st.metric(label="Total Programs & Projects", value="95 PAPs", delta="Across 4 Phases")
    with kpi3:
        st.metric(label="Implementation Period", value="2026 - 2040", delta="Long-term")
    with kpi4:
        st.metric(label="Overall Completion Status", value="15%", delta="On Track 🟢")

    st.markdown("---")

    # CHARTS ROW
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_phase = px.bar(
            df_projects,
            x="Phase",
            y="Cost_PhP_M",
            color="Status",
            title="Investment by Phase & Status (PhP Millions)",
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
            title="Top Project Cost Distribution Share",
            hole=0.4,
            template="plotly_dark",
            height=320,
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # BOTTOM GRID: MAP VIEWER & RISK TABLE
    bot_col1, bot_col2 = st.columns(2)
    with bot_col1:
        st.markdown("### Spatial Development & Land Use Map Viewer")
        geojson_files = [f for f in os.listdir(".") if f.endswith(".geojson")]
        if geojson_files:
            selected_zone = st.selectbox("Filter by Zone Layer", geojson_files, key="home_zone")
            try:
                gdf = gpd.read_file(selected_zone)
                st.success(f"Loaded layer: {selected_zone} ({len(gdf)} records)")
                st.dataframe(gdf.drop(columns="geometry", errors="ignore"), height=180, use_container_width=True)
            except Exception as e:
                st.error(f"Error reading layer: {e}")
        else:
            st.warning("No geojson files found.")

    with bot_col2:
        st.markdown("### Monitoring & Evaluation (M&E) / Risk Matrix")
        st.dataframe(df_projects, height=220, use_container_width=True)

# --- 2. INVESTMENT PHASING VIEW ---
elif nav_selection == "Investment Phasing":
    st.title("💰 Investment & Phasing Program")
    st.dataframe(df_projects, use_container_width=True)

# --- 3. SPATIAL MAP VIEWER ---
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    geojson_files = [f for f in os.listdir(".") if f.endswith(".geojson")]
    
    if geojson_files:
        selected_layer = st.selectbox("Select Zone Layer to Inspect", geojson_files, key="map_zone")
        
        try:
            gdf = gpd.read_file(selected_layer)
            st.success(f"Successfully loaded layer: **{selected_layer}** ({len(gdf)} features found)")
            
            # Display attribute table
            st.subheader("Layer Attribute Table")
            st.dataframe(gdf.drop(columns="geometry", errors="ignore"), use_container_width=True)

            # Render map natively using Streamlit
            if not gdf.empty:
                st.subheader("Spatial Map View")
                if gdf.crs is not None and gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs(epsg=4326)
                st.map(gdf)

        except Exception as e:
            st.error(f"Error processing {selected_layer}: {e}")
    else:
            st.warning("No `.geojson` files found in the repository.")

# --- 4. M&E & RISK MATRIX VIEW ---
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    st.dataframe(df_projects, use_container_width=True)
