import pytest
from unittest.mock import MagicMock, AsyncMock
from google.adk.agents.callback_context import CallbackContext
from app.app_utils.memory import track_city_visit_callback, initialize_user_memory

@pytest.mark.asyncio
async def test_track_city_visit_callback():
    tool = MagicMock()
    tool.name = "get_weather"
    args = {"city": "Paris"}
    tool_context = MagicMock()
    tool_context.state = {}
    
    await track_city_visit_callback(tool, args, tool_context)
    
    assert tool_context.state["user:visited_cities"] == ["Paris"]

@pytest.mark.asyncio
async def test_track_city_visit_callback_existing():
    tool = MagicMock()
    tool.name = "get_weather"
    args = {"location": "london"}
    tool_context = MagicMock()
    tool_context.state = {"user:visited_cities": ["Paris"]}
    
    await track_city_visit_callback(tool, args, tool_context)
    
    assert "London" in tool_context.state["user:visited_cities"]
    assert "Paris" in tool_context.state["user:visited_cities"]

@pytest.mark.asyncio
async def test_initialize_user_memory():
    callback_context = MagicMock(spec=CallbackContext)
    callback_context.state = {}
    
    await initialize_user_memory(callback_context)
    
    assert callback_context.state["user:visited_cities"] == []
