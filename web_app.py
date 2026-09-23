"""
web_app.py — FastAPI web wrapper for StudyMate AI
Launches the same study session in a browser with terminal-style UI.
"""

import asyncio
import json
import logging
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# Pre-warm imports so the session thread starts fast
_ = __import__("agents")
_ = __import__("tasks")

app = FastAPI()
logger = logging.getLogger("studymate.web")

# The CLI session currently uses module-level state in main/tasks/ui. Keep one
# active session per process until those modules are converted to session scope.
session_lock = threading.Lock()


@dataclass
class SessionContext:
    ws: WebSocket
    loop: asyncio.AbstractEventLoop
    input_queue: list[str] = field(default_factory=list)
    input_event: threading.Event = field(default_factory=threading.Event)
    closed: threading.Event = field(default_factory=threading.Event)

HTML_PATH = Path(__file__).parent / "templates" / "index.html"


def _ws_send(context, msg):
    """Fire-and-forget WebSocket send — never blocks the session thread."""
    if context.closed.is_set():
        return
    try:
        asyncio.run_coroutine_threadsafe(context.ws.send_json(msg), context.loop)
    except RuntimeError:
        context.closed.set()


def _patch_ui(context):
    """Replace ui.* functions to send output via WebSocket."""
    import ui

    def _agent_output(name, text, width=58):
        lines = text.split("\n")
        _ws_send(context, {"type": "agent_output", "name": name, "lines": lines})

    def _display_question(q_num, skill, question, options):
        _ws_send(context, {"type": "question", "q_num": q_num, "skill": skill,
                           "question": question, "options": options})

    def _display_learning_path(text):
        _ws_send(context, {"type": "learning_path", "text": text})

    def _score_display(correct, total, label="Score"):
        pct = int((correct / total) * 100) if total > 0 else 0
        _ws_send(context, {"type": "score", "correct": correct, "total": total,
                           "label": label, "pct": pct})

    def _input_prompt(text):
        _ws_send(context, {"type": "input", "prompt": text})
        context.input_event.clear()
        while not context.closed.is_set():
            if context.input_event.wait(timeout=0.5):
                return context.input_queue.pop(0)
        raise RuntimeError("Browser session disconnected while waiting for input")

    async def _start_loader(message):
        _ws_send(context, {"type": "loader", "message": message})
        stop = asyncio.Event()
        task = asyncio.create_task(asyncio.sleep(0))
        return task, stop

    # Apply patches — send directly to WS instead of queue
    ui.header = lambda title, width=60: _ws_send(context, {"type": "header", "title": title})
    ui.section = lambda title: _ws_send(context, {"type": "section", "title": title})
    ui.agent_output = _agent_output
    ui.result_box = lambda text, width=58: _ws_send(context, {"type": "result_box", "text": text})
    ui.info = lambda text: _ws_send(context, {"type": "info", "text": text})
    ui.ok = lambda text: _ws_send(context, {"type": "ok", "text": text})
    ui.warn = lambda text: _ws_send(context, {"type": "warn", "text": text})
    ui.fail = lambda text: _ws_send(context, {"type": "fail", "text": text})
    ui.input_prompt = _input_prompt
    ui.option_list = lambda opts: _ws_send(context, {"type": "option_list", "options": opts})
    ui.separator = lambda char="═", color=None: _ws_send(context, {"type": "separator"})
    ui.score_display = _score_display
    ui.display_question = _display_question
    ui.display_learning_path = _display_learning_path
    ui.teaching_options = lambda: _ws_send(context, {"type": "teaching_options"})
    ui.progress_bar = lambda value, total, width=20, color=None: ""
    ui.start_loader = _start_loader


def _track_profile(context):
    """Watch for profile data changes and send updates."""
    import tasks
    prev = ""
    while True:
        try:
            if tasks.LEARNER and tasks.LEARNER.get("name"):
                cur = f"{tasks.LEARNER['name']}|{tasks.LEARNER.get('role','')}|{tasks.LEARNER.get('certification','')}"
                if cur != prev:
                    prev = cur
                    _ws_send(context, {"type": "profile", "name": tasks.LEARNER["name"],
                                       "role": tasks.LEARNER.get("role", ""),
                                       "cert": tasks.LEARNER.get("certification", "")})
            import time
            time.sleep(1)
        except Exception:
            break


def _run_session(context):
    """Run study session in a background thread."""
    sys.path.insert(0, str(Path(__file__).parent))
    import main
    tracker = threading.Thread(target=_track_profile, args=(context,), daemon=True)
    tracker.start()
    try:
        asyncio.run(main.run_studymate())
    except SystemExit:
        pass
    except Exception as e:
        _ws_send(context, {"type": "error", "text": str(e)})
    finally:
        _ws_send(context, {"type": "session_end"})
        context.closed.set()


@app.get("/")
async def index():
    if not HTML_PATH.exists():
        logger.error("Web UI template is missing")
        return HTMLResponse("<h1>templates/index.html not found</h1>", status_code=500)
    html = HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/healthz")
async def health():
    """Return process health without exposing configuration or user data."""
    return {"status": "ok", "service": "studymate-web"}


@app.get("/readyz")
async def readiness():
    """Report whether an AI provider is configured for a new session."""
    import agents

    status = agents.get_runtime_status()
    if not status["configured"]:
        logger.warning("Readiness check failed: no model provider configured")
        return {
            "status": "not_ready",
            "service": "studymate-web",
            "reason": "No AI provider configured",
        }
    logger.info("Readiness check passed for configured providers")
    return {
        "status": "ready",
        "service": "studymate-web",
        "providers": status["providers"],
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if not session_lock.acquire(blocking=False):
        logger.warning("WebSocket session rejected because another session is active")
        await ws.close(code=1013, reason="Another StudyMate session is already active")
        return

    await ws.accept()
    logger.info("WebSocket session accepted")
    context = SessionContext(ws=ws, loop=asyncio.get_running_loop())

    # Send immediate startup signal
    await ws.send_json({"type": "startup"})

    _patch_ui(context)
    session_thread = threading.Thread(target=_run_session, args=(context,), daemon=True)
    session_thread.start()

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("WebSocket client sent invalid JSON")
                await ws.send_json({"type": "error", "text": "Invalid message format."})
                continue
            if not isinstance(msg, dict) or msg.get("type") != "input_response":
                await ws.send_json({"type": "error", "text": "Unsupported message type."})
                continue
            value = msg.get("value", "")
            if not isinstance(value, str):
                await ws.send_json({"type": "error", "text": "Input value must be text."})
                continue
            if len(value) > 4000:
                logger.warning("WebSocket input rejected because it exceeded the size limit")
                await ws.send_json({"type": "error", "text": "Input is too long."})
                continue
            context.input_queue.append(value)
            context.input_event.set()
    except WebSocketDisconnect:
        logger.info("WebSocket session disconnected")
        context.closed.set()
        context.input_event.set()
    finally:
        if session_lock.locked():
            session_lock.release()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
