"""Qdrant payload filter compilation (US-05.04)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qdrant_client.models import (
    Condition,
    FieldCondition,
    Filter,
    MatchText,
    MatchValue,
)

FilterOperator = Literal["and", "or"]

_EXACT_MATCH_FIELDS = frozenset(
    {
        "language",
        "content_type",
        "source_type",
        "node_type",
        "name",
        "parent_class",
        "package_name",
        "parent_module",
    }
)


@dataclass(frozen=True)
class FilterClause:
    """A single payload field predicate."""

    field: str
    value: str


@dataclass(frozen=True)
class FilterExpression:
    """Nested AND/OR filter expression."""

    operator: FilterOperator
    clauses: tuple[FilterClause | FilterExpression, ...]


def compile_qdrant_filter(
    filters: dict[str, str] | None = None,
    *,
    expression: FilterExpression | None = None,
) -> Filter | None:
    """Compile user filters into a Qdrant ``Filter`` object."""
    if expression is not None:
        return _compile_expression(expression)
    if not filters:
        return None
    clauses = tuple(FilterClause(field=key, value=value) for key, value in filters.items())
    return _compile_expression(FilterExpression(operator="and", clauses=clauses))


def _compile_expression(expression: FilterExpression) -> Filter:
    conditions: list[Condition] = [_compile_clause(clause) for clause in expression.clauses]
    if expression.operator == "and":
        return Filter(must=conditions)
    return Filter(should=conditions)


def _compile_clause(clause: FilterClause | FilterExpression) -> Condition:
    if isinstance(clause, FilterExpression):
        return _compile_expression(clause)
    return _compile_field(clause.field, clause.value)


def _compile_field(field: str, value: str) -> FieldCondition:
    if field == "file_path":
        return _compile_file_path_condition(value)
    if field in _EXACT_MATCH_FIELDS:
        return FieldCondition(key=field, match=MatchValue(value=value))
    return FieldCondition(key=field, match=MatchValue(value=value))


def _compile_file_path_condition(value: str) -> FieldCondition:
    if value.endswith("*"):
        prefix = value[:-1]
        if prefix.endswith("/"):
            return FieldCondition(key="file_path", match=MatchText(text=prefix))
        return FieldCondition(key="file_path", match=MatchText(text=f"{prefix}/"))
    return FieldCondition(key="file_path", match=MatchValue(value=value))
