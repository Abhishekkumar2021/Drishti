"""Read source file tool (Monaco / citation navigation)."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from drishti.agent.tools.runtime import AgentToolRuntime
from drishti.utils.language import LanguageRegistry
from drishti.utils.paths import is_path_within_root


def build_read_source_tool(runtime: AgentToolRuntime) -> BaseTool:
    """Return a LangChain tool that reads a file under an allowed ingest root."""

    @tool
    def read_source(repo_path: str, file_path: str) -> str:
        """Read UTF-8 text from a repository file for citation follow-up.

        Args:
            repo_path: Absolute or configured root path to the indexed repository.
            file_path: Relative path within the repo (no ``..`` segments).
        """
        allowed = [Path(root) for root in runtime.settings.ingestion_root_allowlist()]
        repo_root = Path(repo_path).expanduser().resolve()
        if allowed and not any(is_path_within_root(repo_root, root) for root in allowed):
            return json.dumps({"error": "repo_path is not under an allowed ingestion root"})

        relative = file_path.strip().lstrip("/")
        if not relative or ".." in Path(relative).parts:
            return json.dumps({"error": "file_path must be a safe relative path"})

        absolute = (repo_root / relative).resolve()
        if not is_path_within_root(absolute, repo_root):
            return json.dumps({"error": "file_path escapes repository root"})
        if not absolute.is_file():
            return json.dumps({"error": f"source file not found: {relative}"})

        content = absolute.read_text(encoding="utf-8", errors="replace")
        language = LanguageRegistry().detect(relative)
        line_count = content.count("\n") + (1 if content else 0)
        return json.dumps(
            {
                "file_path": relative,
                "language": language,
                "line_count": line_count,
                "content": content[:8000],
            },
            ensure_ascii=False,
        )

    return read_source
