# StudyMate AI

Adaptive certification preparation with eight cooperating AI agents, deterministic
mastery scoring, weak-topic remediation, and terminal or browser interfaces.

## Features

- Learner profiling and certification selection
- Knowledge assessment and personalized learning path
- Adaptive teaching and examination loop
- Mastery at **85% or higher with no weak skills**
- Report-card generation
- Optional official-source web search through SerpAPI
- Local versioned session persistence and recovery
- FastAPI/WebSocket browser UI

## Requirements

- Python 3.10+
- An API key for at least one model provider:
  - `GROQ_API_KEY`
  - `ROUTER_API_KEY` for OpenRouter
- Optional `SERPAPI_KEY` for web search

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
GROQ_API_KEY=your_groq_key
# ROUTER_API_KEY=your_openrouter_key
# SERPAPI_KEY=your_serpapi_key

STUDYMATE_SESSION_ID=unique-user-id
STUDYMATE_MAX_LEARNING_CYCLES=5
STUDYMATE_MODEL_TIMEOUT_SECONDS=45
STUDYMATE_MODEL_MAX_RETRIES=3
STUDYMATE_SEARCH_TIMEOUT_SECONDS=15
```

Never commit `.env` or API keys.

## Run

Terminal interface:

```bash
python main.py
```

Browser interface:

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>.

Operational endpoints:

- `GET /healthz` — process health
- `GET /readyz` — configured model-provider readiness
- `WS /ws` — browser session

Only one browser session is supported per process. Use separate processes or
deployments for concurrent users.

## Workflow

```text
Profiler -> Knowledge -> Learning Path -> Planner
-> Teaching -> Examiner -> Manager -> CEO -> Report Card
```

The adaptive cycle repeats:

```text
Teaching -> Examiner -> Manager -> CEO
```

It stops when mastery reaches 85% with no weak skills, or when
`STUDYMATE_MAX_LEARNING_CYCLES` is reached. The default is five cycles.

Sessions are stored as local, versioned JSON files. Set a unique
`STUDYMATE_SESSION_ID` for each user or deployment. Runtime session files are
ignored by Git.

## Testing

```bash
python -m unittest discover -s tests -q
```

The test suite covers workflow state, mastery scoring, agent handoffs,
provider/search failures, persistence and recovery, terminal rendering, and
FastAPI/WebSocket behavior.

## Project Structure

```text
agents.py              Model providers and agent implementations
tasks.py               Agent prompts and learner validation
workflow.py            Typed state, transitions, scoring, and orchestration
main.py                Terminal session runner and persistence
web_app.py             FastAPI/WebSocket wrapper
ui.py                  Terminal rendering
data/data.py           Synthetic learner and certification data
tools/web_search.py    Optional SerpAPI integration
templates/index.html   Browser UI
tests/                 Automated tests
requirements.txt       Runtime dependencies
```

## Deployment Notes

Configure secrets through the deployment environment, then start with:

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Check `/healthz` and `/readyz` before accepting traffic. Keep the previous
application version available for rollback. Do not copy session files or
secrets into logs, tickets, or public artifacts.

## Limitations

- AI model and search availability depends on external providers.
- Search is optional; unavailable search does not fabricate citations.
- The included learner and certification data is synthetic.
- This project is a learning platform prototype, not an official
  certification exam simulator.

## License

MIT. See [LICENSE](LICENSE).
