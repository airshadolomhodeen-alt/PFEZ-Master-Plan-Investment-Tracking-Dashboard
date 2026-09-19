import os
import json
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PFEZ Master Plan & Investment Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM STYLING ---
st.markdown(
    """
    <style>
        .main { background-color: #0E1117; }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        h1, h2, h3 { color: #FAFAFA; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image("https://img.icons8.com/color/96/port.png", width=60)
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
    "**Project:** Polloc Freeport and Economic Zone (PFEZ)\n**Authority:** Bangsamoro Economic Zone Authority (BEZA)[cite: 1]"
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
            "Commercial Spine Setup",
            "Staff Housing Cluster Phase 1",
        ],
        "Phase": [
            "Phase 1 (2026-2030)",
            "Phase 1 (2026-2030)",
            "Phase 2 (2029-2035)",
            "Phase 2 (2029-2035)",
            "Phase 3 (2032-2038)",
            "Phase 1 (2026-2030)",
            "Phase 2 (2029-2035)",
        ],
        "Sector": [
            "Port Infrastructure",
            "Logistics / Transport",
            "Halal Industry",
            "Environment / Tourism",
            "Utilities",
            "Commercial",
            "Residential",
        ],
        "Cost_PhP_M": [1800, 650, 900, 250, 750, 400, 550],
        "Status": [
            "In Progress",
            "Completed",
            "Planning",
            "Not Started",
            "Planning",
            "In Progress",
            "Not Started",
        ],
        "Risk_Level": ["Low", "Low", "Medium", "Low", "High", "Medium", "Low"],
    }
    return pd.DataFrame(data)

df_projects = load_project_data()

# --- 1. DASHBOARD HOME VIEW ---
if nav_selection == "Dashboard Home":
    st.title("🛡️ PFEZ: Master Plan & Investment Tracking Dashboard")
    st.markdown("*Data Source: Phase 3 Site Development Plan and Investment Program (SDPIP) / BEZA*[cite: 1]")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Estimated Cost", value="PhP 5.3 Billion", delta="95 PAPs")
    with col2:
        st.metric(label="Total Programs & Projects", value="95 PAPs", delta="Across 4 Phases")
    with col3:
        st.metric(label="Implementation Period", value="2026 - 2040", delta="Long-term")
    with col4:
        st.metric(label="Overall Completion Status", value="15%", delta="On Track 🟢")

    st.markdown("### Investment Distribution & Project Phasing")
    col_a, col_b = st.columns(2)

    with col_a:
        fig_phase = px.bar(
            df_projects,
            x="Phase",
            y="Cost_PhP_M",
            color="Sector",
            title="Investment by Phase & Sector (PhP Millions)",
            template="plotly_dark",
        )
        st.plotly_chart(fig_phase, use_container_width=True)

    with col_b:
        fig_pie = px.pie(
            df_projects,
            names="Sector",
            values="Cost_PhP_M",
            title="Budget Allocation Share by Sector",
            hole=0.4,
            template="plotly_dark",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# --- 2. INVESTMENT PHASING VIEW ---
elif nav_selection == "Investment Phasing":
    st.title("💰 Investment & Phasing Program")
    st.write("Filter and analyze the financial breakdown across 95 strategic projects.")

    selected_phase = st.selectbox(
        "Filter by Implementation Phase",
        ["All Phases"] + list(df_projects["Phase"].unique()),
    )
    filtered_df = (
        df_projects
        if selected_phase == "All Phases"
        else df_projects[df_projects["Phase"] == selected_phase]
    )
    st.dataframe(filtered_df, use_container_width=True)

# --- 3. SPATIAL MAP VIEWER ---
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.write("Interactive visualization of your QGIS exported layers loaded from GitHub repository.")

    # Find local geojson files in the repository directory
    geojson_files = [f for f in os.listdir(".") if f.endswith(".geojson")]

    if geojson_files:
        selected_layer = st.selectbox("Select Zone Layer to Inspect", geojson_files)
        
        try:
            # Read using geopandas
            gdf = gpd.read_file(selected_layer)
            st.success(f"Successfully loaded layer: **{selected_layer}** ({len(gdf)} features found)")
            
            # Display attribute table
            st.subheader("Layer Attribute Table")
            st.dataframe(gdf.drop(columns="geometry", errors="ignore"), use_container_width=True)

            # Render map if geometry allows
            if not gdf.empty:
                st.subheader("Spatial Distribution Map")
                # Fallback centroid calculation for map center
                centroid = gdf.to_crs(epsg=4326).geometry.centroid.iloc[0]
                lat, lon = centroid.y, centroid.x
                
                # Plotly scatter mapbox or line map
                fig_map = px.choropleth_mapbox(
                    gdf,
                    geojson=gdf.geometry,
                    locations=gdf.index,
                    center={"lat": lat, "lon": lon},
                    zoom=14,
                    mapbox_style="carto-positron",
                    title=f"Map View: {selected_layer.replace('.geojson', '')}"
                )
                fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, height=500)
                st.plotly_chart(fig_map, use_container_width=True)

        except Exception as e:
            st.error(f"Error processing {selected_layer}: {e}")
    else:
        st.warning("No `.geojson` files found in the current directory.")

# --- 4. M&E & RISK MATRIX VIEW ---
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    st.write("Track project progress statuses, KPIs, and pre-identified risk parameters.")
    st.dataframe(df_projects, use_container_width=True)
