"""Tests for ID generation."""

from __future__ import annotations

import pytest

from forge.core.ids import gen_id, PREFIXES


class TestGenId:
    """Tests for the gen_id function."""

    def test_generates_prefixed_id(self):
        """IDs should start with the correct prefix and underscore."""
        for entity, prefix in PREFIXES.items():
            id_str = gen_id(entity)
            assert id_str.startswith(f"{prefix}_"), f"Expected {prefix}_, got {id_str}"
            assert len(id_str) == len(prefix) + 1 + 8  # prefix_suffix(8)

    def test_generates_unique_ids(self):
        """Generated IDs should be unique."""
        ids = {gen_id("project") for _ in range(100)}
        assert len(ids) == 100

    def test_different_prefixes_produce_different_ids(self):
        """Different entity types should have different prefixes."""
        proj_id = gen_id("project")
        agent_id = gen_id("agent")
        ses_id = gen_id("session")
        assert proj_id.startswith("proj_")
        assert agent_id.startswith("agent_")
        assert ses_id.startswith("ses_")

    def test_accepts_custom_prefix(self):
        """gen_id should accept custom prefix strings."""
        custom_id = gen_id("custom")
        assert custom_id.startswith("custom_")

    def test_rejects_invalid_prefix(self):
        """gen_id should reject very short or very long prefixes."""
        with pytest.raises(ValueError):
            gen_id("x")
        with pytest.raises(ValueError):
            gen_id("a" * 20 + "longprefix")
