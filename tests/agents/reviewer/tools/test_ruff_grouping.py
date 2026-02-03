"""
Tests for RuffGroupingParser - ENH-002-S3.
"""

import json
import pytest

from tapps_agents.agents.reviewer.tools.ruff_grouping import (
    GroupedRuffIssues,
    RuffGroupingConfig,
    RuffGroupingParser,
    RuffIssue,
    RuffParsingError,
)

pytestmark = pytest.mark.unit


def _ruff_diagnostic(code: str, message: str, row: int = 1, column: int = 1, fixable: bool = False):
    return {
        "code": {"name": code, "severity": "error" if code.startswith(("E", "F")) else "warning"},
        "message": message,
        "location": {"row": row, "column": column},
        "fix": {"applicability": "safe"} if fixable else None,
    }


class TestRuffGroupingParserParseAndGroup:
    def test_empty_json_returns_empty_groups(self):
        parser = RuffGroupingParser()
        result = parser.parse_and_group("[]")
        assert result.total_issues == 0
        assert result.unique_codes == 0
        assert result.groups == {}
        assert result.fixable_count == 0

    def test_groups_by_code(self):
        parser = RuffGroupingParser()
        data = [
            _ruff_diagnostic("F401", "unused import", 1, 1, fixable=True),
            _ruff_diagnostic("F401", "unused import", 2, 1, fixable=True),
            _ruff_diagnostic("E501", "line too long", 10, 1),
        ]
        result = parser.parse_and_group(json.dumps(data))
        assert result.total_issues == 3
        assert result.unique_codes == 2
        assert "F401" in result.groups
        assert "E501" in result.groups
        assert len(result.groups["F401"]) == 2
        assert len(result.groups["E501"]) == 1
        assert result.fixable_count == 2

    def test_invalid_json_raises(self):
        parser = RuffGroupingParser()
        with pytest.raises(RuffParsingError):
            parser.parse_and_group("not json")
        with pytest.raises(RuffParsingError):
            parser.parse_and_group("{}")

    def test_severity_summary(self):
        parser = RuffGroupingParser()
        data = [
            _ruff_diagnostic("F401", "a"),
            _ruff_diagnostic("E501", "b"),
            _ruff_diagnostic("W291", "c"),
        ]
        result = parser.parse_and_group(json.dumps(data))
        assert result.severity_summary
        assert result.total_issues == 3


class TestRuffGroupingParserSortGroups:
    def test_sort_by_severity_errors_first(self):
        parser = RuffGroupingParser()
        groups = {
            "W291": (RuffIssue("W291", "w", 1, 1, "warning", False),),
            "F401": (RuffIssue("F401", "e", 1, 1, "error", False),),
        }
        sorted_pairs = parser.sort_groups(groups, by="severity")
        assert sorted_pairs[0][0] == "F401"
        assert sorted_pairs[1][0] == "W291"

    def test_sort_by_count_descending(self):
        parser = RuffGroupingParser()
        groups = {
            "A": (RuffIssue("A", "a", 1, 1, "error", False),),
            "B": (
                RuffIssue("B", "b1", 1, 1, "error", False),
                RuffIssue("B", "b2", 2, 1, "error", False),
            ),
        }
        sorted_pairs = parser.sort_groups(groups, by="count")
        assert sorted_pairs[0][0] == "B"
        assert sorted_pairs[1][0] == "A"

    def test_sort_by_code_alphabetical(self):
        parser = RuffGroupingParser()
        groups = {
            "Z99": (RuffIssue("Z99", "z", 1, 1, "error", False),),
            "A01": (RuffIssue("A01", "a", 1, 1, "error", False),),
        }
        sorted_pairs = parser.sort_groups(groups, by="code")
        assert sorted_pairs[0][0] == "A01"
        assert sorted_pairs[1][0] == "Z99"


class TestRuffGroupingParserRenderGrouped:
    def test_render_markdown_contains_headers(self):
        parser = RuffGroupingParser()
        grouped = GroupedRuffIssues(
            groups={"F401": (RuffIssue("F401", "unused", 1, 1, "error", True),)},
            total_issues=1,
            unique_codes=1,
            severity_summary={"error": 1},
            fixable_count=1,
        )
        md = parser.render_grouped(grouped, format="markdown")
        assert "Issues by Code" in md
        assert "F401" in md
        assert "auto-fixable" in md or "1" in md

    def test_render_json_valid(self):
        parser = RuffGroupingParser()
        grouped = GroupedRuffIssues(
            groups={"E501": (RuffIssue("E501", "long", 1, 1, "error", False),)},
            total_issues=1,
            unique_codes=1,
            severity_summary={"error": 1},
            fixable_count=0,
        )
        out = parser.render_grouped(grouped, format="json")
        data = json.loads(out)
        assert data["total_issues"] == 1
        assert "E501" in data["groups"]

    def test_render_html_contains_details(self):
        parser = RuffGroupingParser()
        grouped = GroupedRuffIssues(
            groups={"F401": (RuffIssue("F401", "unused", 1, 1, "error", False),)},
            total_issues=1,
            unique_codes=1,
            severity_summary={"error": 1},
            fixable_count=0,
        )
        html = parser.render_grouped(grouped, format="html")
        assert "<details>" in html
        assert "F401" in html


class TestGroupedRuffIssuesToDict:
    def test_to_dict_roundtrip(self):
        grouped = GroupedRuffIssues(
            groups={"X": (RuffIssue("X", "msg", 1, 1, "error", False),)},
            total_issues=1,
            unique_codes=1,
            severity_summary={"error": 1},
            fixable_count=0,
        )
        d = grouped.to_dict()
        assert d["total_issues"] == 1
        assert d["unique_codes"] == 1
        assert "X" in d["groups"]
        assert len(d["groups"]["X"]) == 1
        assert d["groups"]["X"][0]["message"] == "msg"
