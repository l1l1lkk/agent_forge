"""Tests for the ClaudeParser — converts Claude stream-json to forge Events."""

from __future__ import annotations

import json

import pytest

from forge.core.events import Event
from forge.runtime.parsers.claude_parser import ClaudeParser

SESSION_ID = "ses_test123"


class TestClaudeParser:
    """Tests for Claude stream-json parsing."""

    def test_parse_system_init(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "system",
            "subtype": "init",
            "session_id": "abc",
            "model": "claude-sonnet-4-6",
            "cwd": "/tmp/project",
        })
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "session_started"
        assert event.session_id == SESSION_ID
        assert event.payload["model"] == "claude-sonnet-4-6"

    def test_parse_assistant_text(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello, I will help you."}
                ]
            }
        })
        event = parser.parse_line(line)
        assert event is not None
        # Should get the assistant_message event (last emitted)
        assert event.type == "assistant_message"

    def test_parse_assistant_tool_use(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "id": "tool_001",
                        "input": {"command": "ls"},
                    }
                ]
            }
        })
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "assistant_message"

    def test_parse_tool_result(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_001",
                        "content": "file1.py\nfile2.py",
                        "is_error": False,
                    }
                ]
            }
        })
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "tool_result"
        assert event.payload["tool_use_id"] == "tool_001"

    def test_parse_result_success(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "result",
            "subtype": "success",
            "result": "Task completed",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        })
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "session_status"
        assert event.payload["status"] == "completed"

    def test_parse_result_error(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({
            "type": "result",
            "subtype": "error",
            "errors": ["Something went wrong"],
        })
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "error"

    def test_parse_empty_line(self):
        parser = ClaudeParser(SESSION_ID)
        event = parser.parse_line("")
        assert event is None

    def test_parse_invalid_json(self):
        parser = ClaudeParser(SESSION_ID)
        event = parser.parse_line("not valid json {{{")
        assert event is None

    def test_parse_unknown_type(self):
        parser = ClaudeParser(SESSION_ID)
        line = json.dumps({"type": "some_future_event", "data": "value"})
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == "some_future_event"
        assert event.payload["raw"]["type"] == "some_future_event"

    def test_parse_lines(self):
        parser = ClaudeParser(SESSION_ID)
        lines = [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi"}]}}),
            json.dumps({"type": "result", "subtype": "success"}),
        ]
        events = parser.parse_lines(lines)
        assert len(events) >= 3  # system + text_delta + assistant_message + result
        assert events[0].type == "session_started"

    def test_sequence_numbers_increment(self):
        parser = ClaudeParser(SESSION_ID)
        lines = [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "A"}]}}),
            json.dumps({"type": "result", "subtype": "success"}),
        ]
        events = parser.parse_lines(lines)
        seqs = [e.seq for e in events]
        assert seqs == sorted(seqs), "Sequence numbers should be monotonic"
        assert len(set(seqs)) == len(seqs), "Sequence numbers should be unique"
