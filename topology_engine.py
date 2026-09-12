import math
import geopandas as gpd


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def safe_compactness(geometry):
    if geometry is None or geometry.is_empty:
        return 0.0

    perimeter = geometry.length
    area = geometry.area

    if perimeter <= 0 or area <= 0:
        return 0.0

    return (4.0 * math.pi * area) / (perimeter ** 2)


def count_vertices(geometry):
    if geometry is None or geometry.is_empty:
        return 0

    try:
        if geometry.geom_type == "Polygon":
            return len(geometry.exterior.coords)

        if geometry.geom_type == "MultiPolygon":
            return sum(
                len(poly.exterior.coords)
                for poly in geometry.geoms
            )

        return 0

    except Exception:
        return 0


def calculate_area_anomaly(area, median_area):
    if median_area <= 0:
        return "NORMAL"

    ratio = area / median_area

    if ratio < 0.35:
        return "VERY SMALL"

    if ratio > 2.8:
        return "VERY LARGE"

    return "NORMAL"


# ============================================================
# CONTINUOUS CONFIDENCE SCORE
# ============================================================

def calculate_confidence(
    geometry,
    area,
    median_area,
    compactness,
    overlap_area,
):
    """
    Calculate a deterministic parcel-level confidence score.

    The score is based on:
    - geometry validity
    - compactness / shape regularity
    - parcel area deviation
    - overlap with neighbouring parcels

    This is a prototype QC confidence score, not a legal
    cadastral accuracy certification.
    """

    # --------------------------------------------------------
    # Invalid / missing geometry
    # --------------------------------------------------------

    if geometry is None or geometry.is_empty:
        return 40.0

    if not geometry.is_valid:
        return 52.0

    # --------------------------------------------------------
    # Start from a high-quality baseline
    # --------------------------------------------------------

    score = 97.0

    # --------------------------------------------------------
    # 1. Shape quality
    #
    # Compactness:
    # 1.0 = perfect circle
    # lower = increasingly irregular
    # --------------------------------------------------------

    if compactness < 0.35:
        score -= 15.0
    elif compactness < 0.45:
        score -= 10.0
    elif compactness < 0.55:
        score -= 6.0
    elif compactness < 0.65:
        score -= 3.0
    elif compactness < 0.75:
        score -= 1.0

    # --------------------------------------------------------
    # 2. Area consistency
    #
    # Instead of only saying NORMAL/ANOMALY, use the actual
    # distance from the median parcel size.
    # --------------------------------------------------------

    if median_area > 0 and area > 0:

        area_ratio = area / median_area

        # Distance from the expected size.
        deviation = abs(math.log(area_ratio))

        if deviation > 1.4:
            score -= 12.0
        elif deviation > 1.0:
            score -= 9.0
        elif deviation > 0.7:
            score -= 6.0
        elif deviation > 0.4:
            score -= 3.0
        elif deviation > 0.2:
            score -= 1.0

    # --------------------------------------------------------
    # 3. Overlap
    # --------------------------------------------------------

    if overlap_area > 0 and area > 0:

        overlap_ratio = overlap_area / area

        if overlap_ratio > 0.25:
            score -= 25.0
        elif overlap_ratio > 0.15:
            score -= 20.0
        elif overlap_ratio > 0.08:
            score -= 14.0
        elif overlap_ratio > 0.03:
            score -= 8.0
        else:
            score -= 3.0

    # --------------------------------------------------------
    # 4. Very small geometry
    # --------------------------------------------------------

    if area < 1.0:
        score -= 20.0

    # --------------------------------------------------------
    # Keep score in a realistic range
    # --------------------------------------------------------

    score = max(35.0, min(98.0, score))

    return round(score, 1)


# ============================================================
# MAIN PARCEL ANALYSIS
# ============================================================

def analyze_parcels(geojson_path):

    gdf = gpd.read_file(geojson_path)

    if "parcel_id" not in gdf.columns:
        gdf["parcel_id"] = [
            f"P-{1001 + i}"
            for i in range(len(gdf))
        ]

    gdf["parcel_id"] = gdf["parcel_id"].astype(str)

    # --------------------------------------------------------
    # Area statistics
    # --------------------------------------------------------

    areas = gdf.geometry.area

    median_area = (
        float(areas.median())
        if len(areas)
        else 0.0
    )

    results = []

    # ========================================================
    # PARCEL-BY-PARCEL ANALYSIS
    # ========================================================

    for idx, row in gdf.iterrows():

        geometry = row.geometry
        parcel_id = str(row["parcel_id"])

        # ----------------------------------------------------
        # Basic geometry values
        # ----------------------------------------------------

        area = (
            float(geometry.area)
            if geometry is not None
            and not geometry.is_empty
            else 0.0
        )

        compactness = safe_compactness(geometry)

        vertex_count = count_vertices(geometry)

        invalid_geometry = (
            geometry is None
            or geometry.is_empty
            or not geometry.is_valid
        )

        # ----------------------------------------------------
        # Calculate overlap with other parcels
        # ----------------------------------------------------

        overlap_area = 0.0

        if geometry is not None and not geometry.is_empty:

            for jdx, other in gdf.iterrows():

                if idx == jdx:
                    continue

                other_geom = other.geometry

                if (
                    other_geom is None
                    or other_geom.is_empty
                ):
                    continue

                try:

                    if geometry.intersects(other_geom):

                        overlap = (
                            geometry
                            .intersection(other_geom)
                            .area
                        )

                        overlap_area += max(
                            0.0,
                            float(overlap),
                        )

                except Exception:
                    pass

        # ----------------------------------------------------
        # Area classification
        # ----------------------------------------------------

        area_anomaly = calculate_area_anomaly(
            area,
            median_area,
        )

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = calculate_confidence(
            geometry=geometry,
            area=area,
            median_area=median_area,
            compactness=compactness,
            overlap_area=overlap_area,
        )

        # ----------------------------------------------------
        # Explainable issues
        # ----------------------------------------------------

        issues = []

        if invalid_geometry:
            issues.append("invalid geometry")

        if overlap_area > 0.01:
            issues.append("overlap detected")

        if area < 1.0:
            issues.append("sliver geometry")

        if compactness < 0.55 and area > 0:
            issues.append("irregular shape")

        if area_anomaly != "NORMAL":
            issues.append(
                f"area anomaly: "
                f"{area_anomaly.lower()}"
            )

        # ----------------------------------------------------
        # Priority
        # ----------------------------------------------------

        if confidence < 70:
            priority = "HIGH"
            color = "#EF4444"

        elif confidence < 85:
            priority = "MEDIUM"
            color = "#F59E0B"

        else:
            priority = "LOW"
            color = "#22C55E"

        # ----------------------------------------------------
        # Explainability text
        # ----------------------------------------------------

        if issues:

            xai_reason = (
                "AI flags "
                + ", ".join(issues)
                + "."
            )

        else:

            xai_reason = (
                "Geometry is valid, shows no significant "
                "overlap, and falls within expected parcel "
                "characteristics."
            )

        # ----------------------------------------------------
        # Topology status
        # ----------------------------------------------------

        topology_status = (
            "PASS - VALID"
            if (
                not invalid_geometry
                and overlap_area <= 0.01
                and area >= 1.0
            )
            else "REVIEW - ISSUES"
        )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append(
            {
                "parcel_id": parcel_id,
                "geometry": geometry,
                "area_sqm": round(area, 4),
                "confidence": confidence,
                "topology_status": topology_status,
                "xai_reason": xai_reason,
                "priority": priority,
                "color": color,
                "compactness": round(
                    compactness,
                    3,
                ),
                "vertex_count": vertex_count,
                "overlap_area": round(
                    overlap_area,
                    4,
                ),
                "area_anomaly": area_anomaly,
            }
        )

    # ========================================================
    # RETURN GIS RESULT
    # ========================================================

    return gpd.GeoDataFrame(
        results,
        geometry="geometry",
        crs=gdf.crs,
    )
