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


import os
import httpx
from mcp.server.fastmcp import FastMCP
from google.adk.agents import Agent
from google.adk.apps import App
from vertexai.agent_engines.templates.adk import AdkApp
from google.cloud import secretmanager

# Global cache for the API key
_WEATHER_API_KEY = None

def get_weather_api_key():
    """Retrieves the weather API key from environment or Secret Manager."""
    global _WEATHER_API_KEY
    if _WEATHER_API_KEY is not None:
        return _WEATHER_API_KEY

    # 1. Try environment variable first (Cloud Run secret mounting)
    _WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
    if _WEATHER_API_KEY:
        return _WEATHER_API_KEY

    # 2. Fallback to Secret Manager SDK
    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            # Fallback for local testing if project is not in env
            return None
            
        client = secretmanager.SecretManagerServiceClient()
        # Expecting a secret named 'weather-api-key'
        name = f"projects/{project_id}/secrets/weather-api-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        _WEATHER_API_KEY = response.payload.data.decode("UTF-8").strip()
        return _WEATHER_API_KEY
    except Exception as e:
        print(f"Warning: Could not retrieve 'weather-api-key' from Secret Manager: {e}")
        return None

# 1. Define tools for the ADK Agent
async def get_lat_lon(city: str):
    """Retrieves latitude and longitude for a city.
    
    Args:
        city: The name of the city.
    """
    api_key = get_weather_api_key()
    if not api_key:
        return {"error": "API key not configured."}

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={api_key}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            if data.get("status") == "OK" and data.get("results"):
                location = data["results"][0]["geometry"]["location"]
                return {"lat": float(location["lat"]), "lon": float(location["lng"])}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "City not found"}

async def get_current_weather_api(lat: float, lon: float):
    """Retrieves current weather from Google Weather API using coordinates.
    
    Args:
        lat: Latitude.
        lon: Longitude.
    """
    api_key = get_weather_api_key()
    if not api_key:
        return {"error": "Weather API key not configured. Please set WEATHER_API_KEY or create a 'weather-api-key' secret."}
        
    url = f"https://weather.googleapis.com/v1/currentConditions:lookup?key={api_key}&location.latitude={lat}&location.longitude={lon}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            return data
        except Exception as e:
            return {"error": str(e)}

# 2. Initialize the ADK Agent and AdkApp
weather_agent = Agent(
    name="WeatherSpecialist",
    model="gemini-2.5-flash",
    instruction="""
    You are a weather specialist. To answer a query about a city's weather:
    1. First, get the latitude and longitude of the city using 'get_lat_lon'.
    2. Then, use those coordinates to retrieve the current weather using 'get_current_weather_api'.
    3. Finally, present the weather information (Temperature, Condition, Humidity) in a clear Markdown table.
    """,
    tools=[get_lat_lon, get_current_weather_api]
)

weather_app = App(root_agent=weather_agent, name="WeatherApp")
app_executor = AdkApp(app=weather_app)

# 3. Create the MCP Server
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
mcp = FastMCP("Weather-Agent-MCP", transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))

@mcp.tool()
async def get_weather(city: str) -> str:
    """Retrieves the current weather for a specified city using an ADK agent."""
    prompt = f"What is the current weather in {city}?"
    
    user_id = "mcp-user"
    session = await app_executor.async_create_session(user_id=user_id)
    print(f"DEBUG: session type={type(session)}, session={session}")
    
    if hasattr(session, "id"):
        session_id = session.id
    elif isinstance(session, dict):
        session_id = session.get("id")
    else:
        session_id = str(session)
        
    response_text = ""
    async for event in app_executor.async_stream_query(
        user_id=user_id,
        session_id=session_id,
        message=prompt
    ):
        if isinstance(event, dict) and 'content' in event:
            content = event['content']
            if 'parts' in content:
                for part in content['parts']:
                    if 'text' in part:
                        response_text += part['text']
                        
    return response_text

# 4. Expose the MCP server as a Starlette app (compatible with FastAPI/Uvicorn)
app = mcp.sse_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)