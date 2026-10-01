# ==========================================
# EXECUTIVE REVENUE VISUALIZATION SYSTEM
# ==========================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def get_modebar_config():
    """Centralized Plotly modebar configuration."""
    return {"displayModeBar": "hover", "responsive": True}


def apply_executive_theme(fig):
    """Applies executive dark theme palette and gridline defaults."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B0E14",
        plot_bgcolor="#0F141D",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            color="#F0F6FC",
            size=12,
        ),
        margin=dict(l=60, r=30, t=70, b=40),
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#2B3245",
        zeroline=False,
        tickfont=dict(size=10, color="#8B949E"),
        title_font=dict(size=12, color="#C9D1D9"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#2B3245",
        zeroline=False,
        tickfont=dict(size=10, color="#8B949E"),
        title_font=dict(size=12, color="#C9D1D9"),
    )
    return fig


def configure_executive_legend(fig):
    """Positions legend horizontally above the plotting area to prevent overlap."""
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0,
            font=dict(size=11, color="#C9D1D9"),
            bgcolor="rgba(0,0,0,0)",
        )
    )
    return fig


def format_php_axis(fig, axis="y", scale=1e6, suffix="M", title="Revenue (PhP)"):
    """Standardizes financial axes to Philippine Peso units without scientific notation."""
    if axis == "y":
        fig.update_yaxes(
            title_text=title, tickprefix="PhP ", ticksuffix=suffix, showticklabels=True
        )
    elif axis == "x":
        fig.update_xaxes(
            title_text=title, tickprefix="PhP ", ticksuffix=suffix, showticklabels=True
        )
    return fig


# ==========================================
# COMPONENT 1: HISTORICAL REVENUE TIME SERIES
# ==========================================


def render_historical_revenue_chart(df):
    """Generates Component 1: Historical Revenue Time Series & Trend Analysis."""
    # Data Validation
    required_cols = ["Date", "Collected_Revenue"]
    if df is None or df.empty or not all(c in df.columns for c in required_cols):
        st.warning(
            "Revenue visualization unavailable: required revenue fields are missing."
        )
        return

    df_plot = df.copy()
    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    df_plot["Collected_Revenue"] = pd.to_numeric(
        df_plot["Collected_Revenue"], errors="coerce"
    )
    df_plot = df_plot.dropna(subset=["Date", "Collected_Revenue"]).sort_values("Date")

    if df_plot.empty:
        st.warning("Revenue visualization unavailable: no valid numerical date rows.")
        return

    revenue = df_plot["Collected_Revenue"]
    rev_in_m = revenue / 1e6

    # 1. Rolling 3-Month Moving Average
    df_plot["MA3"] = revenue.rolling(window=3, min_periods=3).mean() / 1e6

    # 2. Historical OLS Trendline
    x_numeric = np.arange(len(df_plot))
    if len(df_plot) > 1:
        slope, intercept = np.polyfit(x_numeric, revenue, 1)
        df_plot["OLS_Trend"] = (slope * x_numeric + intercept) / 1e6
    else:
        df_plot["OLS_Trend"] = rev_in_m

    # 3. Statistical Band (Historical Only)
    mean_rev = revenue.mean()
    std_rev = revenue.std() if len(revenue) > 1 else 0.0
    upper_band_m = (mean_rev + std_rev) / 1e6
    lower_band_m = max(0.0, (mean_rev - std_rev) / 1e6)

    fig = go.Figure()

    # Statistical Band Fill
    fig.add_trace(
        go.Scatter(
            x=pd.concat([df_plot["Date"], df_plot["Date"][::-1]]),
            y=np.concatenate(
                [
                    np.full(len(df_plot), upper_band_m),
                    np.full(len(df_plot), lower_band_m),
                ]
            ),
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.08)",
            line=dict(color="rgba(96, 165, 250, 0.3)", width=1, dash="dot"),
            hoverinfo="skip",
            name="Historical Mean ± 1σ",
            showlegend=True,
        )
    )

    # Actual Revenue Line
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=rev_in_m,
            mode="lines+markers",
            name="Actual Monthly Revenue",
            line=dict(color="#38BDF8", width=2.5),
            marker=dict(size=6, symbol="circle"),
            customdata=revenue,
            hovertemplate="<b>%{x|%B %Y}</b><br>Actual Revenue: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # OLS Trendline
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=df_plot["OLS_Trend"],
            mode="lines",
            name="OLS Trend",
            line=dict(color="#10B981", width=1.8),
            hovertemplate="<b>%{x|%B %Y}</b><br>OLS Trend: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # 3-Month Moving Average
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date"],
            y=df_plot["MA3"],
            mode="lines",
            name="3-Month Moving Average",
            line=dict(color="#F59E0B", width=2.2),
            hovertemplate="<b>%{x|%B %Y}</b><br>3-Mo Moving Avg: PhP %{y:.2f}M<extra></extra>",
        )
    )

    # Target Line (PhP 2.50M)
    fig.add_hline(
        y=2.50,
        line_color="#EF4444",
        line_width=1.5,
        line_dash="dash",
        annotation_text="Monthly Target — PhP 2.50M",
        annotation_position="top right",
        annotation_font=dict(color="#EF4444", size=10),
    )

    fig.update_layout(
        title=dict(
            text="<b>Historical Revenue Time Series & Statistical Baseline</b><br><sup>Monthly collection performance vs. OLS trend, moving average, and target boundary</sup>",
            font=dict(size=16),
        )
    )
    apply_executive_theme(fig)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", title="Monthly Revenue (PhP Millions)")

    st.plotly_chart(
        fig, use_container_width=True, config=get_modebar_config(), key="comp1_chart"
    )


# ==========================================
# COMPONENT 2: HISTORICAL REVENUE BREAKDOWN
# ==========================================


def render_revenue_breakdown_chart(df):
    """Generates Component 2: Stacked Bar Historical Revenue Breakdown by Stream."""
    required_cols = [
        "Date",
        "Traditional",
        "Non_Traditional",
        "Collected_Revenue",
    ]
    if df is None or df.empty or not all(c in df.columns for c in required_cols):
        st.warning(
            "Revenue breakdown visualization unavailable: required revenue fields are missing."
        )
        return

    df_plot = df.copy()
    df_plot["Date"] = pd.to_datetime(df_plot["Date"], errors="coerce")
    for col in ["Traditional", "Non_Traditional", "Collected_Revenue"]:
        df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce").fillna(0.0)

    df_plot = df_plot.dropna(subset=["Date"]).sort_values("Date")

    trad_m = df_plot["Traditional"] / 1e6
    non_trad_m = df_plot["Non_Traditional"] / 1e6
    total_m = df_plot["Collected_Revenue"] / 1e6

    fig = go.Figure()

    # Stacked Bar 1: Traditional
    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=trad_m,
            name="Traditional Revenue (Ship Calls)",
            marker_color="#A855F7",
            customdata=np.stack((trad_m, non_trad_m, total_m), axis=-1),
            hovertemplate="<b>%{x|%B %Y}</b><br>Traditional: PhP %{customdata[0]:.2f}M<br>Non-Traditional: PhP %{customdata[1]:.2f}M<br><b>Total Revenue: PhP %{customdata[2]:.2f}M</b><extra></extra>",
        )
    )

    # Stacked Bar 2: Non-Traditional
    fig.add_trace(
        go.Bar(
            x=df_plot["Date"],
            y=non_trad_m,
            name="Non-Traditional Revenue (Leases / Rentals)",
            marker_color="#F97316",
            customdata=np.stack((trad_m, non_trad_m, total_m), axis=-1),
            hovertemplate="<b>%{x|%B %Y}</b><br>Traditional: PhP %{customdata[0]:.2f}M<br>Non-Traditional: PhP %{customdata[1]:.2f}M<br><b>Total Revenue: PhP %{customdata[2]:.2f}M</b><extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text="<b>Revenue Composition by Stream (Traditional vs. Non-Traditional)</b><br><sup>Monthly breakdown comparing port vessel operations against contractual leases</sup>",
            font=dict(size=16),
        ),
    )
    apply_executive_theme(fig)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", title="Revenue (PhP Millions)")

    st.plotly_chart(
        fig, use_container_width=True, config=get_modebar_config(), key="comp2_chart"
    )


# ==========================================
# COMPONENT 3: INTEGRATED FORECAST MODEL
# ==========================================


def render_revenue_forecast_chart(df_forecast):
    """Generates Component 3: Long-term Integrated Revenue Forecast (2026–2040)."""
    required_cols = [
        "Year",
        "Baseline (PhP Billion)",
        "Master Plan Integrated (PhP Billion)",
    ]
    if (
        df_forecast is None
        or df_forecast.empty
        or not all(c in df_forecast.columns for c in required_cols)
    ):
        st.warning(
            "Integrated forecast visualization unavailable: missing required scenario fields."
        )
        return

    df_plot = df_forecast.copy()
    df_plot["Year"] = pd.to_numeric(df_plot["Year"], errors="coerce")
    df_plot["BAU_M"] = (
        pd.to_numeric(df_plot["Baseline (PhP Billion)"], errors="coerce") * 1000.0
    )
    df_plot["Master_M"] = (
        pd.to_numeric(
            df_plot["Master Plan Integrated (PhP Billion)"], errors="coerce"
        )
        * 1000.0
    )
    df_plot = df_plot.dropna(subset=["Year", "BAU_M", "Master_M"]).sort_values("Year")

    fig = go.Figure()

    # BAU Line
    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["BAU_M"],
            mode="lines+markers",
            name="Business-As-Usual (BAU)",
            line=dict(color="#94A3B8", width=2, dash="dash"),
            marker=dict(size=5),
            hovertemplate="<b>Year %{x}</b><br>BAU Revenue: PhP %{y:.1f}M<extra></extra>",
        )
    )

    # Master Plan Line (with fill to BAU)
    fig.add_trace(
        go.Scatter(
            x=df_plot["Year"],
            y=df_plot["Master_M"],
            mode="lines+markers",
            name="Master Plan Integrated Revenue",
            line=dict(color="#10B981", width=2.8),
            marker=dict(size=6, symbol="circle"),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.12)",
            customdata=df_plot["Master_M"] - df_plot["BAU_M"],
            hovertemplate="<b>Year %{x}</b><br>Integrated Revenue: PhP %{y:.1f}M<br>Incremental Potential: +PhP %{customdata:.1f}M<extra></extra>",
        )
    )

    # Milestone Annotations
    milestones = [
        (2028, "Phase I PAPs Online", df_plot),
        (2031, "Phase II Hub Active", df_plot),
        (2035, "Phase III Port Extension", df_plot),
    ]

    for year, text, df_ref in milestones:
        match = df_ref[df_ref["Year"] == year]
        if not match.empty:
            y_val = match["Master_M"].values[0]
            fig.add_annotation(
                x=year,
                y=y_val,
                text=f"<b>{text}</b>",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#10B981",
                arrowsize=1,
                arrowwidth=1.5,
                ax=0,
                ay=-35,
                font=dict(size=10, color="#F0F6FC"),
                bgcolor="#161B22",
                bordercolor="#10B981",
                borderwidth=1,
                borderpad=4,
            )

    fig.update_layout(
        title=dict(
            text="<b>Integrated Revenue Projection & Investment Value Gap (2026–2040)</b><br><sup>Evaluating organic BAU trajectory against accelerated Master Plan infrastructure deployment</sup>",
            font=dict(size=16),
        )
    )
    apply_executive_theme(fig)
    configure_executive_legend(fig)
    format_php_axis(fig, axis="y", scale=1, suffix="M", title="Annual Revenue (PhP Millions)")

    st.plotly_chart(
        fig, use_container_width=True, config=get_modebar_config(), key="comp3_chart"
    )
