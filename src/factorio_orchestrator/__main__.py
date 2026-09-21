"""Command-line entry point for one explicit Inspect benchmark evaluation."""
import argparse
import json
import os
from pathlib import Path

from inspect_ai import eval

from factorio_benchmark.smelt_session import SmeltSessionRuntime

from .agent import OpenAICompatibleAgentConfig, run_openai_agent
from .config import OrchestrationConfig
from .task import smelt_one_iron_plate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    args = parser.parse_args()
    config = OrchestrationConfig.from_mapping(json.loads(args.config.read_text(encoding="utf-8")))
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        parser.error(f"{args.api_key_env} must name a non-empty model API key")
    runtime = SmeltSessionRuntime(**config.runtime.__dict__, run_name=args.run_name)
    agent_config = OpenAICompatibleAgentConfig(base_url=config.model_base_url, api_key=api_key)

    async def callback(request):
        return await run_openai_agent(request, config=agent_config)

    eval(
        smelt_one_iron_plate(runtime=runtime, model_id=config.model_id, callback=callback),
        model=config.inspect_model,
        model_base_url=config.model_base_url,
    )


if __name__ == "__main__":
    main()
