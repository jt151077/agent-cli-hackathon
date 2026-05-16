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
import google.auth
from typing import Optional
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import google_search
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse



_, project_id = google.auth.default()
# Handle specific environment issues where the default project lacks API access
if project_id == "cloudshell-gca":
    project_id = "jeremy-tus82cf1"

os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

from .tourist_agent import tourist_agent

def pii_verification_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Verifies that the request doesn't include any PII information."""
    # Simple regex for email and phone numbers
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"

    for content in llm_request.contents:
        for part in content.parts:
            if hasattr(part, 'text') and part.text:
                text = part.text
                if re.search(email_pattern, text) or re.search(phone_pattern, text):
                    return LlmResponse(
                        content={
                            "role": "model",
                            "parts": [{"text": "I'm sorry, but I cannot process requests containing personal information like email addresses or phone numbers for security reasons."}]
                        }
                    )
    return None

search_agent = Agent(
    name="search_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="You are a specialist in Google Search. Use the search tool to find information.",
    tools=[google_search],
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
      You are a helpful travel assistant.
      * For general information or web searches, use the search_agent.
      * For any questions about visiting cities, tourism, travel recommendations, or weather in a city, you MUST use the tourist_agent.
    """,
    tools=[AgentTool(search_agent), AgentTool(tourist_agent)],
    before_model_callback=[pii_verification_callback],
)

app = App(
    root_agent=root_agent,
    name="app",
)
