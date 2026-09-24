import geopandas as gpd
from shapely.geometry import Polygon, box

from priorityclip.cli import main
from priorityclip.core import partition


def frame(geometries, priorities):
    return gpd.GeoDataFrame(
        {"name": [f"area-{i}" for i in range(len(geometries))], "priority": priorities},
        geometry=geometries,
        crs="EPSG:3857",
    )


def test_priority_controls_shared_area_and_preserves_union():
    source = frame([box(0, 0, 10, 10), box(5, 0, 15, 10)], [2, 1])
    result = partition(source, "priority")
    assert list(result.geometries["name"]) == ["area-1", "area-0"]
    assert list(result.report["result_area_m2"]) == [100.0, 50.0]
    assert result.coverage_error_area == 0
    assert result.maximum_overlap_area == 0


def test_equal_priorities_keep_input_order_and_empty_is_valid():
    source = frame([box(0, 0, 10, 10), box(0, 0, 10, 10)], [1, 1])
    result = partition(source, "priority")
    assert list(result.geometries["name"]) == ["area-0", "area-1"]
    assert result.report.iloc[1]["empty"]


def test_invalid_geometry_and_geographic_crs_are_rejected():
    bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0), (0, 0)])
    invalid = frame([bowtie], [1])
    try:
        partition(invalid, "priority")
        raise AssertionError("invalid geometry was accepted")
    except ValueError as exc:
        assert "Invalid" in str(exc)
    geographic = frame([box(0, 0, 1, 1)], [1]).to_crs("EPSG:4326")
    try:
        partition(geographic, "priority")
        raise AssertionError("geographic CRS was accepted")
    except ValueError as exc:
        assert "projected" in str(exc)


def test_cli_writes_geopackage_and_report(tmp_path):
    source = tmp_path / "source.gpkg"
    output = tmp_path / "output.gpkg"
    report = tmp_path / "areas.csv"
    frame([box(0, 0, 10, 10), box(5, 0, 15, 10)], [1, 2]).to_file(
        source, layer="areas", driver="GPKG", index=False
    )
    assert main([
        "partition", str(source), "--layer", "areas", "--priority", "priority",
        "--output", str(output), "--report", str(report),
    ]) == 0
    written = gpd.read_file(output, layer="partitioned")
    assert len(written) == 2
    assert report.read_text(encoding="utf-8").startswith("source_index,priority")
