import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import root_agent

def test_delegation_to_tourist_agent():
    """Verify that a travel-related query is delegated to the tourist_agent."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="What is there to do in Tokyo?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    
    # Debug events
    for event in events:
        print(f"Event author: {event.author}")
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Text: {part.text[:50]}...")
                if part.function_call:
                    print(f"Function Call: {part.function_call.name}")
    
    # Check if tourist_agent was invoked
    tourist_agent_invoked = False
    for event in events:
        if event.author == "tourist_agent":
            tourist_agent_invoked = True
            break
        # Also check for function calls to tourist_agent
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "tourist_agent":
                    tourist_agent_invoked = True
                    break
    
    assert tourist_agent_invoked, "Expected delegation to tourist_agent"

def test_delegation_to_search_agent():
    """Verify that a general query is delegated to the search_agent."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Search for the latest news about AI.")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    
    # Check if search_agent was invoked
    search_agent_invoked = False
    for event in events:
        if event.author == "search_agent":
            search_agent_invoked = True
            break
        # Also check for function calls to search_agent
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "search_agent":
                    search_agent_invoked = True
                    break
    
    assert search_agent_invoked, "Expected delegation to search_agent"
