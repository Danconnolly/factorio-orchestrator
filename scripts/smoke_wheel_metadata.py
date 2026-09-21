#!/usr/bin/env python3
"""Check that the two compatible local wheels declare and install together."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from email.parser import Parser
from pathlib import Path


def metadata(path: Path):
    with zipfile.ZipFile(path) as wheel:
        name = next(entry for entry in wheel.namelist() if entry.endswith(".dist-info/METADATA"))
        return Parser().parsestr(wheel.read(name).decode("utf-8"))


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: smoke_wheel_metadata.py BENCHMARK_WHEEL ORCHESTRATOR_WHEEL")
    benchmark, orchestrator = (Path(argument).resolve() for argument in sys.argv[1:])
    for wheel in (benchmark, orchestrator):
        if not wheel.is_file():
            raise SystemExit(f"wheel not found: {wheel}")
    benchmark_metadata = metadata(benchmark)
    orchestrator_metadata = metadata(orchestrator)
    if (benchmark_metadata["Name"], benchmark_metadata["Version"]) != ("factorio-benchmark", "0.1.0"):
        raise SystemExit("benchmark wheel metadata is not factorio-benchmark 0.1.0")
    requirements = [requirement.replace(" ", "") for requirement in orchestrator_metadata.get_all("Requires-Dist", [])]
    if "factorio-benchmark==0.1.0" not in requirements:
        raise SystemExit("orchestrator wheel must require factorio-benchmark ==0.1.0")
    with tempfile.TemporaryDirectory() as target:
        subprocess.run(["uv", "pip", "install", "--no-deps", "--target", target,
                        str(benchmark), str(orchestrator)], check=True)
    print("wheel metadata and paired --no-deps installation smoke passed")


if __name__ == "__main__":
    main()
