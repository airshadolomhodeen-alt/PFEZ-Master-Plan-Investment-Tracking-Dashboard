# ⚓ Polloc Freeport and Economic Zone (PFEZ): Master Plan & Investment Tracking Dashboard

An interactive, production-ready enterprise dashboard built with **Streamlit**, **Pandas**, **GeoPandas**, and **Plotly** to visualize the Phase 3 Site Development Plan and Investment Program (SDPIP) for the **Polloc Freeport and Economic Zone (PFEZ)** under the Bangsamoro Economic Zone Authority (BEZA)[cite: 1].

---

## 🚀 Key Features

* **Interactive KPI Metrics:** Tracks high-level financial commitments, program timelines (2026–2040)[cite: 1], and overall completion progress.
* **Investment & Phasing Program:** Dynamic filters across implementation phases, sectors, and funding arrangements for 95 Strategic Programs and Projects (PAPs)[cite: 1].
* **Spatial Development Map Viewer:** Direct parsing and rendering of QGIS-exported GeoJSON zoning layers (e.g., Port Operations Zone, Commercial Spine, Mangrove Ecopark, and Planned Unit Development)[cite: 1].
* **Risk & M&E Matrix:** Built-in tabular tracking for project statuses, bottlenecks, and pre-identified risk levels.

---

## 📁 Repository Structure

```text
├── .streamlit/
│   └── config.toml             # Streamlit dark theme & server configurations
├── .devcontainer/
│   └── devcontainer.json       # VS Code containerization configuration
├── app.py                      # Main Streamlit application script
├── theme.py                    # Modular UI styles and banners
├── requirements.txt            # Python package dependencies
├── *.geojson                   # QGIS spatial zoning files and polygons
└── README.md                   # Project documentation
