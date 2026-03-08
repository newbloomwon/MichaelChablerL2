"""Query parser for Punkt search functionality.

Parses user search queries into an Abstract Syntax Tree (AST) with:
  - Field filters with operators (=, !=, >, <, >=, <=)
  - Implicit AND logic for multiple filters
  - Quoted value support
  - Plain text search on message field
  - Pipe commands for aggregation (stats, sort, head)
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class QueryParseError(Exception):
    """Exception raised when query parsing fails."""

    def __init__(self, message: str, position: int = 0):
        self.message = message
        self.position = position
        super().__init__(f"{message} at position {position}")


@dataclass
class FilterNode:
    """Represents a single filter condition."""
    field: str
    operator: str
    value: str

    def __repr__(self) -> str:
        return f"FilterNode({self.field!r}, {self.operator!r}, {self.value!r})"


@dataclass
class TextSearch:
    """Represents plain text search terms."""
    terms: List[str]

    def __repr__(self) -> str:
        return f"TextSearch({self.terms!r})"


@dataclass
class StatsCommand:
    """Represents a stats aggregation command."""
    function: str
    field: Optional[str]
    group_by: str

    def __repr__(self) -> str:
        return f"StatsCommand({self.function!r}, {self.field!r}, {self.group_by!r})"


@dataclass
class HeadCommand:
    """Represents a head (limit) command."""
    count: int

    def __repr__(self) -> str:
        return f"HeadCommand({self.count!r})"


@dataclass
class SortCommand:
    """Represents a sort command."""
    field: str
    order: str

    def __repr__(self) -> str:
        return f"SortCommand({self.field!r}, {self.order!r})"


@dataclass
class ParsedQuery:
    """Complete parsed query result."""
    filters: List[FilterNode]
    text_search: Optional[TextSearch]
    pipe_commands: List[Union[StatsCommand, HeadCommand, SortCommand]]

    def __repr__(self) -> str:
        return (
            f"ParsedQuery("
            f"filters={self.filters!r}, "
            f"text_search={self.text_search!r}, "
            f"pipe_commands={self.pipe_commands!r})"
        )


def _tokenize_filter_section(filter_str: str) -> List[str]:
    """Tokenize filter section preserving quoted values."""
    tokens = []
    current_token = ""
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(filter_str):
        char = filter_str[i]

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_token += char
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_token += char
        elif char.isspace() and not (in_single_quote or in_double_quote):
            if current_token:
                tokens.append(current_token)
                current_token = ""
        else:
            current_token += char

        i += 1

    if current_token:
        tokens.append(current_token)

    return tokens


def _extract_quoted_value(value: str) -> str:
    """Remove quotes from value if present."""
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_filter_token(token: str) -> Optional[FilterNode]:
    """Parse a single token into a FilterNode if it's a valid filter."""
    operators = [">=", "<=", "!=", "=", ">", "<"]

    for op in operators:
        if op in token:
            parts = token.split(op, 1)
            if len(parts) == 2:
                field, raw_value = parts
                if not field:
                    raise QueryParseError(f"Empty field name in filter token '{token}'", 0)
                if not raw_value:
                    raise QueryParseError(f"Empty value in filter token '{token}'", 0)

                value = _extract_quoted_value(raw_value)
                return FilterNode(field, op, value)

    return None


def _parse_pipe_commands(commands_str: str) -> List[Union[StatsCommand, HeadCommand, SortCommand]]:
    """Parse pipe-separated commands into command objects."""
    commands = []
    pipe_parts = [p.strip() for p in commands_str.split("|")]

    for cmd_str in pipe_parts:
        if not cmd_str:
            continue

        cmd_tokens = cmd_str.split()
        if not cmd_tokens:
            continue

        cmd_type = cmd_tokens[0].lower()

        if cmd_type == "stats":
            if len(cmd_tokens) < 4:
                raise QueryParseError(
                    f"Invalid stats command: '{cmd_str}'. "
                    f"Expected: stats <function> by <field>",
                    0
                )

            function = cmd_tokens[1].lower()

            if function == "count":
                # Syntax: stats count by <group_field>
                if cmd_tokens[2].lower() != "by":
                    raise QueryParseError(
                        f"Invalid stats command: '{cmd_str}'. "
                        f"Expected: stats count by <field>",
                        0
                    )
                group_by = cmd_tokens[3]
                commands.append(StatsCommand(function, None, group_by))
            elif function in ["sum", "avg", "min", "max"]:
                # Syntax: stats <function> <field> by <group_field>
                if len(cmd_tokens) < 5:
                    raise QueryParseError(
                        f"Function '{function}' requires a field. "
                        f"Expected: stats {function} <field> by <group_field>",
                        0
                    )
                field = cmd_tokens[2]
                if cmd_tokens[3].lower() != "by":
                    raise QueryParseError(
                        f"Invalid stats command: '{cmd_str}'. "
                        f"Expected 'by' keyword after field name",
                        0
                    )
                group_by = cmd_tokens[4]
                commands.append(StatsCommand(function, field, group_by))
            else:
                raise QueryParseError(
                    f"Unknown stats function: '{function}'. "
                    f"Supported: count, sum, avg, min, max",
                    0
                )

        elif cmd_type == "head":
            if len(cmd_tokens) < 2:
                raise QueryParseError(
                    f"Invalid head command: '{cmd_str}'. "
                    f"Expected: head <count>",
                    0
                )

            try:
                count = int(cmd_tokens[1])
                if count <= 0:
                    raise ValueError("Count must be positive")
                commands.append(HeadCommand(count))
            except ValueError as e:
                raise QueryParseError(
                    f"Invalid count in head command: '{cmd_tokens[1]}'. "
                    f"Must be a positive integer",
                    0
                ) from e

        elif cmd_type == "sort":
            if len(cmd_tokens) < 3:
                raise QueryParseError(
                    f"Invalid sort command: '{cmd_str}'. "
                    f"Expected: sort <field> <asc|desc>",
                    0
                )

            field = cmd_tokens[1]
            order = cmd_tokens[2].lower()

            if order not in ["asc", "desc"]:
                raise QueryParseError(
                    f"Invalid sort order: '{cmd_tokens[2]}'. "
                    f"Must be 'asc' or 'desc'",
                    0
                )

            commands.append(SortCommand(field, order))

        else:
            raise QueryParseError(
                f"Unknown pipe command: '{cmd_type}'. "
                f"Supported: stats, head, sort",
                0
            )

    return commands


def parse_query(query_string: str) -> ParsedQuery:
    """
    Parse a query string into structured AST.

    Supports:
      1. Field filters with operators: level=ERROR, timestamp>"2025-02-07T00:00:00Z"
      2. Implicit AND logic: multiple filters combined
      3. Plain text search: words without operators search message field
      4. Pipe commands: | stats count by source | head 50

    Args:
        query_string: Raw query from user

    Returns:
        ParsedQuery with filters, text_search, and pipe_commands

    Raises:
        QueryParseError: If query is malformed
    """
    if not query_string or not query_string.strip():
        raise QueryParseError("Query cannot be empty", 0)

    query_string = query_string.strip()
    logger.debug(f"Parsing query: {query_string}")

    pipe_index = query_string.find("|")

    if pipe_index == -1:
        filter_section = query_string
        commands_section = ""
    else:
        filter_section = query_string[:pipe_index].strip()
        commands_section = query_string[pipe_index + 1:].strip()

    filters = []
    text_terms = []

    if filter_section:
        tokens = _tokenize_filter_section(filter_section)

        for token in tokens:
            filter_node = _parse_filter_token(token)
            if filter_node:
                filters.append(filter_node)
            else:
                text_terms.append(token)

    text_search = TextSearch(text_terms) if text_terms else None

    pipe_commands = []
    if commands_section:
        if not commands_section.strip():
            raise QueryParseError("Dangling pipe without commands", pipe_index)

        pipe_commands = _parse_pipe_commands(commands_section)

    result = ParsedQuery(
        filters=filters,
        text_search=text_search,
        pipe_commands=pipe_commands
    )

    logger.debug(f"Parsed query result: {result}")
    return result
