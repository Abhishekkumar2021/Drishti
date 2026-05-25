"""LangGraph RAG agent: retrieve → generate → grade."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from drishti.agent.nodes import generate_answer, retrieve_context
from drishti.agent.state import AgentState
from drishti.generation.llm import ChatLLM
from drishti.generation.pipeline import RAGPipeline


def build_rag_graph(rag: RAGPipeline, llm: ChatLLM) -> StateGraph:
    """Compile retrieve-grade-generate graph over hybrid search + LLM."""

    def retrieve(state: AgentState) -> AgentState:
        return retrieve_context(rag, state)

    def generate(state: AgentState) -> AgentState:
        return generate_answer(rag, llm, state)

    def route_after_generate(state: AgentState) -> Literal["retrieve", "__end__"]:
        if state.get("needs_retry"):
            return "retrieve"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_conditional_edges("generate", route_after_generate)
    return graph
