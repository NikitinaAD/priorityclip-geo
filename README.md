# priorityclip-geo

[![CI](https://github.com/NikitinaAD/priorityclip-geo/actions/workflows/ci.yml/badge.svg)](https://github.com/NikitinaAD/priorityclip-geo/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/priorityclip-geo.svg)](https://pypi.org/project/priorityclip-geo/)
[![Python](https://img.shields.io/pypi/pyversions/priorityclip-geo.svg)](https://pypi.org/project/priorityclip-geo/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Turn overlapping polygons into a deterministic, priority-respecting partition.**

Overlapping administrative areas, work zones, or classification polygons cannot
always coexist in a final layer. `priorityclip` assigns every shared square metre
to exactly one source feature, preserves the total union, and writes an audit table
showing what was removed.

![Three overlapping polygons become a non-overlapping partition](https://raw.githubusercontent.com/NikitinaAD/priorityclip-geo/main/docs/demo.svg)

## Quick start

```bash
python -m pip install priorityclip-geo
priorityclip partition areas.gpkg \
  --layer candidates \
  --priority priority \
  --output partitioned.gpkg \
  --report areas.csv
```

Lower numeric values win. Equal values retain stable input order. Output rows are
written in the order in which they were processed.

## Reproducible example

The bundled example creates three synthetic polygons in EPSG:3857. No external
data is required.

```bash
python examples/make_example.py
priorityclip partition examples/overlap.geojson \
  --priority priority \
  --output examples/partitioned.gpkg \
  --report examples/areas.csv
```

Expected area audit:

| source row | priority | source m² | result m² | removed m² |
|---|---:|---:|---:|---:|
| 0 (`alpha`) | 1 | 100 | 100 | 0 |
| 1 (`beta`) | 2 | 100 | 60 | 40 |
| 2 (`gamma`) | 3 | 80 | 40 | 40 |

The result has zero pairwise overlap and the same 200 m² union as the input.

## Python API

```python
from priorityclip import PartitionResult, partition

result: PartitionResult = partition(frame, "priority")
result.geometries.to_file("partitioned.gpkg", layer="partitioned")
result.report.to_csv("areas.csv", index=False)
```

`partition(frame, priority, *, tolerance=None)` accepts a GeoDataFrame and the
name of a numeric priority column. `PartitionResult` exposes:

- `geometries`: attributes plus the non-overlapping output geometry;
- `report`: source index, priority, source/result/removed area, part count, and
  whether the result became empty;
- source and result union areas;
- maximum coverage error and pairwise overlap.

## Guarantees

- Lower numeric priority owns shared area.
- Equal priorities preserve source order.
- Source attributes and one output row per input row are retained.
- The output union matches the input union within a scale-aware tolerance.
- Pairwise result overlap remains below the same tolerance.
- CLI outputs are replaced atomically after successful processing.

## Limits

- Input geometries must be valid Polygon or MultiPolygon features.
- The CRS must be projected with horizontal units in metres.
- Invalid, missing, or empty input geometries are rejected rather than repaired.
- Repeated pairwise overlap validation is intended for small and medium datasets;
  very large layers may need spatial indexing in a future release.

Run `priorityclip --help` for all CLI options. Exit code `0` means success and `2`
means invalid input or a processing failure.

## Development

```bash
python -m pip install -e ".[test]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Copyright 2026 Alena Nikitina. Licensed under the [Apache License 2.0](https://github.com/NikitinaAD/priorityclip-geo/blob/main/LICENSE).
