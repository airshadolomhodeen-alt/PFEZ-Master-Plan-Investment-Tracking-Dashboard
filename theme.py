# theme.py - Modular UI styling and components for PFEZ Dashboard
import streamlit as st

def apply_enterprise_theme():
    """Injects custom dark-mode enterprise CSS styles into Streamlit."""
    st.markdown("""
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
    """, unsafe_allow_html=True)

def render_top_banner():
    """Renders the standardized PFEZ header banner."""
    st.markdown("""
        <div style="background-color: #161B22; padding: 15px; border-radius: 8px; border: 1px solid #30363D; text-align: center; margin-bottom: 20px;">
            <h2 style="color: #58A6FF; margin: 0; font-size: 22px;">POLLOC FREEDOM AND ECONOMIC ZONE (PFEZ): MASTER PLAN & INVESTMENT TRACKING DASHBOARD</h2>
            <p style="color: #8B949E; margin: 5px 0 0 0; font-size: 13px;">Data Source: Phase 3 SDPIP Report / Bangsamoro Economic Zone Authority (BEZA)</p>
        </div>
    """, unsafe_allow_html=True)
