import json
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from guide.providers.ollama_adapter import OllamaAdapter

def mcp_tools_to_ollama(tools) -> list[dict]:
    converted = []
    for tool in tools:
        converted.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema,
            },
        })
    return converted

def mcp_result_to_text(result) -> str:
    parts = []
    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)
        parts.append(text if text is not None else str(item))
    return "\n".join(parts)

class GuideAgent:
    def __init__(self, model: OllamaAdapter):
        self.model = model
        self.exit_stack = AsyncExitStack()
        self.session = None

    async def __aenter__(self):
        params = StdioServerParameters(
            command=sys.executable,
            args=["guide/mcp_server.py"],
            env=None,
        )
        read_stream, write_stream = await self.exit_stack.enter_async_context(stdio_client(params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.aclose()

    async def ask(self, message: str, current_tab: str | None) -> dict:
        tool_list = await self.session.list_tools()
        ollama_tools = mcp_tools_to_ollama(tool_list.tools)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an onboarding guide for Omniscol. "
                    "Use the tools to answer only from the provided UI map. "
                    "If a current_tab is provided, start from that tab. "
                    "Use get_tab_image when explaining a tab."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"current_tab": current_tab, "question": message},
                    ensure_ascii=False
                ),
            },
        ]

        image_url = None

        while True:
            response = await self.model.chat(messages=messages, tools=ollama_tools)
            assistant_message = response["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                return {
                    "answer": assistant_message.get("content", ""),
                    "image_url": image_url,
                }

            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                result = await self.session.call_tool(name, args)
                result_text = mcp_result_to_text(result)

                if name == "get_tab_image":
                    try:
                        payload = json.loads(result_text)
                        image_url = payload.get("image_url")
                    except Exception:
                        pass

                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result_text,
                })