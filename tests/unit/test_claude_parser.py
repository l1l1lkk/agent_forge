"""Tests for ClaudeParser — now returns list[Event] per parse_line."""

import json
import pytest
from forge.runtime.parsers.claude_parser import ClaudeParser

SID = "ses_test123"

def _first(line: str):
    """Parse and return the first event, or None."""
    events = ClaudeParser(SID).parse_line(line)
    return events[0] if events else None


class TestClaudeParser:
    def test_parse_system_init(self):
        line = json.dumps({"type":"system","subtype":"init","session_id":"abc","model":"claude-sonnet-4-6","cwd":"/tmp"})
        event = _first(line)
        assert event is not None
        assert event.type == "session_started"

    def test_parse_assistant_text(self):
        line = json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":"Hello"}]}})
        events = ClaudeParser(SID).parse_line(line)
        types = [e.type for e in events]
        assert "assistant_text_delta" in types
        assert "assistant_message" in types

    def test_parse_assistant_tool_use(self):
        line = json.dumps({"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","id":"t1","input":{"command":"ls"}}]}})
        events = ClaudeParser(SID).parse_line(line)
        types = [e.type for e in events]
        assert "tool_call_started" in types

    def test_parse_tool_result(self):
        parser = ClaudeParser(SID)
        line = json.dumps({"type":"user","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","content":"ok","is_error":False}]}})
        events = parser.parse_line(line)
        assert len(events) >= 1
        assert events[0].type == "tool_result"

    def test_parse_result_success(self):
        line = json.dumps({"type":"result","subtype":"success","result":"done","usage":{}})
        events = ClaudeParser(SID).parse_line(line)
        assert events[0].type == "session_status"
        assert events[0].payload["status"] == "completed"

    def test_parse_result_error(self):
        line = json.dumps({"type":"result","subtype":"error","errors":["fail"]})
        events = ClaudeParser(SID).parse_line(line)
        assert events[0].type == "error"

    def test_parse_empty_line(self):
        events = ClaudeParser(SID).parse_line("")
        assert events == []

    def test_parse_invalid_json(self):
        events = ClaudeParser(SID).parse_line("not json {{{")
        assert events == []

    def test_parse_unknown_type(self):
        line = json.dumps({"type":"future_event","data":"v"})
        events = ClaudeParser(SID).parse_line(line)
        assert len(events) == 1
        assert events[0].type == "future_event"

    def test_parse_lines(self):
        parser = ClaudeParser(SID)
        all_events = []
        for line in [
            json.dumps({"type":"system","subtype":"init"}),
            json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":"Hi"}]}}),
            json.dumps({"type":"result","subtype":"success"}),
        ]:
            all_events.extend(parser.parse_line(line))
        assert len(all_events) >= 4  # init + text_delta + assistant_message + result

    def test_sequence_numbers_increment(self):
        parser = ClaudeParser(SID)
        all_events = []
        for line in [
            json.dumps({"type":"system","subtype":"init"}),
            json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":"A"}]}}),
            json.dumps({"type":"result","subtype":"success"}),
        ]:
            all_events.extend(parser.parse_line(line))
        seqs = [e.seq for e in all_events]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == len(seqs)
