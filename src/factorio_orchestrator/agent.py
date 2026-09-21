"""In-process OpenAI-compatible agent restricted to benchmark MCP access."""
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping
from urllib.parse import urlparse

from factorio_benchmark.session import CallbackRequest
from inspect_ai.agent import agent_bridge
from inspect_ai.tool import ToolDef
from inspect_ai.tool._mcp import mcp_server_http, mcp_tools
from openai import AsyncOpenAI


@dataclass(frozen=True)
class OpenAICompatibleAgentConfig:
    base_url: str
    api_key: str
    max_turns: int = 12


def constrained_mcp_url(config: Mapping[str, Any]) -> str:
    servers = config.get("mcpServers")
    if not isinstance(servers, Mapping) or set(servers) != {"factorio"}:
        raise ValueError("agent requires exactly one factorio MCP server")
    server = servers["factorio"]
    if not isinstance(server, Mapping) or server.get("transport") != "streamable-http":
        raise ValueError("agent requires the streamable HTTP constrained MCP server")
    url = server.get("url")
    parsed = urlparse(url) if isinstance(url, str) else None
    if parsed is None or parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}:
        raise ValueError("agent MCP server must be loopback")
    return url


async def run_openai_agent(request: CallbackRequest, *, config: OpenAICompatibleAgentConfig,
                           client_factory: Callable[..., AsyncOpenAI] = AsyncOpenAI) -> dict[str, str]:
    """Call an OpenAI-compatible agent through Inspect's in-process bridge.

    The broker URL is validated before any client exists.  Tool definitions
    and calls come solely from that MCP server; no RCON/Lua tool is created.
    """
    constrained_mcp_url(request.mcp_config)
    if config.max_turns < 1:
        raise ValueError("max_turns must be positive")
    url = constrained_mcp_url(request.mcp_config)
    client = client_factory(api_key=config.api_key, base_url=config.base_url)
    server = mcp_server_http(name="factorio", url=url)
    available = await mcp_tools(server).tools()
    definitions = {ToolDef(tool).name: tool for tool in available}
    tools = [{"type": "function", "function": {
        "name": definition.name, "description": definition.description,
        "parameters": definition.parameters.model_dump(),
    }} for definition in map(ToolDef, available)]
    messages: list[dict[str, Any]] = [{"role": "user", "content": request.prompt}]
    async with agent_bridge(client_mcp_servers=False, web_search=False, code_execution=False):
        for _ in range(config.max_turns):
            completion = await client.chat.completions.create(model="inspect", messages=messages, tools=tools)
            message = completion.choices[0].message
            calls = message.tool_calls or []
            if not calls:
                return {"answer": message.content or ""}
            messages.append(message.model_dump(exclude_none=True))
            for call in calls:
                import json
                tool = definitions.get(call.function.name)
                if tool is None:
                    raise ValueError("model requested a tool outside the constrained MCP server")
                result = await tool(**json.loads(call.function.arguments))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
    return {"answer": "turn limit reached"}
