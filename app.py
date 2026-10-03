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
# 2. DATA LOADERS & DATA PIPELINE
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

@st.cache_data
def load_psic_data():
    file_path = "PSIC_rev 5.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path, sheet_name="Detailed Structure", engine="openpyxl")
            df.columns = [str(c).strip() for c in df.columns]
            
            sections, divisions, groups, classes, sub_classes = [], [], [], [], []
            cur_sec, cur_div, cur_grp, cur_cls, cur_sub = None, None, None, None, None
            
            for _, row in df.iterrows():
                sec, div, grp, cls, sub = row['Section'], row['Division'], row['Group'], row['Class'], row['Sub-Class']
                
                if pd.notna(sec):
                    cur_sec, cur_div, cur_grp, cur_cls, cur_sub = sec, None, None, None, None
                if pd.notna(div):
                    cur_div, cur_grp, cur_cls, cur_sub = div, None, None, None
                if pd.notna(grp):
                    cur_grp, cur_cls, cur_sub = grp, None, None
                if pd.notna(cls):
                    cur_cls, cur_sub = cls, None
                if pd.notna(sub):
                    cur_sub = sub
                    
                sections.append(cur_sec)
                divisions.append(cur_div)
                groups.append(cur_grp)
                classes.append(cur_cls)
                sub_classes.append(cur_sub)
                
            df['Section'] = sections
            df['Division'] = divisions
            df['Group'] = groups
            df['Class'] = classes
            df['Sub-Class'] = sub_classes
            
            df['Division'] = df['Division'].apply(lambda x: str(int(x)) if pd.notna(x) and str(x).strip()!='' else "")
            df['Group'] = df['Group'].apply(lambda x: str(x).split('.')[0].zfill(3) if pd.notna(x) and str(x).strip()!='' else "")
            df['Class'] = df['Class'].apply(lambda x: str(x).split('.')[0].zfill(3) if pd.notna(x) and str(x).strip()!='' else "")
            df['Sub-Class'] = df['Sub-Class'].apply(lambda x: str(x).split('.')[0].zfill(4) if pd.notna(x) and str(x).strip()!='' else "")
            
            return df
        except Exception as e:
            return pd.DataFrame()
    else:
        return pd.DataFrame(columns=['Section', 'Division', 'Group', 'Class', 'Sub-Class', 'Description'])

df_psic = load_psic_data()


# ==========================================
# 3. TOP EXECUTIVE BANNER
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
# 4. SIDEBAR NAVIGATION & BRANDING
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/port.png", width=45)
st.sidebar.title("PFEZ Navigation")
nav_selection = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard Home",
        "Investment Phasing (Phases 1–4)",
        "Master Plan Projects Directory",
        "PSIC Industry Classification",
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
# 5. MAP RENDERER HELPER
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
# MODULE 1: DASHBOARD HOME VIEW
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
                        The PFEZ Master Development Plan commits <b>PhP {df_master['Cost_PhP_B'].sum():.3f} Billion</b> across <b>{len(df_master)} Programs and Projects (PAPs)</b> structured into <b>4 Implementation Phases (2026–2040)</b>. Executing <b>Phase 1 (39 Immediate PAPs)</b> requires technical reinforcement: <b>one Engineer V, one Engineer III, and two Engineer I positions</b>. Without direct engineering oversight, project execution delays threaten foundational works and projected revenue trajectories.
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
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #58A6FF;">
                <span style="background-color: #1F6FE5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 1 (2026–2030)</span>
                <h3 style="color: #58A6FF; margin: 8px 0 2px 0; font-size: 18px;">PhP {p1_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p1_m['PAPs_Count'].values[0]} PAPs</b> | Institutional Setup, BOSS & Baselines</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col2:
        p2_m = phase_summary[phase_summary['Phase'].str.contains('Phase 2')]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #F0883E;">
                <span style="background-color: #D25D11; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 2 (2029–2035)</span>
                <h3 style="color: #F0883E; margin: 8px 0 2px 0; font-size: 18px;">PhP {p2_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p2_m['PAPs_Count'].values[0]} PAPs</b> | Container Yard & Halal Processing Hub</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col3:
        p3_m = phase_summary[phase_summary['Phase'].str.contains('Phase 3')]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #A371F7;">
                <span style="background-color: #8957E5; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 3 (2032–2038)</span>
                <h3 style="color: #A371F7; margin: 8px 0 2px 0; font-size: 18px;">PhP {p3_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p3_m['PAPs_Count'].values[0]} PAPs</b> | Wharf Extension & Land Reclamation</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p_col4:
        p4_m = phase_summary[phase_summary['Phase'].str.contains('Phase 4')]
        st.markdown(
            f"""
            <div class="phase-card" style="border-top: 4px solid #238636;">
                <span style="background-color: #238636; color: #FFF; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">PHASE 4 (2035–2040)</span>
                <h3 style="color: #2EA043; margin: 8px 0 2px 0; font-size: 18px;">PhP {p4_m['Total_Budget_B'].values[0]:,.3f} Billion</h3>
                <p style="color: #8B949E; margin: 0; font-size: 11px;"><b>{p4_m['PAPs_Count'].values[0]} PAPs</b> | IT Park & Eco-Tourism Development</p>
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
            color_discrete_sequence=["#58A6FF", "#F0883E", "#A371F7", "#238636"]
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

# ==========================================
# MODULE 2: INVESTMENT PHASING VIEW
# ==========================================
elif nav_selection == "Investment Phasing (Phases 1–4)":
    st.title("💰 Investment & Phasing Program (2026–2040)")
    st.markdown("Detailed evaluator breakdown of the **95 Programs and Projects (PAPs)** amounting to **PhP 8.524 Billion** across 4 implementation phases.")
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("Phase 1 (2026–2030)", "PhP 0.284 Billion", "39 Initial PAPs")
    with col_p2:
        st.metric("Phase 2 (2029–2035)", "PhP 1.949 Billion", "32 Core PAPs")
    with col_p3:
        st.metric("Phase 3 (2032–2038)", "PhP 6.124 Billion", "16 Major Capital PAPs")
    with col_p4:
        st.metric("Phase 4 (2035–2040)", "PhP 0.168 Billion", "8 Finalizing PAPs")
        
    st.markdown("---")
    
    selected_phase = st.selectbox("Select Phase to Inspect Projects:", options=["All Phases", "Phase 1 (2026–2030)", "Phase 2 (2029–2035)", "Phase 3 (2032–2038)", "Phase 4 (2035–2040)"])
    
    if selected_phase == "All Phases":
        df_phase_view = df_master
    else:
        df_phase_view = df_master[df_master['Phase'] == selected_phase]

    st.markdown(f"**Displaying {len(df_phase_view)} PAPs | Total Budget: PhP {df_phase_view['Cost_PhP_B'].sum():,.3f} Billion**")
    st.dataframe(df_phase_view[["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "Phase", "PCM Stage", "ESTIMATE AMOUNT"]], use_container_width=True, height=450)

# ==========================================
# MODULE 3: MASTER PLAN PROJECTS DIRECTORY VIEW
# ==========================================
elif nav_selection == "Master Plan Projects Directory":
    st.title("📋 Master Plan Programs & Projects (PAPs) Directory")
    st.markdown(f"Complete searchable database of **{len(df_master)} PAPs** totaling **PhP {df_master['Cost_PhP_B'].sum():,.3f} Billion**.")

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

    st.dataframe(
        df_filtered[["PROJECT NO.", "PROJECT TITLE", "SECTOR", "CATEGORY", "Phase", "PCM Stage", "ESTIMATE AMOUNT"]],
        use_container_width=True,
        height=480
    )

# ==========================================
# MODULE: PSIC INDUSTRY CLASSIFICATION
# ==========================================
elif nav_selection == "PSIC Industry Classification":
    st.title("🏭 Philippine Standard Industrial Classification (PSIC Rev. 5)")
    st.markdown(f"Searchable registry of economic sectors, divisions, and industry classes (Total Records: **{len(df_psic):,}**).")

    # Official PSIC Section Description Dictionary
    section_names = {
        'A': 'Agriculture, Forestry and Fishing',
        'B': 'Mining and Quarrying',
        'C': 'Manufacturing',
        'D': 'Electricity, Gas, Steam & Air Conditioning',
        'E': 'Water Supply & Waste Management',
        'F': 'Construction',
        'G': 'Wholesale and Retail Trade; Repair of Vehicles',
        'H': 'Transportation and Storage',
        'I': 'Accommodation and Food Service Activities',
        'J': 'Information and Communication',
        'K': 'Financial and Insurance Activities',
        'L': 'Real Estate Activities',
        'M': 'Professional, Scientific, and Technical Activities',
        'N': 'Administrative and Support Service Activities',
        'O': 'Public Administration & Defense',
        'P': 'Education',
        'Q': 'Human Health and Social Work Activities',
        'R': 'Arts, Entertainment and Recreation',
        'S': 'Other Service Activities',
        'T': 'Activities of Households as Employers',
        'U': 'Activities of Extraterritorial Organizations'
    }

    # Ecozone relevance banner
    st.markdown(
        """
        <div style="background-color: #161b22; border-left: 4px solid #58A6FF; padding: 14px 16px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #30363d;">
            <h4 style="margin: 0 0 6px 0; color: #58A6FF; font-size: 15px;">Freeport & Special Economic Zone Sector Alignment</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13px; line-height: 1.5;">
                PFEZ and BEZA locators primarily draw from key industrial classifications including <b>Manufacturing (Section C)</b>, <b>Transportation & Storage (Section H)</b>, and <b>IT & Technical Services (Sections J, K, M)</b>. Explore the structural density and market share distribution below.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_psic.empty:
        df_psic['Filled_Section'] = df_psic['Section'].ffill()
        sec_counts = df_psic.groupby('Filled_Section').size().reset_index(name='Record_Count')
        
        # Map clean official section titles
        sec_counts['Description'] = sec_counts['Filled_Section'].map(section_names).fillna('Other Activities')
        sec_counts['Display_Label'] = sec_counts['Filled_Section'] + " - " + sec_counts['Description']
        sec_counts = sec_counts.sort_values(by='Record_Count', ascending=True)

        # Highlight core ecozone sectors
        ecozones_core = ['C', 'H', 'G', 'J', 'K', 'M', 'N']
        sec_counts['Is_Core_Ecozone'] = sec_counts['Filled_Section'].isin(ecozones_core)
        sec_counts['Color'] = sec_counts['Is_Core_Ecozone'].apply(lambda x: '#58A6FF' if x else '#30363d')

        # 1. PRIMARY VIEW: Executive Bar Chart & Donut Summary Layout
        chart_col1, chart_col2 = st.columns([1.6, 1], gap="medium")

        with chart_col1:
            fig_psic = go.Figure(go.Bar(
                y=sec_counts['Display_Label'],
                x=sec_counts['Record_Count'],
                orientation='h',
                marker=dict(color=sec_counts['Color']),
                text=sec_counts['Record_Count'],
                textposition='auto'
            ))
            fig_psic.update_layout(
                title="<b>PSIC Records by Section</b> (Highlighted = Core Ecozone)",
                template="plotly_dark",
                height=520,
                margin=dict(l=20, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Number of Records", gridcolor="#30363d"),
                yaxis=dict(title="", automargin=True)
            )
            st.plotly_chart(fig_psic, use_container_width=True)

        with chart_col2:
            sec_counts['Category'] = sec_counts['Is_Core_Ecozone'].apply(lambda x: 'Core Ecozone Sectors' if x else 'Other Sectors')
            summary_pie = sec_counts.groupby('Category')['Record_Count'].sum().reset_index()

            fig_donut = px.pie(
                summary_pie, 
                names='Category', 
                values='Record_Count', 
                hole=0.55,
                color='Category',
                color_discrete_map={'Core Ecozone Sectors': '#58A6FF', 'Other Sectors': '#30363d'}
            )
            fig_donut.update_layout(
                title="<b>Ecozone vs. Other Share</b>",
                template="plotly_dark",
                height=520,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")

        # 2. DEDICATED SECTION: Clean Executive Treemap (Section Level Only - No Division Number Clutter)
        st.subheader("🌐 PSIC Rev. 5 Macro Market Map (Section Level Share)")
        st.markdown("Proportional market layout showing the relative volume of classification records across all major economic sections.")

        df_treemap_data = df_psic.copy()
        df_treemap_data['Filled_Section'] = df_treemap_data['Section'].ffill()
        df_treemap_data['Section_Name'] = df_treemap_data['Filled_Section'].map(section_names).fillna('Other')
        df_treemap_data['Record_Weight'] = 1

        # Group by Section name so each block represents a clean, single category with its total record count
        treemap_summary = df_treemap_data.groupby('Section_Name')['Record_Weight'].sum().reset_index(name='Total_Records')

        fig_treemap = px.treemap(
            treemap_summary,
            path=['Section_Name'],
            values='Total_Records',
            color='Total_Records',
            color_continuous_scale='Blues',
            template="plotly_dark"
        )
        fig_treemap.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

        st.markdown("---")

        # 3. FILTERS AND TABLE REGISTRY
        c1, c2 = st.columns([1.2, 1.8])
        with c1:
            sections = sorted([str(s) for s in df_psic['Section'].dropna().unique()])
            selected_sections = st.multiselect("Filter by Section:", options=sections, default=sections)
        with c2:
            search_query = st.text_input("Search Description or Code:", placeholder="Enter keyword (e.g., manufacturing, transport, port, fishing)...")

        df_psic_filtered = df_psic[df_psic['Section'].astype(str).isin(selected_sections)]
        if search_query:
            mask = df_psic_filtered.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
            df_psic_filtered = df_psic_filtered[mask]

        st.markdown(f"**Showing {len(df_psic_filtered):,}/{len(df_psic):,} matching classification records**")
        st.dataframe(df_psic_filtered.drop(columns=['Filled_Section']), use_container_width=True, height=450)
    else:
        st.warning("`PSIC_rev 5.xlsx` was not found or contains no readable sheets.")
# ==========================================
# MODULE: MANPOWER JUSTIFICATION
# ==========================================
elif nav_selection == "Manpower Justification":
    st.title("👷 Technical Engineering Manpower Justification")
    st.markdown("Operational necessity analysis justifying the direct appointment of **Engineer V, Engineer III, and two Engineer I** positions.")

    st.markdown(
        """
        <div style="background-color: #161b22; border-left: 4px solid #58A6FF; padding: 16px; border-radius: 6px; margin-bottom: 24px; border: 1px solid #30363d;">
            <h4 style="margin: 0 0 8px 0; color: #58A6FF; font-size: 16px;">Core Technical Rationale for Evaluators</h4>
            <p style="margin: 0; color: #C9D1D9; font-size: 13.5px; line-height: 1.6;">
                Executing complex infrastructure, port extension, environmental baselines, and institutional development across <b>Phase 1 (39 Immediate PAPs) through Phase 4</b> requires an agile, certified technical workforce. Approving the requested headcount—<b>Engineer V (Division Lead), Engineer III (Senior Technical Lead), and two Engineer I positions (Field Supervision & QA/QC Engineers)</b>—ensures robust project supervision, timely procurement, and high-quality civil engineering execution across all 95 PAPs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.markdown("### Executive Headcount Allocation")
        st.markdown("Summary of requested engineering personnel distribution:")
        
        # Professional metric cards instead of a basic bar chart for integers of 1 and 2
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                <div style="background: #111418; border: 1px solid #30363d; padding: 12px 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div><strong style="color: #58A6FF;">Engineer V</strong><br><span style="font-size: 12px; color: #8b949e;">Division Chief / Strategic Lead</span></div>
                    <span style="background: #1f6feb; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 14px;">1 Slot</span>
                </div>
                <div style="background: #111418; border: 1px solid #30363d; padding: 12px 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div><strong style="color: #58A6FF;">Engineer III</strong><br><span style="font-size: 12px; color: #8b949e;">Senior Project / Technical Lead</span></div>
                    <span style="background: #1f6feb; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 14px;">1 Slot</span>
                </div>
                <div style="background: #111418; border: 1px solid #30363d; padding: 12px 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div><strong style="color: #58A6FF;">Engineer I (Field)</strong><br><span style="font-size: 12px; color: #8b949e;">Civil Works Supervision</span></div>
                    <span style="background: #238636; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 14px;">2 Slots</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("### Functional Mandate Breakdown")
        st.markdown("Core competencies aligned with multi-phase deliverables:")
        
        roles_table = pd.DataFrame({
            "Position Title": ["Engineer V", "Engineer III", "Engineer I (Field)", "Engineer I (QA/QC & GIS)"],
            "Primary Responsibilities": [
                "Division management, strategic program alignment, and multi-agency infrastructure governance",
                "Detailed engineering design review, technical specifications, and procurement oversight",
                "On-site project inspection, contractor compliance, and civil works measurement",
                "Quality assurance, structural monitoring documentation, and GIS layer integration"
            ]
        })
        st.dataframe(roles_table, use_container_width=True, height=230)

# ==========================================
# MODULE 5: REVENUE ANALYTICS VIEW
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📊 Revenue Analytics & Forecasting")
    st.markdown("Executive financial tracking, stream decomposition, and strategic long-term forecast models.")

    st.markdown("### Historical Revenue Time Series & Trend Analysis")
    st.markdown("Monthly performance, rolling momentum, linear trend, and statistical control limits")

    x_numeric = np.arange(len(df_rev))
    y_vals = df_rev["Collected_Revenue"].values
    mean_val = np.mean(y_vals)
    std_val = np.std(y_vals)
    
    slope, intercept = np.polyfit(x_numeric, y_vals, 1)
    trend_line = slope * x_numeric + intercept
    
    ma_3m = pd.Series(y_vals).rolling(window=3, min_periods=1).mean().values

    fig_hist = go.Figure()
    
    fig_hist.add_trace(
        go.Scatter(
            x=df_rev["Date"],
            y=[mean_val] * len(df_rev),
            mode="lines",
            name="Historical Mean ± 1σ",
            line=dict(color="#238636", width=1.5, dash="dash")
        )
    )
    
    fig_hist.add_trace(
        go.Scatter(
            x=df_rev["Date"],
            y=trend_line,
            mode="lines",
            name="OLS Trend",
            line=dict(color="#10B981", width=2)
        )
    )
    
    fig_hist.add_trace(
        go.Scatter(
            x=df_rev["Date"],
            y=ma_3m,
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color="#F59E0B", width=2)
        )
    )
    
    fig_hist.add_trace(
        go.Scatter(
            x=df_rev["Date"],
            y=y_vals,
            mode="lines+markers",
            name="Actual Revenue",
            line=dict(color="#38BDF8", width=2.5),
            marker=dict(size=5)
        )
    )

    fig_hist.add_annotation(
        x=df_rev["Date"].iloc[-1],
        y=2.5e6,
        text="Target: PhP 2.50M",
        showarrow=False,
        xshift=40,
        font=dict(color="#EF4444", size=11)
    )

    fig_hist.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Revenue (PhP Millions)",
        xaxis_title="Observation Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Revenue Stream Composition")
    st.markdown("Monthly breakdown between Traditional core operations and Non-Traditional lease/rental assets")

    fig_stack = go.Figure()
    fig_stack.add_trace(
        go.Bar(
            x=df_rev["Date"],
            y=df_rev["Non_Traditional"],
            name="Non-Traditional Revenue (Leases/Rentals)",
            marker_color="#F97316"
        )
    )
    fig_stack.add_trace(
        go.Bar(
            x=df_rev["Date"],
            y=df_rev["Traditional"],
            name="Traditional Revenue (Ship Calls)",
            marker_color="#8B5CF6"
        )
    )

    fig_stack.update_layout(
        barmode="stack",
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Revenue (PhP Millions)",
        xaxis_title="Observation Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Long-Term Integrated Revenue Forecast (2026–2040)")
    st.markdown("Strategic comparison between Business-As-Usual baseline and Master Plan execution")

    forecast_years = list(range(2026, 2041))
    bau_vals = [40 + (y - 2026) * 1.5 for y in forecast_years]
    master_vals = [43 + (y - 2026) * 4.2 + (0 if y < 2028 else (y - 2027) * 1.8) for y in forecast_years]

    fig_fore = go.Figure()
    
    fig_fore.add_trace(
        go.Scatter(
            x=forecast_years,
            y=master_vals,
            mode='lines',
            name='Incremental Revenue Potential',
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.15)',
            line=dict(color='rgba(16, 185, 129, 0)', width=0),
            showlegend=True
        )
    )

    fig_fore.add_trace(
        go.Scatter(
            x=forecast_years,
            y=bau_vals,
            mode="lines",
            name="Business-As-Usual (BAU)",
            line=dict(color="#8B949E", width=2, dash="dash")
        )
    )
    
    fig_fore.add_trace(
        go.Scatter(
            x=forecast_years,
            y=master_vals,
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color="#10B981", width=3),
            marker=dict(size=6)
        )
    )

    fig_fore.add_annotation(x=2028, y=master_vals[forecast_years.index(2028)], text="Phase I PAPs Online", showarrow=True, arrowhead=2, ax=0, ay=-30)
    fig_fore.add_annotation(x=2032, y=master_vals[forecast_years.index(2032)], text="Phase II Port Expansion", showarrow=True, arrowhead=2, ax=0, ay=-30)
    fig_fore.add_annotation(x=2036, y=master_vals[forecast_years.index(2036)], text="Full Logistics Integration", showarrow=True, arrowhead=2, ax=0, ay=-30)

    fig_fore.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Annual Revenue (PhP Millions)",
        xaxis_title="Forecast Year",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_fore, use_container_width=True)

# ==========================================
# MODULE 6: SPATIAL MAP VIEWER
# ==========================================
elif nav_selection == "Spatial Map Viewer":
    st.title("🗺 Spatial Development & Land Use Map Viewer")
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
# MODULE 7: M&E & RISK MATRIX (PCM ENHANCED)
# ==========================================
elif nav_selection == "M&E & Risk Matrix":
    st.title("🛡️ Monitoring & Evaluation (M&E) & Risk Matrix")
    st.markdown(
        "Project Cycle Management (PCM) framework tracking performance indicators, "
        "stage-gate execution, and strategic risk mitigation across the PFEZ Master Plan."
    )

    tab_risk, tab_logframe, tab_pcm = st.tabs([
        "⚠️ Strategic Risk Register", 
        "📋 Logical Framework (Logframe)", 
        "🔄 PCM Phasing & Stage-Gates"
    ])

    with tab_risk:
        st.markdown("### Strategic Risk Identification & Assessment Matrix")
        
        risk_data = [
            {
                "Risk ID": "RSK-01",
                "PCM Stage": "5. Implementation & Monitoring",
                "Category": "Financial & Budget",
                "Risk Event / Description": "Capital budget delays or slow local revenue remittance hindering Phase 1 execution.",
                "Probability": "Medium",
                "Impact": "High",
                "Risk Score": "HIGH",
                "Mitigation Strategy": "Establish automated revenue-sharing models; sequence PAPs by ROI priority.",
                "Owner": "Finance & BEZA Lead"
            },
            {
                "Risk ID": "RSK-02",
                "PCM Stage": "5. Implementation & Monitoring",
                "Category": "Technical / Manpower",
                "Risk Event / Description": "Delay in approving engineering plantilla positions (Engr V, III, I) leading to weak QA/QC oversight.",
                "Probability": "High",
                "Impact": "High",
                "Risk Score": "CRITICAL",
                "Mitigation Strategy": "Prioritize immediate recruitment justification; deploy interim third-party QA/QC engineering consultants.",
                "Owner": "Engineering Division"
            },
            {
                "Risk ID": "RSK-03",
                "PCM Stage": "3. Formulation & Design",
                "Category": "Environmental & Climate",
                "Risk Event / Description": "Coastal erosion, storm surges, and sea-level rise impacting port and wharf extension.",
                "Probability": "Medium",
                "Impact": "High",
                "Risk Score": "HIGH",
                "Mitigation Strategy": "Conduct EIA & climate resilience studies; integrate green infrastructure and mangrove buffers.",
                "Owner": "Environmental Unit"
            },
            {
                "Risk ID": "RSK-04",
                "PCM Stage": "1. Programming",
                "Category": "Governance & Institutional",
                "Risk Event / Description": "Multi-agency coordination bottlenecks across regional and national agencies (BARMM, BEZA, DPWH).",
                "Probability": "Medium",
                "Impact": "Medium",
                "Risk Score": "MEDIUM",
                "Mitigation Strategy": "Formalize Inter-Agency Steering Committee with quarterly M&E progress reporting.",
                "Owner": "Executive Office"
            },
            {
                "Risk ID": "RSK-05",
                "PCM Stage": "2. Identification",
                "Category": "Operational & Land Use",
                "Risk Event / Description": "Land acquisition and right-of-way (ROW) disputes along economic zone boundaries.",
                "Probability": "Low",
                "Impact": "High",
                "Risk Score": "MEDIUM",
                "Mitigation Strategy": "Execute boundary surveys and formal land relocation frameworks early in Phase 1.",
                "Owner": "Legal & Land Dept"
            }
        ]
        df_risk = pd.DataFrame(risk_data)

        def style_risk(val):
            if val == "CRITICAL":
                return "background-color: #8B0000; color: white; font-weight: bold;"
            elif val == "HIGH":
                return "background-color: #B22222; color: white; font-weight: bold;"
            elif val == "MEDIUM":
                return "background-color: #D2691E; color: white; font-weight: bold;"
            return "background-color: #2E8B57; color: white; font-weight: bold;"

        st.dataframe(
            df_risk.style.map(style_risk, subset=["Risk Score"]),
            use_container_width=True,
            height=320
        )

        st.markdown("<br>", unsafe_allow_html=True)
        r_col1, r_col2 = st.columns(2)
        
        with r_col1:
            st.markdown("#### Risk Severity Breakdown")
            fig_risk_pie = px.pie(
                df_risk,
                names="Risk Score",
                title="Risk Severity Summary",
                color="Risk Score",
                color_discrete_map={
                    "CRITICAL": "#8B0000",
                    "HIGH": "#B22222",
                    "MEDIUM": "#D2691E",
                    "LOW": "#2E8B57"
                },
                template="plotly_dark",
                hole=0.4
            )
            fig_risk_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_risk_pie, use_container_width=True)

        with r_col2:
            st.markdown("#### Risk Distribution by Domain Category")
            fig_cat = px.bar(
                df_risk,
                x="Category",
                color="Risk Score",
                title="Risks per Domain",
                color_discrete_map={
                    "CRITICAL": "#8B0000",
                    "HIGH": "#B22222",
                    "MEDIUM": "#D2691E",
                    "LOW": "#2E8B57"
                },
                template="plotly_dark"
            )
            fig_cat.update_layout(margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_cat, use_container_width=True)

    with tab_logframe:
        st.markdown("### Master Plan Results & Evaluation Framework (Logframe)")
        
        me_data = [
            {
                "Level": "1. Goal / Impact",
                "Objectives & Key Performance Indicators": "Transform PFEZ into a sustainable regional economic hub in BARMM.",
                "Baseline (2024–2026)": "Baseline Port Operations",
                "Target (2040)": "PhP 8.524B Infrastructure Capitalized; 15,000 Direct/Indirect Jobs",
                "Data Source / Verification": "PSA & BEZA Economic Reports",
                "Reporting Frequency": "5 Years"
            },
            {
                "Level": "2. Outcomes",
                "Objectives & Key Performance Indicators": "Increased Port Revenue Generation & Logistics Processing Efficiency",
                "Baseline (2024–2026)": "~PhP 0.082B Historical Cumulative",
                "Target (2040)": ">PhP 2.0B Annual Revenue Target",
                "Data Source / Verification": "BEZA Financial Audit / REVENUE.xlsx",
                "Reporting Frequency": "Annual"
            },
            {
                "Level": "2. Outcomes",
                "Objectives & Key Performance Indicators": "Phase Execution & Master Plan Compliance",
                "Baseline (2024–2026)": "0% Master Plan Execution",
                "Target (2040)": "100% Delivery across 95 PAPs",
                "Data Source / Verification": "Quarterly Project Inspection Logs",
                "Reporting Frequency": "Quarterly"
            },
            {
                "Level": "3. Outputs",
                "Objectives & Key Performance Indicators": "Phase 1 Immediate Infrastructure Deliverables (2026–2030)",
                "Baseline (2024–2026)": "39 Nominated PAPs",
                "Target (2030)": "39 PAPs Completed (PhP 0.284B Invested)",
                "Data Source / Verification": "Engineering QA/QC Field Reports",
                "Reporting Frequency": "Monthly"
            },
            {
                "Level": "4. Inputs",
                "Objectives & Key Performance Indicators": "Technical Engineering Manpower & Operational Capacity",
                "Baseline (2024–2026)": "Understaffed / Proposed",
                "Target (2026)": "4 Key Positions Appointed (Engr V, III, two I)",
                "Data Source / Verification": "BEZA Plantilla / HR Records",
                "Reporting Frequency": "Immediate"
            }
        ]

        df_me = pd.DataFrame(me_data)
        st.dataframe(df_me, use_container_width=True, height=350)

    with tab_pcm:
        st.markdown("### Project Cycle Management (PCM) Phasing Matrix")
        
        pcm_summary = df_master.groupby('Phase').agg(
            Total_PAPs=('PROJECT NO.', 'count'),
            Total_Cost_B=('Cost_PhP_B', 'sum')
        ).reset_index()

        pcm_summary["PCM Stage"] = [
            "5. Implementation & Monitoring",
            "3. Formulation & Design",
            "2. Identification",
            "1. Programming"
        ]
        pcm_summary["Target Year"] = ["2030", "2035", "2038", "2040"]
        pcm_summary["Monitoring Authority"] = [
            "BEZA Engineering Division (Phase 1 Lead)",
            "BEZA Operations & Engineering",
            "BEZA Strategic Planning Unit",
            "BEZA Executive Directorate"
        ]

        st.dataframe(pcm_summary, use_container_width=True, height=250)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Portfolio Phasing Distribution by Capital & Projects Count")
        
        pcm_col1, pcm_col2 = st.columns(2)
        with pcm_col1:
            fig_pcm_bar = px.bar(
                pcm_summary,
                x="Phase",
                y="Total_Cost_B",
                color="PCM Stage",
                title="Capital Investment per PCM Phase (PhP B)",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pcm_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pcm_bar, use_container_width=True)

        with pcm_col2:
            fig_pcm_paps = px.pie(
                pcm_summary,
                names="Phase",
                values="Total_PAPs",
                title="PAPs Count Share per Phase",
                template="plotly_dark",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pcm_paps.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pcm_paps, use_container_width=True)
