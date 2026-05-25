"""LangChain tools wrapping Drishti search, source read, and ingest status."""

from __future__ import annotations

from typing import TYPE_CHECKING

from drishti.agent.tools.ingest import build_ingest_status_tool
from drishti.agent.tools.runtime import AgentToolRuntime
from drishti.agent.tools.search import build_hybrid_search_tool
from drishti.agent.tools.source import build_read_source_tool

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


def build_agent_tools(runtime: AgentToolRuntime) -> list[BaseTool]:
    """Create all agent tools for the active runtime."""
    return [
        build_hybrid_search_tool(runtime),
        build_read_source_tool(runtime),
        build_ingest_status_tool(runtime),
    ]


__all__ = ["AgentToolRuntime", "build_agent_tools"]
