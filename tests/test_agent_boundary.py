from contextlib import asynccontextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from factorio_benchmark.session import CallbackRequest
from factorio_orchestrator.agent import (
    OpenAICompatibleAgentConfig,
    constrained_mcp_url,
    run_openai_agent,
)


class AgentBoundaryTests(unittest.TestCase):
    def test_agent_accepts_only_one_loopback_factorio_mcp_server(self) -> None:
        config = {"mcpServers": {"factorio": {"transport": "streamable-http", "url": "http://127.0.0.1:38123/mcp"}}}
        self.assertEqual(constrained_mcp_url(config), "http://127.0.0.1:38123/mcp")
        with self.assertRaisesRegex(ValueError, "exactly"):
            constrained_mcp_url({"mcpServers": {}})
        with self.assertRaisesRegex(ValueError, "loopback"):
            constrained_mcp_url({"mcpServers": {"factorio": {"transport": "streamable-http", "url": "http://example.test/mcp"}}})


class MCPServerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_unentered_constrained_server_for_discovery_and_tool_result(self) -> None:
        async def smelt_plate(count: int) -> str:
            """Smelt the requested number of iron plates.

            Args:
                count: Number of plates to smelt.
            """
            self.assertEqual(count, 1)
            return "one iron plate"

        class ConfiguredServer:
            async def __aenter__(self):
                return EnteredSession()

            async def __aexit__(self, *args):
                return None

        class EnteredSession:
            pass

        server = ConfiguredServer()
        observed: dict[str, object] = {}

        class MCPSource:
            async def tools(self):
                observed["discovered"] = True
                return [smelt_plate]

        def fake_mcp_tools(received_server):
            self.assertIs(received_server, server)
            observed["server"] = received_server
            return MCPSource()

        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(name="smelt_plate", arguments='{"count": 1}'),
        )
        first_message = SimpleNamespace(
            tool_calls=[tool_call], content=None,
            model_dump=lambda **kwargs: {"role": "assistant", "tool_calls": []},
        )
        second_message = SimpleNamespace(tool_calls=[], content="done")
        completions = []

        async def create(**kwargs):
            completions.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=first_message if len(completions) == 1 else second_message)])

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

        @asynccontextmanager
        async def fake_bridge(**kwargs):
            self.assertEqual(kwargs, {"client_mcp_servers": False, "web_search": False, "code_execution": False})
            yield

        request = CallbackRequest(
            prompt="make one plate",
            mcp_config={"mcpServers": {"factorio": {"transport": "streamable-http", "url": "http://127.0.0.1:38123/mcp"}}},
        )
        with patch("factorio_orchestrator.agent.mcp_server_http", return_value=server), patch(
            "factorio_orchestrator.agent.mcp_tools", side_effect=fake_mcp_tools
        ), patch("factorio_orchestrator.agent.agent_bridge", fake_bridge):
            result = await run_openai_agent(
                request, config=OpenAICompatibleAgentConfig(base_url="http://model.test/v1", api_key="test"),
                client_factory=lambda **kwargs: client,
            )

        self.assertEqual(result, {"answer": "done"})
        self.assertTrue(observed["discovered"])
        self.assertIs(observed["server"], server)
        self.assertEqual(completions[1]["messages"][-1], {
            "role": "tool", "tool_call_id": "call-1", "content": "one iron plate",
        })
