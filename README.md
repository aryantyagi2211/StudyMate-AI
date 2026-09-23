# 🧠 StudyMate AI - Reasoning Agents
### Multi-Step Reasoning AI That Personalizes Your Certification Prep Journey

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Groq](https://img.shields.io/badge/Powered%20by-Groq-black.svg)](https://groq.com)

> **StudyMate AI prototype**  
> 8 AI agents using multi-step reasoning and optional SerpAPI web search

**[Live Demo](#running-it-yourself)** • **[Documentation](#the-8-agents--what-each-one-does)** • **[Architecture](#multi-step-reasoning-architecture)**

---

## 🏆 Reasoning Agents Track Submission

**The Challenge:** Create intelligent agents that solve complex problems through multi-step reasoning

**Our Solution:** StudyMate AI - A multi-agent system with **28+ reasoning steps** that:
- ✅ Understands your learning style through deep questioning
- ✅ Assesses knowledge gaps intelligently  
- ✅ Teaches with adaptive strategies
- ✅ Creates personalized schedules
- ✅ Prioritizes configured official certification sources when web search is available
- ✅ Implements **adaptive feedback loop** until mastery is achieved

**Key Stats:**
- 🤖 **8 Specialized Agents** working in orchestrated collaboration
- 🔄 **Adaptive Loop System** - continues teaching until 85%+ mastery
- 🎯 **28+ Reasoning Steps** per complete learning journey
- 📚 **Source references** are retained when web search returns results
- ⚠️ **External search and model services are optional and can be unavailable**

**Not a chatbot. A reasoning engine.**

---

## The Real Problem We Solve

You've probably tried to prepare for a certification before. You paid for a course. You watched 40 hours of videos. You read documentation. And then you sat in the exam and blanked on the exact concepts you thought you understood.

**Why does this happen?**

Because most learning platforms treat every student the same. They give you the same content, the same schedule, and the same tests — regardless of what you already know, how busy your week is, or whether you actually understood what you just read.

StudyMate AI was built to fix this. Not with more content. With smarter agents that reason about *you*.

---

## What StudyMate AI Actually Does

Instead of a single AI model answering questions, StudyMate AI uses **8 specialized agents** that each have one job and do it well. They pass information to each other, reason about your performance, and adapt the entire learning journey based on what they find.

Here's the key thing that makes it different: **it loops.**

If you score below 70% on the exam, the system doesn't just show you your score and move on. The CEO Agent reads the Manager's report, identifies exactly which concepts you're weak on, sends you back to the Teaching Agent with a completely new explanation approach, then retests you. This loop runs until you hit 85%+.

That's not a feature. That's how actual learning works.

---

## The 8 Agents — What Each One Does

### 🧠 1. Profiler Agent
*"Let me understand who you are before we start"*

Before a single question is asked, the Profiler has a real conversation with you. Not a form. Not a dropdown. A conversation.

It finds out why you actually want this certification (your boss told you to? a promotion? genuine curiosity?), how you're feeling about starting, and what worries you most. This shapes how every other agent talks to you.

---

### 🔍 2. Knowledge Checker
*"What do you already know? Let's find out fast"*

10 diagnostic MCQs covering every skill area in your certification. Questions appear one at a time. After you answer all 10, it ranks every skill:

- **STRONG** → We'll skip this. No wasted time.
- **MEDIUM** → Quick reinforcement only.
- **WEAK** → This is where we focus.

---

### 📚 3. Learning Path Designer
*"Here's exactly what you need — nothing more"*

Takes your skill ranking and builds a focused resource list. For every weak area: the best Microsoft Learn module, a YouTube channel worth watching, a hands-on exercise you can actually do, and a realistic time estimate.

It skips what you're already strong at. Completely. No padding.

---

### 📅 4. Adaptive Planner
*"A schedule for your real life, not your ideal life"*

Asks you how many hours you can actually study per day, when your energy is highest, which days you'll skip, and if anything stressful is coming up. Then it builds a week-by-week plan around those answers — including a 10-minute emergency plan for the days when everything falls apart.

---

### 👨‍🏫 5. Teaching Agent
*"I'll explain this until it actually clicks"*

Takes your weakest skill and teaches it two ways: a plain-language explanation, and a real job scenario where this concept shows up in practice. Then it asks if it made sense.

If you say no — it doesn't repeat itself. It finds a completely different angle, a new analogy, a simpler breakdown. It only moves on when you say you understood.

---

### ✍️ 6. Examiner Agent
*"Let's see what you actually know"*

15 questions: 5 easy MCQs, 5 medium MCQs, 5 hard open-ended questions. Questions appear one at a time. After each MCQ you get instant feedback. After the open-ended questions you get a detailed comparison against the model answer.

Results are scored by difficulty level so the system knows exactly where your gaps are.

---

### 📊 7. Manager Insights Agent
*"Here's what the data actually says"*

Analyzes everything — exam scores by difficulty, which skills failed, your work signals (meeting load, energy level, upcoming stress). Writes a short, honest report for the CEO. Three sections: what went well, what needs attention, and what should happen next.

No fluff. The CEO needs to make a fast decision.

---

### 🎓 8. CEO Decision Maker
*"Ready to move on, or do you need more help?"*

Reads the Manager's report and makes the call:

```
Score 85%+  → "You're ready. Here's your next step."
Score 70-84% → "One more practice round on [specific skill]"
Score below 70% → "Back to teaching. Here's what we'll focus on."
```

This triggers the adaptive loop. The system keeps going until you're actually ready.

---

## The Adaptive Loop — Why This Matters

```
                            📋 INITIAL ASSESSMENT
                                      ↓
                         Profiler → Knowledge Checker
                                      ↓
                    Learning Path → Adaptive Study Plan
                                      ↓
                    ┌─────────────────────────────────┐
                    │     ADAPTIVE LOOP (CORE)        │
                    │                                 │
                    │  👨‍🏫 Teaching Agent              │
                    │         ↓                       │
                    │  ✍️ Examiner Agent              │
                    │         ↓                       │
                    │  📊 Manager Insights            │
                    │         ↓                       │
                    │  🎓 CEO Decision Maker          │
                    │         ↓                       │
                    │  ┌─────────────────┐           │
                    │  │ Score >= 85%?   │           │
                    │  └─────────────────┘           │
                    │    ↙            ↘              │
                    │  YES             NO             │
                    │   ↓              ↓              │
                    │  🎉            📝 Focus         │
                    │  Graduate      Weak Skills      │
                    │                 ↓               │
                    │                Loop Back ←──────┘
                    └─────────────────────────────────┘
```

### The Power of Looping:

Most learning systems are **linear** - you go through once and you're done, ready or not.

StudyMate AI is a **loop** - you stay in it until you're genuinely prepared:

1. **Initial Pass:** Teaching → Exam → Score 65%
2. **Loop 1:** Re-teach weak skills → Exam → Score 78%  
3. **Loop 2:** Final reinforcement → Exam → Score 87% ✅ **Graduate**

**Real student retention:** Studies show adaptive loops improve retention by 40%+ vs. linear learning.

---

## Knowledge Search

When `SERPAPI_KEY` is configured, agents can search the web for
certification-specific material. Queries prioritize known official domains such
as Microsoft Learn, AWS documentation, Google Cloud, Kubernetes, Cisco, and
other certification owners.

Search results are retained with generated knowledge and learning-path output.
If search is unavailable, the application does not create fake citations or
pretend that an unsupported knowledge integration is active.

---

## Multi-Step Reasoning Architecture

Each agent uses **4-step explicit reasoning** (visible in verbose mode):

```
STEP 1 - UNDERSTAND THE PROBLEM:
- What is the student asking?
- What context do I have about their level?

STEP 2 - ANALYZE THE SITUATION:
- What knowledge gaps exist?
- What learning style would work best?

STEP 3 - PLAN THE APPROACH:
- What's the best teaching strategy?
- Should I search for additional information?

STEP 4 - DECIDE & EXECUTE:
- Structure response
- Take action
- Verify understanding
```

### Why This Matters for Reasoning Agents Track:

- ✅ **28+ reasoning steps** per complete student journey
- ✅ **8 specialized agents** collaborating through reasoning
- ✅ **Adaptive reasoning** - agents adjust based on responses
- ✅ **Grounded reasoning** with retained source references when search is available
- ✅ **Visible reasoning** in verbose mode for demos

---

## Workflow and State Model

The application runs the following ordered stages:

`Profiler -> Knowledge -> Learning Path -> Planner -> Teaching -> Examiner -> Manager -> CEO -> Report Card`

The adaptive portion repeats `Teaching -> Examiner -> Manager -> CEO` until the
deterministic score reaches `85%` with no weak skills, or until the configured
maximum cycle count is reached. Workflow state, score, weak skills, sources,
and checkpoints are persisted in the versioned local session file.

---

## Saved Session Schema

StudyMate stores resumable progress in a session-namespaced JSON file. Set
`STUDYMATE_SESSION_ID` to a stable, unique value for each user or deployment;
the value is hashed into the filename so sessions cannot read or overwrite
each other's state. The current schema version is `1` and contains:

- `schema_version`: integer schema identifier
- `learner`: selected learner profile
- `cert`: selected certification data
- `memory`: workflow checkpoints, scores, sources, and agent outputs

The application validates the version and required top-level fields before
resuming a saved session. Schema migrations are intentionally separate from
normal session execution. Corrupted, outdated, or structurally invalid saved
state is reported and discarded so the learner can restart safely.

For a local single-user run, the default session file remains
`.studymate_session.json`. Concurrent users must provide different
`STUDYMATE_SESSION_ID` values.

Session and progress JSON files are local runtime data and are excluded from
version control. The application intentionally uses these small files instead
of adding a database, queue, or external persistence service.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq API (LLaMA 3.1 8B + LLaMA 3.3 70B) |
| Agent Framework | Custom SimpleAgent class with session management |
| Rate Limiting | Multi-key rotation + exponential backoff |
| Data | Synthetic student profiles (no real PII) |
| UI | Terminal UI and FastAPI/WebSocket browser UI |
| Language | Python 3.10+ |

---

## Why Groq Instead of Azure OpenAI

Azure OpenAI requires a paid subscription with credit card verification — which isn't available in all regions. Groq provides free-tier access to LLaMA models with the same OpenAI-compatible API, making this project accessible to anyone who wants to run it.

The agent architecture is model-agnostic. Swapping Groq for Azure OpenAI is a one-line change in `agents.py`.

---

## Running It Yourself

**Prerequisites:**
- Python 3.10+
- At least one model provider key: `GROQ_API_KEY` or `ROUTER_API_KEY`
- Optional `SERPAPI_KEY` for certification web search

**Setup:**

```bash
git clone https://github.com/aryantyagi2211/studymate-ai
cd studymate-ai

python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

**Create a `.env` file:**
```env
# At least one model provider is required
GROQ_API_KEY=your_groq_key
# Or use OpenRouter instead:
# ROUTER_API_KEY=your_openrouter_key

# Optional web search
SERPAPI_KEY=your_serpapi_key

# Optional per-user session isolation
STUDYMATE_SESSION_ID=unique-user-or-deployment-id

# Optional adaptive-loop limit; defaults to 5
STUDYMATE_MAX_LEARNING_CYCLES=5

# Optional bounded external-service settings
STUDYMATE_MODEL_TIMEOUT_SECONDS=45
STUDYMATE_MODEL_MAX_RETRIES=3
STUDYMATE_SEARCH_TIMEOUT_SECONDS=15
```

The default cost is bounded by at most five adaptive learning cycles, three
model attempts per call, and five search results per search request. Increase
these limits only when the provider budget and rate limits have been reviewed.

**Run:**
```bash
# Terminal version
python main.py

# Browser UI
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` for the browser UI. Run the test suite with:

```bash
python -m unittest discover -s tests -q
```

The web app exposes `GET /healthz` for process health and `GET /readyz` for
model-provider readiness. Readiness reports provider names and never returns
API keys or learner data.

Model calls and SerpAPI requests use bounded timeouts and retry counts. Invalid
provider configuration fails with an actionable startup/session error instead
of silently falling back.

The browser wrapper allows one active session per process. Use separate
processes or deployments for concurrent users.

### Minimal deployment and rollback

1. Build or install the pinned environment with `pip install -r requirements.txt`.
2. Configure secrets through the deployment environment, not source control.
3. Start the service with `uvicorn web_app:app --host 127.0.0.1 --port 8000`.
4. Verify `/healthz` and `/readyz` before accepting traffic.
5. Keep the previous application version available. To roll back, stop the
   current process, restore the previous code and dependency environment, and
   restart it with the same session ID configuration.

Runtime session files are local and excluded from version control. Back them up
only through the deployment's protected storage process; do not copy them into
logs, tickets, or public artifacts.

**Enable Verbose Mode** (see reasoning in action):
```python
# In agents.py, add:
teaching_agent.verbose = True
learning_path_agent.verbose = True

# You'll see:
# [MULTI-STEP REASONING]
# STEP 1 - UNDERSTAND THE PROBLEM: ...
# [SEARCH RESULTS]
# [RETAINED SOURCE REFERENCES]
```

---

## Project Structure

```
studymate-ai/
├── agents.py          # All 8 agent definitions with multi-step reasoning
├── tasks.py           # Task prompts for each agent
├── main.py            # Terminal orchestrator
├── web_app.py         # FastAPI/WebSocket browser wrapper
├── workflow.py        # Typed state, scoring, and orchestration rules
├── ui.py              # Terminal UI rendering helpers
├── tools/
│   ├── web_search.py        # Optional SerpAPI search
│   └── __init__.py
├── data/
│   └── data.py        # Synthetic learner + certification data
├── tests/             # Workflow, UI, recovery, and web tests
├── requirements.txt   # Runtime dependencies
├── .env               # Your API keys (not committed)
└── README.md          # This file
```

---

## Synthetic Data Notice

All student data used in this project is synthetic and created specifically for this demo. No real names, real emails, real employee records, or any PII was used. Learner IDs like `L-1001` and employee IDs like `EMP-001` are fictional identifiers.

---

## Security & Compliance

This project follows Microsoft Agents League security and compliance guidelines:

✅ **No Confidential Information** - All code and data are public-safe  
✅ **No Credentials in Code** - API keys stored in `.env` (gitignored)  
✅ **Synthetic Data Only** - No real PII or customer data  
✅ **Secret Scanning** - GitHub secret protection enabled  
✅ **Open Source License** - MIT License applied  
✅ **Security Best Practices** - Error handling, input validation, fallback mechanisms

**Security Reporting:** If you find a security issue, please report via GitHub Security Advisories rather than public issues.

---

## Current Limitations

- Model-provider availability depends on configured API keys and external
  service uptime.
- SerpAPI search is optional; when unavailable, the application does not
  fabricate citations or source records.
- The browser wrapper supports one active session per process because legacy
  agent modules still contain process-level state.
- Session persistence is lightweight local JSON, not a multi-node database.
- Generated content is checked for certification and skill alignment, but it is
  not an official exam or a substitute for the provider's current blueprint.
- Custom certifications receive generated skill categories when no built-in
  certification guide is available.

---

## Built By

**Aryan Tyagi** — [github.com/aryantyagi2211](https://github.com/aryantyagi2211)

*Microsoft Agents League Hackathon 2026 · Reasoning Agents Track*

---

## License

MIT License - feel free to use this project as a foundation for your own multi-agent systems.

---

## Acknowledgments

- **Groq** for lightning-fast LLM inference
- **Microsoft Learn** for comprehensive certification resources
- Built with passion for making certification prep smarter, not harder

---

> *"The best learning system isn't the one with the most content. It's the one that knows when to stop, when to loop back, and when you're actually ready."*

---

### ⭐ If this project helped you, consider giving it a star!

**Found a bug?** [Open an issue](https://github.com/aryantyagi2211/studymate-ai/issues)  
**Want to contribute?** [Submit a PR](https://github.com/aryantyagi2211/studymate-ai/pulls)  
**Questions?** Reach out via GitHub or email