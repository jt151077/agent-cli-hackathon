# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
from typing import Optional

import google.auth
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini, LlmRequest, LlmResponse
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .app_utils.memory import initialize_user_memory, save_to_memory_bank
from .app_utils.skills import get_ai_skills
from .tourist_agent import tourist_agent

_, project_id = google.auth.default()
# Handle specific environment issues where the default project lacks API access
if project_id == "cloudshell-gca":
    project_id = "jeremy-6584596x"

os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


def pii_verification_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Verifies that the request doesn't include any PII information."""
    # Simple regex for email, phone numbers, and Social Security Numbers
    pii_patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    for content in llm_request.contents:
        if content.parts:
            for part in content.parts:
                if hasattr(part, "text") and part.text:
                    text = part.text
                    for pii_type, pattern in pii_patterns.items():
                        if re.search(pattern, text):
                            return LlmResponse(
                                content={
                                    "role": "model",
                                    "parts": [
                                        {
                                            "text": (
                                                "Good day. I hope this message finds you well. "
                                                f"I must politely inform you that I am unable to process requests containing personal information ({pii_type}) for security and privacy reasons. "
                                                "Please let me know if there is anything else I can assist you with to ensure your travel planning remains a pleasure."
                                            )
                                        }
                                    ],
                                }
                            )
    return None


# Initialize dynamic skills
ai_skills = get_ai_skills()

search_agent = Agent(
    name="search_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
      You are a distinguished research assistant for a high-end concierge. 
      Your goal is to provide precise and professional information.
      Always maintain a polite and formal tone.
      Use the search tool to find accurate answers.
    """,
    tools=[GoogleSearchTool()],
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
      You are a distinguished travel coordinator and head concierge. Your goal is to provide a seamless and professional experience.
      
      User Travel History: {user:visited_cities}
      
      CRITICAL RULES:
      * At the start of a new conversation, you MUST begin with a warm, professional greeting (e.g., \"Good day,\" \"It is a pleasure to assist you\"). For subsequent interactions in the same conversation, use a polite but concise acknowledgment instead of a full formal greeting.
      * If the user's travel history is NOT empty, you MUST elegantly remind them of the cities they've visited in your response.
      * For general information or web searches, use the search_agent.
      * For any questions about visiting cities, tourism, travel recommendations, or weather in a city, you MUST use the tourist_agent.
      * When relaying information from a sub-agent, ALWAYS ensure the final output is a cohesive, professional concierge response that includes an appropriate greeting (consistent with the conversation state) and a professional closing.
      * Always conclude with a professional and helpful closing, offering further assistance (e.g., \"Should you require any further recommendations, I remain at your service\").
    """,
    tools=[
        AgentTool(search_agent), 
        AgentTool(tourist_agent), 
        PreloadMemoryTool(),
        ai_skills
    ],
    before_agent_callback=[initialize_user_memory],
    after_agent_callback=[save_to_memory_bank],
    before_model_callback=[pii_verification_callback],
)

app = App(
    root_agent=root_agent,
    name="app",
)
