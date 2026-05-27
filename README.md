# Travel Assistant Agent (ADK Silverfin)

This project implements a sophisticated travel assistant using the Google Agent Development Kit (ADK) and Gemini 2.5 Flash. It features a multi-agent architecture with specialized agents for tourism and search, integrated user memory, and safety filters.

## Architecture

The system uses a **Root Agent** that orchestrates delegation to specialized agents:

- **Root Agent**: The main entry point. It manages user memory (visited cities) and decides which sub-agent to invoke.
- **Tourist Agent**: Specialized in visiting cities, tourism, travel recommendations, and weather.
- **Search Agent**: Specialized in general information retrieval using Google Search.

### Key Features

- **User Memory**: Persists user travel history (e.g., visited cities) across sessions using ADK memory callbacks.
- **PII Verification**: A safety callback that detects and blocks personal information (emails, phone numbers, SSNs) before it reaches the model.
- **Multi-Agent Delegation**: Uses `AgentTool` to seamlessly hand off tasks between specialized agents.

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- [google-agents-cli](https://pypi.org/project/google-agents-cli/) installed.
- Google Cloud project with Vertex AI API enabled.

### Installation

```bash
# Install dependencies
agents-cli install
```

### Running Locally

```bash
# Launch the interactive playground
agents-cli playground
```

## Testing and Evaluation

The project includes a robust testing and evaluation framework to ensure agent reliability and safety.

### Unit & Integration Tests

We use `pytest` for automated testing of core components.

- **Unit Tests** (`tests/unit/`):
    - `test_pii_callback.py`: Verifies that PII is correctly detected and blocked.
    - `test_memory_callbacks.py`: Ensures user memory is correctly initialized and saved.
- **Integration Tests** (`tests/integration/`):
    - `test_delegation.py`: Verifies that the Root Agent correctly delegates queries to the Tourist or Search agents.
    - `test_agent_runtime_app.py`: Tests the full application flow.

**Run tests:**
```bash
uv run pytest tests/unit tests/integration
```

### Evaluation (Latest Improvements)

We use `agents-cli eval` to perform data-driven evaluations of agent behavior. Evaluation sets are located in `tests/eval/evalsets/`.

**Run default evaluations:**
```bash
agents-cli eval run
```

**Run specific evaluation set:**
```bash
agents-cli eval run --evalset tests/eval/evalsets/travel.evalset.json
```

#### Evaluation Metrics

- **Tool Trajectory Score**: Measures if the agent calls the correct tools in the expected sequence.
- **Response Match Score**: Evaluates the quality and accuracy of the agent's final response against expected output.

#### Evaluation Sets

- `basic.evalset.json`: Core capability tests.
- `travel.evalset.json`: Scenarios specific to travel recommendations and city information.

## Deployment

The agent is designed to be deployed to **Agent Runtime** on Google Cloud.

```bash
# Deploy to dev environment (requires approval)
agents-cli deploy
```

For full CI/CD pipelines, use `agents-cli infra cicd`.
