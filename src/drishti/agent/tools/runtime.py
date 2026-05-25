"""Runtime dependencies for LangChain agent tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drishti.config import Settings
    from drishti.search.pipeline import HybridSearchPipeline
    from drishti.services.platform_service import PlatformService


@dataclass(frozen=True)
class AgentToolRuntime:
    """Services tools call — never hit external APIs directly."""

    settings: Settings
    search: HybridSearchPipeline
    platform: PlatformService | None = None
