"""Configurable Tree-sitter extraction rules (US-03.06)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any


@dataclass(frozen=True)
class LanguageRule:
    """Per-language Tree-sitter extraction settings."""

    language: str
    query_file: str
    min_chunk_lines: int


@dataclass(frozen=True)
class ParserRules:
    """Loaded parser rule configuration."""

    version: int
    default_min_chunk_lines: int
    languages: dict[str, LanguageRule]

    def min_chunk_lines_for(self, language: str) -> int:
        """Return the minimum chunk line threshold for a language."""
        rule = self.languages.get(language)
        if rule is None:
            return self.default_min_chunk_lines
        return rule.min_chunk_lines

    def query_file_for(self, language: str) -> str:
        """Return the packaged query filename for a language."""
        rule = self.languages.get(language)
        if rule is None:
            msg = f"No Tree-sitter rules registered for language: {language}"
            raise KeyError(msg)
        return rule.query_file


def load_parser_rules() -> ParserRules:
    """Load parser rules from the packaged JSON configuration."""
    package = "drishti.ingestion.queries"
    try:
        rules_file = resources.files(package).joinpath("parser_rules.json")
    except (ModuleNotFoundError, TypeError) as exc:
        msg = f"Could not resolve rules package {package!r}"
        raise FileNotFoundError(msg) from exc
    if not rules_file.is_file():
        msg = "parser_rules.json not found in ingestion query assets"
        raise FileNotFoundError(msg)
    payload: dict[str, Any] = json.loads(rules_file.read_text(encoding="utf-8"))
    defaults = payload.get("defaults", {})
    default_min = int(defaults.get("min_chunk_lines", 3))
    languages: dict[str, LanguageRule] = {}
    for language, config in payload.get("languages", {}).items():
        if not isinstance(config, dict):
            continue
        languages[language] = LanguageRule(
            language=language,
            query_file=str(config["query"]),
            min_chunk_lines=int(config.get("min_chunk_lines", default_min)),
        )
    return ParserRules(
        version=int(payload.get("version", 1)),
        default_min_chunk_lines=default_min,
        languages=languages,
    )
