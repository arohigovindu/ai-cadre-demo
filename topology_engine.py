import math
import geopandas as gpd


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
            return sum(len(poly.exterior.coords) for poly in geometry.geoms)
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


def analyze_parcels(geojson_path):
    gdf = gpd.read_file(geojson_path)
    if "parcel_id" not in gdf.columns:
        gdf["parcel_id"] = [f"P-{1001 + i}" for i in range(len(gdf))]
    gdf["parcel_id"] = gdf["parcel_id"].astype(str)

    # GeoJSON is normally stored in latitude/longitude. Project it to a
    # local metric CRS for meaningful area, overlap and geometry checks.
    metric_gdf = gdf.copy()
    if metric_gdf.crs is not None and metric_gdf.crs.is_geographic:
        try:
            metric_gdf = metric_gdf.to_crs(metric_gdf.estimate_utm_crs())
        except Exception:
            metric_gdf = metric_gdf.to_crs(epsg=3857)

    metric_geometries = metric_gdf.geometry
    areas = metric_geometries.area
    median_area = float(areas.median()) if len(areas) else 0.0
    results = []

    for idx, row in gdf.iterrows():
        geometry = row.geometry
        metric_geometry = metric_geometries.loc[idx]
        parcel_id = str(row["parcel_id"])
        area = float(metric_geometry.area) if metric_geometry is not None and not metric_geometry.is_empty else 0.0
        compactness = safe_compactness(metric_geometry)
        vertex_count = count_vertices(geometry)
        overlap_area = 0.0
        invalid_geometry = geometry is None or geometry.is_empty or not geometry.is_valid

        if metric_geometry is not None and not metric_geometry.is_empty:
            for jdx, other_metric in metric_geometries.items():
                if idx == jdx:
                    continue
                if other_metric is None or other_metric.is_empty:
                    continue
                try:
                    if metric_geometry.intersects(other_metric):
                        overlap = metric_geometry.intersection(other_metric).area
                        overlap_area += max(0.0, float(overlap))
                except Exception:
                    pass

        area_anomaly = calculate_area_anomaly(area, median_area)

        issues = []
        confidence = 95.0

        if invalid_geometry:
            issues.append("invalid geometry")
            confidence -= 35

        if overlap_area > 0.01:
            issues.append("overlap detected")
            confidence -= min(25, overlap_area / max(area, 1.0) * 100)

        if area < 1.0:
            issues.append("sliver geometry")
            confidence -= 20

        if compactness < 0.35 and area > 0:
            issues.append("irregular shape")
            confidence -= 8

        if area_anomaly != "NORMAL":
            issues.append(f"area anomaly: {area_anomaly.lower()}")
            confidence -= 7

        confidence = max(35.0, min(98.0, confidence))

        if issues:
            xai_reason = "AI flags " + ", ".join(issues) + "."
        else:
            xai_reason = (
                "Geometry is valid, shows no significant overlap, "
                "and falls within expected parcel characteristics."
            )

        if confidence < 70:
            priority = "HIGH"
            color = "#EF4444"
        elif confidence < 85:
            priority = "MEDIUM"
            color = "#F59E0B"
        else:
            priority = "LOW"
            color = "#22C55E"

        result = {
            "parcel_id": parcel_id,
            "geometry": geometry,
            "area_sqm": round(area, 2),
            "confidence": round(confidence, 1),
            "topology_status": (
                "PASS - VALID"
                if not invalid_geometry and overlap_area <= 0.01 and area >= 1.0
                else "REVIEW - ISSUES"
            ),
            "xai_reason": xai_reason,
            "priority": priority,
            "color": color,
            "compactness": round(compactness, 3),
            "vertex_count": vertex_count,
            "overlap_area": round(overlap_area, 2),
            "area_anomaly": area_anomaly,
        }

        # Preserve source metadata such as the survey packet / region.
        for column in gdf.columns:
            if column not in {"parcel_id", "geometry"}:
                result[column] = row[column]

        results.append(result)

    return gpd.GeoDataFrame(results, geometry="geometry", crs=gdf.crs)
