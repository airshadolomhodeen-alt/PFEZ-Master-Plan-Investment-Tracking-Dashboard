import json
import numpy as np
import pandas as pd
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
        .metric-card {
            background-color: #1E2530;
            border: 1px solid #2D3748;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.image(
    "https://img.icons8.com/color/96/port.png", width=60
)  # Placeholder icon
st.sidebar.title("PFEZ Navigations")
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

# --- MOCK DATA GENERATION (Replace with real datasets/CSV if available) ---
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
    st.markdown(
        "*Data Source: Phase 3 Site Development Plan and Investment Program (SDPIP) / BEZA*[cite: 1]"
    )
    st.markdown("---")

    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Estimated Cost", value="PhP 5.3 Billion", delta="95 PAPs"
        )
    with col2:
        st.metric(
            label="Total Programs & Projects",
            value="95 PAPs",
            delta="Across 4 Phases",
        )
    with col3:
        st.metric(
            label="Implementation Period", value="2026 - 2040", delta="Long-term"
        )
    with col4:
        st.metric(
            label="Overall Completion Status", value="15%", delta="On Track 🟢"
        )

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
    st.write(
        "Filter and analyze the financial breakdown across 95 strategic projects."
    )

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

    total_filtered_cost = filtered_df["Cost_PhP_M"].sum()
    st.success(
        f"**Total Cost for Selected Filter:** PhP {total_filtered_cost:,.2f} Million"
    )

# --- 3. SPATIAL MAP VIEWER ---
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")
    st.write(
        "Upload and explore your exported QGIS GeoJSON zoning file to visualize polygons interactively."
    )

    uploaded_geojson = st.file_uploader(
        "Upload your QGIS Zoning GeoJSON file", type=["json", "geojson"]
    )

    if uploaded_geojson is not None:
        try:
            geojson_data = json.load(uploaded_geojson)
            st.success("GeoJSON successfully loaded from QGIS!")

            # Quick summary of features if available
            features = geojson_data.get("features", [])
            st.info(f"Total Zoning Zones/Polygons Detected: {len(features)}")

            # Basic Map using Plotly or PyDeck if coordinates exist
            # (Streamlit built-in map rendering)
            records = []
            for f in features:
                props = f.get("properties", {})
                records.append(props)
            if records:
                st.subheader("Zoning Attributes Table")
                st.dataframe(pd.DataFrame(records), use_container_width=True)

        except Exception as e:
            st.error(f"Error reading GeoJSON file: {e}")
    else:
        st.warning(
            "⚠️ Please upload your exported QGIS GeoJSON file above to render the map layers."
        )

        # Fallback dummy display message
        st.info(
            "Expected QGIS layers include: Port Operations Zone, Commercial Spine, Mangrove Ecopark, Planned Unit Development (PUD), and Residential Zone[cite: 1]."
        )

# --- 4. M&E & RISK MATRIX VIEW ---
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    st.write(
        "Track project progress statuses, KPIs, and pre-identified risk parameters."
    )

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        status_filter = st.selectbox(
            "Filter Status", ["All"] + list(df_projects["Status"].unique())
        )
    with col_filter2:
        risk_filter = st.selectbox(
            "Filter Risk Level",
            ["All"] + list(df_projects["Risk_Level"].unique()),
        )

    m_e_df = df_projects.copy()
    if status_filter != "All":
        m_e_df = m_e_df[m_e_df["Status"] == status_filter]
    if risk_filter != "All":
        m_e_df = m_e_df[m_e_df["Risk_Level"] == risk_filter]

    st.dataframe(m_e_df, use_container_width=True)
