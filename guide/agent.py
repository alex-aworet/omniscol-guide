import json
import sys
import asyncio
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

    async def ask(self, message: str, page_context: dict) -> dict:
        tool_list = await self.session.list_tools()
        ollama_tools = mcp_tools_to_ollama(tool_list.tools)

        # Build system context from page_context
        system_context = {
            "current_route": page_context.get("route"),
            "current_tab": page_context.get("active_tab"),
            "visible_sections": page_context.get("visible_sections", [])
        }
        
        # Get current tab details from route if available
        current_tab_details = None
        if system_context["current_route"]:
            try:
                current_tab_details = await self.session.call_tool("get_tab_by_route", {"route": system_context["current_route"]})
                current_tab_details = mcp_result_to_text(current_tab_details)
            except:
                pass

        system_prompt = (
            "You are an expert onboarding assistant for a school platform. You have complete knowledge of the platform structure through the site_map.json database.\n"
            "\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. You have access to complete platform data via search_ui() and other tools - USE IT IMMEDIATELY for any question\n"
            "2. Always provide DIRECT, CONFIDENT answers based on the site_map data\n"
            "3. NEVER express uncertainty about where the user is - the route is DEFINITIVE\n"
            "4. For ANY question about features/actions, IMMEDIATELY use search_ui() to find them\n"
            "\n"
            "ROUTE MATCHING LOGIC - ABSOLUTELY CRITICAL:\n"
            "The user's current route is: {system_context['current_route']}\n"
            "When you search for a feature:\n"
            "1. Get the search results with their routes\n"
            "2. COMPARE the result route with the current route EXACTLY\n"
            "3. If result_route == current_route:\n"
            "   → User IS ON THAT PAGE (100% CERTAIN)\n"
            "   → Answer ONLY with the action: 'Click the X button' or 'Look for X section'\n"
            "   → DO NOT provide navigation\n"
            "4. If result_route != current_route:\n"
            "   → User is on a DIFFERENT page (100% CERTAIN)\n"
            "   → State where they are clearly\n"
            "   → Then provide navigation: 'Go to Admin > Users > Teachers. Then click the Add button'\n"
            "\n"
            "TONE:\n"
            "- Be CERTAIN and CONFIDENT\n"
            "- State the user's current location if they need to navigate elsewhere\n"
            "- Use definitive language: 'Click', 'Look', 'Find', 'Go to'\n"
            "- Be clear and concise\n"
            "\n"
            f"Current Page Information:\n"
            f"- Route: {system_context['current_route']}\n"
            f"- Tab: {system_context['current_tab']}\n"
            f"- Visible Sections: {', '.join(system_context['visible_sections']) if system_context['visible_sections'] else 'None'}\n"
            f"{f'- Tab Details: {current_tab_details}' if current_tab_details else ''}\n"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "page_context": system_context,
                        "question": message
                    },
                    ensure_ascii=False
                ),
            },
        ]

        while True:
            response = await self.model.chat(messages=messages, tools=ollama_tools)
            assistant_message = response["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                return {
                    "answer": assistant_message.get("content", ""),
                }

            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                result = await self.session.call_tool(name, args)
                result_text = mcp_result_to_text(result)

                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result_text,
                })

    async def auto_summarize(self, page_context: dict) -> dict:
        """Automatically generate a summary of the current page using a silent system prompt."""
        try:
            # Use asyncio.wait_for to add a timeout of 10 seconds
            return await asyncio.wait_for(
                self._generate_summary(page_context),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            # If Ollama takes too long or isn't running, try mock mode
            return self._generate_mock_summary(page_context)
        except Exception as e:
            # Return a helpful error message or mock summary
            return self._generate_mock_summary(page_context)

    def _generate_mock_summary(self, page_context: dict) -> dict:
        """Generate a mock summary based on the route - useful for testing without Ollama."""
        route = page_context.get("route", "/")
        
        mock_summaries = {
            "/": "Welcome to the Omniscol platform! This is your dashboard where you can access all school management features. Browse the menu to explore different sections.",
            "/admin": "This is the Administration panel where you can manage system settings, users, and configurations. Select a specific section from the menu to get started.",
            "/admin/teachers": "The Teachers management section allows you to view all registered teachers, add new teachers to the system, and manage their information and roles.",
            "/admin/students": "Here you can manage all student records including enrollment, grades, and personal information. You can add new students or edit existing records.",
            "/schedules": "The Schedules section displays timetables and class schedules for the school. You can view lessons and manage scheduling here.",
            "/schedule/lessons": "View and manage all lessons scheduled for your classes. You can see lesson details and make schedule adjustments.",
            "/home": "Your personal home page with quick access to important information and recent activity on the platform.",
            "/guide": "The Guide Assistant is here to help you navigate the platform. Ask any questions about features or how to use the system.",
        }
        
        # Find the best matching route
        summary = None
        for route_key in sorted(mock_summaries.keys(), key=len, reverse=True):
            if route.startswith(route_key):
                summary = mock_summaries[route_key]
                break
        
        # Fallback to a generic summary
        if not summary:
            summary = f"You're on the {route or 'main'} page. This section provides access to related features and functions. Use the menu to navigate or ask for help."
        
        return {"summary": summary}


    async def _generate_summary(self, page_context: dict) -> dict:
        """Internal method to generate summary with full error propagation."""
        tool_list = await self.session.list_tools()
        ollama_tools = mcp_tools_to_ollama(tool_list.tools)

        # Build system context from page_context
        system_context = {
            "current_route": page_context.get("route"),
            "current_tab": page_context.get("active_tab"),
            "visible_sections": page_context.get("visible_sections", [])
        }
        
        # Get current tab details from route if available
        current_tab_details = None
        if system_context["current_route"]:
            try:
                current_tab_details = await self.session.call_tool("get_tab_by_route", {"route": system_context["current_route"]})
                current_tab_details = mcp_result_to_text(current_tab_details)
            except:
                pass

        # Silent system prompt for auto-summarization
        system_prompt = (
            "You are a brief, helpful onboarding assistant for a school platform. "
            "Generate a concise, natural summary of the current page the user is viewing.\n"
            "\n"
            f"Current Page: {system_context['current_route']}\n"
            f"Tab: {system_context['current_tab']}\n"
            f"Visible Sections: {', '.join(system_context['visible_sections']) if system_context['visible_sections'] else 'None'}\n"
            f"{f'Details: {current_tab_details}' if current_tab_details else ''}\n"
            "\n"
            "Provide a brief, 2-3 sentence summary of what this page is for and what the user can do here. "
            "Be conversational and helpful, not technical. Do not ask questions or wait for further input."
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": "Generate a summary of this page.",
            },
        ]

        while True:
            response = await self.model.chat(messages=messages, tools=ollama_tools)
            assistant_message = response["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                return {
                    "summary": assistant_message.get("content", ""),
                }

            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                result = await self.session.call_tool(name, args)
                result_text = mcp_result_to_text(result)

                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result_text,
                })