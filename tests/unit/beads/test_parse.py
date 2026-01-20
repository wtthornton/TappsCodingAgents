"""
Unit tests for tapps_agents.beads.parse: parse_bd_id_from_stdout.
"""

import pytest

from tapps_agents.beads.parse import parse_bd_id_from_stdout


@pytest.mark.unit
class TestParseBdIdFromStdout:
    def test_created_issue_line(self) -> None:
        assert parse_bd_id_from_stdout("Created issue: Proj-a1b2") == "Proj-a1b2"
        assert parse_bd_id_from_stdout("Created issue: Repo-xyz99") == "Repo-xyz99"

    def test_created_issue_with_unicode(self) -> None:
        assert parse_bd_id_from_stdout("Created issue: Proj-abc12") == "Proj-abc12"

    def test_multiline_prefers_created_line(self) -> None:
        out = "Some line\nCreated issue: X-yz1\nOther"
        assert parse_bd_id_from_stdout(out) == "X-yz1"

    def test_fallback_to_first_prefix_hash(self) -> None:
        assert parse_bd_id_from_stdout("No created here but Proj-a1b2c3") == "Proj-a1b2c3"

    def test_returns_none_when_empty(self) -> None:
        assert parse_bd_id_from_stdout("") is None
        assert parse_bd_id_from_stdout("  \n  ") is None

    def test_returns_none_when_no_match(self) -> None:
        assert parse_bd_id_from_stdout("Created issue: (no id)") is None
        assert parse_bd_id_from_stdout("nope") is None

    def test_min_suffix_length_3(self) -> None:
        assert parse_bd_id_from_stdout("Created issue: P-abc") == "P-abc"
        assert parse_bd_id_from_stdout("Created issue: P-ab") is None
