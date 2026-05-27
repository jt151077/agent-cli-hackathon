# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import Gemini
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams
from google.genai import types

from .app_utils.memory import track_city_visit_callback

WEATHER_AGENT_URL = "https://weather-agent-hef23kydta-uc.a.run.app"
WEATHER_SSE_URL = f"{WEATHER_AGENT_URL}/sse"


def get_id_token(url: str) -> str | None:
    """Gets an ID token for a given audience (URL)."""
    try:
        request = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(request, audience=url)
    except Exception:
        return None


def get_auth_headers(context: ReadonlyContext | None = None) -> dict[str, str]:
    """Callback for McpToolset to provide authentication headers."""
    token = get_id_token(WEATHER_AGENT_URL)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# Define the MCP toolset for weather
weather_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url=WEATHER_SSE_URL, timeout=300, sse_read_timeout=300
    ),
    header_provider=get_auth_headers,
)

tourist_agent = Agent(
    name="tourist_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    before_tool_callback=[track_city_visit_callback],
    instruction="""
      You are a tourist information expert. Provide interesting facts and places to visit for the given city.
      You MUST also provide the current weather for the city by calling the get_weather tool from your available tools.
      Include the weather information exactly as returned by the tool in your response.
      Keep the overall answer concise.
    """,
    tools=[weather_toolset],
)
