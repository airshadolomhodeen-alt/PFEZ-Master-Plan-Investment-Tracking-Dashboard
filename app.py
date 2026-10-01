import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# EXECUTIVE VISUAL DESIGN SYSTEM & HELPERS
# ==========================================

EXECUTIVE_THEME = {
    "template": "plotly_dark",
    "paper_bgcolor": "#0B0E14",
    "plot_bgcolor": "#0F141D",
    "grid_color": "#2B3245",
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    "color_actual": "#38BDF8",
    "color_ols": "#10B981",
    "color_ma": "#F59E0B",
    "color_target": "#EF4444",
    "color_trad": "#A855F7",
    "color_nontrad": "#F97316",
    "color_bau": "#94A3B8",
    "color_integrated": "#10B981",
    "color_fill_gap": "rgba(16, 185, 129, 0.12)",
    "color_stat_band": "rgba(59, 130, 246, 0.08)",
    "color_stat_line": "rgba(96, 165, 250, 0.4)",
}

def apply_executive_theme(fig, title_text="", subtitle_text="", height=480):
    """Applies standardized executive dark styling to Plotly figure."""
    full_title = f"<b>{title_text}</b>"
    if subtitle_text:
        full_title += f"<br><sup style='color:#8B949E; font-size:12px;'>{subtitle_text}</sup>"

    fig.update_layout(
        template=EXECUTIVE_THEME["template"],
        height=height,
        paper_bgcolor=EXECUTIVE_THEME["paper_bgcolor"],
        plot_bgcolor=EXECUTIVE_THEME["plot_bgcolor"],
        font=dict(family=EXECUTIVE_THEME["font_family"], color="#F0F6FC", size=12),
        title=dict(text=full_title, font=dict(size=18), x=0.0, xanchor="left"),
        margin=dict(l=60, r=30, t=80, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor=EXECUTIVE_THEME["grid_color"],
            gridwidth=0.5,
            tickfont=dict(size=11, color="#8B949E"),
            title_font=dict(size=12, color="#C9D1D9"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=EXECUTIVE_THEME["grid_color"],
            gridwidth=0.5,
            tickfont=dict(size=11, color="#8B949E"),
            title_font=dict(size=12, color="#C9D1D9"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0,
            font=dict(size=11, color="#C9D1D9"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig

def configure_modebar():
    """Returns standard executive Plotly modebar configuration."""
    return {"displayModeBar": "hover", "responsive": True}


# ==========================================
# COMPONENT 1: HISTORICAL REVENUE & TREND
# ==========================================

def render_component_1_historical_revenue(df_rev_input):
    """
    Renders Component 1: Historical Revenue Time Series, OLS Trendline,
    3-Month MA, Monthly Target (PhP 2.50M), and Statistical Control Band.
    """
    if df_rev_input is None or df_rev_input.empty:
        st.warning("Revenue visualization unavailable: required revenue fields are missing.")
        return

    # Defensive Validation & Copy
    df_plot = df_rev_input.copy()
    req_cols = ["Date", "Collected_Revenue"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue visualization unavailable: missing column '{col}'.")
            return

    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    df_plot["Collected_Revenue"] = pd.to_numeric(df_plot["Collected_Revenue"], errors="coerce")
    df_plot = df_plot.dropna(subset=["Date", "Collected_Revenue"]).sort_values("Date").reset_index(drop=True)

    if df_plot.empty:
        st.warning("Revenue visualization unavailable: no valid numerical observations.")
        return

    # Statistical Calculations (Historical Only)
    revenue_m = df_plot["Collected_Revenue"] / 1e6
    mean_rev = revenue_m.mean()
    std_rev = revenue_m.std()
    upper_band = mean_rev + std_rev
    lower_band = max(0.0, mean_rev - std_rev)

    # 3-Month Rolling Average
    df_plot["MA_3M"] = revenue_m.rolling(window=3, min_periods=3).mean()

    # Reproducible OLS Trendline
    x_idx = np.arange(len(df_plot))
    slope, intercept = np.polyfit(x_idx, revenue_m.values, 1)
    ols_trend = slope * x_idx + intercept

    fig = go.Figure()

    # 1. Statistical Control Band (+/- 1 Std Dev)
    fig.add_trace(
        go.Scatter(
            x=pd.concat([df_plot["Date"], df_plot["Date"][::-1]]),
            y=np.concatenate([np.full(len(df_plot), upper_band), np.full(len(df_plot), lower_band)]),
            fill="todense",
            fillcolor=EXECUTIVE_THEME["color_stat_band"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Historical Mean ± 1σ",
            showlegend=True,
        )
    )

    # Upper/Lower Boundary Dot Lines
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=np.full(len(df_plot), upper_band),
            mode="lines",
            line=dict(color=EXECUTIVE_THEME["color_stat_line"], width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=np.full(len(df_plot), lower_band),
            mode="lines",
            line=dict(color=EXECUTIVE_THEME["color_stat_line"], width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # 2. OLS Trendline
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=ols_trend,
            mode="lines",
            name="OLS Trend",
            line=dict(color=EXECUTIVE_THEME["color_ols"], width=1.8),
            hovertemplate="<b>OLS Trend</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 3. 3-Month Moving Average
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=df_plot["MA_3M"],
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color=EXECUTIVE_THEME["color_ma"], width=2.2),
            hovertemplate="<b>3M Moving Avg</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 4. Actual Monthly Revenue
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=revenue_m,
            mode="lines+markers",
            name="Actual Revenue",
            line=dict(color=EXECUTIVE_THEME["color_actual"], width=2.5),
            marker=dict(size=6, symbol="circle"),
            hovertemplate="<b>Month</b>: %{x|%B %Y}<br><b>Actual Revenue</b>: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 5. Target Reference Line (PhP 2.50M)
    fig.add_hline(
        y=2.50,
        line_dash="dash",
        line_color=EXECUTIVE_THEME["color_target"],
        line_width=1.5,
        annotation_text="Monthly Target — PhP 2.50M",
        annotation_position="top right",
        annotation_font=dict(size=10, color=EXECUTIVE_THEME["color_target"]),
    )

    apply_executive_theme(
        fig,
        title_text="Historical Revenue Performance & Statistical Momentum",
        subtitle_text="Actual monthly revenue collections vs. OLS trend, 3M moving average, and target baseline",
        height=450,
    )
    fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
    fig.update_xaxes(title_text="Timeline")

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())


# ==========================================
# COMPONENT 2: REVENUE BREAKDOWN BY STREAM
# ==========================================

def render_component_2_revenue_breakdown(df_rev_input):
    """
    Renders Component 2: Historical Revenue Stream Composition as a Stacked Bar Chart
    comparing Traditional (Ship Calls) and Non-Traditional (Leases/Rentals) revenue.
    """
    if df_rev_input is None or df_rev_input.empty:
        st.warning("Revenue breakdown unavailable: required revenue fields are missing.")
        return

    df_plot = df_rev_input.copy()
    req_cols = ["Date", "Traditional", "Non_Traditional"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue breakdown unavailable: missing column '{col}'.")
            return

    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    df_plot["Traditional"] = pd.to_numeric(df_plot["Traditional"], errors="coerce").fillna(0.0)
    df_plot["Non_Traditional"] = pd.to_numeric(df_plot["Non_Traditional"], errors="coerce").fillna(0.0)
    df_plot = df_plot.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    df_plot["Trad_M"] = df_plot["Traditional"] / 1e6
    df_plot["NonTrad_M"] = df_plot["Non_Traditional"] / 1e6
    df_plot["Total_M"] = df_plot["Trad_M"] + df_plot["NonTrad_M"]

    fig = go.Figure()

    # Traditional Revenue (Stacked Base)
    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=df_plot["Trad_M"],
            name="Traditional Revenue",
            marker_color=EXECUTIVE_THEME["color_trad"],
            customdata=np.stack((df_plot["NonTrad_M"], df_plot["Total_M"]), axis=-1),
            hovertemplate=(
                "<b>Month</b>: %{x|%B %Y}<br>"
                "Traditional: PhP %{y:.2f}M<br>"
                "Non-Traditional: PhP %{customdata[0]:.2f}M<br>"
                "<b>Total Revenue</b>: PhP %{customdata[1]:.2f}M<extra></extra>"
            ),
        )
    )

    # Non-Traditional Revenue (Stacked Level 2)
    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=df_plot["NonTrad_M"],
            name="Non-Traditional Revenue",
            marker_color=EXECUTIVE_THEME["color_nontrad"],
            customdata=np.stack((df_plot["Trad_M"], df_plot["Total_M"]), axis=-1),
            hovertemplate=(
                "<b>Month</b>: %{x|%B %Y}<br>"
                "Traditional: PhP %{customdata[0]:.2f}M<br>"
                "Non-Traditional: PhP %{y:.2f}M<br>"
                "<b>Total Revenue</b>: PhP %{customdata[1]:.2f}M<extra></extra>"
            ),
        )
    )

    apply_executive_theme(
        fig,
        title_text="Historical Revenue Composition by Stream",
        subtitle_text="Monthly breakdown between Traditional (Maritime/Ship Calls) and Non-Traditional (Ecozone Leases)",
        height=420,
    )
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Revenue (PhP Millions)", tickprefix="PhP ", ticksuffix="M")
    fig.update_xaxes(title_text="Timeline")

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())


# ==========================================
# COMPONENT 3: INTEGRATED FORECAST MODEL
# ==========================================

def render_component_3_integrated_forecast(df_forecast_input):
    """
    Renders Component 3: Long-Term Integrated Revenue Forecast (2026–2040)
    comparing BAU vs Master Plan Integrated scenarios with value gap shading.
    """
    if df_forecast_input is None or df_forecast_input.empty:
        st.warning("Revenue forecast model unavailable: required projection data is missing.")
        return

    df_plot = df_forecast_input.copy()
    req_cols = ["Year", "Baseline (PhP Billion)", "Master Plan Integrated (PhP Billion)"]
    for col in req_cols:
        if col not in df_plot.columns:
            st.warning(f"Revenue forecast model unavailable: missing column '{col}'.")
            return

    df_plot["Year"] = pd.to_numeric(df_plot["Year"], errors="coerce")
    df_plot["BAU_M"] = pd.to_numeric(df_plot["Baseline (PhP Billion)"], errors="coerce") * 1000.0
    df_plot["Integrated_M"] = pd.to_numeric(df_plot["Master Plan Integrated (PhP Billion)"], errors="coerce") * 1000.0
    df_plot = df_plot.dropna(subset=["Year", "BAU_M", "Integrated_M"]).sort_values("Year").reset_index(drop=True)

    fig = go.Figure()

    # 1. Shaded Incremental Revenue Value Gap
    fig.add_trace(
        go.Scatter(
            x=pd.concat([df_plot["Year"], df_plot["Year"][::-1]]),
            y=pd.concat([df_plot["Integrated_M"], df_plot["BAU_M"][::-1]]),
            fill="tonext",
            fillcolor=EXECUTIVE_THEME["color_fill_gap"],
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Incremental Revenue Potential",
            showlegend=True,
        )
    )

    # 2. Business-As-Usual (BAU) Trace
    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["BAU_M"],
            mode="lines+markers",
            name="Business-As-Usual (BAU)",
            line=dict(color=EXECUTIVE_THEME["color_bau"], width=2, dash="dash"),
            marker=dict(size=5),
            hovertemplate="<b>Year</b>: %{x}<br><b>BAU Revenue</b>: PhP %{y:,.1f}M<extra></extra>",
        )
    )

    # 3. Master Plan Integrated Trace
    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["Integrated_M"],
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color=EXECUTIVE_THEME["color_integrated"], width=2.8),
            marker=dict(size=6, symbol="circle"),
            hovertemplate="<b>Year</b>: %{x}<br><b>Integrated Revenue</b>: PhP %{y:,.1f}M<extra></extra>",
        )
    )

    # Milestone Callout Annotations
    if 2028 in df_plot["Year"].values:
        val_2028 = df_plot.loc[df_plot["Year"] == 2028, "Integrated_M"].values[0]
        fig.add_annotation(
            x=2028,
            y=val_2028,
            text="Phase I PAPs Online",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#10B981",
            arrowsize=1,
            arrowwidth=1.5,
            ax=0,
            ay=-35,
            font=dict(size=10, color="#10B981"),
            bgcolor="#0F141D",
            bordercolor="#10B981",
            borderwidth=1,
            borderpad=4,
        )

    if 2035 in df_plot["Year"].values:
        val_2035 = df_plot.loc[df_plot["Year"] == 2035, "Integrated_M"].values[0]
        fig.add_annotation(
            x=2035,
            y=val_2035,
            text="Full Ecozone Logistics Integration",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#10B981",
            arrowsize=1,
            arrowwidth=1.5,
            ax=-40,
            ay=-35,
            font=dict(size=10, color="#10B981"),
            bgcolor="#0F141D",
            bordercolor="#10B981",
            borderwidth=1,
            borderpad=4,
        )

    apply_executive_theme(
        fig,
        title_text="Projected Long-Term Annual Revenue Trajectory (2026–2040)",
        subtitle_text="Comparative trajectory between Baseline BAU and Master Plan Integrated Development Scenarios",
        height=480,
    )
    fig.update_yaxes(title_text="Annual Revenue (PhP Millions)", tickprefix="PhP ", tickformat=",d", ticksuffix="M")
    fig.update_xaxes(title_text="Year", dtick=2)

    st.plotly_chart(fig, use_container_width=True, config=configure_modebar())
