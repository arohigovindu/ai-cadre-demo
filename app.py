import html
import time

import folium
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium

from topology_engine import analyze_parcels


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI-CADRE | Urban Cadastral Mapping",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SESSION STATE
# ============================================================

if "parcel_decisions" not in st.session_state:
    st.session_state.parcel_decisions = {}

if "selected_parcel" not in st.session_state:
    st.session_state.selected_parcel = None

if "drone_image" not in st.session_state:
    st.session_state.drone_image = None

if "extraction_run" not in st.session_state:
    st.session_state.extraction_run = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.html(
    """
    <style>
    :root {
        --ink: #17302a;
        --muted: #6d7e78;
        --line: #dfe8e3;
        --paper: #f5f7f4;
        --card: #ffffff;
        --green: #2f6f4e;
        --green-dark: #173d2d;
        --green-soft: #e9f3ec;
        --teal: #3c7d78;
        --sand: #d8b77a;
        --terracotta: #b86b4b;
        --red: #b94a48;
        --amber: #c38a32;
    }

    .stApp { background: var(--paper); color: var(--ink); }
    .block-container { padding: 0.7rem 2rem 3rem; max-width: 1550px; }

    /* Sticky navigation */
    html { scroll-behavior: smooth; }
    .cadre-nav-wrap {
        position: sticky; top: 0; z-index: 99999;
        margin: -0.7rem -2rem 18px; padding: 0 2rem 8px;
        background: var(--paper);
    }
    .cadre-nav {
        background: var(--green-dark); border-radius: 0 0 16px 16px;
        padding: 11px 18px; color: white;
        display:flex; align-items:center; gap:20px;
        box-shadow: 0 7px 22px rgba(23,61,45,.16);
        min-height:58px;
    }
    .cadre-brand-block { display:flex; align-items:center; gap:10px; flex:0 0 auto; }
    .cadre-logo { width:40px; height:40px; display:flex; align-items:center; justify-content:center; flex:0 0 40px; }
    .cadre-brand { font-size:18px; font-weight:900; letter-spacing:-.45px; line-height:1; }
    .cadre-subbrand { font-size:9px; color:#b8cec2; margin-top:4px; letter-spacing:.35px; text-transform:uppercase; }
    .cadre-nav-links { display:flex; align-items:center; justify-content:center; gap:4px; flex:1; flex-wrap:wrap; }
    .cadre-nav-link {
        color:#dce9e2; text-decoration:none; font-size:10px; font-weight:800;
        padding:7px 9px; border-radius:7px; white-space:nowrap;
        transition:background .15s ease, color .15s ease;
    }
    .cadre-nav-link:hover { background:#285640; color:#ffffff; }
    .cadre-status {
        display:flex; align-items:center; gap:7px; flex:0 0 auto;
        color:#d8e9df; font-size:9px; font-weight:800;
        border-left:1px solid #3b614f; padding-left:13px;
    }
    .status-dot { width:7px; height:7px; border-radius:50%; background:#7cc58c; box-shadow:0 0 0 3px rgba(124,197,140,.12); }
    .anchor-target { height:0; scroll-margin-top:86px; }

    /* Hero */
    .hero {
        background: linear-gradient(115deg, #173d2d 0%, #245943 58%, #3c7d78 100%);
        border-radius:18px; padding:25px 28px; color:white; margin-bottom:18px;
        box-shadow:0 10px 28px rgba(31,75,56,.14); position:relative; overflow:hidden;
    }
    .hero:after { content:""; position:absolute; width:220px; height:220px; right:-60px; top:-90px; border:1px solid rgba(255,255,255,.12); border-radius:50%; box-shadow:0 0 0 28px rgba(255,255,255,.04), 0 0 0 56px rgba(255,255,255,.025); }
    .hero-kicker { color:#d8e9c9; font-size:10px; font-weight:850; letter-spacing:1.2px; margin-bottom:6px; }
    .hero-title { font-size:31px; font-weight:850; margin:0; letter-spacing:-.9px; }
    .hero-text { color:#d8e8df; max-width:760px; line-height:1.5; margin-top:8px; font-size:13px; }
    .hero-flow { margin-top:15px; font-size:11px; font-weight:750; color:#f1e7ca; }

    /* Sections */
    .section-title { font-size:18px; font-weight:850; color:var(--ink); margin-top:20px; margin-bottom:3px; letter-spacing:-.2px; }
    .section-subtitle { color:var(--muted); font-size:11px; margin-bottom:11px; }

    /* KPI */
    .kpi-card { background:var(--card); border:1px solid var(--line); border-radius:13px; padding:15px 16px; min-height:94px; box-shadow:0 2px 12px rgba(24,52,41,.035); }
    .kpi-label { color:#71817b; font-size:10px; font-weight:850; text-transform:uppercase; letter-spacing:.65px; }
    .kpi-value { color:var(--ink); font-size:26px; font-weight:900; margin-top:4px; }
    .kpi-note { color:#82908b; font-size:10px; margin-top:1px; }

    /* Cards */
    .card { background:var(--card); border:1px solid var(--line); border-radius:13px; padding:17px; box-shadow:0 2px 12px rgba(24,52,41,.035); }
    .card-title { font-size:15px; font-weight:850; color:var(--ink); margin-bottom:4px; }
    .card-subtitle { font-size:11px; color:#778680; margin-bottom:11px; }

    /* Status */
    .status-pass,.status-fail,.status-warn { display:inline-block; border-radius:999px; padding:4px 9px; font-size:10px; font-weight:850; }
    .status-pass { background:#e7f2ea; color:#2d6b49; }
    .status-fail { background:#f9e9e7; color:#a64340; }
    .status-warn { background:#fbf1dd; color:#9b6b1d; }

    /* Explainability */
    .xai-box { background:#f0f5f1; border:1px solid #d7e5db; border-left:3px solid var(--teal); border-radius:10px; padding:12px; color:#40574e; font-size:11px; line-height:1.5; }
    .xai-title { font-size:10px; font-weight:850; color:#356b62; margin-bottom:3px; text-transform:uppercase; letter-spacing:.6px; }

    /* Signals */
    .signal { background:#f7f9f7; border:1px solid #e5ebe7; border-radius:9px; padding:9px; margin-bottom:7px; }
    .signal-label { font-size:9px; color:#7b8984; text-transform:uppercase; font-weight:850; }
    .signal-value { font-size:14px; color:#234137; font-weight:850; margin-top:2px; }

    /* Workflow */
    .workflow-card { background:white; border:1px solid var(--line); border-radius:12px; padding:13px; min-height:105px; }
    .workflow-number { width:26px; height:26px; border-radius:8px; background:#e6f0e9; color:var(--green); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:900; margin-bottom:8px; }
    .workflow-name { font-size:12px; font-weight:850; color:#254238; }
    .workflow-desc { font-size:10px; color:#76847f; margin-top:3px; line-height:1.35; }

    /* Upload */
    .upload-info { background:#f3f7f3; border:1px dashed #bdd0c3; border-radius:11px; padding:12px 14px; font-size:11px; color:#52675d; line-height:1.45; margin-bottom:10px; }
    .extraction-status { background:#edf6ef; border:1px solid #cce0d1; border-radius:11px; padding:12px; color:#2d6647; font-size:11px; }

    /* Streamlit controls */
    div[data-testid="stFileUploader"] { background:white; border:1px solid var(--line); border-radius:12px; padding:10px; }
    div.stButton > button, div.stDownloadButton > button { border-radius:9px; font-weight:750; border:1px solid #cfdcd4; }
    div.stButton > button[kind="primary"] { background:#2f6f4e; border-color:#2f6f4e; }
    div[data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:10px; border-radius:10px; }
    div[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }

    .footer { text-align:center; color:#89958f; font-size:10px; padding:22px 0 5px; }

    @media (max-width: 900px) {
        .cadre-nav { gap:10px; padding:10px 12px; }
        .cadre-nav-links { justify-content:flex-start; overflow-x:auto; flex-wrap:nowrap; }
        .cadre-status { display:none; }
        .cadre-brand { font-size:16px; }
        .cadre-subbrand { display:none; }
        .hero-title { font-size:25px; }
    }
    </style>
    """
)


# ============================================================
# LOAD PARCEL DATA
# ============================================================

gdf = analyze_parcels("sample_parcels.geojson")

if gdf.empty:
    st.error("No parcel features were found in sample_parcels.geojson.")
    st.stop()


# ============================================================
# SAFE METRICS
# ============================================================

total_parcels = len(gdf)

topology_pass = int(
    gdf["topology_status"]
    .astype(str)
    .str.startswith("PASS")
    .sum()
)

high_priority = int(
    (gdf["priority"].astype(str) == "HIGH").sum()
)

avg_confidence = float(gdf["confidence"].mean())


# ============================================================
# NAVBAR
# ============================================================

st.html(
    """
    <div class="cadre-nav-wrap">
        <div class="cadre-nav">
            <div class="cadre-brand-block">
                <div class="cadre-logo">
                    <svg viewBox="0 0 48 48" width="40" height="40" aria-label="AI-CADRE logo" role="img">
                        <path d="M24 3.5 43 14v20L24 44.5 5 34V14Z" fill="#d8b77a"/>
                        <path d="M24 3.5 43 14 24 24.5 5 14Z" fill="#f1e7ca"/>
                        <path d="M24 24.5 43 14v20L24 44.5Z" fill="#3c7d78"/>
                        <path d="M5 14 24 24.5v20L5 34Z" fill="#2f6f4e"/>
                        <path d="M24 11.5c-4.7 0-8.5 3.8-8.5 8.5 0 6.2 8.5 14.2 8.5 14.2s8.5-8 8.5-14.2c0-4.7-3.8-8.5-8.5-8.5Z" fill="#fff"/>
                        <circle cx="24" cy="20" r="3.2" fill="#b86b4b"/>
                    </svg>
                </div>
                <div>
                    <div class="cadre-brand">AI-CADRE</div>
                    <div class="cadre-subbrand">Urban Cadastral Mapping</div>
                </div>
            </div>

            <div class="cadre-nav-links">
                <a class="cadre-nav-link" href="#dashboard">Dashboard</a>
                <a class="cadre-nav-link" href="#survey">Survey Input</a>
                <a class="cadre-nav-link" href="#parcel-map">Parcel Map</a>
                <a class="cadre-nav-link" href="#qc">QC Checks</a>
                <a class="cadre-nav-link" href="#field">Field Verification</a>
                <a class="cadre-nav-link" href="#export">Export</a>
            </div>

            <div class="cadre-status">
                <span class="status-dot"></span> SYSTEM ONLINE
            </div>
        </div>
    </div>
    """
)


# ============================================================
# HERO
# ============================================================

st.html(
    """<div id="dashboard" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="hero">
        <div class="hero-kicker">SIH26012 • URBAN CADASTRAL MAPPING</div>

        <div class="hero-title">
            From drone imagery to validated parcel layers
        </div>

        <div class="hero-text">
            Turn survey imagery into structured parcel information, run geometry
            quality checks, review flagged features, and export GIS-ready
            cadastral data with the surveyor in control.
        </div>

        <div class="hero-flow">
            Survey → Extract → Check → Review → Export
        </div>
    </div>
    """
)


# ============================================================
# DRONE IMAGERY INPUT
# ============================================================

st.html(
    """<div id="survey" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">Survey Imagery</div>
    <div class="section-subtitle">
        Add a drone image to start a survey run.
    </div>
    """
)

upload_col, info_col = st.columns([1.7, 1])

with upload_col:
    st.html(
        """
        <div class="upload-info">
            <b>Image input</b><br>JPG, JPEG or PNG survey imagery.
            <br>
            Used as the source layer for feature extraction.
        </div>
        """
    )

    uploaded_image = st.file_uploader(
        "Choose survey image",
        type=["jpg", "jpeg", "png"],
        key="drone_uploader",
    )

with info_col:
    if uploaded_image is not None:
        file_size_kb = uploaded_image.size / 1024

        st.html(
            f"""
            <div class="card">
                <div class="card-title">Survey Image</div>
                <div class="signal">
                    <div class="signal-label">Filename</div>
                    <div class="signal-value">
                        {html.escape(uploaded_image.name)}
                    </div>
                </div>
                <div class="signal">
                    <div class="signal-label">File Size</div>
                    <div class="signal-value">
                        {file_size_kb:.1f} KB
                    </div>
                </div>
                <div style="color:#748396;font-size:11px;margin-top:7px;">
                    Ready for processing.
                </div>
            </div>
            """
        )

if uploaded_image is not None:
    st.markdown("#### Image Preview")

    st.image(
        uploaded_image,
        caption="Survey image",
        use_container_width=True,
    )

    extraction_col1, extraction_col2 = st.columns([1, 2])

    with extraction_col1:
        run_extraction = st.button(
            "Run Extraction",
            type="primary",
            use_container_width=True,
        )

    with extraction_col2:
        st.caption(
            "Prototype inference mode • Deep-learning segmentation model "
            "can be connected to this pipeline later."
        )

    if run_extraction:
        st.session_state.drone_image = uploaded_image.name
        st.session_state.extraction_run = True

        with st.spinner(
            "Processing imagery and preparing map layers..."
        ):
            time.sleep(1.2)

        st.success("Extraction complete.")

if st.session_state.extraction_run and uploaded_image is not None:
    st.html(
        """
        <div class="extraction-status">
            <b>✓ Run complete</b><br>
            The imagery has been ingested and the cadastral feature
            extraction pipeline is ready for model-based inference.
        </div>
        """
    )

    # --------------------------------------------------------
    # EXTRACTION RESULTS
    # --------------------------------------------------------

    st.html(
        """
        <div class="section-title">Extracted Features</div>
        <div class="section-subtitle">
            Feature counts from the current survey run.
        </div>
        """
    )

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.html(
            """
            <div class="kpi-card">
                <div class="kpi-label">Parcels</div>
                <div class="kpi-value">24</div>
                <div class="kpi-note">Boundary candidates</div>
            </div>
            """
        )

    with r2:
        st.html(
            """
            <div class="kpi-card">
                <div class="kpi-label">Buildings</div>
                <div class="kpi-value">18</div>
                <div class="kpi-note">Footprint candidates</div>
            </div>
            """
        )

    with r3:
        st.html(
            """
            <div class="kpi-card">
                <div class="kpi-label">Roads / Paths</div>
                <div class="kpi-value">7</div>
                <div class="kpi-note">Access candidates</div>
            </div>
            """
        )

    with r4:
        st.html(
            """
            <div class="kpi-card">
                <div class="kpi-label">Mean confidence</div>
                <div class="kpi-value">91%</div>
                <div class="kpi-note">Current run</div>
            </div>
            """
        )

    e1, e2 = st.columns(2)

    with e1:
        first_id = str(gdf.iloc[0]["parcel_id"])
        first_area = float(gdf.iloc[0].get("area_sqm", gdf.iloc[0].geometry.area))

        st.html(
            f"""
            <div class="card">
                <div class="card-title">Parcel Information</div>

                <div class="signal">
                    <div class="signal-label">Parcel ID</div>
                    <div class="signal-value">
                        {html.escape(first_id)}
                    </div>
                </div>

                <div class="signal">
                    <div class="signal-label">Geometry Area</div>
                    <div class="signal-value">
                        {first_area:.2f} m²
                    </div>
                </div>

                <div class="signal">
                    <div class="signal-label">Priority</div>
                    <div class="signal-value">
                        {html.escape(str(gdf.iloc[0]["priority"]))}
                    </div>
                </div>
            </div>
            """
        )

    with e2:
        st.html(
            """
            <div class="card">
                <div class="card-title">Extraction Notes</div>
                <div class="card-subtitle">
                    Key signals used for review
                </div>

                <div class="xai-box">
                    <div class="xai-title">Review focus</div>

                    The system identifies visible spatial patterns from
                    drone imagery and proposes cadastral features for
                    downstream GIS validation.

                    <br><br>

                    <b>Primary signals:</b>
                    boundary contrast, geometric continuity,
                    connected regions and spatial separation.

                    <br><br>

                    These are <b>preliminary results</b>.
                    Final acceptance remains with the authorized surveyor.
                </div>
            </div>
            """
        )

    st.info(
        "Demo mode: extraction counts are prototype values; parcel review and GIS checks are active."
    )


# ============================================================
# OVERVIEW METRICS
# ============================================================

st.html(
    """<div id="overview" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">Survey Overview</div>
    <div class="section-subtitle">
        Parcel quality and review status
    </div>
    """
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Parcels</div>
            <div class="kpi-value">{total_parcels}</div>
            <div class="kpi-note">Current layer</div>
        </div>
        """
    )

with k2:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Topology pass</div>
            <div class="kpi-value">{topology_pass}</div>
            <div class="kpi-note">Geometry checks</div>
        </div>
        """
    )

with k3:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Review needed</div>
            <div class="kpi-value">{high_priority}</div>
            <div class="kpi-note">Needs attention</div>
        </div>
        """
    )

with k4:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg. confidence</div>
            <div class="kpi-value">{avg_confidence:.1f}%</div>
            <div class="kpi-note">Parcel score</div>
        </div>
        """
    )


# ============================================================
# WEB GIS WORKSPACE
# ============================================================

st.html(
    """<div id="parcel-map" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">Parcel Map</div>
    <div class="section-subtitle">
        Select a parcel to inspect geometry and review status.
    </div>
    """
)

map_col, inspector_col = st.columns([1.55, 1])


# ============================================================
# MAP
# ============================================================

with map_col:
    map_gdf = gdf.copy()

    try:
        map_gdf = map_gdf.to_crs(epsg=4326)
    except Exception:
        pass

    try:
        center_geom = map_gdf.geometry.union_all()
    except Exception:
        try:
            from shapely.ops import unary_union
            center_geom = unary_union(map_gdf.geometry)
        except Exception:
            center_geom = map_gdf.geometry.iloc[0]

    center = [
        center_geom.centroid.y,
        center_geom.centroid.x,
    ]

    m = folium.Map(
        location=center,
        zoom_start=16,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    try:
        bounds = map_gdf.total_bounds
        m.fit_bounds(
            [
                [bounds[1], bounds[0]],
                [bounds[3], bounds[2]],
            ]
        )
    except Exception:
        pass

    for _, row in map_gdf.iterrows():
        parcel_id = str(row["parcel_id"])
        confidence_value = float(row["confidence"])
        priority = str(row["priority"])

        decision = st.session_state.parcel_decisions.get(
            parcel_id,
            "PENDING",
        )

        if parcel_id == str(st.session_state.selected_parcel):
            fill_color = "#3C7D78"
        elif decision == "ACCEPTED":
            fill_color = "#4F8A61"
        elif decision == "REJECTED":
            fill_color = "#B94A48"
        elif decision == "FIELD VERIFICATION":
            fill_color = "#C38A32"
        elif confidence_value < 70:
            fill_color = "#B94A48"
        elif confidence_value < 85:
            fill_color = "#C38A32"
        else:
            fill_color = "#4F8A61"

        popup_html = f"""
        <div style="font-family:Arial;min-width:190px;">
            <b>Parcel {html.escape(parcel_id)}</b><br><br>
            Confidence: {confidence_value:.1f}%<br>
            Geometry: {html.escape(str(row["topology_status"]))}<br>
            Priority: {html.escape(priority)}<br>
            Decision: {html.escape(decision)}
        </div>
        """

        tooltip = folium.Tooltip(
            f"Parcel {parcel_id} • {confidence_value:.1f}%"
        )

        feature = {
            "type": "Feature",
            "geometry": row["geometry"].__geo_interface__,
            "properties": {
                "parcel_id": parcel_id,
            },
        }

        folium.GeoJson(
            feature,
            style_function=lambda feature, fc=fill_color: {
                "fillColor": fc,
                "color": "#25483A",
                "weight": 2,
                "fillOpacity": 0.5,
            },
            highlight_function=lambda feature: {
                "weight": 4,
                "fillOpacity": 0.72,
            },
            tooltip=tooltip,
            popup=folium.Popup(
                popup_html,
                max_width=300,
            ),
        ).add_to(m)

    folium.LayerControl().add_to(m)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index:9999;
        background:white;
        padding:12px 14px;
        border:1px solid #ddd;
        border-radius:8px;
        font-size:11px;
        box-shadow:0 2px 8px rgba(0,0,0,.15);
    ">
        <b>Parcel status</b><br>
        <span style="color:#22C55E;">●</span> Good<br>
        <span style="color:#F59E0B;">●</span> Review<br>
        <span style="color:#EF4444;">●</span> Issue<br>
        <span style="color:#38BDF8;">●</span> Selected
    </div>
    """

    m.get_root().html.add_child(
        folium.Element(legend_html)
    )

    map_result = st_folium(
        m,
        use_container_width=True,
        height=590,
        returned_objects=["last_active_drawing"],
    )

    clicked = map_result.get("last_active_drawing")

    if clicked:
        properties = clicked.get("properties", {})
        clicked_id = properties.get("parcel_id")

        if clicked_id is not None:
            clicked_id = str(clicked_id)

            if clicked_id in gdf["parcel_id"].astype(str).tolist():
                if clicked_id != str(
                    st.session_state.selected_parcel
                ):
                    st.session_state.selected_parcel = clicked_id
                    st.rerun()


# ============================================================
# PARCEL INSPECTOR
# ============================================================

with inspector_col:
    st.html(
        """
        <div class="card-title">Parcel Inspector</div>
        <div class="card-subtitle">
            Check the parcel and record a decision.
        </div>
        """
    )

    parcel_ids = (
        gdf["parcel_id"]
        .astype(str)
        .tolist()
    )

    if st.session_state.selected_parcel in parcel_ids:
        default_index = parcel_ids.index(
            st.session_state.selected_parcel
        )
    else:
        default_index = 0

    selected_id = st.selectbox(
        "Select Parcel",
        parcel_ids,
        index=default_index,
        format_func=lambda x: f"Parcel {x}",
    )

    st.session_state.selected_parcel = selected_id

    selected_rows = gdf[
        gdf["parcel_id"].astype(str) == str(selected_id)
    ]

    if selected_rows.empty:
        st.warning("Selected parcel could not be found.")
        st.stop()

    p = selected_rows.iloc[0]

    confidence = float(p["confidence"])

    if confidence >= 85:
        confidence_label = "HIGH"
        confidence_class = "status-pass"
    elif confidence >= 70:
        confidence_label = "MEDIUM"
        confidence_class = "status-warn"
    else:
        confidence_label = "LOW"
        confidence_class = "status-fail"

    st.html(
        f"""
        <div class="card">
            <div class="card-title">
                Parcel {html.escape(str(selected_id))}
            </div>

            <div style="margin:10px 0;">
                <span class="{confidence_class}">
                    {confidence_label} CONFIDENCE
                </span>
            </div>

            <div style="
                background:#e8edf2;
                height:9px;
                border-radius:10px;
                overflow:hidden;
                margin:10px 0;
            ">
                <div style="
                    width:{confidence}%;
                    height:100%;
                    background:#1684c5;
                    border-radius:10px;
                "></div>
            </div>

            <div style="
                display:flex;
                justify-content:space-between;
                font-size:12px;
                color:#657587;
            ">
                <span>Confidence</span>
                <b>{confidence:.1f}%</b>
            </div>
        </div>
        """
    )

    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    if "area_sqm" in p.index:
        area_value = float(p["area_sqm"])
    elif "area" in p.index:
        area_value = float(p["area"])
    else:
        try:
            area_value = float(p.geometry.area)
        except Exception:
            area_value = 0.0

    topology = str(p["topology_status"])

    if topology.startswith("PASS"):
        topology_badge = (
            '<span class="status-pass">✓ TOPOLOGY VALID</span>'
        )
        topology_description = (
            "No significant geometry conflicts detected."
        )
    else:
        topology_badge = (
            '<span class="status-fail">⚠ REVIEW REQUIRED</span>'
        )
        topology_description = (
            "Geometry requires surveyor review before approval."
        )

    st.html(
        f"""
        <div class="card">
            <div class="card-title">Parcel Information</div>

            <div class="signal">
                <div class="signal-label">Parcel ID</div>
                <div class="signal-value">
                    {html.escape(str(p["parcel_id"]))}
                </div>
            </div>

            <div class="signal">
                <div class="signal-label">Geometry Area</div>
                <div class="signal-value">
                    {area_value:.2f} m²
                </div>
            </div>

            <div class="signal">
                <div class="signal-label">Priority</div>
                <div class="signal-value">
                    {html.escape(str(p["priority"]))}
                </div>
            </div>

            <div style="margin-top:10px;">
                {topology_badge}
            </div>

            <div style="
                color:#748396;
                font-size:11px;
                margin-top:7px;
            ">
                {topology_description}
            </div>
        </div>
        """
    )

    # --------------------------------------------------------
    # AI FEATURE SIGNALS
    # --------------------------------------------------------

    compactness = (
        float(p["compactness"])
        if "compactness" in p.index
        else 0.0
    )

    vertex_count = (
        int(p["vertex_count"])
        if "vertex_count" in p.index
        else 0
    )

    overlap_area = (
        float(p["overlap_area"])
        if "overlap_area" in p.index
        else 0.0
    )

    area_anomaly = (
        str(p["area_anomaly"])
        if "area_anomaly" in p.index
        else "NORMAL"
    )

    st.html(
        """
        <div class="card-title">Feature Signals</div>
        <div class="card-subtitle">
            Geometry checks behind the parcel score
        </div>
        """
    )

    s1, s2 = st.columns(2)

    with s1:
        st.html(
            f"""
            <div class="signal">
                <div class="signal-label">Compactness</div>
                <div class="signal-value">
                    {compactness:.3f}
                </div>
            </div>

            <div class="signal">
                <div class="signal-label">Vertices</div>
                <div class="signal-value">
                    {vertex_count}
                </div>
            </div>
            """
        )

    with s2:
        st.html(
            f"""
            <div class="signal">
                <div class="signal-label">Overlap Area</div>
                <div class="signal-value">
                    {overlap_area:.2f} m²
                </div>
            </div>

            <div class="signal">
                <div class="signal-label">Area Pattern</div>
                <div class="signal-value">
                    {html.escape(area_anomaly)}
                </div>
            </div>
            """
        )

    # --------------------------------------------------------
    # XAI
    # --------------------------------------------------------

    reason = html.escape(
        str(p["xai_reason"])
    )

    st.html(
        f"""
        <div class="xai-box">
            <div class="xai-title">
                Why it was flagged
            </div>

            {reason}

            <br><br>

            <b>Human-in-the-loop:</b>
            The parcel is a preliminary result. Final validation remains with the authorized surveyor.
        </div>
        """
    )

    # --------------------------------------------------------
    # SURVEYOR DECISION
    # --------------------------------------------------------

    st.html(
        """
        <div class="card-title">👷 Surveyor Decision</div>
        """
    )

    b1, b2 = st.columns(2)
    b3, b4 = st.columns(2)

    with b1:
        if st.button(
            "✓ Accept",
            use_container_width=True,
            key=f"accept_{selected_id}",
        ):
            st.session_state.parcel_decisions[
                selected_id
            ] = "ACCEPTED"
            st.rerun()

    with b2:
        if st.button(
            "✎ Edit Required",
            use_container_width=True,
            key=f"edit_{selected_id}",
        ):
            st.session_state.parcel_decisions[
                selected_id
            ] = "EDIT REQUIRED"
            st.rerun()

    with b3:
        if st.button(
            "✕ Reject",
            use_container_width=True,
            key=f"reject_{selected_id}",
        ):
            st.session_state.parcel_decisions[
                selected_id
            ] = "REJECTED"
            st.rerun()

    with b4:
        if st.button(
            "⚑ Field GT",
            use_container_width=True,
            key=f"field_{selected_id}",
        ):
            st.session_state.parcel_decisions[
                selected_id
            ] = "FIELD VERIFICATION"
            st.rerun()

    current_decision = st.session_state.parcel_decisions.get(
        selected_id,
        "PENDING",
    )

    if current_decision == "ACCEPTED":
        st.success("Parcel accepted.")
    elif current_decision == "EDIT REQUIRED":
        st.info("Parcel marked for editing.")
    elif current_decision == "REJECTED":
        st.error("Parcel rejected.")
    elif current_decision == "FIELD VERIFICATION":
        st.warning("Parcel queued for field verification.")
    else:
        st.info("Awaiting survey decision.")


# ============================================================
# GIS QUALITY CONTROL
# ============================================================

st.html(
    """<div id="qc" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">GIS Quality Control</div>
    <div class="section-subtitle">
        Geometry checks before approval.
    </div>
    """
)

q1, q2, q3, q4 = st.columns(4)

valid_geometry = int(
    gdf.geometry.is_valid.sum()
)

overlap_count = int(
    (gdf["overlap_area"] > 0.01).sum()
)

sliver_count = (
    int((gdf["area_sqm"] < 1.0).sum())
    if "area_sqm" in gdf.columns
    else 0
)

field_checks = sum(
    1
    for value in st.session_state.parcel_decisions.values()
    if value == "FIELD VERIFICATION"
)

with q1:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Valid geometry</div>
            <div class="kpi-value">{valid_geometry}/{total_parcels}</div>
            <div class="kpi-note">Validity check</div>
        </div>
        """
    )

with q2:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Overlap flags</div>
            <div class="kpi-value">{overlap_count}</div>
            <div class="kpi-note">Potential conflicts</div>
        </div>
        """
    )

with q3:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Sliver flags</div>
            <div class="kpi-value">{sliver_count}</div>
            <div class="kpi-note">Very small shapes</div>
        </div>
        """
    )

with q4:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Field Checks</div>
            <div class="kpi-value">{field_checks}</div>
            <div class="kpi-note">Ground checks</div>
        </div>
        """
    )


# ============================================================
# FIELD VERIFICATION QUEUE
# ============================================================

st.html(
    """<div id="field" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">Field Verification Queue</div>
    <div class="section-subtitle">
        Parcels that need on-site verification.
    </div>
    """
)

field_rows = []

for _, row in gdf.iterrows():
    pid = str(row["parcel_id"])

    decision = st.session_state.parcel_decisions.get(
        pid,
        "PENDING",
    )

    if (
        str(row["priority"]) == "HIGH"
        or decision == "FIELD VERIFICATION"
    ):
        field_rows.append(
            {
                "Parcel": pid,
                "Confidence": f'{float(row["confidence"]):.1f}%',
                "Priority": str(row["priority"]),
                "Topology": str(row["topology_status"]),
                "Decision": decision,
            }
        )

if field_rows:
    st.dataframe(
        field_rows,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success(
        "No parcels currently require field verification."
    )


# ============================================================
# DECISION SUMMARY
# ============================================================

st.html(
    """
    <div class="section-title">📋 Surveyor Decision Summary</div>
    <div class="section-subtitle">
        Current review status.
    </div>
    """
)

accepted = sum(
    1
    for x in st.session_state.parcel_decisions.values()
    if x == "ACCEPTED"
)

edited = sum(
    1
    for x in st.session_state.parcel_decisions.values()
    if x == "EDIT REQUIRED"
)

rejected = sum(
    1
    for x in st.session_state.parcel_decisions.values()
    if x == "REJECTED"
)

field_verification = sum(
    1
    for x in st.session_state.parcel_decisions.values()
    if x == "FIELD VERIFICATION"
)

pending = total_parcels - (
    accepted
    + edited
    + rejected
    + field_verification
)

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.metric("Accepted", accepted)

with d2:
    st.metric("Edit Required", edited)

with d3:
    st.metric("Rejected", rejected)

with d4:
    st.metric("Pending", max(0, pending))


# ============================================================
# WORKFLOW
# ============================================================

st.html(
    """
    <div class="section-title">⚙️ Survey Workflow</div>
    <div class="section-subtitle">
        From imagery to GIS-ready parcel data.
    </div>
    """
)

w1, w2, w3, w4, w5, w6 = st.columns(6)

workflow = [
    (
        "1",
        "Data",
        "Survey imagery + GIS",
    ),
    (
        "2",
        "AI Extraction",
        "Detect features",
    ),
    (
        "3",
        "Parcel Proposal",
        "Create parcel layer",
    ),
    (
        "4",
        "Topology",
        "Run geometry checks",
    ),
    (
        "5",
        "Confidence",
        "Prioritise review",
    ),
    (
        "6",
        "Surveyor",
        "Surveyor decision",
    ),
]

for col, item in zip(
    [w1, w2, w3, w4, w5, w6],
    workflow,
):
    number, name, desc = item

    with col:
        st.html(
            f"""
            <div class="workflow-card">
                <div class="workflow-number">
                    {html.escape(number)}
                </div>

                <div class="workflow-name">
                    {html.escape(name)}
                </div>

                <div class="workflow-desc">
                    {html.escape(desc)}
                </div>
            </div>
            """
        )


# ============================================================
# GEOJSON EXPORT
# ============================================================

st.html(
    """<div id="export" class="anchor-target"></div>"""
)

st.html(
    """
    <div class="section-title">GIS Export</div>
    <div class="section-subtitle">
        Export the parcel layer for GIS use.
    </div>
    """
)

export_gdf = gdf.copy()

export_gdf["surveyor_decision"] = (
    export_gdf["parcel_id"]
    .astype(str)
    .map(
        lambda x: st.session_state.parcel_decisions.get(
            x,
            "PENDING",
        )
    )
)

geojson_data = export_gdf.to_json()

ex1, ex2 = st.columns(2)

with ex1:
    st.download_button(
        "Download Parcel GeoJSON",
        data=geojson_data,
        file_name="ai_cadre_preliminary_parcels.geojson",
        mime="application/geo+json",
        use_container_width=True,
    )

approved_gdf = export_gdf[
    export_gdf["surveyor_decision"] == "ACCEPTED"
]

with ex2:
    if len(approved_gdf) > 0:
        approved_geojson = approved_gdf.to_json()

        st.download_button(
            "Download Approved",
            data=approved_geojson,
            file_name="ai_cadre_approved_parcels.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )
    else:
        st.button(
            "⬇️ Approved Parcels",
            disabled=True,
            use_container_width=True,
        )


# ============================================================
# HUMAN-IN-THE-LOOP NOTE
# ============================================================

st.html(
    """
    <div class="xai-box">
        <div class="xai-title">
            Survey review required
        </div>

        Extracted boundaries and features are <b>preliminary</b>.
        Geometry checks flag parcels that need attention before export.
        Final cadastral approval remains with the authorized surveyor.
    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">
        <b>AI-CADRE</b> • SIH26012 • Urban Cadastral Mapping &amp; Feature Extraction
        <br>
        SIH 2026 prototype • Human-in-the-loop survey review
    </div>
    """
)
