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

# Configure page layout
st.set_page_config(
    page_title="Geospatial Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🗺️ Interactive Spatial Analytics")

# Sample Folium Map
m = folium.Map(location=[12.8797, 121.7740], zoom_start=6, tiles="OpenStreetMap")
folium.Marker(
    location=[14.5995, 120.9842],
    popup="Metro Manila",
    tooltip="Click for info",
).add_to(m)

# Render inside Streamlit
st_data = st_folium(m, width="100%", height=500)
