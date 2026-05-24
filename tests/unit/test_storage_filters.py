"""Unit tests for Qdrant filter compilation (US-05.04)."""

from __future__ import annotations

import pytest
from qdrant_client.models import FieldCondition, Filter, MatchText, MatchValue

from drishti.storage.filters import FilterClause, FilterExpression, compile_qdrant_filter

pytestmark = pytest.mark.unit


class TestCompileQdrantFilter:
    def test_empty_filters_return_none(self) -> None:
        assert compile_qdrant_filter(None) is None
        assert compile_qdrant_filter({}) is None

    def test_dict_filters_compile_to_and(self) -> None:
        compiled = compile_qdrant_filter({"language": "python", "content_type": "code"})
        assert isinstance(compiled, Filter)
        assert compiled.must is not None
        assert len(compiled.must) == 2

    def test_file_path_prefix_uses_match_text(self) -> None:
        compiled = compile_qdrant_filter({"file_path": "src/auth/*"})
        assert compiled is not None
        assert compiled.must is not None
        condition = compiled.must[0]
        assert isinstance(condition, FieldCondition)
        assert isinstance(condition.match, MatchText)

    def test_exact_match_fields(self) -> None:
        compiled = compile_qdrant_filter({"language": "java"})
        assert compiled is not None
        assert compiled.must is not None
        condition = compiled.must[0]
        assert isinstance(condition, FieldCondition)
        assert isinstance(condition.match, MatchValue)
        assert condition.match.value == "java"

    def test_or_expression(self) -> None:
        expression = FilterExpression(
            operator="or",
            clauses=(
                FilterClause(field="language", value="python"),
                FilterClause(field="language", value="java"),
            ),
        )
        compiled = compile_qdrant_filter(expression=expression)
        assert compiled is not None
        assert compiled.should is not None
        assert len(compiled.should) == 2
