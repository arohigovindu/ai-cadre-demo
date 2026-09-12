import html
import json
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


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #F5F7FA;
        color: #0F172A;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* ---------- NAVBAR ---------- */

    .top-nav {
        background: #07111F;
        border-radius: 16px;
        padding: 15px 24px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
        border: 1px solid #172235;
    }

    .nav-brand {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.4px;
    }

    .nav-subtitle {
        color: #94A3B8;
        font-size: 12px;
        margin-top: 2px;
    }

    .nav-badge {
        background: #0F2238;
        border: 1px solid #1E3A5F;
        color: #7DD3FC;
        padding: 7px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
    }

    /* ---------- HERO ---------- */

    .hero {
        background:
            linear-gradient(
                135deg,
                #07111F 0%,
                #0B1E33 60%,
                #0F3048 100%
            );
        border-radius: 20px;
        padding: 34px 38px;
        margin-bottom: 24px;
        color: white;
        border: 1px solid #17324D;
    }

    .hero-eyebrow {
        color: #7DD3FC;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: -1.3px;
        line-height: 1.1;
        margin-bottom: 10px;
    }

    .hero-text {
        max-width: 820px;
        color: #CBD5E1;
        font-size: 14px;
        line-height: 1.65;
    }

    .workflow-line {
        margin-top: 22px;
        padding: 12px 16px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        color: #E2E8F0;
        font-size: 12px;
        font-weight: 600;
    }

    /* ---------- SECTION HEADINGS ---------- */

    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
        margin-top: 24px;
        margin-bottom: 4px;
    }

    .section-caption {
        color: #64748B;
        font-size: 12px;
        margin-bottom: 16px;
    }

    /* ---------- KPI CARDS ---------- */

    .kpi-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 15px;
        padding: 19px;
        min-height: 120px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }

    .kpi-label {
        color: #64748B;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.4px;
    }

    .kpi-value {
        color: #0F172A;
        font-size: 29px;
        font-weight: 800;
        margin-top: 7px;
    }

    .kpi-note {
        color: #94A3B8;
        font-size: 11px;
        margin-top: 4px;
    }

    /* ---------- CARDS ---------- */

    .panel-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }

    .info-row {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px;
        margin-top: 10px;
    }

    .info-label {
        color: #64748B;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.7px;
    }

    .info-value {
        color: #0F172A;
        font-size: 14px;
        font-weight: 700;
        margin-top: 5px;
    }

    /* ---------- STATUS BADGES ---------- */

    .status-pass {
        display: inline-block;
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        border-radius: 20px;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: 800;
    }

    .status-fail {
        display: inline-block;
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
        border-radius: 20px;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: 800;
    }

    .status-warning {
        display: inline-block;
        background: #FFF7ED;
        color: #C2410C;
        border: 1px solid #FED7AA;
        border-radius: 20px;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: 800;
    }

    .decision-pending {
        color: #64748B;
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        padding: 5px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    .decision-accepted {
        color: #047857;
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        padding: 5px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    .decision-edit {
        color: #0369A1;
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        padding: 5px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    .decision-rejected {
        color: #B91C1C;
        background: #FEF2F2;
        border: 1px solid #FECACA;
        padding: 5px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    .decision-field {
        color: #92400E;
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        padding: 5px 9px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    /* ---------- XAI ---------- */

    .xai-box {
        background: #F0F9FF;
        border: 1px solid #BAE6FD;
        border-radius: 13px;
        padding: 15px;
        margin-top: 12px;
    }

    /* ---------- MAP LEGEND ---------- */

    .map-legend {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 13px;
        font-size: 10px;
        color: #475569;
        margin-top: 10px;
    }

    .legend-dot {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        margin-right: 5px;
    }

    /* ---------- FEATURE SIGNAL ---------- */

    .signal-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 11px;
        padding: 12px;
        margin-bottom: 8px;
    }

    .signal-title {
        font-size: 10px;
        font-weight: 800;
        color: #64748B;
        letter-spacing: 0.4px;
    }

    .signal-value {
        font-size: 16px;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }

    /* ---------- WORKFLOW ---------- */

    .workflow-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 17px;
        min-height: 145px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.03);
    }

    .workflow-number {
        color: #0284C7;
        font-size: 11px;
        font-weight: 800;
    }

    .workflow-name {
        color: #0F172A;
        font-size: 15px;
        font-weight: 800;
        margin-top: 7px;
    }

    .workflow-description {
        color: #64748B;
        font-size: 11px;
        line-height: 1.5;
        margin-top: 6px;
    }

    /* ---------- FOOTER ---------- */

    .footer {
        margin-top: 40px;
        padding: 20px;
        text-align: center;
        color: #94A3B8;
        font-size: 11px;
        border-top: 1px solid #E2E8F0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD + ANALYZE PARCELS
# ============================================================

gdf = analyze_parcels("sample_parcels.geojson")

parcel_ids = gdf["parcel_id"].tolist()

if not parcel_ids:
    st.error("No parcel features were found in sample_parcels.geojson.")
    st.stop()

if (
    st.session_state.selected_parcel is None
    or st.session_state.selected_parcel not in parcel_ids
):
    st.session_state.selected_parcel = parcel_ids[0]


# ============================================================
# NAVBAR
# ============================================================

st.html(
    """
    <div class="top-nav">
        <div>
            <div class="nav-brand">🛰️ AI-CADRE</div>
            <div class="nav-subtitle">
                Cadastral AI Co-Pilot • Urban Parcel Intelligence
            </div>
        </div>
        <div class="nav-badge">
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
        <div class="hero-eyebrow">
            SIH26012 • URBAN CADASTRAL MAPPING
        </div>

        <div class="hero-title">
            AI-powered cadastral intelligence
        </div>

        <div class="hero-text">
            Transform geospatial data into preliminary, validated and
            GIS-ready parcel information — while keeping the authorized
            surveyor in control of every final decision.
        </div>

        <div class="workflow-line">
            AI Proposes&nbsp;&nbsp; → &nbsp;&nbsp;
            GIS Validates&nbsp;&nbsp; → &nbsp;&nbsp;
            Confidence Prioritizes&nbsp;&nbsp; → &nbsp;&nbsp;
            Surveyor Approves
        </div>
    </div>
    """
)


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================

total_parcels = len(gdf)

pass_count = int(
    gdf["topology_status"]
    .astype(str)
    .str.startswith("PASS")
    .sum()
)

high_priority = int(
    gdf["priority"]
    .astype(str)
    .str.startswith("HIGH")
    .sum()
)

avg_confidence = float(gdf["confidence"].mean())

accepted_count = sum(
    value == "ACCEPTED"
    for value in st.session_state.parcel_decisions.values()
)

field_count = sum(
    value == "FIELD VERIFICATION"
    for value in st.session_state.parcel_decisions.values()
)

pending_count = total_parcels - len(st.session_state.parcel_decisions)


st.html(
    """
    <div class="section-title">
        Survey Overview
    </div>
    <div class="section-caption">
        Current automated parcel-analysis status
    </div>
    """
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">TOTAL PARCELS</div>
            <div class="kpi-value">{total_parcels}</div>
            <div class="kpi-note">Detected parcel candidates</div>
        </div>
        """
    )

with k2:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">TOPOLOGY PASS</div>
            <div class="kpi-value">{pass_count}/{total_parcels}</div>
            <div class="kpi-note">Geometry validation</div>
        </div>
        """
    )

with k3:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">HIGH PRIORITY</div>
            <div class="kpi-value">{high_priority}</div>
            <div class="kpi-note">Requires additional review</div>
        </div>
        """
    )

with k4:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">AVG. CONFIDENCE</div>
            <div class="kpi-value">{avg_confidence:.0f}%</div>
            <div class="kpi-note">AI-assisted confidence score</div>
        </div>
        """
    )


# ============================================================
# MAPPING WORKSPACE
# ============================================================

st.html(
    """
    <div class="section-title">
        Cadastral Mapping Workspace
    </div>
    <div class="section-caption">
        Click a parcel directly on the GIS layer or select it from the inspector.
    </div>
    """
)

map_col, inspector_col = st.columns([1.65, 1])


# ============================================================
# MAP
# ============================================================

with map_col:

    map_gdf = gdf.copy()

    # Folium requires latitude/longitude coordinates.
    if map_gdf.crs is not None:
        try:
            map_gdf = map_gdf.to_crs(epsg=4326)
        except Exception:
            pass

    # Calculate map centre.
    try:
        union_geom = map_gdf.geometry.union_all()
    except Exception:
        union_geom = map_gdf.geometry.unary_union

    center = union_geom.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=15,
        tiles="CartoDB positron",
        control_scale=True
    )

    # Fit map to parcel bounds.
    try:
        bounds = map_gdf.total_bounds
        minx, miny, maxx, maxy = bounds

        if all(
            value is not None
            for value in [minx, miny, maxx, maxy]
        ):
            m.fit_bounds(
                [[miny, minx], [maxy, maxx]]
            )
    except Exception:
        pass

    # --------------------------------------------------------
    # ADD PARCELS
    # --------------------------------------------------------

    for _, row in map_gdf.iterrows():

        parcel_id = str(row["parcel_id"])
        confidence = float(row["confidence"])

        decision = st.session_state.parcel_decisions.get(
            parcel_id,
            "PENDING REVIEW"
        )

        topology = str(row["topology_status"])

        # Selected parcel gets blue highlight.
        if parcel_id == st.session_state.selected_parcel:
            fill_color = "#38BDF8"
            border_color = "#0284C7"
            weight = 5

        elif decision == "ACCEPTED":
            fill_color = "#10B981"
            border_color = "#047857"
            weight = 3

        elif decision == "REJECTED":
            fill_color = "#EF4444"
            border_color = "#B91C1C"
            weight = 3

        elif decision == "FIELD VERIFICATION":
            fill_color = "#F59E0B"
            border_color = "#B45309"
            weight = 3

        elif confidence < 70:
            fill_color = "#EF4444"
            border_color = "#DC2626"
            weight = 3

        elif confidence < 85:
            fill_color = "#F59E0B"
            border_color = "#D97706"
            weight = 3

        else:
            fill_color = "#22C55E"
            border_color = "#15803D"
            weight = 3

        popup_html = f"""
        <div style="font-family:Arial; min-width:180px;">
            <b style="font-size:14px;">Parcel {html.escape(parcel_id)}</b>
            <hr style="margin:7px 0;">
            <b>Confidence:</b> {confidence:.0f}%<br>
            <b>Topology:</b> {html.escape(topology)}<br>
            <b>Priority:</b> {html.escape(str(row["priority"]))}<br>
            <b>Decision:</b> {html.escape(decision)}
        </div>
        """

        tooltip_text = (
            f"Parcel {parcel_id} | "
            f"Confidence {confidence:.0f}% | "
            f"{topology}"
        )

        folium.GeoJson(
            row["geometry"],
            name=parcel_id,
            style_function=lambda feature,
            fill_color=fill_color,
            border_color=border_color,
            weight=weight: {
                "fillColor": fill_color,
                "color": border_color,
                "weight": weight,
                "fillOpacity": 0.55
            },
            highlight_function=lambda feature: {
                "weight": 6,
                "color": "#0EA5E9",
                "fillOpacity": 0.70
            },
            tooltip=tooltip_text,
            popup=folium.Popup(
                popup_html,
                max_width=280
            ),
            zoom_on_click=False
        ).add_to(m)

    folium.LayerControl().add_to(m)

    map_result = st_folium(
        m,
        use_container_width=True,
        height=600,
        returned_objects=["last_active_drawing"]
    )

    # --------------------------------------------------------
    # DETECT MAP CLICK
    # --------------------------------------------------------

    clicked = map_result.get("last_active_drawing")

    if clicked:
        properties = clicked.get("properties", {})

        clicked_id = properties.get("parcel_id")

        if clicked_id in parcel_ids:
            if st.session_state.selected_parcel != clicked_id:
                st.session_state.selected_parcel = clicked_id
                st.rerun()

    st.html(
        """
        <div class="map-legend">
            <b>Map Legend</b><br><br>

            <span class="legend-dot"
                  style="background:#22C55E;"></span>
            High confidence<br>

            <span class="legend-dot"
                  style="background:#F59E0B;"></span>
            Medium confidence<br>

            <span class="legend-dot"
                  style="background:#EF4444;"></span>
            Low confidence / review<br>

            <span class="legend-dot"
                  style="background:#38BDF8;"></span>
            Selected parcel
        </div>
        """
    )


# ============================================================
# PARCEL INSPECTOR
# ============================================================

with inspector_col:

    st.html(
        """
        <div class="panel-card">
        """
    )

    selected_id = st.selectbox(
        "Select Parcel",
        parcel_ids,
        format_func=lambda x: f"Parcel {x}",
        key="selected_parcel"
    )

    selected_rows = gdf[
        gdf["parcel_id"] == selected_id
    ]

    if selected_rows.empty:
        st.warning("Parcel not found.")
        st.stop()

    p = selected_rows.iloc[0]

    confidence = float(p["confidence"])

    if confidence >= 85:
        confidence_status = "HIGH CONFIDENCE"
    elif confidence >= 70:
        confidence_status = "MEDIUM CONFIDENCE"
    else:
        confidence_status = "LOW CONFIDENCE"

    # --------------------------------------------------------
    # CONFIDENCE CARD
    # --------------------------------------------------------

    st.html(
        f"""
        <div style="
            background:#F8FAFC;
            border:1px solid #E2E8F0;
            border-radius:14px;
            padding:18px;
            margin-top:12px;
        ">

            <div style="
                color:#64748B;
                font-size:11px;
                font-weight:700;
                letter-spacing:0.5px;
            ">
                AI CONFIDENCE SCORE
            </div>

            <div style="
                font-size:34px;
                font-weight:800;
                color:#0F172A;
                margin-top:4px;
            ">
                {confidence:.0f}%
            </div>

            <div style="
                color:#64748B;
                font-size:11px;
            ">
                {confidence_status}
            </div>

            <div style="
                background:#E2E8F0;
                height:7px;
                border-radius:10px;
                margin-top:12px;
                overflow:hidden;
            ">
                <div style="
                    background:#38BDF8;
                    width:{confidence}%;
                    height:100%;
                    border-radius:10px;
                "></div>
            </div>
        </div>
        """
    )

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    area_value = float(p["area_sqm"])

   area_value = float(
    p.get("area_sqm", p.get("area", 0))
)

st.html(
    f"""
    <div class="info-row">
        <div class="info-label">PARCEL IDENTIFIER</div>
        <div class="info-value">
            {html.escape(str(p["parcel_id"]))}
        </div>
    </div>

    <div class="info-row">
        <div class="info-label">GEOMETRY AREA</div>
        <div class="info-value">
            {area_value:.2f} sq. units
        </div>
    </div>

    <div class="info-row">
        <div class="info-label">PRIORITY</div>
        <div class="info-value">
            {html.escape(str(p["priority"]))}
        </div>
    </div>
    """
)

    # --------------------------------------------------------
    # TOPOLOGY
    # --------------------------------------------------------

    topology = str(p["topology_status"])

    if topology.startswith("PASS"):

        topology_badge = """
        <span class="status-pass">
            ✓ TOPOLOGY VALID
        </span>
        """

        topology_description = """
        No significant geometry conflicts detected.
        """

    else:

        topology_badge = """
        <span class="status-fail">
            ⚠ REVIEW REQUIRED
        </span>
        """

        topology_description = """
        Geometry requires surveyor review before approval.
        """

    st.html(
        f"""
        <div class="info-row">

            <div class="info-label">
                TOPOLOGY VALIDATION
            </div>

            <div style="margin-top:7px;">
                {topology_badge}
            </div>

            <div style="
                color:#64748B;
                font-size:12px;
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

    st.markdown("### AI Feature Signals")

    signal1, signal2 = st.columns(2)

    with signal1:

        compactness = float(p["compactness"])

        st.html(
            f"""
            <div class="signal-card">
                <div class="signal-title">
                    SHAPE REGULARITY
                </div>
                <div class="signal-value">
                    {compactness:.2f}
                </div>
            </div>
            """
        )

    with signal2:

        vertices = int(p["vertex_count"])

        st.html(
            f"""
            <div class="signal-card">
                <div class="signal-title">
                    BOUNDARY VERTICES
                </div>
                <div class="signal-value">
                    {vertices}
                </div>
            </div>
            """
        )

    signal3, signal4 = st.columns(2)

    with signal3:

        overlap = float(p["overlap_area"])

        st.html(
            f"""
            <div class="signal-card">
                <div class="signal-title">
                    OVERLAP AREA
                </div>
                <div class="signal-value">
                    {overlap:.3f}
                </div>
            </div>
            """
        )

    with signal4:

        anomaly = str(p["area_anomaly"])

        st.html(
            f"""
            <div class="signal-card">
                <div class="signal-title">
                    AREA SIGNAL
                </div>
                <div class="signal-value">
                    {html.escape(anomaly)}
                </div>
            </div>
            """
        )

    # --------------------------------------------------------
    # EXPLAINABLE AI
    # --------------------------------------------------------

    xai_reason = html.escape(str(p["xai_reason"]))

    st.html(
        f"""
        <div class="xai-box">

            <div style="
                font-size:12px;
                color:#0369A1;
                font-weight:700;
                margin-bottom:7px;
            ">
                💡 EXPLAINABLE AI
            </div>

            <div style="
                font-size:13px;
                color:#0F172A;
                line-height:1.5;
            ">
                {xai_reason}
            </div>

            <div style="
                font-size:11px;
                color:#64748B;
                margin-top:10px;
            ">
                AI recommendation is advisory.
                Final validation remains with the authorized surveyor.
            </div>

        </div>
        """
    )

    # --------------------------------------------------------
    # SURVEYOR DECISION
    # --------------------------------------------------------

    st.markdown("### Surveyor Decision")

    b1, b2 = st.columns(2)

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
            "✎ Edit",
            use_container_width=True,
            key=f"edit_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "EDIT REQUIRED"

            st.rerun()

    b3, b4 = st.columns(2)

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
            "📍 Field GT",
            use_container_width=True,
            key=f"field_{selected_id}"
        ):

            st.session_state.parcel_decisions[
                selected_id
            ] = "FIELD VERIFICATION"

            st.rerun()

    decision = st.session_state.parcel_decisions.get(
        selected_id,
        "PENDING REVIEW"
    )

    if decision == "ACCEPTED":

        st.success(
            f"✓ {selected_id} accepted by surveyor."
        )

    elif decision == "EDIT REQUIRED":

        st.info(
            f"✎ {selected_id} requires boundary editing."
        )

    elif decision == "REJECTED":

        st.error(
            f"✕ {selected_id} rejected."
        )

    elif decision == "FIELD VERIFICATION":

        st.warning(
            f"📍 {selected_id} added to field verification."
        )

    else:

        st.info(
            f"⏳ {selected_id} is awaiting surveyor decision."
        )

    st.html("</div>")


# ============================================================
# GIS QUALITY CONTROL
# ============================================================

st.html(
    """
    <div class="section-title">
        GIS Quality Control
    </div>
    <div class="section-caption">
        Automated checks performed before surveyor approval
    </div>
    """
)

invalid_count = int(
    (~gdf.geometry.is_valid).sum()
)

overlap_count = int(
    gdf["topology_status"]
    .astype(str)
    .str.contains("OVERLAP")
    .sum()
)

sliver_count = int(
    gdf["topology_status"]
    .astype(str)
    .str.contains("SLIVER")
    .sum()
)

valid_count = total_parcels - invalid_count

q1, q2, q3, q4 = st.columns(4)

with q1:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">VALID GEOMETRIES</div>
            <div class="kpi-value">{valid_count}</div>
            <div class="kpi-note">Closed and valid polygons</div>
        </div>
        """
    )

with q2:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">OVERLAPS</div>
            <div class="kpi-value">{overlap_count}</div>
            <div class="kpi-note">Potential boundary conflicts</div>
        </div>
        """
    )

with q3:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">SLIVERS</div>
            <div class="kpi-value">{sliver_count}</div>
            <div class="kpi-note">Small geometry anomalies</div>
        </div>
        """
    )

with q4:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">FIELD CHECKS</div>
            <div class="kpi-value">{field_count}</div>
            <div class="kpi-note">Queued by surveyor</div>
        </div>
        """
    )


# ============================================================
# FIELD VERIFICATION QUEUE
# ============================================================

st.html(
    """
    <div class="section-title">
        Field Verification Queue
    </div>
    <div class="section-caption">
        Parcels requiring GNSS / CORS-assisted ground verification
    </div>
    """
)

queue_rows = []

for _, row in gdf.iterrows():

    pid = row["parcel_id"]

    decision = st.session_state.parcel_decisions.get(
        pid,
        "PENDING REVIEW"
    )

    if (
        str(row["priority"]).startswith("HIGH")
        or decision == "FIELD VERIFICATION"
    ):

        queue_rows.append(
            {
                "Parcel ID": pid,
                "Confidence": f'{float(row["confidence"]):.0f}%',
                "Topology": row["topology_status"],
                "Priority": row["priority"],
                "Decision": decision
            }
        )

if queue_rows:

    st.dataframe(
        queue_rows,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No parcels are currently waiting for field verification."
    )


# ============================================================
# DECISION SUMMARY
# ============================================================

st.html(
    """
    <div class="section-title">
        Surveyor Decision Summary
    </div>
    <div class="section-caption">
        Human-in-the-loop review status for the current session
    </div>
    """
)

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.metric(
        "Accepted",
        accepted_count
    )

with d2:
    edit_count = sum(
        value == "EDIT REQUIRED"
        for value in st.session_state.parcel_decisions.values()
    )

    st.metric(
        "Edit Required",
        edit_count
    )

with d3:
    rejected_count = sum(
        value == "REJECTED"
        for value in st.session_state.parcel_decisions.values()
    )

    st.metric(
        "Rejected",
        rejected_count
    )

with d4:
    st.metric(
        "Pending",
        pending_count
    )


# ============================================================
# WORKFLOW
# ============================================================

st.html(
    """
    <div class="section-title">
        AI-CADRE Workflow
    </div>
    <div class="section-caption">
        End-to-end cadastral processing pipeline
    </div>
    """
)

workflow_cols = st.columns(6)

workflow = [
    (
        "01",
        "Data",
        "Drone imagery, orthorectified data, DSM/DTM and existing GIS layers."
    ),
    (
        "02",
        "AI Extraction",
        "Identify parcel boundaries and relevant cadastral features."
    ),
    (
        "03",
        "Parcel Proposal",
        "Generate preliminary parcel polygons from extracted features."
    ),
    (
        "04",
        "Topology",
        "Detect overlaps, invalid geometry and sliver polygons."
    ),
    (
        "05",
        "Confidence",
        "Rank parcel proposals using geometry and validation signals."
    ),
    (
        "06",
        "Surveyor",
        "Authorized surveyor reviews, edits, accepts or sends to field GT."
    )
]

for col, item in zip(workflow_cols, workflow):

    number, name, description = item

    with col:

        st.html(
            f"""
            <div class="workflow-card">

                <div class="workflow-number">
                    {number}
                </div>

                <div class="workflow-name">
                    {name}
                </div>

                <div class="workflow-description">
                    {description}
                </div>

            </div>
            """
        )


# ============================================================
# EXPORT SECTION
# ============================================================

st.html(
    """
    <div class="section-title">
        GIS Export
    </div>
    <div class="section-caption">
        Download preliminary cadastral outputs for downstream GIS workflows
    </div>
    """
)

export_col1, export_col2 = st.columns(2)

# ------------------------------------------------------------
# ALL PARCELS EXPORT
# ------------------------------------------------------------

with export_col1:

    export_all = gdf.copy()

    export_all["surveyor_decision"] = [
        st.session_state.parcel_decisions.get(
            pid,
            "PENDING REVIEW"
        )
        for pid in export_all["parcel_id"]
    ]

    st.download_button(
        label="📥 Export Preliminary GeoJSON",
        data=export_all.to_json(),
        file_name="ai_cadre_preliminary_cadastre.geojson",
        mime="application/geo+json",
        use_container_width=True
    )

# ------------------------------------------------------------
# APPROVED PARCELS EXPORT
# ------------------------------------------------------------

with export_col2:

    approved_ids = [
        pid
        for pid, decision
        in st.session_state.parcel_decisions.items()
        if decision == "ACCEPTED"
    ]

    approved = gdf[
        gdf["parcel_id"].isin(approved_ids)
    ].copy()

    approved["surveyor_decision"] = "ACCEPTED"

    st.download_button(
        label="✅ Export Approved Parcels",
        data=approved.to_json(),
        file_name="ai_cadre_approved_cadastre.geojson",
        mime="application/geo+json",
        use_container_width=True,
        disabled=approved.empty
    )


# ============================================================
# HUMAN-IN-THE-LOOP NOTE
# ============================================================

st.html(
    """
    <div style="
        margin-top:25px;
        background:#F8FAFC;
        border:1px solid #CBD5E1;
        border-radius:14px;
        padding:18px;
    ">

        <div style="
            font-size:12px;
            font-weight:800;
            color:#334155;
            margin-bottom:6px;
        ">
            HUMAN-IN-THE-LOOP PRINCIPLE
        </div>

        <div style="
            font-size:12px;
            line-height:1.6;
            color:#64748B;
        ">
            AI-CADRE generates preliminary cadastral intelligence and
            prioritizes potential issues. It does not replace the
            authorized surveyor. Final cadastral validation remains
            under human supervision.
        </div>

    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">
        🛰️ AI-CADRE • AI-Based Automated Urban Parcel Mapping
        & Cadastral Feature Extraction System
        <br>
        SIH26012 • Robotics & Drones • Software Prototype
    </div>
    """
)
