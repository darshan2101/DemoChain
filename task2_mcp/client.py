"""MCP Client — wrapper that LLM agents use to invoke backend tools."""

from task2_mcp.server import call_tool, get_tool_definitions, TOOLS


class MCPClient:
    """Client interface for calling NOVA backend tools."""

    def __init__(self):
        self.available_tools = list(TOOLS.keys())

    def list_tools(self):
        """Return available tools and their descriptions."""
        return get_tool_definitions()

    def execute(self, tool_name, **kwargs):
        """Call a tool and return its result."""
        return call_tool(tool_name, **kwargs)

    def get_tools_for_llm(self):
        """Format tool definitions for LLM function-calling prompts."""
        lines = ["Available tools:"]
        for name, info in TOOLS.items():
            lines.append(f"\n- {name}: {info['description']}")
            for param, desc in info["parameters"].items():
                lines.append(f"  - {param}: {desc}")
        return "\n".join(lines)
