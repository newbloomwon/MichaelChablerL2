"""Tests for the query parser.

Covers:
- Filter parsing (field=value, operators, implicit AND)
- Text search (plain terms, mixed with filters)
- Pipe commands (stats, head, sort, chained)
- Edge cases (empty input, quoted values, invalid syntax)
"""
import pytest

from app.query.parser import (
    FilterNode,
    HeadCommand,
    ParsedQuery,
    QueryParseError,
    SortCommand,
    StatsCommand,
    TextSearch,
    parse_query,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(q: str) -> ParsedQuery:
    """Thin wrapper so tests stay readable."""
    return parse_query(q)


# ---------------------------------------------------------------------------
# Filter Parsing
# ---------------------------------------------------------------------------

class TestFilterParsing:
    """Tests for field=value style filter tokens."""

    def test_single_field_filter(self):
        """'level=ERROR' produces a single FilterNode with = operator."""
        result = _parse("level=ERROR")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert isinstance(node, FilterNode)
        assert node.field == "level"
        assert node.operator == "="
        assert node.value == "ERROR"
        assert result.text_search is None
        assert result.pipe_commands == []

    def test_multiple_filters_implicit_and(self):
        """'level=ERROR source=nginx' produces two FilterNodes (implicit AND)."""
        result = _parse("level=ERROR source=nginx")

        assert len(result.filters) == 2

        level_filter = result.filters[0]
        assert level_filter.field == "level"
        assert level_filter.operator == "="
        assert level_filter.value == "ERROR"

        source_filter = result.filters[1]
        assert source_filter.field == "source"
        assert source_filter.operator == "="
        assert source_filter.value == "nginx"

        assert result.text_search is None
        assert result.pipe_commands == []

    def test_not_equal_operator(self):
        """'level!=DEBUG' produces a FilterNode with != operator."""
        result = _parse("level!=DEBUG")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "level"
        assert node.operator == "!="
        assert node.value == "DEBUG"

    def test_greater_than_operator(self):
        """Timestamp filter with > operator (quoted ISO value)."""
        result = _parse('timestamp>"2025-02-07T00:00:00Z"')

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "timestamp"
        assert node.operator == ">"
        # Quotes are stripped by _extract_quoted_value
        assert node.value == "2025-02-07T00:00:00Z"

    def test_less_equal_operator(self):
        """'status<=500' produces a FilterNode with <= operator."""
        result = _parse("status<=500")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "status"
        assert node.operator == "<="
        assert node.value == "500"

    def test_greater_equal_operator(self):
        """'status>=200' produces a FilterNode with >= operator."""
        result = _parse("status>=200")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "status"
        assert node.operator == ">="
        assert node.value == "200"

    def test_less_than_operator(self):
        """'response_time<100' produces a FilterNode with < operator."""
        result = _parse("response_time<100")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "response_time"
        assert node.operator == "<"
        assert node.value == "100"

    def test_three_filters_implicit_and(self):
        """Three filters all end up in the filters list."""
        result = _parse("level=ERROR source=nginx status=500")

        assert len(result.filters) == 3
        fields = [f.field for f in result.filters]
        assert fields == ["level", "source", "status"]


# ---------------------------------------------------------------------------
# Text Search
# ---------------------------------------------------------------------------

class TestTextSearch:
    """Tests for plain text search terms."""

    def test_plain_text_search(self):
        """'connection failed' produces a TextSearch with both terms."""
        result = _parse("connection failed")

        assert result.filters == []
        assert result.text_search is not None
        assert isinstance(result.text_search, TextSearch)
        assert "connection" in result.text_search.terms
        assert "failed" in result.text_search.terms
        assert len(result.text_search.terms) == 2
        assert result.pipe_commands == []

    def test_single_word_text_search(self):
        """A single unstructured word produces a one-item TextSearch."""
        result = _parse("timeout")

        assert result.filters == []
        assert result.text_search is not None
        assert result.text_search.terms == ["timeout"]

    def test_mixed_filter_and_text(self):
        """'level=ERROR connection failed' yields one filter and a text search."""
        result = _parse("level=ERROR connection failed")

        assert len(result.filters) == 1
        assert result.filters[0].field == "level"
        assert result.filters[0].value == "ERROR"

        assert result.text_search is not None
        assert "connection" in result.text_search.terms
        assert "failed" in result.text_search.terms

    def test_text_search_before_filter(self):
        """Text terms before a filter are captured in text_search."""
        result = _parse("connection level=ERROR")

        assert len(result.filters) == 1
        assert result.filters[0].field == "level"

        assert result.text_search is not None
        assert "connection" in result.text_search.terms


# ---------------------------------------------------------------------------
# Pipe Commands
# ---------------------------------------------------------------------------

class TestPipeCommands:
    """Tests for | stats, | head, | sort commands."""

    def test_stats_count_by(self):
        """'| stats count by source' produces StatsCommand(count, None, source)."""
        result = _parse("level=ERROR | stats count by source")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, StatsCommand)
        assert cmd.function == "count"
        assert cmd.field is None
        assert cmd.group_by == "source"

    def test_stats_avg_by(self):
        """'| stats avg response_time by source' produces StatsCommand with field."""
        result = _parse("level=ERROR | stats avg response_time by source")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, StatsCommand)
        assert cmd.function == "avg"
        assert cmd.field == "response_time"
        assert cmd.group_by == "source"

    def test_stats_sum_by(self):
        """'| stats sum bytes by source' produces StatsCommand with sum function."""
        result = _parse("source=nginx | stats sum bytes by source")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, StatsCommand)
        assert cmd.function == "sum"
        assert cmd.field == "bytes"
        assert cmd.group_by == "source"

    def test_stats_min_by(self):
        """'| stats min response_time by source' produces StatsCommand with min."""
        result = _parse("level=INFO | stats min response_time by source")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert cmd.function == "min"
        assert cmd.field == "response_time"

    def test_stats_max_by(self):
        """'| stats max response_time by source' produces StatsCommand with max."""
        result = _parse("level=INFO | stats max response_time by source")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert cmd.function == "max"
        assert cmd.field == "response_time"

    def test_head_command(self):
        """'| head 50' produces HeadCommand(50)."""
        result = _parse("level=ERROR | head 50")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, HeadCommand)
        assert cmd.count == 50

    def test_head_command_count_one(self):
        """'| head 1' is valid with count=1."""
        result = _parse("level=ERROR | head 1")

        cmd = result.pipe_commands[0]
        assert isinstance(cmd, HeadCommand)
        assert cmd.count == 1

    def test_sort_command_desc(self):
        """'| sort timestamp desc' produces SortCommand(timestamp, desc)."""
        result = _parse("level=ERROR | sort timestamp desc")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, SortCommand)
        assert cmd.field == "timestamp"
        assert cmd.order == "desc"

    def test_sort_command_asc(self):
        """'| sort timestamp asc' produces SortCommand with order=asc."""
        result = _parse("level=ERROR | sort timestamp asc")

        assert len(result.pipe_commands) == 1
        cmd = result.pipe_commands[0]
        assert isinstance(cmd, SortCommand)
        assert cmd.field == "timestamp"
        assert cmd.order == "asc"

    def test_chained_pipes(self):
        """'| stats count by level | head 10' produces two commands in order."""
        result = _parse("source=nginx | stats count by level | head 10")

        assert len(result.pipe_commands) == 2

        stats_cmd = result.pipe_commands[0]
        assert isinstance(stats_cmd, StatsCommand)
        assert stats_cmd.function == "count"
        assert stats_cmd.group_by == "level"

        head_cmd = result.pipe_commands[1]
        assert isinstance(head_cmd, HeadCommand)
        assert head_cmd.count == 10

    def test_chained_sort_and_head(self):
        """'| sort timestamp desc | head 25' chains sort then head."""
        result = _parse("level=ERROR | sort timestamp desc | head 25")

        assert len(result.pipe_commands) == 2
        assert isinstance(result.pipe_commands[0], SortCommand)
        assert isinstance(result.pipe_commands[1], HeadCommand)
        assert result.pipe_commands[1].count == 25

    def test_pipe_command_with_no_filter(self):
        """A bare pipe command without any preceding filter works fine."""
        result = _parse("| head 100")

        assert result.filters == []
        assert result.text_search is None
        assert len(result.pipe_commands) == 1
        assert isinstance(result.pipe_commands[0], HeadCommand)


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases, error conditions, and whitespace handling."""

    def test_empty_query_raises_error(self):
        """An empty string raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("")

    def test_whitespace_only_raises_error(self):
        """A whitespace-only string raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("   ")

    def test_quoted_value_with_spaces(self):
        """source="my app log" keeps the full value including spaces."""
        result = _parse('source="my app log"')

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.field == "source"
        assert node.operator == "="
        assert node.value == "my app log"

    def test_single_quoted_value(self):
        """source='my log' with single quotes also strips quotes."""
        result = _parse("source='my log'")

        assert len(result.filters) == 1
        node = result.filters[0]
        assert node.value == "my log"

    def test_invalid_pipe_command_raises_error(self):
        """An unknown pipe command raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("level=ERROR | notacommand")

    def test_invalid_sort_order_raises_error(self):
        """An invalid sort order like 'random' raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("level=ERROR | sort timestamp random")

    def test_head_with_zero_count_raises_error(self):
        """head 0 is rejected because count must be positive."""
        with pytest.raises(QueryParseError):
            parse_query("level=ERROR | head 0")

    def test_head_with_non_integer_raises_error(self):
        """head with a non-integer argument raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("level=ERROR | head abc")

    def test_stats_with_unknown_function_raises_error(self):
        """An unknown stats function raises QueryParseError."""
        with pytest.raises(QueryParseError):
            parse_query("level=ERROR | stats median by source")

    def test_whitespace_handling_extra_spaces(self):
        """Extra spaces between tokens are ignored gracefully."""
        result = _parse("level=ERROR   source=nginx")

        assert len(result.filters) == 2
        assert result.filters[0].field == "level"
        assert result.filters[1].field == "source"

    def test_leading_trailing_whitespace(self):
        """Leading and trailing whitespace around the full query is stripped."""
        result = _parse("  level=ERROR  ")

        assert len(result.filters) == 1
        assert result.filters[0].value == "ERROR"

    def test_full_complex_query(self):
        """A complete realistic query parses all components correctly."""
        query = 'level=ERROR source=nginx status>=500 connection | stats count by source | head 20'
        result = _parse(query)

        # Three filters
        assert len(result.filters) == 3
        assert result.filters[0] == FilterNode("level", "=", "ERROR")
        assert result.filters[1] == FilterNode("source", "=", "nginx")
        assert result.filters[2] == FilterNode("status", ">=", "500")

        # One text search term
        assert result.text_search is not None
        assert "connection" in result.text_search.terms

        # Two pipe commands
        assert len(result.pipe_commands) == 2
        stats = result.pipe_commands[0]
        head = result.pipe_commands[1]
        assert isinstance(stats, StatsCommand)
        assert stats.function == "count"
        assert stats.group_by == "source"
        assert isinstance(head, HeadCommand)
        assert head.count == 20

    def test_parsed_query_dataclass_fields(self):
        """ParsedQuery exposes filters, text_search, and pipe_commands attributes."""
        result = _parse("level=INFO")

        assert hasattr(result, "filters")
        assert hasattr(result, "text_search")
        assert hasattr(result, "pipe_commands")

    def test_filter_node_repr(self):
        """FilterNode has a useful repr."""
        node = FilterNode("level", "=", "ERROR")
        assert "level" in repr(node)
        assert "ERROR" in repr(node)

    def test_stats_command_repr(self):
        """StatsCommand has a useful repr."""
        cmd = StatsCommand("count", None, "source")
        assert "count" in repr(cmd)
        assert "source" in repr(cmd)

    def test_head_command_repr(self):
        """HeadCommand has a useful repr."""
        cmd = HeadCommand(50)
        assert "50" in repr(cmd)

    def test_sort_command_repr(self):
        """SortCommand has a useful repr."""
        cmd = SortCommand("timestamp", "desc")
        assert "timestamp" in repr(cmd)
        assert "desc" in repr(cmd)
