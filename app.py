import streamlit as st
import folium
from streamlit_folium import st_folium
from topology_engine import analyze_parcels

st.set_page_config(layout="wide", page_title="AI-CADRE Surveyor Dashboard")

st.title("🛰️ AI-CADRE: Cadastral AI Co-Pilot Dashboard")
st.caption("AI Proposes, GIS Validates, Confidence Prioritizes, and the Surveyor Approves!")

gdf = analyze_parcels("sample_parcels.geojson")

# Fix 1: Pass 2 into st.columns(2)
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Web-GIS Map View")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="OpenStreetMap")
    
    for _, row in gdf.iterrows():
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=row['color']: {
                'fillColor': color,
                'color': color,
                'weight': 3,
                'fillOpacity': 0.5
            },
            tooltip=f"Parcel: {row['parcel_id']} | Confidence: {row['confidence']}%"
        ).add_to(m)
        
    st_folium(m, width=700, height=480)

with col2:
    st.subheader("🔍 Parcel Inspector")
    selected_id = st.selectbox("Select Parcel ID:", gdf['parcel_id'].tolist())
    
    # Fix 2: Added  to iloc to select row data
    p = gdf[gdf['parcel_id'] == selected_id].iloc
    
    st.metric("Confidence Score", f"{p['confidence']}%")
    st.write(f"**Priority:** {p['priority']}")
    st.write(f"**Topology Check:** {p['topology_status']}")
    
    st.info(f"💡 **Explainable AI Flag:** {p['xai_reason']}")
    
    b1, b2 = st.columns(2)
    with b1:
        if st.button("✅ Approve"):
            st.success(f"{selected_id} Approved!")
    with b2:
        if st.button("🚩 Flag for Field GT"):
            st.warning(f"{selected_id} Flagged!")

    st.markdown("---")
    st.download_button(
        label="📥 Export Approved GeoJSON",
        data=gdf.to_json(),
        file_name="approved_cadastre.geojson",
        mime="application/json"
    )
