"""Create the synthetic dataset used in the README."""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


def main() -> None:
    output = Path(__file__).with_name("overlap.geojson")
    frame = gpd.GeoDataFrame(
        {
            "name": ["alpha", "beta", "gamma"],
            "priority": [1, 2, 3],
        },
        geometry=[box(0, 0, 10, 10), box(6, 0, 16, 10), box(3, 6, 13, 14)],
        crs="EPSG:3857",
    )
    frame.to_file(output, driver="GeoJSON", index=False)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
