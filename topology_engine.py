import geopandas as gpd

def analyze_parcels(geojson_path):
    gdf = gpd.read_file(geojson_path)
    results = []

    for idx, row in gdf.iterrows():
        current_poly = row['geometry']
        parcel_id = row.get('parcel_id', f"P-{1000 + idx}")
        
        overlaps = gdf[gdf.index != idx].geometry.intersection(current_poly)
        overlap_area = sum([o.area for o in overlaps if not o.is_empty])
        
        confidence = 95.0
        topology_status = "PASS"
        xai_reason = "Boundary geometry clean & verified."
        
        if overlap_area > 0.01:
            topology_status = "FAIL (OVERLAP)"
            confidence = 62.0
            xai_reason = f"Topology Alert: Overlap detected ({round(overlap_area, 2)} sq. units with adjacent plot)."
        elif current_poly.area < 1.0:
            topology_status = "FAIL (SLIVER)"
            confidence = 45.0
            xai_reason = "Topology Alert: Invalid sliver polygon generated from noise."

        if confidence < 70:
            priority = "HIGH (Requires Field GT)"
            color = "#FF0000"
        elif confidence < 85:
            priority = "MEDIUM (Desktop Review)"
            color = "#FFA500"
        else:
            priority = "LOW (Auto-Approve Candidate)"
            color = "#00FF00"

        results.append({
            'parcel_id': parcel_id,
            'geometry': current_poly,
            'area_sqm': round(current_poly.area, 2),
            'confidence': confidence,
            'topology_status': topology_status,
            'xai_reason': xai_reason,
            'priority': priority,
            'color': color
        })

    return gpd.GeoDataFrame(results, crs=gdf.crs)
