import pytest
from unittest.mock import MagicMock
from google.adk.models import LlmRequest, LlmResponse
from google.adk.agents.callback_context import CallbackContext
from app.agent import pii_verification_callback
from google.genai import types

def test_pii_verification_callback_no_pii():
    callback_context = MagicMock(spec=CallbackContext)
    llm_request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="What is the weather in London?")]
            )
        ]
    )
    
    response = pii_verification_callback(callback_context, llm_request)
    assert response is None

def test_pii_verification_callback_with_email():
    callback_context = MagicMock(spec=CallbackContext)
    llm_request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="My email is test@example.com")]
            )
        ]
    )
    
    response = pii_verification_callback(callback_context, llm_request)
    assert isinstance(response, LlmResponse)
    assert "personal information (email)" in response.content.parts[0].text

def test_pii_verification_callback_with_phone():
    callback_context = MagicMock(spec=CallbackContext)
    llm_request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="Call me at 123-456-7890")]
            )
        ]
    )
    
    response = pii_verification_callback(callback_context, llm_request)
    assert isinstance(response, LlmResponse)
    assert "personal information (phone)" in response.content.parts[0].text

def test_pii_verification_callback_with_ssn():
    callback_context = MagicMock(spec=CallbackContext)
    llm_request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text="My SSN is 123-45-6789")]
            )
        ]
    )
    
    response = pii_verification_callback(callback_context, llm_request)
    assert isinstance(response, LlmResponse)
    assert "personal information (ssn)" in response.content.parts[0].text
