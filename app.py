import os
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
    page_title="PFEZ Master Development Plan & Technical Capacity Dashboard",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM EXECUTIVE DARK STYLING ---
st.markdown(
    """
    <style>
        .main { background-color: #0D1117; }
        .block-container { padding-top: 0.8rem; padding-bottom: 1.5rem; padding-left: 1.5rem; padding-right: 1.5rem; }
        h1, h2, h3, h4 { color: #F0F6FC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        
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

        .phase-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
        }

        @media (max-width: 768px) {
            .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
            div[data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; margin-bottom: 10px; }
        }
    </style>
""",
    unsafe_allow_html=True,
)

# --- STRICT DATA LOADING (NO MOCK FALLBACKS & REMOVED BLANK FUTURE MONTHS) ---
@st.cache_data
def load_masterplan_data():
    file_path = "MASTERPLAN PROJECTS.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, encoding="latin1")
    except Exception:
        try:
            df = pd.read_csv(file_path, encoding="cp1252")
        except Exception:
            return pd.DataFrame()
            
    df.columns = [c.strip() for c in df.columns]
    
    if 'SECTOR' in df.columns:
        df['SECTOR'] = df['SECTOR'].astype(str).str.strip()
    if 'CATEGORY' in df.columns:
        df['CATEGORY'] = df['CATEGORY'].astype(str).str.strip()
    
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
        except ValueError:
            return 0.0

    if 'ESTIMATE AMOUNT' in df.columns:
        df['Cost_PhP'] = df['ESTIMATE AMOUNT'].apply(parse_amount)
        df['Cost_PhP_B'] = df['Cost_PhP'] / 1e9
    else:
        df['Cost_PhP'] = 0.0
        df['Cost_PhP_B'] = 0.0

    def assign_phase(p_no):
        try:
            p_int = int(p_no)
            if p_int <= 39:
                return "Phase 1 (2026–2030)"
            elif p_int <= 71:
                return "Phase 2 (2029–2035)"
            elif p_int <= 87:
                return "Phase 3 (2032–2038)"
            else:
                return "Phase 4 (2035–2040)"
        except (ValueError, TypeError):
            return "Unassigned"

    if 'PROJECT NO.' in df.columns:
        df['Phase'] = df['PROJECT NO.'].apply(assign_phase)
    else:
        df['Phase'] = "Unassigned"

    return df


@st.cache_data
def load_revenue_data():
    file_path = "REVENUE.xlsx"
    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        df_raw = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
        clean_rows = []
        for idx in range(2, len(df_raw)):
            row = df_raw.iloc[idx]
            m_str = str(row["Unnamed: 0"]).strip()
            if m_str == "nan" or "total" in m_str.lower():
                continue
            
            def parse_num(val):
                if pd.isna(val):
                    return 0.0
                s = str(val).replace("₱", "").replace(",", "").replace("\n", "").strip()
                try:
                    return float(s)
                except ValueError:
                    return 0.0

            clean_rows.append({
                "Month_Raw": m_str,
                "Traditional": parse_num(row["Unnamed: 2"]),
                "Non_Traditional": parse_num(row["Unnamed: 4"]),
                "BTO_Remittance": parse_num(row["Unnamed: 6"]),
                "BIR_Remittance": parse_num(row["Unnamed: 8"]),
                "Collected_Revenue": parse_num(row["Unnamed: 10"])
            })
        
        df_clean = pd.DataFrame(clean_rows)
        if not df_clean.empty:
            df_clean["Date"] = pd.date_range(start="2024-01-01", periods=len(df_clean), freq="MS")
            # --- FILTER OUT NO DATA / ZERO REVENUE PERIODS (e.g. July 2026 to Dec 2026) ---
            df_clean = df_clean[df_clean["Collected_Revenue"] > 0].reset_index(drop=True)
            
        return df_clean
    except Exception:
        return pd.DataFrame()

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
try:
    st.sidebar.image("https://img.icons8.com/color/96/port.png", width=45)
except Exception:
    pass

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
if not df_master.empty:
    st.sidebar.info(
        f"**Project Portfolio:** PFEZ Master Plan\n\n**Total PAPs:** {len(df_master)} Projects\n\n**Total Estimated Capital:** PhP {df_master['Cost_PhP_B'].sum():.3f} Billion\n\n**Target Horizon:** 2026–2040 (4 Phases)"
    )
else:
    st.sidebar.warning("MASTERPLAN PROJECTS.csv data file not found or corrupted.")

# --- SIDEBAR AUTHOR BRANDING ---
st.sidebar.markdown("---")
st.sidebar.markdown("### Project Lead & Author")

if os.path.exists("AirSad.png"):
    st.sidebar.image("AirSad.png", width=120)
else:
    try:
        st.sidebar.image("https://img.icons8.com/fluency/96/user-male-circle.png", width=75)
    except Exception:
        pass

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

# --- MAP RENDERER HELPER ---
def render_multi_layer_map(selected_files, height=310):
    all_gdfs = []
    legend_items = []
    total_files = max(len(selected_files), 1)
    
    m = folium.Map(location=[7.34, 124.28], zoom_start=14.5, tiles=None)
    esri_tile_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
    
    folium.TileLayer(
        tiles=esri_tile_url,
        attr="Esri",
        name="Esri World Street Map",
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
        
    st_folium(m, width="100%", height=height)
    return legend_items

# ==========================================
# 1. DASHBOARD HOME VIEW
# ==========================================
if nav_selection == "Dashboard Home":

    if df_master.empty:
        st.error("MASTERPLAN PROJECTS.csv data is missing or unreadable. Please check file path.")
    else:
        total_paps = len(df_master)
        total_cap = df_master['Cost_PhP_B'].sum()
        p1_df = df_master[df_master['Phase'] == 'Phase 1 (2026–2030)']
        p1_cost_b = p1_df['Cost_PhP_B'].sum()
        p1_paps = len(p1_df)

        st.markdown(
            f"""
            <div class="callout-box">
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <span style="font-size: 24px;">🏗</span>
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #58A6FF; font-size: 15px;">STRATEGIC JUSTIFICATION FOR TECHNICAL ENGINEERING MANPOWER EXPANSION</h4>
                        <p style="margin: 0; color: #C9D1D9; font-size: 12px; line-height: 1.5;">
                            The PFEZ Master Development Plan commits <b>PhP {total_cap:.3f} Billion</b> across <b>{total_paps} Programs and Projects (PAPs)</b> structured into <b>4 Implementation Phases (2026–2040)</b>. Executing <b>Phase 1 ({p1_paps} Immediate PAPs)</b> requires technical reinforcement: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>. Without direct engineering oversight, project execution delays threaten foundational works and projected revenue trajectory.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric(label="Total Capital Budget", value=f"PhP {total_cap:.3f} Billion", delta=f"{total_paps} Official PAPs")
        with k2:
            st.metric(label="Phase 1 Immediate Budget", value=f"PhP {p1_cost_b:.3f} Billion", delta=f"{p1_paps} Deliverables")
        with k3:
            st.metric(label="Engineering Request", value="4 Positions", delta="Engineer V, III, and two I")
        with k4:
            rev_total = f"PhP {df_rev['Collected_Revenue'].sum()/1e9:.3f} Billion" if not df_rev.empty else "N/A"
            st.metric(label="Historical Revenue Baseline", value=rev_total, delta="Recorded Actuals")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎯 Evaluator View: Phase Implementation Roadmap")
        
        phase_summary = df_master.groupby('Phase').agg(
            PAPs_Count=('PROJECT NO.', 'count'),
            Total_Budget_B=('Cost_PhP_B', 'sum')
        ).reset_index()

        phases_order = ["Phase 1 (2026–2030)", "Phase 2 (2029–2035)", "Phase 3 (2032–2038)", "Phase 4 (2035–2040)"]
        cols = st.columns(len(phases_order))
        
        colors = ["#58A6FF", "#F0883E", "#A371F7", "#238636"]
        
        for idx, p_name in enumerate(phases_order):
            with cols[idx]:
                p_m = phase_summary[phase_summary['Phase'] == p_name]
                if not p_m.empty:
                    val_b = p_m['Total_Budget_B'].values[0]
                    cnt = p_m['PAPs_Count'].values[0]
                    st.markdown(
                        f"""
                        <div class="phase-card" style="border-top: 4px solid {colors[idx % len(colors)]};">
                            <span style="background-color: {colors[idx % len(colors)]}; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">{p_name.upper()}</span>
                            <h3 style="color: {colors[idx % len(colors)]}; margin: 8px 0 2px 0; font-size: 18px;">PhP {val_b:,.3f} B</h3>
                            <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{cnt} PAPs</b></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown("<br>", unsafe_allow_html=True)

        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            fig_phase = px.bar(
                phase_summary,
                x="Phase",
                y="Total_Budget_B",
                text_auto=".3f",
                title="Capital Expenditure Allocation by Implementation Phase (PhP Billion)",
                template="plotly_dark",
                height=330,
                color="Phase",
                color_discrete_sequence=colors
            )
            fig_phase.update_layout(
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="PhP Billion",
                showlegend=False
            )
            st.plotly_chart(fig_phase, use_container_width=True)

        with c_col2:
            sector_agg = df_master.groupby('SECTOR')['Cost_PhP_B'].sum().reset_index()
            fig_sec = px.pie(
                sector_agg,
                names="SECTOR",
                values="Cost_PhP_B",
                title="Capital Budget Distribution across Sectors",
                hole=0.45,
                template="plotly_dark",
                height=330,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_sec.update_layout(
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_sec, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

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
                st.warning("No .geojson files available in current working directory.")

        with bot_col2:
            st.markdown("### Historical Revenue Time Series & Trend Analysis")
            if not df_rev.empty and "Collected_Revenue" in df_rev.columns:
                x_numeric = np.arange(len(df_rev))
                y_vals = df_rev["Collected_Revenue"].values
                
                if len(y_vals) > 1:
                    slope, intercept = np.polyfit(x_numeric, y_vals, 1)
                    trend_line = slope * x_numeric + intercept
                    trend_status = "📈 UPTREND" if slope >= 0 else "📉 DOWNTREND"
                    trend_color = "#238636" if slope >= 0 else "#DA3633"

                    st.markdown(
                        f"""
                        <div style="background-color: #161B22; border: 1px solid #30363D; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 11px; color: #8B949E;">Actual Historical Collection Trend:</span><br>
                                <span style="font-size: 16px; font-weight: bold; color: {trend_color};">{trend_status}</span>
                            </div>
                            <div style="font-size: 11px; color: #C9D1D9; text-align: right;">
                                Monthly Avg: <b>PhP {df_rev['Collected_Revenue'].mean()/1e6:.2f} Million</b><br>Cumulative: <b>PhP {df_rev['Collected_Revenue'].sum()/1e9:.3f} Billion</b>
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
                else:
                    st.info("Insufficient revenue records to establish trendline.")
            else:
                st.warning("REVENUE.xlsx data not available.")

# ==========================================
# 2. INVESTMENT PHASING VIEW
# ==========================================
elif nav_selection == "Investment Phasing (Phases 1–4)":
    st.title("💰 Investment & Phasing Program (2026–2040)")
    
    if df_master.empty:
        st.error("No project data available in MASTERPLAN PROJECTS.csv.")
    else:
        phases = sorted(df_master['Phase'].unique())
        
        cols = st.columns(len(phases))
        for idx, p in enumerate(phases):
            p_sub = df_master[df_master['Phase'] == p]
            with cols[idx]:
                st.metric(p, f"PhP {p_sub['Cost_PhP_B'].sum():.3f} B", f"{len(p_sub)} PAPs")
            
        st.markdown("---")
        
        selected_phase = st.selectbox("Select Phase to Inspect Projects:", options=["All Phases"] + phases)
        
        if selected_phase == "All Phases":
            df_phase_view = df_master
        else:
            df_phase_view = df_master[df_master['Phase'] == selected_phase]

        st.markdown(f"**Displaying {len(df_phase_view)} PAPs | Total Budget: PhP {df_phase_view['Cost_PhP_B'].sum():,.3f} Billion**")
        
        display_cols = [c for c in ["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "Phase", "ESTIMATE AMOUNT"] if c in df_phase_view.columns]
        st.dataframe(df_phase_view[display_cols], use_container_width=True, height=450)

# ==========================================
# 3. MASTER PLAN PROJECTS DIRECTORY VIEW
# ==========================================
elif nav_selection == "Master Plan Projects Directory":
    st.title("📋 Master Plan Programs & Projects (PAPs) Directory")
    
    if df_master.empty:
        st.error("No project data available.")
    else:
        st.markdown(f"Searchable database of **{len(df_master)} PAPs** totaling **PhP {df_master['Cost_PhP_B'].sum():,.3f} Billion**.")

        col_filter1, col_filter2, col_filter3 = st.columns(3)
        with col_filter1:
            selected_phases = st.multiselect("Filter by Phase:", options=sorted(df_master['Phase'].unique()), default=sorted(df_master['Phase'].unique()))
        with col_filter2:
            selected_sectors = st.multiselect("Filter by Sector:", options=sorted(df_master['SECTOR'].unique()), default=sorted(df_master['SECTOR'].unique()))
        with col_filter3:
            selected_cats = st.multiselect("Filter by Category:", options=sorted(df_master['CATEGORY'].unique()), default=sorted(df_master['CATEGORY'].unique()))

        df_filtered = df_master[
            (df_master['Phase'].isin(selected_phases)) & 
            (df_master['SECTOR'].isin(selected_sectors)) & 
            (df_master['CATEGORY'].isin(selected_cats))
        ]

        st.markdown(f"**Showing {len(df_filtered)} of {len(df_master)} Projects | Subtotal: PhP {df_filtered['Cost_PhP_B'].sum():,.3f} Billion**")

        display_cols = [c for c in ["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "Phase", "ESTIMATE AMOUNT"] if c in df_filtered.columns]
        st.dataframe(df_filtered[display_cols], use_container_width=True, height=480)

# ==========================================
# 4. MANPOWER & INFRASTRUCTURE JUSTIFICATION VIEW
# ==========================================
elif nav_selection == "Manpower Justification":
    st.title("👷 Technical Engineering Manpower Justification")
    st.markdown("Operational necessity analysis justifying the direct appointment of **Engineer V, Engineer III, and two Engineer I** positions.")

    st.markdown(
        """
        <div class="callout-box">
            <h4 style="margin: 0 0 6px 0; color: #58A6FF;">Core Technical Rationale for Evaluators</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.5;">
                Executing complex infrastructure, port extension, environmental baselines, and institutional development across all phases requires a dedicated technical engineering team. Approving the requested headcount—<b>Engineer V (Division Chief), Engineer III (Senior Technical Lead), and two Engineer I positions (Field Supervision & QA/QC Engineers)</b>—ensures robust project supervision, timely procurement, and precise civil engineering execution.
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
# 5. REVENUE ANALYTICS & FORECASTING VIEW
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & Master Plan Forecasting")

    if df_rev.empty:
        st.error("REVENUE.xlsx data file is missing or contains no readable records.")
    else:
        tab_hist, tab_trad, tab_nontrad, tab_fore = st.tabs([
            "📊 Historical Revenue Analytics",
            "⚓ Traditional Revenue Streams",
            "🏢 Non Traditional Revenue Streams",
            "📈 Integrated Master Plan Forecast"
        ])

        with tab_hist:
            fig_hist = go.Figure()
            if "Traditional" in df_rev.columns:
                fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Traditional"], mode='lines+markers', name='Traditional Revenue', line=dict(color='#A371F7', width=2)))
            if "Non_Traditional" in df_rev.columns:
                fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Non_Traditional"], mode='lines+markers', name='Non-Traditional Revenue', line=dict(color='#F0883E', width=2)))
            if "Collected_Revenue" in df_rev.columns:
                fig_hist.add_trace(go.Scatter(x=df_rev["Date"], y=df_rev["Collected_Revenue"], mode='lines+markers', name='Total Revenue Collected', line=dict(width=3, color='#58A6FF')))
            
            fig_hist.update_layout(
                template="plotly_dark",
                title="Monthly Revenue Collections by Stream (PhP)",
                xaxis_title="Timeline",
                yaxis_title="Revenue (PhP)",
                height=380,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with tab_trad:
            if "Traditional" in df_rev.columns and "Month_Raw" in df_rev.columns:
                df_trad = df_rev[["Month_Raw", "Traditional"]].copy()

                col_t1, col_t2 = st.columns([1, 1])

                with col_t1:
                    fig_bar_trad = px.bar(
                        df_trad,
                        x="Traditional",
                        y="Month_Raw",
                        orientation="h",
                        template="plotly_dark",
                        height=450,
                        color_discrete_sequence=["#1F6FE5"],
                        labels={"Traditional": "Revenue (PhP)", "Month_Raw": "Period"}
                    )
                    fig_bar_trad.update_layout(
                        margin=dict(l=10, r=10, t=30, b=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_bar_trad, use_container_width=True)

                with col_t2:
                    st.dataframe(
                        df_trad.rename(columns={"Month_Raw": "Period", "Traditional": "Revenue (PhP)"}),
                        use_container_width=True,
                        height=450
                    )

        with tab_nontrad:
            if "Non_Traditional" in df_rev.columns and "Month_Raw" in df_rev.columns:
                df_nontrad = df_rev[["Month_Raw", "Non_Traditional"]].copy()

                col_nt1, col_nt2 = st.columns([1, 1])

                with col_nt1:
                    fig_bar_nontrad = px.bar(
                        df_nontrad,
                        x="Non_Traditional",
                        y="Month_Raw",
                        orientation="h",
                        template="plotly_dark",
                        height=450,
                        color_discrete_sequence=["#F0883E"],
                        labels={"Non_Traditional": "Revenue (PhP)", "Month_Raw": "Period"}
                    )
                    fig_bar_nontrad.update_layout(
                        margin=dict(l=10, r=10, t=30, b=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_bar_nontrad, use_container_width=True)

                with col_nt2:
                    st.dataframe(
                        df_nontrad.rename(columns={"Month_Raw": "Period", "Non_Traditional": "Revenue (PhP)"}),
                        use_container_width=True,
                        height=450
                    )

        with tab_fore:
            st.markdown("### Integrated Revenue Forecast Model (2026–2040)")
            
            col_param1, col_param2 = st.columns(2)
            with col_param1:
                base_growth = st.slider("Organic Baseline Growth (%)", min_value=1.0, max_value=10.0, value=3.5, step=0.5)
            with col_param2:
                pap_multiplier = st.slider("PAPs Implementation Multiplier", min_value=1.0, max_value=2.5, value=1.4, step=0.1)

            annual_base = df_rev["Collected_Revenue"].sum()
            if len(df_rev) > 0 and annual_base > 0:
                annual_avg_base = (annual_base / len(df_rev)) * 12
                
                years = list(range(2026, 2041))
                baseline_proj = []
                masterplan_proj = []
                
                for y in years:
                    n = y - 2025
                    b_val = annual_avg_base * ((1 + (base_growth / 100)) ** n)
                    baseline_proj.append(b_val)
                    
                    phase_mult = 1.20 if y <= 2028 else (1.55 if y <= 2031 else (2.00 if y <= 2035 else 2.40))
                    m_val = b_val * (1 + (phase_mult - 1) * pap_multiplier)
                    masterplan_proj.append(m_val)

                df_forecast = pd.DataFrame({
                    "Year": years,
                    "Baseline (PhP Billion)": [v / 1e9 for v in baseline_proj],
                    "Master Plan Integrated (PhP Billion)": [v / 1e9 for v in masterplan_proj]
                })

                fig_fore = go.Figure()
                fig_fore.add_trace(go.Scatter(x=df_forecast["Year"], y=df_forecast["Baseline (PhP Billion)"], mode='lines+markers', name='Business-As-Usual', line=dict(dash='dash', color='#8B949E')))
                fig_fore.add_trace(go.Scatter(x=df_forecast["Year"], y=df_forecast["Master Plan Integrated (PhP Billion)"], mode='lines+markers', name='Master Plan Integrated Revenue', line=dict(width=3, color='#238636')))

                fig_fore.update_layout(
                    template="plotly_dark",
                    title="Projected Annual Revenue Trajectory (PhP Billion)",
                    xaxis_title="Year",
                    yaxis_title="Annual Revenue (PhP Billion)",
                    height=400,
                    margin=dict(l=10, r=10, t=40, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_fore, use_container_width=True)

# ==========================================
# 6. SPATIAL MAP VIEWER
# ==========================================
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺️ Spatial Development & Land Use Map Viewer")

    map_type = st.radio("Select View Mode:", ["Local QGIS Zoning Layers (Folium)", "Global Open Zone Map"], horizontal=True)

    if map_type == "Global Open Zone Map":
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
# 7. M&E & RISK MATRIX VIEW
# ==========================================
elif nav_selection == "M&E & Risk Matrix":
    st.title("📊 Monitoring & Evaluation (M&E) & Risk Matrix")
    
    if df_master.empty:
        st.error("No project data available to evaluate risk matrix.")
    else:
        risk_summary = df_master.groupby('Phase').agg(
            Total_Projects=('PROJECT NO.', 'count'),
            Total_Cost_B=('Cost_PhP_B', 'sum')
        ).reset_index()

        st.dataframe(risk_summary, use_container_width=True, height=300)
