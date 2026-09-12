import math
import geopandas as gpd


def safe_compactness(geometry):

    try:

        area = float(geometry.area)
        perimeter = float(geometry.length)

        if area <= 0 or perimeter <= 0:
            return 0.0

        value = (
            4 * math.pi * area
        ) / (
            perimeter ** 2
        )

        return max(
            0.0,
            min(1.0, value)
        )

    except Exception:

        return 0.0


def count_vertices(geometry):

    try:

        if geometry.geom_type == "Polygon":

            return len(
                geometry.exterior.coords
            )

        elif geometry.geom_type == "MultiPolygon":

            return sum(
                len(poly.exterior.coords)
                for poly in geometry.geoms
            )

        return 0

    except Exception:

        return 0


def calculate_area_anomaly(
    area,
    median_area
):

    if median_area <= 0:
        return "NORMAL"

    ratio = area / median_area

    if ratio < 0.35:
        return "VERY SMALL"

    if ratio < 0.60:
        return "SMALL"

    if ratio > 2.50:
        return "VERY LARGE"

    if ratio > 1.70:
        return "LARGE"

    return "NORMAL"


def analyze_parcels(geojson_path):

    gdf = gpd.read_file(
        geojson_path
    )


    if gdf.empty:

        return gpd.GeoDataFrame(
            columns=[
                "parcel_id",
                "geometry",
                "area_sqm",
                "confidence",
                "topology_status",
                "xai_reason",
                "priority",
                "color",
                "compactness",
                "vertex_count",
                "overlap_area",
                "area_anomaly"
            ],

            geometry="geometry",

            crs=gdf.crs
        )


    # ========================================================
    # PARCEL IDS
    # ========================================================

    if "parcel_id" not in gdf.columns:

        gdf["parcel_id"] = [

            f"P-{1000 + idx}"

            for idx in range(
                len(gdf)
            )

        ]


    gdf["parcel_id"] = (
        gdf["parcel_id"]
        .astype(str)
    )


    # ========================================================
    # AREA
    # ========================================================

    areas = []

    for geometry in gdf.geometry:

        try:

            areas.append(
                float(geometry.area)
            )

        except Exception:

            areas.append(0.0)


    positive_areas = [

        value

        for value in areas

        if value > 0

    ]


    if positive_areas:

        sorted_areas = sorted(
            positive_areas
        )

        middle = len(
            sorted_areas
        ) // 2


        if len(sorted_areas) % 2 == 0:

            median_area = (
                sorted_areas[middle - 1]
                +
                sorted_areas[middle]
            ) / 2

        else:

            median_area = sorted_areas[
                middle
            ]

    else:

        median_area = 1.0


    # ========================================================
    # ANALYSIS
    # ========================================================

    results = []


    for idx, row in gdf.iterrows():

        geometry = row["geometry"]

        parcel_id = str(
            row["parcel_id"]
        )


        # ----------------------------------------------------
        # BASIC GEOMETRY
        # ----------------------------------------------------

        try:

            area = float(
                geometry.area
            )

        except Exception:

            area = 0.0


        try:

            is_valid = bool(
                geometry.is_valid
            )

        except Exception:

            is_valid = False


        try:

            is_empty = bool(
                geometry.is_empty
            )

        except Exception:

            is_empty = True


        compactness = safe_compactness(
            geometry
        )


        vertex_count = count_vertices(
            geometry
        )


        area_anomaly = calculate_area_anomaly(
            area,
            median_area
        )


        # ----------------------------------------------------
        # OVERLAP
        # ----------------------------------------------------

        overlap_area = 0.0

        overlap_parcels = []


        if not is_empty:

            for other_idx, other_row in gdf.iterrows():

                if other_idx == idx:
                    continue


                other_geometry = (
                    other_row["geometry"]
                )


                try:

                    intersection = (
                        geometry.intersection(
                            other_geometry
                        )
                    )


                    if not intersection.is_empty:

                        intersection_area = float(
                            intersection.area
                        )


                        if intersection_area > 0:

                            overlap_area += (
                                intersection_area
                            )


                            overlap_parcels.append(
                                str(
                                    other_row[
                                        "parcel_id"
                                    ]
                                )
                            )


                except Exception:

                    continue


        # ----------------------------------------------------
        # TOPOLOGY
        # ----------------------------------------------------

        topology_status = "PASS"


        if (
            not is_valid
            or is_empty
        ):

            topology_status = (
                "FAIL (INVALID GEOMETRY)"
            )


        elif overlap_area > 0.01:

            topology_status = (
                "FAIL (OVERLAP)"
            )


        elif area < 1.0:

            topology_status = (
                "FAIL (SLIVER)"
            )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = 95.0

        reasons = []


        if (
            not is_valid
            or is_empty
        ):

            confidence -= 35

            reasons.append(
                "geometry validity issue"
            )


        if overlap_area > 0.01:

            confidence -= 28

            reasons.append(
                f"overlap with "
                f"{len(overlap_parcels)} "
                f"adjacent parcel(s)"
            )


        if area < 1.0:

            confidence -= 25

            reasons.append(
                "very small/sliver geometry"
            )


        if compactness < 0.35:

            confidence -= 10

            reasons.append(
                "irregular boundary shape"
            )

        elif compactness < 0.55:

            confidence -= 5

            reasons.append(
                "moderately irregular boundary"
            )


        if area_anomaly == "VERY SMALL":

            confidence -= 7

            reasons.append(
                "area significantly below "
                "parcel median"
            )


        elif area_anomaly == "VERY LARGE":

            confidence -= 4

            reasons.append(
                "area significantly above "
                "parcel median"
            )


        confidence = max(
            35.0,
            min(98.0, confidence)
        )


        # ----------------------------------------------------
        # XAI
        # ----------------------------------------------------

        if reasons:

            xai_reason = (
                "Review recommended because "
                + ", ".join(reasons)
                + "."
            )

        else:

            xai_reason = (
                "Boundary geometry is clean, "
                "topology checks passed, and no "
                "major anomalous geometry signals "
                "were detected."
            )


        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        if confidence < 70:

            priority = (
                "HIGH (Requires Field GT)"
            )

            color = "#EF4444"


        elif confidence < 85:

            priority = (
                "MEDIUM (Desktop Review)"
            )

            color = "#F59E0B"


        else:

            priority = (
                "LOW (Auto-Approve Candidate)"
            )

            color = "#22C55E"


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        results.append({

            "parcel_id": parcel_id,

            "geometry": geometry,

            # IMPORTANT:
            # app.py expects this exact name.
            "area_sqm": round(
                area,
                4
            ),

            "confidence": round(
                confidence,
                1
            ),

            "topology_status":
                topology_status,

            "xai_reason":
                xai_reason,

            "priority":
                priority,

            "color":
                color,

            "compactness":
                round(
                    compactness,
                    3
                ),

            "vertex_count":
                vertex_count,

            "overlap_area":
                round(
                    overlap_area,
                    4
                ),

            "area_anomaly":
                area_anomaly

        })


    # ========================================================
    # RETURN
    # ========================================================

    return gpd.GeoDataFrame(
        results,
        geometry="geometry",
        crs=gdf.crs
    )
