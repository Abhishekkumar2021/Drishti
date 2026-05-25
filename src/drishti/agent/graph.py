"""LangGraph RAG agent: retrieve → generate → grade."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph

from drishti.agent.nodes import expand_query, generate_answer, retrieve_context
from drishti.agent.state import AgentState
from drishti.generation.llm import ChatLLM
from drishti.generation.pipeline import RAGPipeline


def build_rag_graph(rag: RAGPipeline, llm: ChatLLM) -> StateGraph[AgentState, None, AgentState]:
    """Compile retrieve-grade-generate graph over hybrid search + LLM."""

    def retrieve(state: AgentState) -> AgentState:
        return retrieve_context(rag, state)

    def generate(state: AgentState) -> AgentState:
        return generate_answer(rag, llm, state)

    def expand(state: AgentState) -> AgentState:
        return expand_query(llm, state)

    def route_after_generate(state: AgentState) -> Literal["retrieve", "expand_query", "__end__"]:
        if not state.get("needs_retry"):
            return "__end__"
        passes = state.get("retrieval_pass", 0)
        max_passes = state.get("max_passes", 2)
        if passes >= max_passes:
            return "__end__"
        if state.get("retry_mode") == "low_confidence" and not state.get("query_expanded"):
            return "expand_query"
        return "retrieve"

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("expand_query", expand)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("expand_query", "retrieve")
    graph.add_conditional_edges("generate", route_after_generate)
    return graph
