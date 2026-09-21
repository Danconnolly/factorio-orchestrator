# Factorio orchestrator

Experiment orchestration for player-constrained Factorio benchmarks.

This repository will use Inspect AI for model execution, evaluation logs, the viewer, repeated trials, and aggregate metrics. It will invoke `factorio-benchmark` as the authoritative single-attempt harness.

## Boundary

`factorio-benchmark` owns scenario fixtures, Factorio lifecycle, the constrained MCP broker, run bundles, and independent scoring. This repository must not gain evaluator RCON access or mutate benchmark fixtures.

The first vertical slice will run one Inspect task for `smelt-one-iron-plate`, link its Inspect log to the isolated benchmark run bundle, and score the attempt from the benchmark's evaluator result.

## Use

Install with `uv sync`. Configuration is explicit and portable; these paths
are examples, not defaults:

```json
{
  "model_id": "qwen3.8@sha256:REPLACE_WITH_RECORDED_DIGEST",
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

The model API key is runtime-only (for example `OPENAI_API_KEY`) and never
goes to benchmark artifacts. The in-process callback receives only the
benchmark prompt and loopback Streamable HTTP MCP configuration. It uses
`model="inspect"` with Inspect `agent_bridge` and only broker-discovered MCP
tools—never generic RCON or Lua tools.

Run the offline checks with:

```bash
uv run python -m unittest discover -s tests -v
uv build
```

After saving the JSON above as `orchestrator.json`, a live invocation is
explicit about its artifact name and model-secret environment variable:

```bash
OPENAI_API_KEY=... uv run python -m factorio_orchestrator --config orchestrator.json --run-name qwen-smelt-001
```

No live Qwen/Factorio run is claimed here. A live run requires the supplied
runtime paths and a recorded digest-qualified model identity.
