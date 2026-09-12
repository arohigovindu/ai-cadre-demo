import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


def analyze_parcels(geojson_path):

    gdf = gpd.read_file(geojson_path)

    results = []

    for idx, row in gdf.iterrows():

        current_poly = row["geometry"]
        parcel_id = row.get("parcel_id", f"P-{1000 + idx}")

        # -----------------------------------
        # Basic geometry checks
        # -----------------------------------

        is_valid = current_poly.is_valid

        # Self intersection / invalid geometry
        if not is_valid:

            topology_status = "FAIL (INVALID)"
            confidence = 40.0

            xai_reason = (
                "Topology Alert: Invalid polygon geometry "
                "or self-intersection detected."
            )

        else:

            # -----------------------------------
            # Check overlap with neighbouring parcels
            # -----------------------------------

            other_geometries = gdf[
                gdf.index != idx
            ].geometry

            overlaps = other_geometries.intersection(
                current_poly
            )

            overlap_area = sum(
                o.area
                for o in overlaps
                if not o.is_empty
            )

            # -----------------------------------
            # Sliver check
            # -----------------------------------

            if current_poly.area < 1.0:

                topology_status = "FAIL (SLIVER)"
                confidence = 45.0

                xai_reason = (
                    "Topology Alert: Very small polygon "
                    "likely caused by segmentation noise."
                )

            elif overlap_area > 0.01:

                topology_status = "FAIL (OVERLAP)"
                confidence = 62.0

                xai_reason = (
                    f"Topology Alert: Overlap detected "
                    f"({round(overlap_area, 2)} sq. units "
                    f"with adjacent parcel)."
                )

            else:

                topology_status = "PASS"
                confidence = 95.0

                xai_reason = (
                    "Boundary geometry is valid and "
                    "no significant overlap was detected."
                )

        # -----------------------------------
        # Verification priority
        # -----------------------------------

        if confidence < 70:

            priority = "HIGH"
            color = "#EF4444"

        elif confidence < 85:

            priority = "MEDIUM"
            color = "#F59E0B"

        else:

            priority = "LOW"
            color = "#22C55E"

        results.append({

            "parcel_id": parcel_id,

            "geometry": current_poly,

            "area_sqm": round(
                current_poly.area, 2
            ),

            "confidence": confidence,

            "topology_status": topology_status,

            "xai_reason": xai_reason,

            "priority": priority,

            "color": color

        })

    return gpd.GeoDataFrame(
        results,
        crs=gdf.crs
    )
