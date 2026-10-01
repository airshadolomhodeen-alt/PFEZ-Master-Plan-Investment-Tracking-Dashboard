import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# REUSABLE EXECUTIVE VISUALIZATION SYSTEM
# ==========================================

EXECUTIVE_THEME = {
    "paper_bgcolor": "#0B0E14",
    "plot_bgcolor": "#0F141D",
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "font_color": "#F0F6FC",
    "grid_color": "#2B3245",
    "accent_blue": "#38BDF8",
    "accent_green": "#10B981",
    "accent_amber": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_purple": "#A855F7",
    "accent_orange": "#F97316",
    "accent_gray": "#94A3B8",
}

def get_modebar_config():
    """Returns standardized Plotly modebar configuration."""
    return {
        "displayModeBar": "hover",
        "responsive": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }

def apply_executive_theme(fig, title_text, height=450):
    """Applies executive dark template, font hierarchy, and responsive margins."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor=EXECUTIVE_THEME["paper_bgcolor"],
        plot_bgcolor=EXECUTIVE_THEME["plot_bgcolor"],
        font=dict(family=EXECUTIVE_THEME["font_family"], color=EXECUTIVE_THEME["font_color"]),
        title=dict(
            text=title_text,
            font=dict(size=18, color="#F0F6FC", weight="bold"),
            x=0.0,
            xanchor="left",
            y=0.98,
            yanchor="top",
        ),
        margin=dict(l=20, r=20, t=85, b=20),
        hoverlabel=dict(
            bgcolor="#161B22",
            font_size=12,
            font_family=EXECUTIVE_THEME["font_family"],
            bordercolor="#30363D",
        ),
    )
    return fig

def configure_executive_legend(fig):
    """Positions legend above the plotting area to prevent layout overlap."""
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            font=dict(size=11, color="#C9D1D9"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        )
    )
    return fig

def format_php_axis(fig, axis="y", scale="millions", title=None):
    """Formats financial axes with clean Philippine Peso (PhP) units."""
    prefix = "PhP "
    suffix = "M" if scale == "millions" else ("B" if scale == "billions" else "")
    
    axis_config = dict(
        gridcolor=EXECUTIVE_THEME["grid_color"],
        gridwidth=1,
        zerolinecolor=EXECUTIVE_THEME["grid_color"],
        tickfont=dict(size=11, color="#8B949E"),
        title=dict(text=title if title else f"Amount ({prefix}{suffix})", font=dict(size=12, color="#C9D1D9")),
        ticksuffix=suffix,
        tickprefix=prefix,
        separate_thousands=True,
    )
    
    if axis == "y":
        fig.update_yaxes(**axis_config)
    elif axis == "x":
        fig.update_xaxes(**axis_config)
    return fig


# ==========================================
# COMPONENT 1: HISTORICAL REVENUE & TREND
# ==========================================
def create_historical_revenue_chart(df_rev_input):
    """Generates the refactored Historical Revenue Time Series & Trend Analysis figure."""
    if df_rev_input is None or df_rev_input.empty or "Collected_Revenue" not in df_rev_input.columns:
        return None

    df_plot = df_rev_input.copy()
    df_plot["Date"] = pd.to_datetime(df_plot["Date"])
    df_plot = df_plot.sort_values("Date").reset_index(drop=True)

    # Convert values to Millions for clear presentation
    revenue_m = df_plot["Collected_Revenue"] / 1e6
    dates = df_plot["Date"]

    # Calculate 3-Month Moving Average
    ma_3m = revenue_m.rolling(window=3, min_periods=3).mean()

    # Calculate OLS Trendline
    x_numeric = np.arange(len(df_plot))
    slope, intercept = np.polyfit(x_numeric, revenue_m, 1)
    ols_trend = slope * x_numeric + intercept

    # Descriptive Statistics (Historical Only)
    mean_rev = revenue_m.mean()
    std_rev = revenue_m.std()
    upper_band = mean_rev + std_rev
    lower_band = max(0, mean_rev - std_rev)

    fig = go.Figure()

    # 1. Statistical Control Band (+/- 1 Std Dev)
    fig.add_trace(
        go.Scatter(
            x=pd.concat([dates, dates[::-1]]),
            y=pd.concat([pd.Series([upper_band] * len(dates)), pd.Series([lower_band] * len(dates))[::-1]]),
            fill="toself",
            fillcolor="rgba(56, 189, 248, 0.08)",
            line=dict(color="rgba(56, 189, 248, 0.2)", width=1, dash="dot"),
            hoverinfo="skip",
            name="Historical Mean ± 1σ Band",
        )
    )

    # 2. Monthly Target Reference Line (PhP 2.50M)
    fig.add_hline(
        y=2.50,
        line_dash="dash",
        line_color=EXECUTIVE_THEME["accent_red"],
        line_width=1.5,
        annotation_text="Target: PhP 2.50M",
        annotation_position="top right",
        annotation_font=dict(size=10, color=EXECUTIVE_THEME["accent_red"]),
    )

    # 3. OLS Trend Line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ols_trend,
            mode="lines",
            name="OLS Trend",
            line=dict(color=EXECUTIVE_THEME["accent_green"], width=1.8, dash="solid"),
            hovertemplate="<b>OLS Trend</b><br>Date: %{x|%b %Y}<br>Trend: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 4. 3-Month Moving Average
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ma_3m,
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color=EXECUTIVE_THEME["accent_amber"], width=2.2),
            hovertemplate="<b>3-Month MA</b><br>Date: %{x|%b %Y}<br>MA: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 5. Actual Revenue Line & Markers
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=revenue_m,
            mode="lines+markers",
            name="Actual Collected Revenue",
            line=dict(color=EXECUTIVE_THEME["accent_blue"], width=2.5),
            marker=dict(size=6, color=EXECUTIVE_THEME["accent_blue"], symbol="circle"),
            hovertemplate="<b>Actual Revenue</b><br>Month: %{x|%B %Y}<br>Collection: <b>PhP %{y:.2f}M</b><extra></extra>",
        )
    )

    apply_executive_theme(fig, "Historical Revenue Collection & Performance Trend", height=460)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", scale="millions", title="Monthly Collection (PhP M)")
    
    fig.update_xaxes(
        gridcolor=EXECUTIVE_THEME["grid_color"],
        tickfont=dict(size=11, color="#8B949E"),
        title=dict(text="Timeline", font=dict(size=12, color="#C9D1D9")),
    )

    return fig


# ==========================================
# COMPONENT 2: REVENUE BREAKDOWN BY STREAM
# ==========================================
def create_revenue_breakdown_chart(df_rev_input):
    """Generates the refactored Revenue Stream Breakdown Stacked Bar figure."""
    if df_rev_input is None or df_rev_input.empty or "Traditional" not in df_rev_input.columns:
        return None

    df_plot = df_rev_input.copy()
    df_plot["Date"] = pd.to_datetime(df_plot["Date"])
    df_plot = df_plot.sort_values("Date").reset_index(drop=True)

    trad_m = df_plot["Traditional"] / 1e6
    non_trad_m = df_plot["Non_Traditional"] / 1e6
    total_m = df_plot["Collected_Revenue"] / 1e6
    dates = df_plot["Date"]

    fig = go.Figure()

    # Traditional Revenue (Port/Ship Calls)
    fig.add_trace(
        go.Bar(
            x=dates,
            y=trad_m,
            name="Traditional Revenue (Ship Calls)",
            marker_color=EXECUTIVE_THEME["accent_purple"],
            customdata=np.stack((non_trad_m, total_m), axis=-1),
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "Traditional: <b>PhP %{y:.2f}M</b><br>"
                "Non-Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Total Revenue: <b>PhP %{customdata[1]:.2f}M</b><extra></extra>"
            ),
        )
    )

    # Non-Traditional Revenue (Ecozone Leases)
    fig.add_trace(
        go.Bar(
            x=dates,
            y=non_trad_m,
            name="Non-Traditional Revenue (Leases/Rentals)",
            marker_color=EXECUTIVE_THEME["accent_orange"],
            customdata=np.stack((trad_m, total_m), axis=-1),
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "Non-Traditional: <b>PhP %{y:.2f}M</b><br>"
                "Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Total Revenue: <b>PhP %{customdata[1]:.2f}M</b><extra></extra>"
            ),
        )
    )

    fig.update_layout(barmode="stack")
    apply_executive_theme(fig, "Monthly Revenue Composition by Stream", height=420)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", scale="millions", title="Revenue (PhP M)")

    fig.update_xaxes(
        gridcolor=EXECUTIVE_THEME["grid_color"],
        tickfont=dict(size=11, color="#8B949E"),
        title=dict(text="Timeline", font=dict(size=12, color="#C9D1D9")),
    )

    return fig


# ==========================================
# COMPONENT 3: FORECAST MODEL (2026–2040)
# ==========================================
def create_revenue_forecast_chart(df_forecast_input):
    """Generates the refactored Long-Term Integrated Revenue Forecast figure."""
    if df_forecast_input is None or df_forecast_input.empty or "Baseline (PhP Billion)" not in df_forecast_input.columns:
        return None

    df_plot = df_forecast_input.copy()

    years = df_plot["Year"]
    bau_m = df_plot["Baseline (PhP Billion)"] * 1000  # Convert Billions to Millions
    mp_m = df_plot["Master Plan Integrated (PhP Billion)"] * 1000

    fig = go.Figure()

    # 1. Incremental Value Gap Shading
    fig.add_trace(
        go.Scatter(
            x=pd.concat([years, years[::-1]]),
            y=pd.concat([mp_m, bau_m[::-1]]),
            fill="toself",
            fillcolor="rgba(16, 185, 129, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Incremental Master Plan Value Gap",
        )
    )

    # 2. BAU Baseline Scenario Line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=bau_m,
            mode="lines+markers",
            name="Business-As-Usual Baseline",
            line=dict(color=EXECUTIVE_THEME["accent_gray"], width=2, dash="dash"),
            marker=dict(size=5, color=EXECUTIVE_THEME["accent_gray"]),
            hovertemplate="<b>BAU Baseline</b><br>Year: %{x}<br>Revenue: PhP %{y:,.1f}M<extra></extra>",
        )
    )

    # 3. Master Plan Integrated Line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=mp_m,
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color=EXECUTIVE_THEME["accent_green"], width=2.8),
            marker=dict(size=7, color=EXECUTIVE_THEME["accent_green"], symbol="circle"),
            customdata=mp_m - bau_m,
            hovertemplate=(
                "<b>Master Plan Integrated</b><br>"
                "Year: %{x}<br>"
                "Projected Revenue: <b>PhP %{y:,.1f}M</b><br>"
                "Incremental Value Gap: <b>+PhP %{customdata:,.1f}M</b><extra></extra>"
            ),
        )
    )

    # Executive Phase Callout Annotations
    if 2028 in years.values:
        val_2028 = mp_m[years == 2028].values[0]
        fig.add_annotation(
            x=2028,
            y=val_2028,
            text="Phase I PAPs Online",
            showarrow=True,
            arrowhead=2,
            arrowcolor=EXECUTIVE_THEME["accent_green"],
            arrowsize=1,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            font=dict(size=10, color="#FFFFFF"),
            bgcolor="#161B22",
            bordercolor=EXECUTIVE_THEME["accent_green"],
            borderwidth=1,
            borderpad=4,
        )

    if 2035 in years.values:
        val_2035 = mp_m[years == 2035].values[0]
        fig.add_annotation(
            x=2035,
            y=val_2035,
            text="Phase III Port Expansion",
            showarrow=True,
            arrowhead=2,
            arrowcolor=EXECUTIVE_THEME["accent_green"],
            arrowsize=1,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            font=dict(size=10, color="#FFFFFF"),
            bgcolor="#161B22",
            bordercolor=EXECUTIVE_THEME["accent_green"],
            borderwidth=1,
            borderpad=4,
        )

    apply_executive_theme(fig, "Projected Annual Revenue Trajectory & Value Creation (2026–2040)", height=480)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", scale="millions", title="Annual Projected Revenue (PhP M)")

    fig.update_xaxes(
        gridcolor=EXECUTIVE_THEME["grid_color"],
        tickmode="linear",
        dtick=2,
        tickfont=dict(size=11, color="#8B949E"),
        title=dict(text="Planning Horizon (Year)", font=dict(size=12, color="#C9D1D9")),
    )

    return fig


# ==========================================
# MODULE 5 REPLACEMENT IN APP.PY
# ==========================================
elif nav_selection == "Revenue Analytics & Forecasting":
    st.title("📈 Revenue Collection Analytics & Master Plan Forecasting")
    st.markdown("Historical revenue analysis (2024–2026) and long-term financial modeling under the **PFEZ Master Plan PAPs (2026–2040)**.")

    st.markdown("### 💡 Revenue Stream Definitions & Classification")
    
    rev_col1, rev_col2 = st.columns(2)
    with rev_col1:
        st.markdown(
            """
            <div style="background-color: #161B22; border-left: 4px solid #A855F7; border-top: 1px solid #30363D; border-right: 1px solid #30363D; border-bottom: 1px solid #30363D; padding: 14px 18px; border-radius: 8px; height: 100%;">
                <h4 style="margin: 0 0 6px 0; color: #A855F7; font-size: 16px;">⚓ Traditional Revenue</h4>
                <p style="margin: 0 0 8px 0; color: #C9D1D9; font-size: 12px; font-weight: 600;">Core Maritime & Vessel Operations</p>
                <p style="margin: 0; color: #8B949E; font-size: 12px; line-height: 1.4;">
                    Generated directly from <b>Domestic and Foreign Vessels ship calls</b>. Includes port dues, berthing/dockage fees, cargo wharfage, pilotage, and vessel tonnage fees.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with rev_col2:
        st.markdown(
            """
            <div style="background-color: #161B22; border-left: 4px solid #F97316; border-top: 1px solid #30363D; border-right: 1px solid #30363D; border-bottom: 1px solid #30363D; padding: 14px 18px; border-radius: 8px; height: 100%;">
                <h4 style="margin: 0 0 6px 0; color: #F97316; font-size: 16px;">🏢 Non-Traditional Revenue</h4>
                <p style="margin: 0 0 8px 0; color: #C9D1D9; font-size: 12px; font-weight: 600;">Ecozone Real Estate, Logistics & Value-Added Services</p>
                <p style="margin: 0; color: #8B949E; font-size: 12px; line-height: 1.4;">
                    Derived from commercial land assets and ecozone facilities. Includes <b>Lease of Contracts, Space Rentals, Container Yard Terminals, and commercial operations</b>.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Render Component 2: Stacked Revenue Breakdown Chart
    st.markdown("### 1. Historical Revenue Composition by Stream")
    fig_breakdown = create_revenue_breakdown_chart(df_rev)
    if fig_breakdown:
        st.plotly_chart(fig_breakdown, use_container_width=True, config=get_modebar_config())
    else:
        st.warning("Revenue breakdown visualization unavailable: required fields are missing.")

    st.markdown("---")

    # Render Component 1: Historical Performance & Trend Analysis
    st.markdown("### 2. Collection Performance & Statistical Trend Analysis")
    fig_historical = create_historical_revenue_chart(df_rev)
    if fig_historical:
        st.plotly_chart(fig_historical, use_container_width=True, config=get_modebar_config())
    else:
        st.warning("Historical trend visualization unavailable: required fields are missing.")

    st.markdown("---")

    # Render Component 3: Long-Term Integrated Forecast
    st.markdown("### 3. Integrated Revenue Forecast Model (2026–2040)")
    
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        base_growth = st.slider("Organic Baseline Annual Growth (%)", min_value=1.0, max_value=10.0, value=3.5, step=0.5)
    with col_param2:
        pap_multiplier = st.slider("PAPs Implementation Multiplier", min_value=1.0, max_value=2.5, value=1.4, step=0.1)

    # Compute Forecast Model Data
    annual_2025_base = df_rev[df_rev["Date"].dt.year == 2025]["Collected_Revenue"].sum() if "Date" in df_rev.columns else 0
    if annual_2025_base == 0:
        annual_2025_base = df_rev["Collected_Revenue"].mean() * 12

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
        "Baseline (PhP Billion)": [v / 1e9 for v in baseline_proj],
        "Master Plan Integrated (PhP Billion)": [v / 1e9 for v in masterplan_proj]
    })

    fig_forecast = create_revenue_forecast_chart(df_forecast)
    if fig_forecast:
        st.plotly_chart(fig_forecast, use_container_width=True, config=get_modebar_config())
    else:
        st.warning("Forecast visualization unavailable: required fields are missing.")
