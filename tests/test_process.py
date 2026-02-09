"""Unit tests for Gemini CLI process manager."""
import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from ai_cli_server.process import GeminiCLIProcess, CLIProcessError


@pytest.fixture
def mock_process():
    """Create a mock asyncio subprocess."""
    process = AsyncMock()
    process.stdin = Mock()
    process.stdin.write = Mock()
    process.stdin.drain = AsyncMock()
    process.stdout = AsyncMock()
    process.stdout.readline = AsyncMock(return_value=b"")
    process.stderr = AsyncMock()
    process.terminate = Mock()
    process.kill = Mock()
    process.wait = AsyncMock()
    process.returncode = None
    return process


class TestGeminiCLIProcessInit:
    """Test GeminiCLIProcess initialization."""

    def test_init_default_cli_path(self):
        """Should use default CLI path when not specified."""
        proc = GeminiCLIProcess()
        assert proc.cli_path.endswith("gemini-cli/bundle/gemini.js")

    def test_init_custom_cli_path(self):
        """Should use custom CLI path when specified."""
        custom_path = "/custom/path/gemini.js"
        proc = GeminiCLIProcess(cli_path=custom_path)
        assert proc.cli_path == custom_path

    def test_init_not_started(self):
        """Should not be started initially."""
        proc = GeminiCLIProcess()
        assert not proc.is_running


class TestGeminiCLIProcessStart:
    """Test starting the Gemini CLI process."""

    @pytest.mark.asyncio
    async def test_start_success(self, mock_process):
        """Should start process with correct arguments."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()

            assert proc.is_running
            assert proc._process is not None

    @pytest.mark.asyncio
    async def test_start_with_stream_json_flag(self, mock_process):
        """Should include --output-format stream-json flag."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            proc = GeminiCLIProcess()
            await proc.start()

            # Check that stream-json flag was passed
            args = mock_exec.call_args[0]
            assert "--output-format" in args
            assert "stream-json" in args

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(self, mock_process):
        """Should raise error if already running."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()

            with pytest.raises(CLIProcessError, match="already running"):
                await proc.start()

    @pytest.mark.asyncio
    async def test_start_cli_not_found_raises_error(self):
        """Should raise error if CLI executable not found."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            proc = GeminiCLIProcess(cli_path="/nonexistent/path")

            with pytest.raises(CLIProcessError, match="not found"):
                await proc.start()


class TestGeminiCLIProcessStop:
    """Test stopping the Gemini CLI process."""

    @pytest.mark.asyncio
    async def test_stop_running_process(self, mock_process):
        """Should terminate running process."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()
            await proc.stop()

            mock_process.terminate.assert_called_once()
            assert not proc.is_running

    @pytest.mark.asyncio
    async def test_stop_not_running_does_nothing(self):
        """Should do nothing if not running."""
        proc = GeminiCLIProcess()
        await proc.stop()  # Should not raise

    @pytest.mark.asyncio
    async def test_stop_waits_for_termination(self, mock_process):
        """Should wait for process to terminate."""
        mock_process.wait = AsyncMock()
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()
            await proc.stop(timeout=5)

            mock_process.wait.assert_called_once()


class TestGeminiCLIProcessSendPrompt:
    """Test sending prompts to the process."""

    @pytest.mark.asyncio
    async def test_send_prompt_success(self, mock_process):
        """Should write prompt to stdin."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()
            await proc.send_prompt("Hello, Gemini!")

            # Check that prompt was written to stdin
            mock_process.stdin.write.assert_called()
            written_data = mock_process.stdin.write.call_args[0][0]
            assert b"Hello, Gemini!" in written_data

    @pytest.mark.asyncio
    async def test_send_prompt_not_running_raises_error(self):
        """Should raise error if process not running."""
        proc = GeminiCLIProcess()

        with pytest.raises(CLIProcessError, match="not running"):
            await proc.send_prompt("Hello")


class TestGeminiCLIProcessRunPromptStream:
    """Test non-interactive per-request prompt execution."""

    @pytest.mark.asyncio
    async def test_run_prompt_stream_yields_events(self):
        """Should yield parsed JSON events from stream-json output."""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"{\"type\": \"message\", \"content\": \"Hi\"}\n",
                b"{\"type\": \"result\", \"stats\": {}}\n",
                b"",
            ]
        )
        mock_process.stderr.read = AsyncMock(return_value=b"")
        mock_process.wait = AsyncMock()
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            proc = GeminiCLIProcess(cli_path="/fake/gemini.js")
            events = []
            async for event in proc.run_prompt_stream("Hello"):
                events.append(event)

        assert len(events) == 2
        assert events[0]["type"] == "message"
        assert events[1]["type"] == "result"

        args = mock_exec.call_args[0]
        assert "-p" in args
        assert "Hello" in args
        assert "--output-format" in args
        assert "stream-json" in args

    @pytest.mark.asyncio
    async def test_run_prompt_stream_skips_invalid_json(self):
        """Should skip invalid JSON lines and keep parsing."""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"not-json\n",
                b"{\"type\": \"result\", \"stats\": {}}\n",
                b"",
            ]
        )
        mock_process.stderr.read = AsyncMock(return_value=b"")
        mock_process.wait = AsyncMock()
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess(cli_path="/fake/gemini.js")
            events = []
            async for event in proc.run_prompt_stream("Hello"):
                events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "result"

    @pytest.mark.asyncio
    async def test_run_prompt_stream_raises_on_nonzero_exit(self):
        """Should raise when process exits with non-zero status."""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(side_effect=[b""])
        mock_process.stderr.read = AsyncMock(return_value=b"boom")
        mock_process.wait = AsyncMock()
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess(cli_path="/fake/gemini.js")
            with pytest.raises(CLIProcessError, match="boom"):
                async for _ in proc.run_prompt_stream("Hello"):
                    pass


class TestGeminiCLIProcessReadEvents:
    """Test reading events from the process."""

    @pytest.mark.asyncio
    async def test_read_events_yields_parsed_json(self, mock_process):
        """Should yield parsed JSON events from stdout."""
        # Mock readline to return JSONL events
        events = [
            json.dumps({"type": "init", "session_id": "abc123"}),
            json.dumps({"type": "message", "content": "Hello"}),
            json.dumps({"type": "result", "response": "Done"}),
        ]
        mock_process.stdout.readline = AsyncMock(
            side_effect=[e.encode() + b"\n" for e in events] + [b""]
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()

            events_list = []
            async for event in proc.read_events():
                events_list.append(event)
                if event.get("type") == "result":
                    break

            assert len(events_list) == 3
            assert events_list[0]["type"] == "init"
            assert events_list[1]["type"] == "message"
            assert events_list[2]["type"] == "result"

    @pytest.mark.asyncio
    async def test_read_events_skips_invalid_json(self, mock_process):
        """Should skip lines that are not valid JSON."""
        lines = [
            json.dumps({"type": "init"}),
            "invalid json",
            json.dumps({"type": "result"}),
        ]
        mock_process.stdout.readline = AsyncMock(
            side_effect=[l.encode() + b"\n" for l in lines] + [b""]
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            proc = GeminiCLIProcess()
            await proc.start()

            events_list = []
            async for event in proc.read_events():
                events_list.append(event)
                if event.get("type") == "result":
                    break

            # Should only get valid JSON events
            assert len(events_list) == 2
            assert events_list[0]["type"] == "init"
            assert events_list[1]["type"] == "result"

    @pytest.mark.asyncio
    async def test_read_events_not_running_raises_error(self):
        """Should raise error if process not running."""
        proc = GeminiCLIProcess()

        with pytest.raises(CLIProcessError, match="not running"):
            async for _ in proc.read_events():
                pass


class TestGeminiCLIProcessContextManager:
    """Test using GeminiCLIProcess as async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops(self, mock_process):
        """Should start on enter and stop on exit."""
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            async with GeminiCLIProcess() as proc:
                assert proc.is_running

        # Should be stopped after exiting context
        mock_process.terminate.assert_called_once()
