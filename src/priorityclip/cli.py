from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd

from . import __version__
from .core import partition


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="priorityclip",
        description="Create a deterministic, priority-respecting polygon partition.",
    )
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = root.add_subparsers(dest="command", required=True)
    command = commands.add_parser("partition")
    command.add_argument("input", type=Path)
    command.add_argument("--layer")
    command.add_argument("--priority", required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--output-layer", default="partitioned")
    command.add_argument("--report", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        frame = gpd.read_file(args.input, layer=args.layer)
        result = partition(frame, args.priority)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        driver = "GPKG" if args.output.suffix.lower() == ".gpkg" else "GeoJSON"
        temporary = args.output.with_name(args.output.stem + ".tmp" + args.output.suffix)
        if temporary.exists():
            temporary.unlink()
        write_args = {"driver": driver, "index": False}
        if driver == "GPKG":
            write_args["layer"] = args.output_layer
        result.geometries.to_file(temporary, **write_args)
        temporary.replace(args.output)
        report_tmp = args.report.with_suffix(args.report.suffix + ".tmp")
        result.report.to_csv(report_tmp, index=False)
        report_tmp.replace(args.report)
        print(
            f"Partitioned {len(frame)} polygons; coverage error "
            f"{result.coverage_error_area:.12g} m^2"
        )
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"priorityclip: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
