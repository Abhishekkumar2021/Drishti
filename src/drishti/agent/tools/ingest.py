"""Workspace ingest status tool."""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool, tool

from drishti.agent.tools.runtime import AgentToolRuntime
from drishti.ingestion.index_state import IndexStateStore


def build_ingest_status_tool(runtime: AgentToolRuntime) -> BaseTool:
    """Return a LangChain tool reporting index state for a workspace."""

    @tool
    def ingest_status(workspace_id: str) -> str:
        """Return indexing status for a workspace (commit, tracked files).

        Args:
            workspace_id: Platform workspace identifier.
        """
        if runtime.platform is None:
            return json.dumps({"error": "platform service unavailable"})

        record = runtime.platform.get_workspace(workspace_id)
        if record is None:
            return json.dumps({"error": f"unknown workspace: {workspace_id}"})

        ingest_root = runtime.platform.ingest_root(workspace_id)
        state = IndexStateStore.for_repository(ingest_root).load()
        if state is None:
            return json.dumps(
                {
                    "workspace_id": workspace_id,
                    "indexed": False,
                    "ingest_root": str(ingest_root),
                },
            )

        return json.dumps(
            {
                "workspace_id": workspace_id,
                "indexed": True,
                "indexed_commit": state.indexed_commit,
                "files_tracked": len(state.files),
                "ingest_root": str(ingest_root),
            },
            ensure_ascii=False,
        )

    return ingest_status
