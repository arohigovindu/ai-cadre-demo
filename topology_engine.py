import math
import geopandas as gpd


def safe_compactness(geometry):
    if geometry is None or geometry.is_empty:
        return 0.0

    try:
        perimeter = geometry.length
        area = geometry.area

        if perimeter <= 0 or area <= 0:
            return 0.0

        return (4.0 * math.pi * area) / (perimeter ** 2)

    except Exception:
        return 0.0


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

    except Exception:
        pass

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


def get_metric_crs(gdf):
    """
    Converts geographic coordinates (latitude/longitude)
    into a suitable local projected CRS so that area,
    perimeter and overlap are measured in metres.
    """

    if gdf.crs is None:
        return None

    try:
        if gdf.crs.is_projected:
            return gdf.crs

        # Automatically choose a suitable UTM CRS
        return gdf.estimate_utm_crs()

    except Exception:
        return None


def analyze_parcels(geojson_path):

    # Read original data
    original_gdf = gpd.read_file(geojson_path)

    # Create parcel IDs if they don't already exist
    if "parcel_id" not in original_gdf.columns:
        original_gdf["parcel_id"] = [
            f"P-{1001 + i}"
            for i in range(len(original_gdf))
        ]

    original_gdf["parcel_id"] = (
        original_gdf["parcel_id"].astype(str)
    )

    # ---------------------------------------------------------
    # IMPORTANT:
    # Keep original geometry for displaying on the map.
    # Create a separate metric version for calculations.
    # ---------------------------------------------------------

    metric_crs = get_metric_crs(original_gdf)

    if metric_crs is not None:
        metric_gdf = original_gdf.to_crs(metric_crs)
    else:
        metric_gdf = original_gdf.copy()

    # Calculate areas in square metres
    areas = metric_gdf.geometry.area

    median_area = (
        float(areas.median())
        if len(areas)
        else 0.0
    )

    results = []

    for idx, row in original_gdf.iterrows():

        geometry_original = row.geometry
        geometry_metric = metric_gdf.loc[idx, "geometry"]

        parcel_id = str(row["parcel_id"])

        # -----------------------------------------------------
        # Basic geometry measurements
        # -----------------------------------------------------

        if (
            geometry_metric is not None
            and not geometry_metric.is_empty
        ):
            area = float(geometry_metric.area)
        else:
            area = 0.0

        compactness = safe_compactness(
            geometry_metric
        )

        vertex_count = count_vertices(
            geometry_original
        )

        # -----------------------------------------------------
        # Overlap detection
        # -----------------------------------------------------

        overlap_area = 0.0

        if (
            geometry_metric is not None
            and not geometry_metric.is_empty
        ):

            for jdx, other_row in metric_gdf.iterrows():

                if idx == jdx:
                    continue

                other_geometry = other_row.geometry

                if (
                    other_geometry is None
                    or other_geometry.is_empty
                ):
                    continue

                try:

                    if geometry_metric.intersects(
                        other_geometry
                    ):

                        overlap = (
                            geometry_metric
                            .intersection(other_geometry)
                            .area
                        )

                        overlap_area += max(
                            0.0,
                            float(overlap)
                        )

                except Exception:
                    pass

        # -----------------------------------------------------
        # Geometry validity
        # -----------------------------------------------------

        invalid_geometry = (
            geometry_metric is None
            or geometry_metric.is_empty
            or not geometry_metric.is_valid
        )

        # -----------------------------------------------------
        # Area anomaly
        # -----------------------------------------------------

        area_anomaly = calculate_area_anomaly(
            area,
            median_area
        )

        # =====================================================
        # CONFIDENCE SCORE
        # =====================================================

        # Start high, then continuously adjust according
        # to actual geometric characteristics.
        confidence = 98.0

        issues = []

        # -----------------------------------------------------
        # 1. Invalid geometry
        # -----------------------------------------------------

        if invalid_geometry:

            issues.append("invalid geometry")
            confidence -= 35.0

        # -----------------------------------------------------
        # 2. Overlap
        # -----------------------------------------------------

        if overlap_area > 0.01:

            overlap_ratio = (
                overlap_area / max(area, 1.0)
            )

            issues.append("overlap detected")

            confidence -= min(
                25.0,
                overlap_ratio * 100.0
            )

        # -----------------------------------------------------
        # 3. Shape irregularity
        #
        # Compactness:
        # 1.0 = very compact
        # lower = increasingly irregular
        # -----------------------------------------------------

        if area > 0:

            shape_penalty = max(
                0.0,
                (0.80 - compactness) * 30.0
            )

            confidence -= min(
                14.0,
                shape_penalty
            )

            if compactness < 0.55:
                issues.append("irregular shape")

        # -----------------------------------------------------
        # 4. Area consistency
        #
        # Compare parcel area with the median parcel area.
        # This is continuous, so parcels don't all get the
        # exact same score.
        # -----------------------------------------------------

        if area > 0 and median_area > 0:

            area_ratio = (
                area / median_area
            )

            area_deviation = abs(
                math.log(area_ratio)
            )

            area_penalty = min(
                8.0,
                area_deviation * 4.0
            )

            confidence -= area_penalty

        # -----------------------------------------------------
        # 5. Very small/sliver geometry
        #
        # IMPORTANT:
        # area is now in square metres, not degrees.
        # -----------------------------------------------------

        if area < 1.0:

            issues.append("sliver geometry")
            confidence -= 20.0

        # -----------------------------------------------------
        # 6. Area anomaly
        # -----------------------------------------------------

        if area_anomaly != "NORMAL":

            issues.append(
                f"area anomaly: "
                f"{area_anomaly.lower()}"
            )

            confidence -= 4.0

        # -----------------------------------------------------
        # Final confidence range
        # -----------------------------------------------------

        confidence = max(
            35.0,
            min(98.0, confidence)
        )

        # -----------------------------------------------------
        # Explainable AI reason
        # -----------------------------------------------------

        if issues:

            xai_reason = (
                "AI flags "
                + ", ".join(issues)
                + "."
            )

        else:

            xai_reason = (
                "Geometry is valid, shows no "
                "significant overlap, and falls "
                "within expected parcel "
                "characteristics."
            )

        # -----------------------------------------------------
        # Priority
        # -----------------------------------------------------

        if confidence < 70:

            priority = "HIGH"
            color = "#EF4444"

        elif confidence < 85:

            priority = "MEDIUM"
            color = "#F59E0B"

        else:

            priority = "LOW"
            color = "#22C55E"

        # -----------------------------------------------------
        # Store result
        # -----------------------------------------------------

        results.append(
            {
                "parcel_id": parcel_id,

                # KEEP ORIGINAL GEOMETRY
                # so the map remains in its original CRS.
                "geometry": geometry_original,

                "area_sqm": round(
                    area,
                    2
                ),

                "confidence": round(
                    confidence,
                    1
                ),

                "topology_status": (
                    "PASS - VALID"
                    if (
                        not invalid_geometry
                        and overlap_area <= 0.01
                        and area >= 1.0
                    )
                    else "REVIEW - ISSUES"
                ),

                "xai_reason": xai_reason,

                "priority": priority,

                "color": color,

                "compactness": round(
                    compactness,
                    3
                ),

                "vertex_count": vertex_count,

                "overlap_area": round(
                    overlap_area,
                    2
                ),

                "area_anomaly": area_anomaly,
            }
        )

    # ---------------------------------------------------------
    # Preserve all original attributes
    # such as region, survey_zone, land_use
    # ---------------------------------------------------------

    result_gdf = original_gdf.copy()

    analysis_gdf = gpd.GeoDataFrame(
        results,
        geometry="geometry",
        crs=original_gdf.crs
    )

    # Add analysis columns
    analysis_columns = [
        "area_sqm",
        "confidence",
        "topology_status",
        "xai_reason",
        "priority",
        "color",
        "compactness",
        "vertex_count",
        "overlap_area",
        "area_anomaly",
    ]

    for column in analysis_columns:
        result_gdf[column] = analysis_gdf[column].values

    return result_gdf
