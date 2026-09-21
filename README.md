# Factorio orchestrator

Experiment orchestration for player-constrained Factorio benchmarks.

This repository will use Inspect AI for model execution, evaluation logs, the viewer, repeated trials, and aggregate metrics. It will invoke `factorio-benchmark` as the authoritative single-attempt harness.

## Boundary

`factorio-benchmark` owns scenario fixtures, Factorio lifecycle, the constrained MCP broker, run bundles, and independent scoring. This repository must not gain evaluator RCON access or mutate benchmark fixtures.

The first vertical slice will run one Inspect task for `smelt-one-iron-plate`, link its Inspect log to the isolated benchmark run bundle, and score the attempt from the benchmark's evaluator result.

## Use

Install the compatible `factorio-benchmark==0.1.2` and
`factorio-orchestrator==0.1.2` wheels together, or use `uv sync` from this
workspace. The orchestrator wheel is not a standalone artifact: its benchmark
wheel is required. Configuration is explicit and portable; these paths are
examples, not defaults:

```json
{
  "model_id": "qwen3.8@sha256:REPLACE_WITH_RECORDED_DIGEST",
  "inspect_model": "openai/qwen3.8",
  "model_base_url": "http://127.0.0.1:11434/v1",
  "runtime": {
    "factorio": "/opt/factorio/bin/x64/factorio",
    "control_python": "/opt/factorio-control/.venv/bin/python",
    "mod_archive": "/opt/factorio-player-mcp.zip",
    "client_template": "/opt/factorio-user-data",
    "runs_dir": "/var/tmp/factorio-runs"
  }
}
```

`model_id` is the digest-qualified, immutable model identity recorded in
benchmark task metadata. `inspect_model` is the explicit Inspect
model/provider ID used to execute the evaluation (for example,
`openai/qwen3.8`); it is deliberately not inferred from, nor used to replace,
`model_id`. Both fields are required, so older configuration files without
`inspect_model` fail closed rather than recording an ambiguous or unpinned run.
`model_base_url` is passed explicitly with `inspect_model` to Inspect, so the
callback's `model="inspect"` agent bridge uses that active model.

The model API key is runtime-only (for example `OPENAI_API_KEY`) and never
goes to benchmark artifacts. The in-process callback receives only the
benchmark prompt and loopback Streamable HTTP MCP configuration. It uses
`model="inspect"` with Inspect `agent_bridge` and only broker-discovered MCP
tools—never generic RCON or Lua tools.

The callback contract is asynchronous and cooperative-cancellation-aware. Its
scenario wall-clock timeout cancels and awaits the callback (including its MCP
client context) before the benchmark tears down the broker, client, and server;
timeout and callback-error outcomes are retained as unscored manifests.

Run the offline checks with:

```bash
uv lock --check
uv run python -m unittest discover -s tests -v
uv build
uv run python scripts/smoke_wheel_metadata.py ../factorio-benchmark/dist/factorio_benchmark-0.1.2-py3-none-any.whl dist/factorio_orchestrator-0.1.2-py3-none-any.whl
```

To refresh an existing development virtual environment after this paired
release, run:

```bash
uv sync
```

The wheel smoke test validates the exact sibling-wheel requirement, installs
both wheels with `--no-deps` into a fresh temporary virtual environment, and
executes the callback-session preflight seam from the installed benchmark
wheel. It proves that the broker, scenario, and baseline resolve from physical
package paths and that the external control Python receives the packaged broker
script path. Isolated mode and a temporary working directory ensure this cannot pass
by importing the benchmark source checkout. It is not a claim that a
network-free full dependency installation is possible.

Inspect 0.3.266's fake-eval smoke can leave AnyIO
`MemoryObjectReceiveStream` instances for third-party finalization. The smoke
tests explicitly collect them under a narrowly scoped filter for that exact
AnyIO `ResourceWarning`; no suite-wide warning setting is needed, and other
`ResourceWarning`s remain visible. To check the focused smoke tests with
warnings promoted to errors:

```bash
PYTHONWARNINGS='error::ResourceWarning' uv run python -m unittest discover -s tests -p 'test_inspect_smoke.py' -v
```

After saving the JSON above as `orchestrator.json`, a live invocation is
explicit about its artifact name and model-secret environment variable:

```bash
OPENAI_API_KEY=... uv run python -m factorio_orchestrator --config orchestrator.json --run-name qwen-smelt-001
```

No live Qwen/Factorio run is claimed here. A live run requires the supplied
runtime paths and a recorded digest-qualified model identity.
