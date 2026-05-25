"""Hybrid search tool wrapping ``HybridSearchPipeline``."""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from drishti.agent.tools.runtime import AgentToolRuntime


def build_hybrid_search_tool(runtime: AgentToolRuntime) -> BaseTool:
    """Return a LangChain tool bound to the shared search pipeline."""

    @tool
    def hybrid_search(query: str, workspace_id: str = "", limit: int = 10) -> str:
        """Search indexed code and documents with hybrid dense+BM25 retrieval.

        Args:
            query: Natural language or symbol-oriented search text.
            workspace_id: Optional workspace scope (limits hits to that workspace prefix).
            limit: Maximum number of chunks to return (default 10).
        """
        filters: dict[str, str] | None = None
        if workspace_id.strip():
            filters = {"file_path": f"workspaces/{workspace_id.strip()}/*"}
        hits = runtime.search.search(
            query,
            filters=filters,
            limit=max(1, min(limit, 50)),
        )
        payload = [
            {
                "chunk_id": hit.chunk_id,
                "score": round(hit.score, 4),
                "file_path": hit.payload.get("file_path", ""),
                "start_line": hit.payload.get("start_line"),
                "end_line": hit.payload.get("end_line"),
                "content_preview": hit.content[:400],
            }
            for hit in hits
        ]
        return json.dumps({"query": query, "results": payload}, ensure_ascii=False)

    return hybrid_search
