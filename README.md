# Factorio orchestrator

Experiment orchestration for player-constrained Factorio benchmarks.

This repository will use Inspect AI for model execution, evaluation logs, the viewer, repeated trials, and aggregate metrics. It will invoke `factorio-benchmark` as the authoritative single-attempt harness.

## Boundary

`factorio-benchmark` owns scenario fixtures, Factorio lifecycle, the constrained MCP broker, run bundles, and independent scoring. This repository must not gain evaluator RCON access or mutate benchmark fixtures.

The first vertical slice will run one Inspect task for `smelt-one-iron-plate`, link its Inspect log to the isolated benchmark run bundle, and score the attempt from the benchmark's evaluator result.

## Status

Repository initialized. No Inspect task or model configuration has been added yet.
