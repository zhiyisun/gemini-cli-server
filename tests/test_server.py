"""Unit tests for FastAPI SSE server."""
import pytest
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from gemini_cli_server.server import app


def _dummy_event_source_response(event_generator):
    """Create a minimal SSE StreamingResponse for tests."""

    async def stream():
        async for item in event_generator:
            event_name = item.get("event")
            if event_name:
                yield f"event: {event_name}\n".encode("utf-8")
            yield f"data: {item.get('data', '')}\n\n".encode("utf-8")

    return StreamingResponse(stream(), media_type="text/event-stream")


class _DummyProcess:
    """Dummy GeminiProcess for per-request tests."""

    def __init__(self, cli_path=None, events=None):
        self.cli_path = cli_path
        self.prompts = []
        self._events = events or [
            {"type": "message", "content": "Hello", "role": "assistant"},
            {"type": "result", "stats": {}},
        ]

    async def run_prompt_stream(self, prompt: str):
        self.prompts.append(prompt)
        for event in self._events:
            yield event


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok(self):
        """Should return OK status."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json().get("session_id") is None


class TestResetEndpoint:
    """Test the session reset endpoint."""

    def test_reset_is_noop(self):
        """Should return a no-op reset response."""
        client = TestClient(app)
        response = client.post("/reset")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "reset"
        assert "No persistent session" in payload["message"]


class TestChatEndpoint:
    """Test the chat SSE endpoint."""

    def test_chat_requires_prompt(self):
        """Should return 422 if prompt is missing."""
        client = TestClient(app)
        response = client.post("/chat", json={})
        
        assert response.status_code == 422

    def test_chat_streams_sse_events(self):
        """Should stream SSE events from Gemini CLI."""
        created = []

        def factory(cli_path=None):
            proc = _DummyProcess(cli_path=cli_path)
            created.append(proc)
            return proc

        with patch("gemini_cli_server.server.GeminiProcess", side_effect=factory), patch(
            "gemini_cli_server.server.EventSourceResponse",
            side_effect=_dummy_event_source_response,
        ):
            client = TestClient(app)

            response = client.post("/chat", json={"prompt": "Hello"})
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            assert "data:" in response.text

    def test_chat_resets_if_requested(self):
        """Should reset session if reset flag is true."""
        with patch(
            "gemini_cli_server.server.EventSourceResponse",
            side_effect=_dummy_event_source_response,
        ), patch("gemini_cli_server.server.GeminiProcess", side_effect=_DummyProcess):
            client = TestClient(app)

            response = client.post("/chat", json={"prompt": "Hello", "reset": True})
            assert response.status_code == 200

    def test_chat_sends_prompt_to_process(self):
        """Should send the prompt to Gemini process."""
        created = []

        def factory(cli_path=None):
            proc = _DummyProcess(cli_path=cli_path)
            created.append(proc)
            return proc

        with patch("gemini_cli_server.server.GeminiProcess", side_effect=factory), patch(
            "gemini_cli_server.server.EventSourceResponse",
            side_effect=_dummy_event_source_response,
        ):
            client = TestClient(app)

            response = client.post("/chat", json={"prompt": "Test prompt"})
            assert response.status_code == 200

        assert created
        assert created[0].prompts == ["Test prompt"]


class TestServerLifecycle:
    """Test server startup and shutdown."""

    @pytest.mark.asyncio
    async def test_startup_validates_cli_path(self, monkeypatch):
        """Should validate configured CLI path on startup."""
        monkeypatch.setenv("GEMINI_CLI_PATH", "/fake/gemini.js")
        with patch("os.path.exists", return_value=True):
            from gemini_cli_server import server
            await server.startup_event()

            assert server.cli_path == "/fake/gemini.js"

    @pytest.mark.asyncio
    async def test_shutdown_stops_process(self):
        """Should stop Gemini process on shutdown."""
        proc = AsyncMock()
        with patch("gemini_cli_server.server.gemini_process", proc):
            from gemini_cli_server.server import shutdown_event
            await shutdown_event()

            proc.stop.assert_called_once()
