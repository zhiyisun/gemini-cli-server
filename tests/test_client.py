"""Unit tests for Gemini CLI client."""
import pytest
from unittest.mock import Mock, patch
import httpx
from gemini_cli_server.client import (
    GeminiClient,
    GeminiClientError,
    OpenAICompatibleClient,
)


class TestGeminiClientInit:
    """Test GeminiClient initialization."""

    def test_init_with_base_url(self):
        """Should initialize with base URL."""
        client = GeminiClient("http://localhost:8000")
        assert client.base_url == "http://localhost:8000"

    def test_init_default_base_url(self):
        """Should use default base URL if not specified."""
        client = GeminiClient()
        assert client.base_url == "http://localhost:8000"


class TestGeminiClientChat:
    """Test chat method."""

    def test_chat_yields_events(self):
        """Should yield parsed events from SSE stream."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[
            "event: init",
            "data: {\"type\": \"init\", \"session_id\": \"abc\"}",
            "",
            "event: message",
            "data: {\"type\": \"message\", \"content\": \"Hello\"}",
            "",
            "event: result",
            "data: {\"type\": \"result\", \"response\": \"Done\"}",
            "",
        ])
        
        with patch("httpx.stream") as mock_stream:
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)
            client = GeminiClient()
            events = list(client.chat("Test prompt"))
            
            assert len(events) == 3
            assert events[0]["type"] == "init"
            assert events[1]["type"] == "message"
            assert events[2]["type"] == "result"

    def test_chat_sends_prompt_in_request(self):
        """Should send prompt in POST request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[
            "data: {\"type\": \"result\"}",
        ])
        
        with patch("httpx.stream") as mock_stream:
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)
            
            client = GeminiClient()
            list(client.chat("Test prompt"))
            
            # Check that POST was called with correct data
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            assert call_args[0][0] == "POST"
            assert "Test prompt" in str(call_args[1]["json"])

    def test_chat_with_reset_flag(self):
        """Should send reset flag when requested."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[
            "data: {\"type\": \"result\"}",
        ])
        
        with patch("httpx.stream") as mock_stream:
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)
            
            client = GeminiClient()
            list(client.chat("Test", reset=True))
            
            call_args = mock_stream.call_args
            json_data = call_args[1]["json"]
            assert json_data["reset"] is True

    def test_chat_raises_on_http_error(self):
        """Should raise error on non-200 status code."""
        with patch("httpx.stream") as mock_stream:
            mock_stream.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=500)
            )
            
            client = GeminiClient()
            
            with pytest.raises(GeminiClientError):
                list(client.chat("Test"))

    def test_chat_skips_non_data_lines(self):
        """Should skip lines that don't start with 'data: '."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[
            "event: message",
            "id: 123",
            "data: {\"type\": \"message\"}",
            "",
            ": comment",
            "data: {\"type\": \"result\"}",
        ])
        
        with patch("httpx.stream") as mock_stream:
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)
            client = GeminiClient()
            events = list(client.chat("Test"))
            
            # Should only get data events
            assert len(events) == 2

    def test_chat_handles_invalid_json_gracefully(self):
        """Should skip lines with invalid JSON."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines = Mock(return_value=[
            "data: not valid json",
            "data: {\"type\": \"result\"}",
        ])
        
        with patch("httpx.stream") as mock_stream:
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)
            client = GeminiClient()
            events = list(client.chat("Test"))
            
            # Should only get valid JSON event
            assert len(events) == 1
            assert events[0]["type"] == "result"


class TestGeminiClientReset:
    """Test reset method."""

    def test_reset_calls_reset_endpoint(self):
        """Should call the /reset endpoint."""
        with patch("httpx.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "reset",
                "message": "Session restarted"
            }
            
            client = GeminiClient()
            result = client.reset()
            
            mock_post.assert_called_once()
            assert "reset" in mock_post.call_args[0][0]
            assert result["status"] == "reset"

    def test_reset_raises_on_error(self):
        """Should raise error if reset fails."""
        with patch("httpx.post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=500)
            )
            
            client = GeminiClient()
            
            with pytest.raises(GeminiClientError):
                client.reset()


class TestGeminiClientHealth:
    """Test health check method."""

    def test_health_returns_status(self):
        """Should return health status from server."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "ok",
                "session_id": "abc123"
            }
            
            client = GeminiClient()
            health = client.health()
            
            assert health["status"] == "ok"
            assert health["session_id"] == "abc123"

    def test_health_raises_on_error(self):
        """Should raise error if health check fails."""
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=503)
            )
            
            client = GeminiClient()
            
            with pytest.raises(GeminiClientError):
                client.health()


class TestGeminiClientContextManager:
    """Test using client as context manager."""

    def test_context_manager_closes_client(self):
        """Should properly clean up resources."""
        with GeminiClient() as client:
            assert client is not None
        
        # Context manager should exit without error


class TestOpenAICompatibleClient:
    """Test OpenAI-compatible facade."""

    def test_chat_completions_non_stream(self):
        """Should return a chat completion response shape."""
        events = iter(
            [
                {"type": "message", "role": "assistant", "content": "Hello"},
                {"type": "result", "stats": {"input_tokens": 1, "output_tokens": 2}},
            ]
        )

        with patch.object(GeminiClient, "chat", return_value=events):
            client = OpenAICompatibleClient()
            response = client.chat.completions.create(messages=[{"role": "user", "content": "Hi"}])

        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["content"] == "Hello"
        assert response["usage"]["total_tokens"] == 3

    def test_chat_completions_stream(self):
        """Should stream chat completion chunks."""
        events = iter(
            [
                {"type": "message", "role": "assistant", "content": "Hi"},
                {"type": "result", "stats": {}},
            ]
        )

        with patch.object(GeminiClient, "chat", return_value=events):
            client = OpenAICompatibleClient()
            chunks = list(
                client.chat.completions.create(
                    messages=[{"role": "user", "content": "Hi"}],
                    stream=True,
                )
            )

        assert chunks[0]["object"] == "chat.completion.chunk"
        assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
