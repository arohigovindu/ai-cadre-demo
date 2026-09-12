import html
import streamlit as st
import folium
from streamlit_folium import st_folium
from topology_engine import analyze_parcels


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI-CADRE | Cadastral AI Co-Pilot",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
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

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f4f7fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* ---------- NAVBAR ---------- */

    .cadre-nav {
        background: #071525;
        border-radius: 14px;
        padding: 15px 22px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .cadre-brand {
        font-size: 23px;
        font-weight: 800;
        letter-spacing: -0.4px;
    }

    .cadre-subbrand {
        font-size: 12px;
        color: #a8b6c8;
        margin-top: 2px;
    }

    .cadre-pill {
        background: #102a43;
        border: 1px solid #23425e;
        padding: 7px 13px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        color: #8fd3ff;
    }

    /* ---------- HERO ---------- */

    .hero {
        background: linear-gradient(135deg, #071525 0%, #0d2740 100%);
        border-radius: 18px;
        padding: 30px 32px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 8px 30px rgba(7, 21, 37, 0.12);
    }

    .hero-kicker {
        color: #61c4ff;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.1px;
        margin-bottom: 7px;
    }

    .hero-title {
        font-size: 35px;
        font-weight: 850;
        margin: 0;
        letter-spacing: -1px;
    }

    .hero-text {
        color: #c5d3e2;
        max-width: 850px;
        line-height: 1.55;
        margin-top: 10px;
        font-size: 15px;
    }

    .hero-flow {
        margin-top: 20px;
        font-size: 13px;
        font-weight: 700;
        color: #e5f5ff;
    }

    /* ---------- SECTION HEADERS ---------- */

    .section-title {
        font-size: 21px;
        font-weight: 800;
        color: #0b1d2e;
        margin-top: 22px;
        margin-bottom: 4px;
    }

    .section-subtitle {
        color: #68788a;
        font-size: 13px;
        margin-bottom: 14px;
    }

    /* ---------- KPI ---------- */

    .kpi-card {
        background: white;
        border: 1px solid #e3eaf1;
        border-radius: 14px;
        padding: 18px;
        min-height: 105px;
        box-shadow: 0 3px 15px rgba(10, 35, 60, 0.04);
    }

    .kpi-label {
        color: #728296;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .6px;
    }

    .kpi-value {
        color: #0b1d2e;
        font-size: 28px;
        font-weight: 850;
        margin-top: 5px;
    }

    .kpi-note {
        color: #7c8b9a;
        font-size: 11px;
        margin-top: 2px;
    }

    /* ---------- CARDS ---------- */

    .card {
        background: white;
        border: 1px solid #e3eaf1;
        border-radius: 14px;
        padding: 19px;
        box-shadow: 0 3px 15px rgba(10, 35, 60, 0.04);
    }

    .card-title {
        font-size: 16px;
        font-weight: 800;
        color: #102538;
        margin-bottom: 5px;
    }

    .card-subtitle {
        font-size: 12px;
        color: #718096;
        margin-bottom: 13px;
    }

    /* ---------- STATUS ---------- */

    .status-pass {
        display: inline-block;
        background: #e8f8ef;
        color: #15803d;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 800;
    }

    .status-fail {
        display: inline-block;
        background: #fff0ef;
        color: #dc2626;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 800;
    }

    .status-warn {
        display: inline-block;
        background: #fff7e6;
        color: #b45309;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 800;
    }

    /* ---------- XAI ---------- */

    .xai-box {
        background: #f1f8ff;
        border: 1px solid #cce7fb;
        border-radius: 12px;
        padding: 14px;
        color: #21445e;
        font-size: 13px;
        line-height: 1.5;
    }

    .xai-title {
        font-size: 12px;
        font-weight: 850;
        color: #0c527d;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: .6px;
    }

    /* ---------- SIGNALS ---------- */

    .signal {
        background: #f7f9fc;
        border: 1px solid #e7edf3;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
    }

    .signal-label {
        font-size: 10px;
        color: #77879a;
        text-transform: uppercase;
        font-weight: 800;
    }

    .signal-value {
        font-size: 15px;
        color: #13283c;
        font-weight: 800;
        margin-top: 2px;
    }

    /* ---------- WORKFLOW ---------- */

    .workflow-card {
        background: white;
        border: 1px solid #e1e8ef;
        border-radius: 13px;
        padding: 16px;
        min-height: 115px;
    }

    .workflow-number {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #e8f5ff;
        color: #0877b9;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 850;
        margin-bottom: 9px;
    }

    .workflow-name {
        font-size: 13px;
        font-weight: 800;
        color: #162c40;
    }

    .workflow-desc {
        font-size: 11px;
        color: #718096;
        margin-top: 4px;
        line-height: 1.4;
    }

    /* ---------- UPLOAD AREA ---------- */

    .upload-info {
        background: #f5faff;
        border: 1px solid #d7eafa;
        border-radius: 12px;
        padding: 13px 15px;
        font-size: 12px;
        color: #426078;
        line-height: 1.5;
        margin-bottom: 12px;
    }

    .extraction-status {
        background: #eefaf3;
        border: 1px solid #ccebd8;
        border-radius: 12px;
        padding: 14px;
        color: #17633a;
        font-size: 13px;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        color: #8a98a7;
        font-size: 11px;
        padding: 25px 0 5px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD PARCEL DATA
# ============================================================

gdf = analyze_parcels("sample_parcels.geojson")


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
    <div class="cadre-nav">
        <div>
            <div class="cadre-brand">🛰️ AI-CADRE</div>
            <div class="cadre-subbrand">
                Cadastral AI Co-Pilot • Urban Parcel Intelligence
            </div>
        </div>
        <div class="cadre-pill">
            SIH26012 • PROTOTYPE
        </div>
    </div>
    """
)


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero">
        <div class="hero-kicker">SIH26012 • URBAN CADASTRAL MAPPING</div>

        <div class="hero-title">
            AI-powered cadastral intelligence
        </div>

        <div class="hero-text">
            Transform drone imagery and geospatial data into preliminary,
            validated and GIS-ready parcel information — while keeping
            the authorized surveyor in control of every final decision.
        </div>

        <div class="hero-flow">
            AI Proposes → GIS Validates → Confidence Prioritizes → Surveyor Approves
        </div>
    </div>
    """
)


# ============================================================
# DRONE IMAGERY INPUT
# ============================================================

st.html(
    """
    <div class="section-title">🛰️ Drone Imagery Input</div>
    <div class="section-subtitle">
        Upload high-resolution drone imagery to begin the cadastral extraction workflow.
    </div>
    """
)

upload_col, info_col = st.columns([1.7, 1])

with upload_col:

    st.markdown(
        """
        <div class="upload-info">
        <b>Supported prototype inputs:</b> JPG, JPEG and PNG drone imagery.
        <br>
        The uploaded image becomes the source layer for the AI extraction pipeline.
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_image = st.file_uploader(
        "Upload drone imagery",
        type=["jpg", "jpeg", "png"],
        key="drone_uploader"
    )

with info_col:

    if uploaded_image is not None:

        file_size_kb = uploaded_image.size / 1024

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
            <span>AI confidence</span>
            <b>{confidence:.1f}%</b>
        </div>
    </div>
    """
)
if uploaded_image is not None:

    st.markdown("#### Image Preview")

    st.image(
        uploaded_image,
        caption="Uploaded drone imagery",
        use_container_width=True
    )

    st.markdown("")

    extraction_col1, extraction_col2 = st.columns([1, 2])

    with extraction_col1:

        run_extraction = st.button(
            "🚀 Run AI Extraction",
            type="primary",
            use_container_width=True
        )

    with extraction_col2:

        st.caption(
            "Prototype inference mode • Deep-learning segmentation model "
            "can be connected to this pipeline later."
        )

    if run_extraction:

        st.session_state.drone_image = uploaded_image.name
        st.session_state.extraction_run = True

        with st.spinner("Processing drone imagery and generating feature proposals..."):

            import time
            time.sleep(1.2)

        st.success(
            "AI extraction pipeline completed successfully."
        )

if st.session_state.extraction_run and uploaded_image is not None:

    st.markdown(
        """
        <div class="extraction-status">
            <b>✓ Extraction complete</b><br>
            The imagery has been ingested and the cadastral feature
            extraction pipeline is ready for model-based inference.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # --------------------------------------------------------
    # EXTRACTION RESULTS
    # --------------------------------------------------------

    st.html(
        """
        <div class="section-title">AI Feature Extraction</div>
        <div class="section-subtitle">
            Preliminary feature proposals generated from the uploaded survey imagery.
        </div>
        """
    )

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Parcel Candidates</div>
                <div class="kpi-value">24</div>
                <div class="kpi-note">Preliminary boundary proposals</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r2:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Buildings</div>
                <div class="kpi-value">18</div>
                <div class="kpi-note">Building footprint candidates</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r3:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Road / Pathways</div>
                <div class="kpi-value">7</div>
                <div class="kpi-note">Access corridor candidates</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with r4:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Mean AI Confidence</div>
                <div class="kpi-value">91%</div>
                <div class="kpi-note">Prototype extraction confidence</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("")

    e1, e2 = st.columns(2)

    with e1:

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

    with e2:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">🔍 AI Interpretation</div>
                <div class="card-subtitle">
                    Explainable signals used to prioritize generated features
                </div>

                <div class="xai-box">
                    <div class="xai-title">Why this extraction matters</div>

                    The system identifies visible spatial patterns from
                    drone imagery and proposes cadastral features for
                    downstream GIS validation.

                    <br><br>

                    <b>Primary signals:</b>
                    boundary contrast, geometric continuity,
                    connected regions and spatial separation.

                    <br><br>

                    These outputs are <b>preliminary proposals</b>.
                    Final cadastral acceptance remains with the
                    authorized surveyor.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("")

    st.info(
        "Prototype note: the current dashboard demonstrates the complete "
        "imagery-ingestion and AI-extraction workflow. The next development "
        "step is to replace these prototype inference values with an actual "
        "segmentation/object-detection model."
    )


# ============================================================
# OVERVIEW METRICS
# ============================================================

st.html(
    """
    <div class="section-title">📊 Cadastral Intelligence Overview</div>
    <div class="section-subtitle">
        Current parcel-level quality and confidence summary
    </div>
    """
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Parcels</div>
            <div class="kpi-value">{total_parcels}</div>
            <div class="kpi-note">Current GIS dataset</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Topology Pass</div>
            <div class="kpi-value">{topology_pass}</div>
            <div class="kpi-note">Geometry checks passed</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">High Priority</div>
            <div class="kpi-value">{high_priority}</div>
            <div class="kpi-note">Requires closer review</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Confidence</div>
            <div class="kpi-value">{avg_confidence:.1f}%</div>
            <div class="kpi-note">AI parcel confidence</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# WEB GIS WORKSPACE
# ============================================================

st.html(
    """
    <div class="section-title">🗺️ Web-GIS Workspace</div>
    <div class="section-subtitle">
        Inspect proposed cadastral parcels, topology status and AI confidence.
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
        center_geom.centroid.x
    ]

    m = folium.Map(
        location=center,
        zoom_start=16,
        tiles="CartoDB positron",
        control_scale=True
    )

    try:
        bounds = map_gdf.total_bounds

        m.fit_bounds(
            [
                [bounds[1], bounds[0]],
                [bounds[3], bounds[2]]
            ]
        )
    except Exception:
        pass

    for _, row in map_gdf.iterrows():

        parcel_id = str(row["parcel_id"])
        confidence = float(row["confidence"])
        priority = str(row["priority"])

        decision = st.session_state.parcel_decisions.get(
            parcel_id,
            "PENDING"
        )

        if parcel_id == str(st.session_state.selected_parcel):
            fill_color = "#38BDF8"

        elif decision == "ACCEPTED":
            fill_color = "#22C55E"

        elif decision == "REJECTED":
            fill_color = "#EF4444"

        elif decision == "FIELD VERIFICATION":
            fill_color = "#F59E0B"

        elif confidence < 70:
            fill_color = "#EF4444"

        elif confidence < 85:
            fill_color = "#F59E0B"

        else:
            fill_color = "#22C55E"

        popup_html = f"""
        <div style="font-family:Arial;min-width:190px;">
            <b>Parcel {html.escape(parcel_id)}</b><br><br>
            Confidence: {confidence:.1f}%<br>
            Topology: {html.escape(str(row["topology_status"]))}<br>
            Priority: {html.escape(priority)}<br>
            Decision: {html.escape(decision)}
        </div>
        """

        tooltip = folium.Tooltip(
            f"Parcel {parcel_id} • {confidence:.1f}% confidence"
        )

        feature = {
            "type": "Feature",
            "geometry": row["geometry"].__geo_interface__,
            "properties": {
                "parcel_id": parcel_id
            }
        }

        folium.GeoJson(
            feature,
            style_function=lambda feature, fc=fill_color: {
                "fillColor": fc,
                "color": "#183246",
                "weight": 2,
                "fillOpacity": 0.55
            },
            highlight_function=lambda feature: {
                "weight": 4,
                "fillOpacity": 0.75
            },
            tooltip=tooltip,
            popup=folium.Popup(
                popup_html,
                max_width=300
            )
        ).add_to(m)

    folium.LayerControl().add_to(m)

    # Map legend
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
        <b>Parcel Confidence</b><br>
        <span style="color:#22C55E;">●</span> High<br>
        <span style="color:#F59E0B;">●</span> Medium<br>
        <span style="color:#EF4444;">●</span> Low<br>
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
        returned_objects=["last_active_drawing"]
    )

    # --------------------------------------------------------
    # CLICKABLE PARCEL SELECTION
    # --------------------------------------------------------

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

    st.markdown(
        """
        <div class="card-title">🔎 Parcel Inspector</div>
        <div class="card-subtitle">
            Review AI proposal and make the surveyor decision.
        </div>
        """,
        unsafe_allow_html=True
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
        format_func=lambda x: f"Parcel {x}"
    )

    st.session_state.selected_parcel = selected_id

    selected_rows = gdf[
        gdf["parcel_id"].astype(str) == str(selected_id)
    ]

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

    st.markdown(
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
                <span>AI confidence</span>
                <b>{confidence:.1f}%</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    if "area_sqm" in p.index:
        area_value = float(p["area_sqm"])
    elif "area" in p.index:
        area_value = float(p["area"])
    else:
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

    st.markdown(
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
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # --------------------------------------------------------
    # AI FEATURE SIGNALS
    # --------------------------------------------------------

    compactness = float(
        p["compactness"]
    ) if "compactness" in p.index else 0

    vertex_count = int(
        p["vertex_count"]
    ) if "vertex_count" in p.index else 0

    overlap_area = float(
        p["overlap_area"]
    ) if "overlap_area" in p.index else 0

    area_anomaly = str(
        p["area_anomaly"]
    ) if "area_anomaly" in p.index else "NORMAL"

    st.markdown(
        """
        <div class="card">
            <div class="card-title">🧠 AI Feature Signals</div>
            <div class="card-subtitle">
                Geometry indicators supporting the confidence score
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    s1, s2 = st.columns(2)

    with s1:

        st.markdown(
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
            """,
            unsafe_allow_html=True
        )

    with s2:

        st.markdown(
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
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # XAI
    # --------------------------------------------------------

    reason = html.escape(
        str(p["xai_reason"])
    )

    st.markdown("")

    st.markdown(
        f"""
        <div class="xai-box">
            <div class="xai-title">
                Explainable AI Reason
            </div>

            {reason}

            <br><br>

            <b>Human-in-the-loop:</b>
            AI provides a preliminary cadastral proposal.
            Final validation remains with the authorized surveyor.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # --------------------------------------------------------
    # SURVEYOR DECISION
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="card-title">👷 Surveyor Decision</div>
        """,
        unsafe_allow_html=True
    )

    b1, b2 = st.columns(2)
    b3, b4 = st.columns(2)

    with b1:

        if st.button(
            "✓ Accept",
            use_container_width=True,
            key=f"accept_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "ACCEPTED"

            st.rerun()

    with b2:

        if st.button(
            "✎ Edit Required",
            use_container_width=True,
            key=f"edit_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "EDIT REQUIRED"

            st.rerun()

    with b3:

        if st.button(
            "✕ Reject",
            use_container_width=True,
            key=f"reject_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "REJECTED"

            st.rerun()

    with b4:

        if st.button(
            "⚑ Field GT",
            use_container_width=True,
            key=f"field_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "FIELD VERIFICATION"

            st.rerun()

    current_decision = st.session_state.parcel_decisions.get(
        selected_id,
        "PENDING"
    )

    st.markdown("")

    if current_decision == "ACCEPTED":

        st.success("✓ Parcel accepted by surveyor.")

    elif current_decision == "EDIT REQUIRED":

        st.info("✎ Parcel marked for geometry editing.")

    elif current_decision == "REJECTED":

        st.error("✕ Parcel rejected.")

    elif current_decision == "FIELD VERIFICATION":

        st.warning("⚑ Parcel queued for field verification.")

    else:

        st.info(
            "No surveyor decision recorded yet."
        )


# ============================================================
# GIS QUALITY CONTROL
# ============================================================

st.markdown("")

st.html(
    """
    <div class="section-title">🧪 GIS Quality Control</div>
    <div class="section-subtitle">
        Automated geometry checks before cadastral approval.
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
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Valid Geometry</div>
            <div class="kpi-value">{valid_geometry}/{total_parcels}</div>
            <div class="kpi-note">Geometry validity check</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with q2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Overlap Flags</div>
            <div class="kpi-value">{overlap_count}</div>
            <div class="kpi-note">Potential conflicts</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with q3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Sliver Flags</div>
            <div class="kpi-value">{sliver_count}</div>
            <div class="kpi-note">Very small geometries</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with q4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Field Checks</div>
            <div class="kpi-value">{field_checks}</div>
            <div class="kpi-note">Queued for ground truth</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# FIELD VERIFICATION QUEUE
# ============================================================

st.markdown("")

st.html(
    """
    <div class="section-title">📍 Field Verification Queue</div>
    <div class="section-subtitle">
        Prioritized parcels requiring GNSS / ground-truth verification.
    </div>
    """
)

field_rows = []

for _, row in gdf.iterrows():

    pid = str(row["parcel_id"])

    decision = st.session_state.parcel_decisions.get(
        pid,
        "PENDING"
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
                "Decision": decision
            }
        )

if field_rows:

    st.dataframe(
        field_rows,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No parcels currently require field verification."
    )


# ============================================================
# DECISION SUMMARY
# ============================================================

st.markdown("")

st.html(
    """
    <div class="section-title">📋 Surveyor Decision Summary</div>
    <div class="section-subtitle">
        Current human-in-the-loop review status.
    </div>
    """
)

accepted = sum(
    1 for x in st.session_state.parcel_decisions.values()
    if x == "ACCEPTED"
)

edited = sum(
    1 for x in st.session_state.parcel_decisions.values()
    if x == "EDIT REQUIRED"
)

rejected = sum(
    1 for x in st.session_state.parcel_decisions.values()
    if x == "REJECTED"
)

pending = total_parcels - (
    accepted + edited + rejected +
    sum(
        1
        for x in st.session_state.parcel_decisions.values()
        if x == "FIELD VERIFICATION"
    )
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

st.markdown("")

st.html(
    """
    <div class="section-title">⚙️ AI-CADRE Workflow</div>
    <div class="section-subtitle">
        End-to-end cadastral intelligence pipeline.
    </div>
    """
)

w1, w2, w3, w4, w5, w6 = st.columns(6)

workflow = [
    (
        "1",
        "Data",
        "Drone imagery, orthophotos and GIS inputs"
    ),
    (
        "2",
        "AI Extraction",
        "Identify parcels, buildings and roads"
    ),
    (
        "3",
        "Parcel Proposal",
        "Generate preliminary parcel polygons"
    ),
    (
        "4",
        "Topology",
        "Validate geometry and spatial conflicts"
    ),
    (
        "5",
        "Confidence",
        "Rank proposals using explainable signals"
    ),
    (
        "6",
        "Surveyor",
        "Approve, edit, reject or field-check"
    )
]

for col, item in zip(
    [w1, w2, w3, w4, w5, w6],
    workflow
):

    number, name, desc = item

    with col:

        st.html(
            f"""
            <div class="workflow-card">

                <div class="workflow-number">
                    {number}
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

st.markdown("")

st.html(
    """
    <div class="section-title">📦 GIS Export</div>
    <div class="section-subtitle">
        Download preliminary cadastral outputs for downstream GIS workflows.
    </div>
    """
)

export_gdf = gdf.copy()

export_gdf["surveyor_decision"] = export_gdf[
    "parcel_id"
].astype(str).map(
    lambda x: st.session_state.parcel_decisions.get(
        x,
        "PENDING"
    )
)

geojson_data = export_gdf.to_json()

ex1, ex2 = st.columns(2)

with ex1:

    st.download_button(
        "⬇️ Download Preliminary GeoJSON",
        data=geojson_data,
        file_name="ai_cadre_preliminary_parcels.geojson",
        mime="application/geo+json",
        use_container_width=True
    )

approved_gdf = export_gdf[
    export_gdf["surveyor_decision"] == "ACCEPTED"
]

with ex2:

    if len(approved_gdf) > 0:

        approved_geojson = approved_gdf.to_json()

        st.download_button(
            "⬇️ Download Approved Parcels",
            data=approved_geojson,
            file_name="ai_cadre_approved_parcels.geojson",
            mime="application/geo+json",
            use_container_width=True
        )

    else:

        st.button(
            "⬇️ Approved Parcels",
            disabled=True,
            use_container_width=True
        )


# ============================================================
# HUMAN-IN-THE-LOOP NOTE
# ============================================================

st.markdown("")

st.html(
    """
    <div class="xai-box">

        <div class="xai-title">
            Human-in-the-loop governance
        </div>

        AI-CADRE is designed as a <b>decision-support system</b>,
        not an autonomous cadastral authority.

        AI-generated boundaries and extracted features are preliminary.
        Automated topology checks identify potential inconsistencies,
        while confidence scores help surveyors prioritize their review.

        Final cadastral approval remains with the authorized
        surveying / land-record authority.

    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">
        AI-CADRE • SIH26012 • AI-Based Automated Urban Parcel Mapping
        & Cadastral Feature Extraction System
        <br>
        Prototype for Smart India Hackathon 2026
    </div>
    """
)
