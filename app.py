import streamlit as st
import folium
from streamlit_folium import st_folium
from topology_engine import analyze_parcels


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI-CADRE | Cadastral AI Co-Pilot",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #F6F8FB;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }


    /* ---------- NAVBAR ---------- */

    .navbar {
        background: #0B1220;
        padding: 16px 28px;
        border-radius: 14px;
        margin-bottom: 28px;
    }

    .brand {
        color: white;
        font-size: 23px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .brand span {
        color: #38BDF8;
    }

    .nav-subtitle {
        color: #94A3B8;
        font-size: 13px;
        margin-top: 2px;
    }


    /* ---------- HERO ---------- */

    .hero {
        background: linear-gradient(
            135deg,
            #0B1220 0%,
            #162A46 100%
        );

        padding: 48px 50px;
        border-radius: 22px;
        margin-bottom: 25px;
        color: white;
    }

    .hero-tag {
        display: inline-block;
        background: rgba(56,189,248,0.12);
        color: #7DD3FC;
        border: 1px solid rgba(125,211,252,0.25);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin-bottom: 16px;
    }

    .hero-title {
        font-size: 43px;
        font-weight: 750;
        line-height: 1.12;
        margin-bottom: 12px;
        color: white;
    }

    .hero-description {
        font-size: 17px;
        line-height: 1.6;
        color: #CBD5E1;
        max-width: 720px;
        margin-bottom: 18px;
    }

    .hero-flow {
        font-size: 13px;
        color: #94A3B8;
        margin-top: 18px;
    }


    /* ---------- SECTION TITLES ---------- */

    .section-title {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        margin-top: 35px;
        margin-bottom: 5px;
    }

    .section-subtitle {
        color: #64748B;
        font-size: 14px;
        margin-bottom: 18px;
    }


    /* ---------- KPI CARDS ---------- */

    .metric-card {
        background: white;
        padding: 22px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        min-height: 115px;
    }

    .metric-label {
        color: #64748B;
        font-size: 13px;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #0F172A;
        font-size: 30px;
        font-weight: 750;
    }

    .metric-description {
        color: #94A3B8;
        font-size: 12px;
        margin-top: 4px;
    }


    /* ---------- WHITE CARDS ---------- */

    .card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 15px;
    }

    .card-title {
        color: #0F172A;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .card-subtitle {
        color: #64748B;
        font-size: 13px;
        margin-bottom: 18px;
    }


    /* ---------- INSPECTOR ---------- */

    .parcel-id {
        font-size: 28px;
        font-weight: 750;
        color: #0F172A;
        margin-bottom: 15px;
    }

    .info-row {
        padding: 10px 0;
        border-bottom: 1px solid #E2E8F0;
    }

    .info-label {
        color: #64748B;
        font-size: 12px;
    }

    .info-value {
        color: #0F172A;
        font-size: 15px;
        font-weight: 600;
    }


    /* ---------- STATUS ---------- */

    .status-pass {
        display: inline-block;
        background: #DCFCE7;
        color: #166534;
        padding: 6px 11px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-fail {
        display: inline-block;
        background: #FEE2E2;
        color: #991B1B;
        padding: 6px 11px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }


    /* ---------- WORKFLOW ---------- */

    .workflow-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        height: 150px;
    }

    .workflow-number {
        color: #38BDF8;
        font-size: 12px;
        font-weight: 700;
    }

    .workflow-icon {
        font-size: 27px;
        margin: 8px 0;
    }

    .workflow-name {
        color: #0F172A;
        font-size: 14px;
        font-weight: 700;
    }

    .workflow-desc {
        color: #64748B;
        font-size: 11px;
        margin-top: 5px;
    }


    /* ---------- XAI ---------- */

    .xai-box {
        background: #F0F9FF;
        border-left: 4px solid #38BDF8;
        padding: 15px;
        border-radius: 8px;
        color: #0F172A;
        font-size: 13px;
        margin-top: 15px;
    }


    /* ---------- FOOTER ---------- */

    .footer {
        text-align: center;
        color: #94A3B8;
        font-size: 12px;
        padding-top: 40px;
        border-top: 1px solid #E2E8F0;
        margin-top: 50px;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATA
# =========================================================

gdf = analyze_parcels("sample_parcels.geojson")


# =========================================================
# NAVBAR
# =========================================================

st.markdown("""
<div class="navbar">

    <div class="brand">
        🛰️ AI-<span>CADRE</span>
    </div>

    <div class="nav-subtitle">
        Cadastral AI Co-Pilot • SIH26012
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# HERO
# =========================================================

st.markdown("""
<div class="hero">

    <div class="hero-tag">
        SIH26012 • URBAN CADASTRAL MAPPING
    </div>

    <div class="hero-title">
        AI-powered cadastral intelligence
    </div>

    <div class="hero-description">
        Transform geospatial imagery into preliminary,
        validated and GIS-ready parcel information —
        while keeping the surveyor in control.
    </div>

    <div class="hero-flow">
        AI Proposes &nbsp; → &nbsp;
        GIS Validates &nbsp; → &nbsp;
        Confidence Prioritizes &nbsp; → &nbsp;
        Surveyor Approves
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# KPI CALCULATIONS
# =========================================================

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

avg_confidence = round(
    gdf["confidence"].mean(),
    1
)


# =========================================================
# KPI CARDS
# =========================================================

st.markdown(
    '<div class="section-title">Survey Overview</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Current cadastral analysis from the loaded survey dataset.'
    '</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">PARCELS ANALYZED</div>
        <div class="metric-value">{total_parcels}</div>
        <div class="metric-description">Detected parcel records</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TOPOLOGY PASS</div>
        <div class="metric-value">{pass_count}</div>
        <div class="metric-description">Valid preliminary geometries</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">HIGH PRIORITY</div>
        <div class="metric-value">{high_priority}</div>
        <div class="metric-description">Require field attention</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">AVG. CONFIDENCE</div>
        <div class="metric-value">{avg_confidence}%</div>
        <div class="metric-description">Across analyzed parcels</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# MAP + INSPECTOR
# =========================================================

st.markdown(
    '<div class="section-title">Cadastral Mapping Workspace</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Inspect parcel boundaries, confidence and topology results in one workspace.'
    '</div>',
    unsafe_allow_html=True
)

map_col, inspector_col = st.columns([2.2, 1])


# =========================================================
# MAP
# =========================================================

with map_col:

    st.markdown("""
    <div class="card">
        <div class="card-title">🗺️ Web-GIS Map</div>
        <div class="card-subtitle">
            Preliminary parcel boundaries and topology status
        </div>
    """, unsafe_allow_html=True)

    # Convert to WGS84 for web map
    map_gdf = gdf.copy()

    if map_gdf.crs is not None:
        try:
            map_gdf = map_gdf.to_crs(epsg=4326)
        except Exception:
            pass

    # Find map center
    if not map_gdf.empty:

        center = map_gdf.geometry.unary_union.centroid

        m = folium.Map(
            location=[center.y, center.x],
            zoom_start=16,
            tiles="CartoDB positron"
        )

        # Fit map to parcels
        bounds = map_gdf.total_bounds

        m.fit_bounds([
            [bounds[1], bounds[0]],
            [bounds[3], bounds[2]]
        ])

    else:

        m = folium.Map(
            location=[10.0, 10.0],
            zoom_start=14,
            tiles="CartoDB positron"
        )


    # Add parcel polygons
    for _, row in map_gdf.iterrows():

        color = row["color"]

        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature, color=color: {
                "fillColor": color,
                "color": color,
                "weight": 3,
                "fillOpacity": 0.35
            },
            tooltip=folium.Tooltip(
                f"""
                <b>Parcel:</b> {row['parcel_id']}<br>
                <b>Confidence:</b> {row['confidence']}%<br>
                <b>Topology:</b> {row['topology_status']}<br>
                <b>Priority:</b> {row['priority']}
                """
            )
        ).add_to(m)


    st_folium(
        m,
        use_container_width=True,
        height=600
    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PARCEL INSPECTOR
# =========================================================

with inspector_col:

    st.markdown("""
    <div class="card">

        <div class="card-title">
            🔎 Parcel Inspector
        </div>

        <div class="card-subtitle">
            Review AI-generated parcel intelligence
        </div>

    """, unsafe_allow_html=True)

    selected_id = st.selectbox(
        "Select Parcel",
        gdf["parcel_id"].tolist()
    )

    selected_rows = gdf[
        gdf["parcel_id"] == selected_id
    ]

    p = selected_rows.iloc[0]


    st.markdown(
        f'<div class="parcel-id">{p["parcel_id"]}</div>',
        unsafe_allow_html=True
    )


    # Confidence
    st.metric(
        "Confidence Score",
        f'{p["confidence"]:.0f}%'
    )


    # Priority
    st.markdown(
        f"""
        <div class="info-row">
            <div class="info-label">VERIFICATION PRIORITY</div>
            <div class="info-value">{p["priority"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Area
    st.markdown(
        f"""
        <div class="info-row">
            <div class="info-label">PARCEL AREA</div>
            <div class="info-value">{p["area_sqm"]} sq. units</div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Topology
    topology = str(p["topology_status"])

    if topology.startswith("PASS"):

        status_html = (
            '<span class="status-pass">✓ '
            + topology +
            '</span>'
        )

    else:

        status_html = (
            '<span class="status-fail">⚠ '
            + topology +
            '</span>'
        )


    st.markdown(
        f"""
        <div class="info-row">
            <div class="info-label">TOPOLOGY STATUS</div>
            <div style="margin-top:5px;">
                {status_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # XAI explanation
    st.markdown(
        f"""
        <div class="xai-box">
            <b>💡 Why is this parcel flagged?</b><br><br>
            {p["xai_reason"]}
        </div>
        """,
        unsafe_allow_html=True
    )


    st.markdown("<br>", unsafe_allow_html=True)


    # Actions
    st.markdown("**Surveyor Decision**")

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "✓ Accept",
            use_container_width=True
        ):
            st.success(
                f"{selected_id} accepted as a preliminary feature."
            )

    with b2:

        if st.button(
            "✎ Edit",
            use_container_width=True
        ):
            st.info(
                f"{selected_id} marked for editing."
            )


    b3, b4 = st.columns(2)

    with b3:

        if st.button(
            "✕ Reject",
            use_container_width=True
        ):
            st.warning(
                f"{selected_id} rejected."
            )

    with b4:

        if st.button(
            "📍 Field GT",
            use_container_width=True
        ):
            st.warning(
                f"{selected_id} added to field verification."
            )


    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TOPOLOGY QUALITY CONTROL
# =========================================================

st.markdown(
    '<div class="section-title">GIS Quality Control</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Automated geometry checks help identify parcels that need human attention.'
    '</div>',
    unsafe_allow_html=True
)

q1, q2, q3, q4 = st.columns(4)

invalid_count = int(
    gdf["topology_status"]
    .astype(str)
    .str.contains("INVALID")
    .sum()
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

with q1:
    st.metric(
        "Valid Geometry",
        pass_count
    )

with q2:
    st.metric(
        "Overlaps",
        overlap_count
    )

with q3:
    st.metric(
        "Slivers",
        sliver_count
    )

with q4:
    st.metric(
        "Invalid Geometry",
        invalid_count
    )


# =========================================================
# VERIFICATION QUEUE
# =========================================================

st.markdown(
    '<div class="section-title">📍 Field Verification Queue</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'High-risk parcels are prioritized for Ground Truth verification.'
    '</div>',
    unsafe_allow_html=True
)

priority_gdf = gdf[
    gdf["priority"]
    .astype(str)
    .str.startswith("HIGH")
].copy()


if len(priority_gdf) > 0:

    display_df = priority_gdf[
        [
            "parcel_id",
            "confidence",
            "topology_status",
            "priority"
        ]
    ].copy()

    display_df.columns = [
        "Parcel ID",
        "Confidence",
        "Topology",
        "Priority"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No high-priority parcels currently require field verification."
    )


# =========================================================
# WORKFLOW
# =========================================================

st.markdown(
    '<div class="section-title">How AI-CADRE Works</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'A human-in-the-loop workflow for preliminary cadastral mapping.'
    '</div>',
    unsafe_allow_html=True
)

w1, w2, w3, w4, w5, w6 = st.columns(6)

workflow = [
    ("01", "📡", "Data", "Drone / GIS inputs"),
    ("02", "🧠", "AI Extraction", "Feature detection"),
    ("03", "⬡", "Parcel Proposal", "Polygon generation"),
    ("04", "✓", "Topology", "Geometry validation"),
    ("05", "📊", "Confidence", "Risk prioritization"),
    ("06", "👷", "Surveyor", "Review & verify"),
]

for col, item in zip(
    [w1, w2, w3, w4, w5, w6],
    workflow
):

    number, icon, name, desc = item

    with col:

        st.markdown(
            f"""
            <div class="workflow-card">

                <div class="workflow-number">
                    {number}
                </div>

                <div class="workflow-icon">
                    {icon}
                </div>

                <div class="workflow-name">
                    {name}
                </div>

                <div class="workflow-desc">
                    {desc}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# EXPORT
# =========================================================

st.markdown(
    '<div class="section-title">GIS Output</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Export the preliminary cadastral layer for downstream GIS workflows.'
    '</div>',
    unsafe_allow_html=True
)

st.download_button(
    label="📥 Export Preliminary GeoJSON",
    data=gdf.to_json(),
    file_name="ai_cadre_preliminary_cadastre.geojson",
    mime="application/geo+json",
    use_container_width=False
)


# =========================================================
# TRUST / DISCLAIMER
# =========================================================

st.markdown("""
<div class="card" style="margin-top:30px;">

    <div class="card-title">
        🛡️ Human-in-the-Loop by Design
    </div>

    <div class="card-subtitle">
        AI-CADRE produces preliminary GIS-ready cadastral features
        for authorized surveyor review. It does not determine ownership,
        settle land disputes, or create legally final land records.
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">

    <b>AI-CADRE</b> • Cadastral AI Co-Pilot • SIH26012

    <br><br>

    AI proposes. GIS validates. Confidence prioritizes.
    The surveyor approves.

</div>
""", unsafe_allow_html=True)
