import asyncio
import json
import unittest
from unittest.mock import patch

import web_app


class FakeWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        self.sent.append(message)

    async def receive_text(self):
        if self.messages:
            return self.messages.pop(0)
        from fastapi import WebSocketDisconnect
        raise WebSocketDisconnect()

    async def close(self, **kwargs):
        self.sent.append({"type": "closed", **kwargs})


class WebAppTests(unittest.TestCase):
    def test_health_endpoint_does_not_expose_secrets(self):
        response = asyncio.run(web_app.health())
        self.assertEqual(response, {"status": "ok", "service": "studymate-web"})

    def test_readiness_reports_missing_provider_without_secret_values(self):
        with patch("agents.get_runtime_status", return_value={
            "configured": False,
            "providers": [],
            "groq_keys_loaded": 0,
            "openrouter_key_loaded": False,
        }):
            response = asyncio.run(web_app.readiness())
        self.assertEqual(response["status"], "not_ready")
        self.assertNotIn("key", json.dumps(response).lower())

    def test_readiness_reports_configured_provider_names_only(self):
        with patch("agents.get_runtime_status", return_value={
            "configured": True,
            "providers": ["groq"],
            "groq_keys_loaded": 2,
            "openrouter_key_loaded": False,
        }):
            response = asyncio.run(web_app.readiness())
        self.assertEqual(response, {
            "status": "ready",
            "service": "studymate-web",
            "providers": ["groq"],
        })

    def test_index_returns_html(self):
        response = asyncio.run(web_app.index())
        self.assertEqual(response.status_code, 200)
        self.assertIn("<html", response.body.decode("utf-8").lower())

    def test_websocket_sends_startup_and_rejects_invalid_json(self):
        websocket = FakeWebSocket(["not-json"])
        with patch.object(web_app, "_run_session", return_value=None):
            asyncio.run(web_app.websocket_endpoint(websocket))

        self.assertTrue(websocket.accepted)
        self.assertEqual(websocket.sent[0], {"type": "startup"})
        self.assertEqual(
            websocket.sent[1],
            {"type": "error", "text": "Invalid message format."},
        )

    def test_websocket_rejects_oversized_input(self):
        websocket = FakeWebSocket([
            json.dumps({"type": "input_response", "value": "x" * 4001}),
        ])
        with patch.object(web_app, "_run_session", return_value=None):
            asyncio.run(web_app.websocket_endpoint(websocket))
        self.assertEqual(websocket.sent[1], {
            "type": "error",
            "text": "Input is too long.",
        })

    def test_websocket_rejects_unsupported_message_type(self):
        websocket = FakeWebSocket([
            json.dumps({"type": "ping"}),
        ])
        with patch.object(web_app, "_run_session", return_value=None):
            asyncio.run(web_app.websocket_endpoint(websocket))
        self.assertEqual(websocket.sent[1], {
            "type": "error",
            "text": "Unsupported message type.",
        })

    def test_ui_patch_emits_structured_score_and_agent_events(self):
        class Context:
            closed = type("Closed", (), {"is_set": lambda self: False})()
            loop = asyncio.get_event_loop_policy().new_event_loop()
            ws = None

        messages = []
        context = Context()
        with patch.object(web_app, "_ws_send", side_effect=lambda ctx, msg: messages.append(msg)):
            import ui
            original_agent_output = ui.agent_output
            original_score_display = ui.score_display
            try:
                web_app._patch_ui(context)
                ui.agent_output("Examiner", "Question ready")
                ui.score_display(8, 10, "Mastery")
            finally:
                ui.agent_output = original_agent_output
                ui.score_display = original_score_display

        self.assertEqual(messages[0], {
            "type": "agent_output",
            "name": "Examiner",
            "lines": ["Question ready"],
        })
        self.assertEqual(messages[1]["type"], "score")
        self.assertEqual(messages[1]["pct"], 80)
