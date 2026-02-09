"""Python client for Gemini CLI Server."""
import json
import time
import uuid
from typing import Iterator, Optional, Dict, Any, Iterable, List

import httpx


class GeminiClientError(Exception):
    """Exception raised for client errors."""
    pass


class GeminiClient:
    """Client for interacting with Gemini CLI Server via HTTP SSE."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 300.0):
        """
        Initialize the Gemini client.

        Args:
            base_url: Base URL of the Gemini CLI server.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, prompt: str, reset: bool = False) -> Iterator[Dict[str, Any]]:
        """
        Send a prompt and stream responses via SSE.

        Args:
            prompt: The prompt to send.
            reset: Whether to reset the session before sending.

        Yields:
            Parsed event dictionaries from the SSE stream.

        Raises:
            GeminiClientError: If the request fails.

        Example:
            >>> client = GeminiClient()
            >>> for event in client.chat("Hello"):
            ...     print(event["type"], event.get("content", ""))
        """
        url = f"{self.base_url}/chat"
        payload = {"prompt": prompt, "reset": reset}

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Accept": "text/event-stream"},
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    # SSE format: "data: <json>\n"
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        try:
                            event = json.loads(data_str)
                            yield event
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue

        except httpx.HTTPStatusError as e:
            # For streaming responses, we can't read the body after consume
            status_info = f"HTTP {e.response.status_code}"
            if e.response.status_code == 503:
                detail = "Gemini CLI server is not available. Make sure the server is running."
            else:
                detail = str(e)
            raise GeminiClientError(f"{status_info}: {detail}")
        except httpx.RequestError as e:
            raise GeminiClientError(f"Request error: {e}")

    def reset(self) -> Dict[str, Any]:
        """
        Reset the session by restarting the Gemini CLI process.

        Returns:
            Response dictionary with reset status.

        Raises:
            GeminiClientError: If the reset fails.

        Example:
            >>> client = GeminiClient()
            >>> result = client.reset()
            >>> print(result["status"])
            reset
        """
        url = f"{self.base_url}/reset"

        try:
            response = httpx.post(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise GeminiClientError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise GeminiClientError(f"Request error: {e}")

    def health(self) -> Dict[str, Any]:
        """
        Check server health and get current session info.

        Returns:
            Health status dictionary.

        Raises:
            GeminiClientError: If the health check fails.

        Example:
            >>> client = GeminiClient()
            >>> health = client.health()
            >>> print(health["status"], health.get("session_id"))
        """
        url = f"{self.base_url}/health"

        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise GeminiClientError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise GeminiClientError(f"Request error: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


def _format_messages_as_prompt(messages: Iterable[Dict[str, Any]]) -> str:
    """Format OpenAI-style messages into a single prompt string."""
    lines: List[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines).strip()


def _extract_usage_from_result(result_event: Dict[str, Any]) -> Dict[str, int]:
    """Best-effort mapping of stats to OpenAI usage fields (handles both Gemini and Qwen)."""
    stats = result_event.get("stats", {})
    input_tokens = stats.get("input_tokens", 0)
    output_tokens = stats.get("output_tokens", 0)
    total_tokens = stats.get("total_tokens", input_tokens + output_tokens)
    return {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _extract_content_from_event(event: Dict[str, Any]) -> Optional[str]:
    """Extract content from event, handling both Gemini and Qwen formats."""
    # Gemini format: type="message", role="assistant", content field
    if event.get("type") == "message" and event.get("role") == "assistant":
        return event.get("content")
    # Qwen format: type="assistant", message.content
    elif event.get("type") == "assistant":
        if isinstance(event.get("message"), dict):
            msg_content = event.get("message", {}).get("content", [])
            if isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text")
    return None


class OpenAICompatibleClient:
    """OpenAI-compatible facade over the Gemini CLI server client."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 300.0):
        self._gemini = GeminiClient(base_url=base_url, timeout=timeout)
        self.chat = _Chat(self._gemini)


class _Chat:
    """OpenAI-compatible chat interface."""

    def __init__(self, gemini_client: GeminiClient):
        self.completions = _Completions(gemini_client)


class _Completions:
    """OpenAI-compatible completions interface."""

    def __init__(self, gemini_client: GeminiClient):
        self._gemini = gemini_client

    def create(
        self,
        *,
        messages: Iterable[Dict[str, Any]],
        model: str = "gemini",
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        prompt = _format_messages_as_prompt(messages)
        if stream:
            return self._stream(prompt=prompt, model=model)
        return self._non_stream(prompt=prompt, model=model)

    def _non_stream(self, prompt: str, model: str) -> Dict[str, Any]:
        content_parts: List[str] = []
        usage: Dict[str, int] = {}
        for event in self._gemini.chat(prompt):
            # Extract content from both Gemini and Qwen formats
            content = _extract_content_from_event(event)
            if content:
                content_parts.append(content)
            elif event.get("type") == "result":
                usage = _extract_usage_from_result(event)

        message_content = "".join(content_parts).strip()
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": message_content},
                    "finish_reason": "stop",
                }
            ],
            "usage": usage,
        }

    def _stream(self, prompt: str, model: str) -> Iterator[Dict[str, Any]]:
        stream_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())
        sent_role = False

        for event in self._gemini.chat(prompt):
            # Extract content from both Gemini and Qwen formats
            content = _extract_content_from_event(event)
            if content:
                delta: Dict[str, Any] = {"content": content}
                if not sent_role:
                    delta["role"] = "assistant"
                    sent_role = True

                yield {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                }

            if event.get("type") == "result":
                yield {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                break
