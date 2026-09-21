import unittest

from factorio_orchestrator.agent import constrained_mcp_url


class AgentBoundaryTests(unittest.TestCase):
    def test_agent_accepts_only_one_loopback_factorio_mcp_server(self) -> None:
        config = {"mcpServers": {"factorio": {"transport": "streamable-http", "url": "http://127.0.0.1:38123/mcp"}}}
        self.assertEqual(constrained_mcp_url(config), "http://127.0.0.1:38123/mcp")
        with self.assertRaisesRegex(ValueError, "exactly"):
            constrained_mcp_url({"mcpServers": {}})
        with self.assertRaisesRegex(ValueError, "loopback"):
            constrained_mcp_url({"mcpServers": {"factorio": {"transport": "streamable-http", "url": "http://example.test/mcp"}}})
