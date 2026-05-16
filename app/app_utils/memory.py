from typing import Any

from google.adk.agents.callback_context import CallbackContext


async def track_city_visit_callback(
    tool: Any, args: dict, tool_context: Any
) -> dict | None:
    """Stores the city name in user-persistent state when a weather tool is called."""
    # tool is a BaseTool object, use tool.name
    tool_name = getattr(tool, "name", "")
    if any(keyword in tool_name.lower() for keyword in ["weather", "get_weather"]):
        city = args.get("city") or args.get("location")
        if city:
            city = city.strip().title()
            # Use 'user:' prefix for cross-session persistence in Agent Engine
            visited = tool_context.state.get("user:visited_cities", [])
            if city not in visited:
                visited.append(city)
                tool_context.state["user:visited_cities"] = visited
    return None


async def initialize_user_memory(callback_context: CallbackContext) -> None:
    """Initializes the visited cities list if it doesn't exist."""
    if "user:visited_cities" not in callback_context.state:
        callback_context.state["user:visited_cities"] = []


async def save_to_memory_bank(callback_context: CallbackContext) -> None:
    """Sends the session's events to Memory Bank for semantic memory generation."""
    await callback_context.add_session_to_memory()
