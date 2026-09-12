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
# CONFIDENCE SCORE
# ============================================================

def calculate_confidence(
    geometry,
    area,
    median_area,
    compactness,
    overlap_area,
):
    """
    Deterministic prototype confidence score.

    The score uses:
    - geometry validity
    - shape regularity
    - area consistency
    - overlap
    - sliver detection

    This represents automated geometry/QC confidence.
    It is NOT a legal cadastral accuracy certification.
    """

    if geometry is None or geometry.is_empty:
        return 40.0

    if not geometry.is_valid:
        return 52.0

    # Strong starting score for a clean parcel.
    score = 97.0

    # --------------------------------------------------------
    # Shape regularity
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
    # Area consistency
    #
    # Use continuous deviation rather than only
    # NORMAL / ANOMALY.
    # --------------------------------------------------------

    if median_area > 0 and area > 0:

        area_ratio = area / median_area

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
    # Overlap
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
    # Sliver
    # --------------------------------------------------------

    if area < 1.0:
        score -= 20.0

    return round(
        max(35.0, min(98.0, score)),
        1,
    )


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_parcels(geojson_path):

    # --------------------------------------------------------
    # Read original GIS layer
    # --------------------------------------------------------

    original_gdf = gpd.read_file(geojson_path)

    if original_gdf.empty:
        return original_gdf

    if "parcel_id" not in original_gdf.columns:
        original_gdf["parcel_id"] = [
            f"P-{1001 + i}"
            for i in range(len(original_gdf))
        ]

    original_gdf["parcel_id"] = (
        original_gdf["parcel_id"].astype(str)
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # The source layer is latitude/longitude.
    #
    # Reproject to a local UTM zone for all metric
    # calculations.
    # --------------------------------------------------------

    if original_gdf.crs is None:
        original_gdf = original_gdf.set_crs(
            epsg=4326
        )

    # Use the geographic centroid to determine the
    # appropriate UTM zone.
    geographic = original_gdf.to_crs(epsg=4326)

    centroid = geographic.geometry.union_all().centroid

    longitude = centroid.x
    latitude = centroid.y

    utm_zone = int(
        (longitude + 180) / 6
    ) + 1

    if latitude >= 0:
        metric_epsg = 32600 + utm_zone
    else:
        metric_epsg = 32700 + utm_zone

    metric_gdf = original_gdf.to_crs(
        epsg=metric_epsg
    )

    # --------------------------------------------------------
    # Median area in REAL square metres
    # --------------------------------------------------------

    areas = metric_gdf.geometry.area

    median_area = (
        float(areas.median())
        if len(areas)
        else 0.0
    )

    results = []

    # ========================================================
    # PARCEL-BY-PARCEL ANALYSIS
    # ========================================================

    for idx in metric_gdf.index:

        geometry = metric_gdf.loc[idx, "geometry"]

        original_geometry = original_gdf.loc[
            idx,
            "geometry",
        ]

        parcel_id = str(
            original_gdf.loc[idx, "parcel_id"]
        )

        # ----------------------------------------------------
        # Area
        # ----------------------------------------------------

        area = (
            float(geometry.area)
            if geometry is not None
            and not geometry.is_empty
            else 0.0
        )

        # ----------------------------------------------------
        # Shape
        # ----------------------------------------------------

        compactness = safe_compactness(
            geometry
        )

        vertex_count = count_vertices(
            geometry
        )

        invalid_geometry = (
            geometry is None
            or geometry.is_empty
            or not geometry.is_valid
        )

        # ----------------------------------------------------
        # Overlap
        # ----------------------------------------------------

        overlap_area = 0.0

        if (
            geometry is not None
            and not geometry.is_empty
        ):

            for jdx in metric_gdf.index:

                if idx == jdx:
                    continue

                other_geom = metric_gdf.loc[
                    jdx,
                    "geometry",
                ]

                if (
                    other_geom is None
                    or other_geom.is_empty
                ):
                    continue

                try:

                    if geometry.intersects(
                        other_geom
                    ):

                        overlap = (
                            geometry
                            .intersection(
                                other_geom
                            )
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
        # Confidence
        # ----------------------------------------------------

        confidence = calculate_confidence(
            geometry=geometry,
            area=area,
            median_area=median_area,
            compactness=compactness,
            overlap_area=overlap_area,
        )

        # ----------------------------------------------------
        # Issues
        # ----------------------------------------------------

        issues = []

        if invalid_geometry:
            issues.append(
                "invalid geometry"
            )

        if overlap_area > 0.01:
            issues.append(
                "overlap detected"
            )

        if area < 1.0:
            issues.append(
                "sliver geometry"
            )

        if compactness < 0.55 and area > 0:
            issues.append(
                "irregular shape"
            )

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
        # Explainability
        # ----------------------------------------------------

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
        # Store original geometry so the map remains
        # in its original coordinate system.
        # ----------------------------------------------------

        result = {
            "parcel_id": parcel_id,
            "geometry": original_geometry,
            "area_sqm": round(
                area,
                2,
            ),
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
                2,
            ),
            "area_anomaly": area_anomaly,
        }

        # Preserve any extra source attributes such as:
        # region, survey_zone, land_use.
        for column in original_gdf.columns:

            if column == "geometry":
                continue

            if column not in result:
                result[column] = (
                    original_gdf.loc[
                        idx,
                        column,
                    ]
                )

        results.append(result)

    # --------------------------------------------------------
    # Return GeoDataFrame in original CRS
    # --------------------------------------------------------

    return gpd.GeoDataFrame(
        results,
        geometry="geometry",
        crs=original_gdf.crs,
    )
