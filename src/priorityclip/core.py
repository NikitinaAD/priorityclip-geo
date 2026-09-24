from __future__ import annotations

from dataclasses import dataclass
import math

import geopandas as gpd
import pandas as pd
from pyproj import CRS
from shapely import union_all
from shapely.geometry import MultiPolygon, Polygon


@dataclass
class PartitionResult:
    geometries: gpd.GeoDataFrame
    report: pd.DataFrame
    source_union_area: float
    result_union_area: float
    coverage_error_area: float
    maximum_overlap_area: float


def _polygonal(geometry):
    if geometry.is_empty or isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry
    polygons = []
    for part in getattr(geometry, "geoms", []):
        if isinstance(part, (Polygon, MultiPolygon)) and not part.is_empty:
            polygons.append(part)
    return union_all(polygons) if polygons else Polygon()


def _validate(frame: gpd.GeoDataFrame, priority: str) -> None:
    if frame.empty:
        raise ValueError("Input dataset is empty")
    if priority not in frame.columns:
        raise ValueError(f"Priority column not found: {priority}")
    if frame.crs is None:
        raise ValueError("Input dataset must have a projected CRS")
    crs = CRS(frame.crs)
    if not crs.is_projected:
        raise ValueError("Input CRS must be projected")
    axes = crs.axis_info[:2]
    if len(axes) < 2 or any(abs(axis.unit_conversion_factor - 1.0) > 1e-9 for axis in axes):
        raise ValueError("Input CRS horizontal units must be metres")
    if frame.geometry.isna().any() or frame.geometry.is_empty.any():
        raise ValueError("Input contains missing or empty geometries")
    bad_type = ~frame.geom_type.isin(["Polygon", "MultiPolygon"])
    if bad_type.any():
        raise ValueError("All input geometries must be Polygon or MultiPolygon")
    invalid = ~frame.geometry.is_valid
    if invalid.any():
        rows = ", ".join(map(str, frame.index[invalid].tolist()[:10]))
        raise ValueError(f"Invalid input geometry at row(s): {rows}")
    values = pd.to_numeric(frame[priority], errors="coerce")
    if values.isna().any() or not values.map(math.isfinite).all():
        raise ValueError("Priorities must be finite numbers")


def partition(
    frame: gpd.GeoDataFrame,
    priority: str,
    *,
    tolerance: float | None = None,
) -> PartitionResult:
    """Give overlapping area to rows with the lowest priority value first.

    Equal priorities retain stable input order. Attributes are preserved and output
    rows are returned in processing order.
    """
    _validate(frame, priority)
    ordered = frame.copy()
    ordered[priority] = pd.to_numeric(ordered[priority])
    ordered["__source_order"] = range(len(ordered))
    ordered = ordered.sort_values([priority, "__source_order"], kind="stable")

    accepted = []
    rows = []
    occupied = Polygon()
    for source_index, row in ordered.iterrows():
        source_geometry = row.geometry
        result_geometry = _polygonal(source_geometry.difference(occupied))
        accepted.append(result_geometry)
        occupied = union_all([occupied, result_geometry])
        parts = 0 if result_geometry.is_empty else (
            len(result_geometry.geoms) if isinstance(result_geometry, MultiPolygon) else 1
        )
        rows.append(
            {
                "source_index": str(source_index),
                "priority": float(row[priority]),
                "source_area_m2": float(source_geometry.area),
                "result_area_m2": float(result_geometry.area),
                "removed_area_m2": float(source_geometry.area - result_geometry.area),
                "parts": parts,
                "empty": bool(result_geometry.is_empty),
            }
        )

    output = ordered.drop(columns="__source_order").copy()
    output.geometry = accepted
    report = pd.DataFrame(rows)
    source_union = union_all(list(frame.geometry))
    result_union = union_all(accepted)
    coverage_error = float(source_union.symmetric_difference(result_union).area)
    overlap = 0.0
    for index, left in enumerate(accepted):
        for right in accepted[index + 1 :]:
            overlap = max(overlap, float(left.intersection(right).area))
    allowed = tolerance if tolerance is not None else max(1e-8, float(source_union.area) * 1e-12)
    if coverage_error > allowed:
        raise RuntimeError(f"Partition coverage invariant failed: {coverage_error} m²")
    if overlap > allowed:
        raise RuntimeError(f"Partition overlap invariant failed: {overlap} m²")
    return PartitionResult(
        geometries=output,
        report=report,
        source_union_area=float(source_union.area),
        result_union_area=float(result_union.area),
        coverage_error_area=coverage_error,
        maximum_overlap_area=overlap,
    )

