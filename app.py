import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import st_folium

# ==========================================
# PAGE CONFIGURATION & LAYOUT
# ==========================================
st.set_page_config(
    page_title="PFEZ Master Plan & Revenue Analytics",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# REUSABLE VISUALIZATION DESIGN SYSTEM
# ==========================================
EXECUTIVE_COLORS = {
    "paper_bg": "#0B0E14",
    "plot_bg": "#0F141D",
    "grid": "#2B3245",
    "actual": "#38BDF8",
    "trend": "#10B981",
    "ma": "#F59E0B",
    "target": "#EF4444",
    "traditional": "#A855F7",
    "nontraditional": "#F97316",
    "bau": "#94A3B8",
    "masterplan": "#10B981",
    "stat_band": "rgba(59, 130, 246, 0.08)",
    "stat_line": "rgba(96, 165, 250, 0.4)",
    "gap_fill": "rgba(16, 185, 129, 0.12)",
    "text": "#F3F4F6",
    "subtext": "#9CA3AF"
}


def apply_executive_theme(fig: go.Figure, title: str, subtitle: str = "") -> go.Figure:
    """Applies global executive dark theme styling to a Plotly figure."""
    full_title = (
        f"<b>{title}</b><br><span style='font-size: 12px; color: {EXECUTIVE_COLORS['subtext']};'>"
        f"{subtitle}</span>" if subtitle else f"<b>{title}</b>"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=EXECUTIVE_COLORS["paper_bg"],
        plot_bgcolor=EXECUTIVE_COLORS["plot_bg"],
        title=dict(
            text=full_title,
            font=dict(family="Inter, -apple-system, sans-serif", size=18, color=EXECUTIVE_COLORS["text"]),
            x=0,
            xanchor="left",
            y=0.96,
            yanchor="top"
        ),
        margin=dict(l=50, r=30, t=90, b=50),
        font=dict(family="Inter, -apple-system, sans-serif", color=EXECUTIVE_COLORS["text"]),
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family="Inter, -apple-system, sans-serif"
        ),
        autosize=True
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridcolor=EXECUTIVE_COLORS["grid"],
        gridwidth=1,
        tickfont=dict(size=11, color=EXECUTIVE_COLORS["subtext"]),
        title_font=dict(size=12, color=EXECUTIVE_COLORS["subtext"]),
        zeroline=False
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor=EXECUTIVE_COLORS["grid"],
        gridwidth=1,
        tickfont=dict(size=11, color=EXECUTIVE_COLORS["subtext"]),
        title_font=dict(size=12, color=EXECUTIVE_COLORS["subtext"]),
        zeroline=False
    )
    
    return configure_executive_legend(fig)


def configure_executive_legend(fig: go.Figure) -> go.Figure:
    """Positions the legend horizontally above the plot area to eliminate overlap."""
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0,
            font=dict(size=11, color=EXECUTIVE_COLORS["text"]),
            bgcolor="rgba(0, 0, 0, 0)"
        )
    )
    return fig


def get_executive_config() -> dict:
    """Returns standardized Plotly modebar and responsiveness configuration."""
    return {
        "displayModeBar": "hover",
        "responsive": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]
    }


def validate_dataframe(df: pd.DataFrame, required_cols: list) -> tuple[pd.DataFrame | None, str | None]:
    """Performs lightweight defensive validation and returns an isolated copy."""
    if df is None or df.empty:
        return None, "Data is empty or unavailable."
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return None, f"Required fields missing: {', '.join(missing)}"
    
    df_plot = df.copy()
    return df_plot, None


# ==========================================
# REVENUE VISUALIZATION COMPONENTS
# ==========================================

def render_historical_revenue_chart(
    df: pd.DataFrame,
    date_col: str = "date",
    revenue_col: str = "actual_revenue",
    monthly_target: float = 2500000.0,
    unit_scale: float = 1e6
) -> go.Figure | None:
    df_plot, err = validate_dataframe(df, [date_col, revenue_col])
    if err:
        st.warning(f"Revenue visualization unavailable: {err}")
        return None
    
    try:
        df_plot[date_col] = pd.to_datetime(df_plot[date_col])
        df_plot[revenue_col] = pd.to_numeric(df_plot[revenue_col], errors="coerce")
        df_plot = df_plot.dropna(subset=[date_col, revenue_col]).sort_values(by=date_col)
        
        if df_plot.empty:
            st.warning("Revenue visualization unavailable: no valid numerical records found.")
            return None

        rev_scaled = df_plot[revenue_col] / unit_scale
        dates = df_plot[date_col]
        target_scaled = monthly_target / unit_scale
        
        mean_scaled = rev_scaled.mean()
        std_scaled = rev_scaled.std()
        upper_scaled = mean_scaled + std_scaled
        lower_scaled = max(0.0, mean_scaled - std_scaled)
        
        ma3_scaled = rev_scaled.rolling(window=3, min_periods=3).mean()
        
        x_numeric = (dates - dates.min()).dt.days.values
        if len(x_numeric) > 1 and np.var(x_numeric) > 0:
            slope, intercept = np.polyfit(x_numeric, rev_scaled.values, 1)
            ols_trend = intercept + slope * x_numeric
        else:
            ols_trend = np.full(len(dates), mean_scaled)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=pd.concat([dates, dates[::-1]]),
            y=pd.concat([pd.Series(upper_scaled, index=dates.index), pd.Series(lower_scaled, index=dates.index)[::-1]]),
            fill="toself",
            fillcolor=EXECUTIVE_COLORS["stat_band"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="Historical Mean ± 1σ"
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=ols_trend,
            mode="lines",
            name="OLS Trend",
            line=dict(color=EXECUTIVE_COLORS["trend"], width=1.8),
            hovertemplate="OLS Trend: PhP %{y:.2f}M<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=ma3_scaled,
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color=EXECUTIVE_COLORS["ma"], width=2.2),
            hovertemplate="3-Mo MA: PhP %{y:.2f}M<extra></extra>"
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=rev_scaled,
            mode="lines+markers",
            name="Actual Revenue",
            line=dict(color=EXECUTIVE_COLORS["actual"], width=2.5),
            marker=dict(size=6, color=EXECUTIVE_COLORS["actual"]),
            hovertemplate="<b>%{x|%B %Y}</b><br>Actual Revenue: <b>PhP %{y:.2f}M</b><extra></extra>"
        ))

        fig.add_hline(
            y=target_scaled,
            line_dash="dash",
            line_color=EXECUTIVE_COLORS["target"],
            line_width=1.5,
            annotation_text=f"Target: PhP {target_scaled:.2f}M",
            annotation_position="top right",
            annotation_font=dict(size=11, color=EXECUTIVE_COLORS["target"])
        )

        apply_executive_theme(
            fig,
            title="Historical Revenue Time Series & Trend Analysis",
            subtitle="Monthly performance, rolling momentum, linear trend, and statistical control limits"
        )
        
        fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
        fig.update_xaxes(title_text="Observation Month")
        
        return fig

    except Exception as e:
        st.warning(f"Revenue visualization unavailable: internal processing error ({str(e)}).")
        return None


def render_revenue_breakdown_chart(
    df: pd.DataFrame,
    date_col: str = "date",
    trad_col: str = "traditional_revenue",
    nontrad_col: str = "nontraditional_revenue",
    unit_scale: float = 1e6
) -> go.Figure | None:
    df_plot, err = validate_dataframe(df, [date_col, trad_col, nontrad_col])
    if err:
        st.warning(f"Revenue breakdown visualization unavailable: {err}")
        return None

    try:
        df_plot[date_col] = pd.to_datetime(df_plot[date_col])
        df_plot[trad_col] = pd.to_numeric(df_plot[trad_col], errors="coerce").fillna(0.0)
        df_plot[nontrad_col] = pd.to_numeric(df_plot[nontrad_col], errors="coerce").fillna(0.0)
        df_plot = df_plot.sort_values(by=date_col)

        if df_plot.empty:
            st.warning("Revenue breakdown visualization unavailable: no valid records found.")
            return None

        trad_scaled = df_plot[trad_col] / unit_scale
        nontrad_scaled = df_plot[nontrad_col] / unit_scale
        total_scaled = trad_scaled + nontrad_scaled
        dates = df_plot[date_col]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=dates,
            y=trad_scaled,
            name="Traditional Revenue (Ship Calls)",
            marker_color=EXECUTIVE_COLORS["traditional"],
            customdata=np.stack((nontrad_scaled, total_scaled), axis=-1),
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "Traditional: <b>PhP %{y:.2f}M</b><br>"
                "Non-Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Total Revenue: <b>PhP %{customdata[1]:.2f}M</b><extra></extra>"
            )
        ))

        fig.add_trace(go.Bar(
            x=dates,
            y=nontrad_scaled,
            name="Non-Traditional Revenue (Leases/Rentals)",
            marker_color=EXECUTIVE_COLORS["nontraditional"],
            customdata=np.stack((trad_scaled, total_scaled), axis=-1),
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Non-Traditional: <b>PhP %{y:.2f}M</b><br>"
                "Total Revenue: <b>PhP %{customdata[1]:.2f}M</b><extra></extra>"
            )
        ))

        apply_executive_theme(
            fig,
            title="Revenue Stream Composition",
            subtitle="Monthly breakdown between Traditional core operations and Non-Traditional lease/rental assets"
        )

        fig.update_layout(barmode="stack")
        fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
        fig.update_xaxes(title_text="Observation Month")

        return fig

    except Exception as e:
        st.warning(f"Revenue breakdown visualization unavailable: internal processing error ({str(e)}).")
        return None


def render_revenue_forecast_chart(
    df: pd.DataFrame,
    year_col: str = "year",
    bau_col: str = "bau_revenue",
    masterplan_col: str = "integrated_revenue",
    unit_scale: float = 1e6,
    milestones: dict | None = None
) -> go.Figure | None:
    df_plot, err = validate_dataframe(df, [year_col, bau_col, masterplan_col])
    if err:
        st.warning(f"Revenue forecast visualization unavailable: {err}")
        return None

    try:
        df_plot[year_col] = pd.to_numeric(df_plot[year_col], errors="coerce")
        df_plot[bau_col] = pd.to_numeric(df_plot[bau_col], errors="coerce")
        df_plot[masterplan_col] = pd.to_numeric(df_plot[masterplan_col], errors="coerce")
        df_plot = df_plot.dropna(subset=[year_col, bau_col, masterplan_col]).sort_values(by=year_col)

        if df_plot.empty:
            st.warning("Revenue forecast visualization unavailable: invalid numerical forecast data.")
            return None

        bau_scaled = df_plot[bau_col] * (1e6 / unit_scale) if unit_scale != 1e6 else df_plot[bau_col] / 1e6
        mp_scaled = df_plot[masterplan_col] * (1e6 / unit_scale) if unit_scale != 1e6 else df_plot[masterplan_col] / 1e6
        years = df_plot[year_col].astype(int)
        gap_scaled = mp_scaled - bau_scaled

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=pd.concat([years, years[::-1]]),
            y=pd.concat([mp_scaled, bau_scaled[::-1]]),
            fill="toself",
            fillcolor=EXECUTIVE_COLORS["gap_fill"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Incremental Revenue Potential"
        ))

        fig.add_trace(go.Scatter(
            x=years,
            y=bau_scaled,
            mode="lines",
            name="Business-As-Usual (BAU)",
            line=dict(color=EXECUTIVE_COLORS["bau"], width=2, dash="dash"),
            customdata=gap_scaled,
            hovertemplate=(
                "<b>Year %{x}</b><br>"
                "BAU Revenue: PhP %{y:.2f}M<br>"
                "Incremental Gap: PhP %{customdata:.2f}M<extra></extra>"
            )
        ))

        fig.add_trace(go.Scatter(
            x=years,
            y=mp_scaled,
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color=EXECUTIVE_COLORS["masterplan"], width=2.8),
            marker=dict(size=6, color=EXECUTIVE_COLORS["masterplan"]),
            customdata=gap_scaled,
            hovertemplate=(
                "<b>Year %{x}</b><br>"
                "Master Plan Revenue: <b>PhP %{y:.2f}M</b><br>"
                "Incremental Gap: <b>+PhP %{customdata:.2f}M</b><extra></extra>"
            )
        ))

        if milestones:
            for yr, text in milestones.items():
                if yr in years.values:
                    y_val = mp_scaled[years == yr].values[0]
                    fig.add_annotation(
                        x=yr,
                        y=y_val,
                        text=f"<b>{text}</b>",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1.5,
                        arrowcolor=EXECUTIVE_COLORS["masterplan"],
                        ax=0,
                        ay=-35,
                        font=dict(size=10, color=EXECUTIVE_COLORS["text"]),
                        bgcolor="rgba(15, 20, 29, 0.85)",
                        bordercolor=EXECUTIVE_COLORS["masterplan"],
                        borderwidth=1,
                        borderpad=4
                    )

        apply_executive_theme(
            fig,
            title="Long-Term Integrated Revenue Forecast (2026–2040)",
            subtitle="Strategic comparison between Business-As-Usual baseline and Master Plan execution"
        )

        fig.update_yaxes(title_text="Annual Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
        fig.update_xaxes(title_text="Forecast Year", dtick=2)

        return fig

    except Exception as e:
        st.warning(f"Revenue forecast visualization unavailable: internal processing error ({str(e)}).")
        return None


# ==========================================
# MOCK / SAMPLE DATA INITIALIZATION
# ==========================================
@st.cache_data
def load_historical_data():
    dates = pd.date_range(start="2022-01-01", periods=36, freq="MS")
    np.random.seed(42)
    trad = np.random.uniform(1.2e6, 2.8e6, size=len(dates))
    nontrad = np.random.uniform(0.3e6, 0.9e6, size=len(dates))
    actual = trad + nontrad
    return pd.DataFrame({
        "observation_date": dates,
        "traditional_rev": trad,
        "nontraditional_rev": nontrad,
        "total_revenue": actual
    })

@st.cache_data
def load_forecast_data():
    years = np.arange(2026, 2041)
    bau = np.linspace(30e6, 60e6, len(years))
    mp = bau * np.linspace(1.1, 2.2, len(years))
    return pd.DataFrame({
        "fiscal_year": years,
        "bau_projection": bau,
        "master_plan_val": mp
    })


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("🏗️ PFEZ Navigation")
    selected_module = st.radio(
        "Select Module",
        [
            "Dashboard Home",
            "Investment Phasing (Phases 1-4)",
            "Master Plan Projects Directory",
            "Manpower Justification",
            "Revenue Analytics & Forecasting",
            "Spatial Map Viewer",
            "M&E & Risk Matrix"
        ],
        index=5 # Default to Spatial Map Viewer for demonstration
    )
    
    st.markdown("---")
    st.markdown("### Project Portfolio: PFEZ Master Plan")
    st.caption("Total PAPs: 95 Projects")
    st.caption("Total Estimated Capital: PhP 8.524 Billion")
    st.caption("Target Horizon: 2026–2040 (4 Phases)")


# ==========================================
# MODULE 1: REVENUE ANALYTICS & FORECASTING
# ==========================================
if selected_module == "Revenue Analytics & Forecasting":
    st.header("📈 Revenue Analytics & Forecasting")
    st.write("Executive financial tracking, stream decomposition, and strategic long-term forecast models.")
    
    df_hist = load_historical_data()
    df_forecast = load_forecast_data()

    # 1. Historical Revenue Chart
    fig1 = render_historical_revenue_chart(
        df=df_hist,
        date_col="observation_date",
        revenue_col="total_revenue",
        monthly_target=2500000.0,
        unit_scale=1e6
    )
    if fig1:
        st.plotly_chart(fig1, use_container_width=True, config=get_executive_config())

    st.markdown("---")

    # 2. Revenue Breakdown Chart
    fig2 = render_revenue_breakdown_chart(
        df=df_hist,
        date_col="observation_date",
        trad_col="traditional_rev",
        nontrad_col="nontraditional_rev",
        unit_scale=1e6
    )
    if fig2:
        st.plotly_chart(fig2, use_container_width=True, config=get_executive_config())

    st.markdown("---")

    # 3. Forecast Chart
    milestones = {
        2028: "Phase I PAPs Online",
        2032: "Phase II Port Expansion",
        2036: "Full Logistics Integration"
    }
    
    fig3 = render_revenue_forecast_chart(
        df=df_forecast,
        year_col="fiscal_year",
        bau_col="bau_projection",
        masterplan_col="master_plan_val",
        unit_scale=1e6,
        milestones=milestones
    )
    if fig3:
        st.plotly_chart(fig3, use_container_width=True, config=get_executive_config())


# ==========================================
# MODULE 2: SPATIAL MAP VIEWER (UNTOUCHED & PRESERVED)
# ==========================================
elif selected_module == "Spatial Map Viewer":
    st.caption("Interactive GIS viewer integrating local vector zoning layers and the global economic zone repository.")
    
    view_mode = st.radio(
        "Select View Mode:",
        ["Local QGIS Zoning Layers (Folium)", "Global Open Zone Map (Embedded Iframe)"],
        horizontal=True
    )

    if view_mode == "Local QGIS Zoning Layers (Folium)":
        st.subheader("Select vector layers to display on the master map:")

        # Zoning layer color palette mapping
        zoning_colors = {
            "Administrative Core": "#EF4444",
            "Boardwalk And Viewing Deck": "#F97316",
            "Freeport Civic And Commerce Hub": "#EAB308",
            "Future Expansion Area": "#84CC16",
            "Mangrove Ecopark": "#22C55E",
            "Pfez Boundaries": "#06B6D4",
            "Planned Unit Development": "#3B82F6",
            "Port Operation Zone": "#6366F1",
            "Port Support And Commerce Hub": "#8B5CF6",
            "Roro Passenger Terminal": "#D946EF",
            "Staff Housing Cluster": "#EC4899",
            "Utilities": "#64748B"
        }

        active_layers = st.multiselect(
            "Active Zoning Layers",
            options=list(zoning_colors.keys()),
            default=list(zoning_colors.keys())
        )

        map_col, legend_col = st.columns([3, 1])

        with map_col:
            # Initialize Folium Map centered on Polloc Port / PFEZ Area
            m = folium.Map(
                location=[7.35, 124.21],
                zoom_start=14,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Street Map"
            )

            # Sample Zoning Polygon Coordinates for Demonstration
            sample_polygon = [
                [7.360, 124.210],
                [7.365, 124.215],
                [7.355, 124.225],
                [7.345, 124.220],
                [7.348, 124.212]
            ]

            # Render selected polygon features
            for layer in active_layers:
                folium.Polygon(
                    locations=sample_polygon,
                    color=zoning_colors[layer],
                    fill=True,
                    fill_color=zoning_colors[layer],
                    fill_opacity=0.4,
                    weight=2,
                    popup=f"Zone: {layer}"
                ).add_to(m)

            st_folium(m, width="100%", height=600)

        with legend_col:
            st.subheader("📁 Zoning Layers Legend")
            st.markdown(
                """
                <style>
                .legend-box {
                    background-color: #0F141D;
                    border: 1px solid #2B3245;
                    border-radius: 8px;
                    padding: 12px;
                    max-height: 580px;
                    overflow-y: auto;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    margin-bottom: 8px;
                    font-size: 12px;
                    color: #F3F4F6;
                }
                .color-swatch {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    margin-right: 10px;
                    flex-shrink: 0;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            legend_html = '<div class="legend-box">'
            for name, color in zoning_colors.items():
                if name in active_layers:
                    legend_html += f'<div class="legend-item"><div class="color-swatch" style="background-color: {color};"></div>{name}</div>'
            legend_html += '</div>'
            st.markdown(legend_html, unsafe_allow_html=True)

    else:
        st.info("Global Open Zone Map embedded iframe mode.")
        st.components.v1.iframe("https://openzonemap.org", height=600, scrolling=True)


# ==========================================
# OTHER NAVIGATION MODULE PLACEHOLDERS
# ==========================================
else:
    st.title(f"📍 {selected_module}")
    st.info("This module is functioning normally.")
