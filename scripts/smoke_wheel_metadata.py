#!/usr/bin/env python3
"""Check that the paired release wheels install and execute together."""
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
    if (benchmark_metadata["Name"], benchmark_metadata["Version"]) != ("factorio-benchmark", "0.1.2"):
        raise SystemExit("benchmark wheel metadata is not factorio-benchmark 0.1.2")
    if (orchestrator_metadata["Name"], orchestrator_metadata["Version"]) != ("factorio-orchestrator", "0.1.3"):
        raise SystemExit("orchestrator wheel metadata is not factorio-orchestrator 0.1.3")
    requirements = [requirement.replace(" ", "") for requirement in orchestrator_metadata.get_all("Requires-Dist", [])]
    if "factorio-benchmark==0.1.2" not in requirements:
        raise SystemExit("orchestrator wheel must require factorio-benchmark ==0.1.2")
    with tempfile.TemporaryDirectory() as temporary_directory:
        environment = Path(temporary_directory) / "venv"
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run(["uv", "venv", str(environment)], check=True)
        subprocess.run(["uv", "pip", "install", "--python", str(python), "--no-deps",
                        str(benchmark), str(orchestrator)], check=True)
        subprocess.run([str(python), "-I", "-c", '''
import importlib.metadata
from pathlib import Path
import tempfile
from unittest.mock import patch

from factorio_benchmark.smelt_session import SmeltSessionRuntime, run_smelt_callback_session
from factorio_benchmark.assets import runtime_assets

assert importlib.metadata.version("factorio-benchmark") == "0.1.2"
assert importlib.metadata.version("factorio-orchestrator") == "0.1.3"
assert "site-packages" in Path(__import__("factorio_benchmark").__file__).parts
assets = runtime_assets()
assert all(path.is_file() for path in (assets.broker, assets.scenario, assets.baseline))
assert "site-packages/scripts" not in str(assets.broker)
async def callback(request):
    return {"answer": "done"}
calls = []
class Result:
    returncode = 0
    stdout = ""
    stderr = ""
def checked(command, **kwargs):
    calls.append(command)
    return Result()
with tempfile.TemporaryDirectory() as directory, patch(
    "factorio_benchmark.smelt_session.subprocess.run", side_effect=checked,
):
    result = run_smelt_callback_session(runtime=SmeltSessionRuntime(
        factorio=Path("/factorio/bin/x64/factorio"),
        control_python=Path("/control-venv/bin/python"),
        mod_archive=Path("/mods/factorio-player-mcp.zip"),
        client_template=Path("/client-template"), runs_dir=Path(directory),
        run_name="callback-run",
    ), model_id="test-model", callback=callback)
assert calls[0] == ["/control-venv/bin/python", str(assets.broker), "--check-runtime"]
assert result["terminal_status"] == "runner_failed"
'''], check=True, cwd=temporary_directory)
    print("wheel metadata and installed callback-session smoke passed")


if __name__ == "__main__":
    main()
