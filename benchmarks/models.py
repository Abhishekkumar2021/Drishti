"""Pydantic models for evaluation data structures."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Difficulty(StrEnum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GoldenQA(BaseModel):
    """A single golden Q&A entry for evaluation."""

    id: str = Field(..., description="Unique identifier for the Q&A pair")
    category: str = Field(..., description="Question category (code_structure, api, search, etc.)")
    difficulty: Difficulty = Field(..., description="Question difficulty level")
    question: str = Field(..., description="The evaluation question")
    expected_files: list[str] = Field(..., description="Files that should be retrieved")
    expected_chunks: list[str] = Field(
        default_factory=list, description="Specific chunks/symbols expected"
    )
    ground_truth_answer: str = Field(..., description="The correct answer for faithfulness eval")


class RetrievalResult(BaseModel):
    """Result of a single retrieval operation."""

    qa_id: str
    question: str
    retrieved_files: list[str] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    expected_files: list[str] = Field(default_factory=list)
    retrieval_time_ms: float = 0.0


class GenerationResult(BaseModel):
    """Result of a single generation operation."""

    qa_id: str
    question: str
    generated_answer: str
    ground_truth_answer: str
    context_used: str
    generation_time_ms: float = 0.0


class MetricScores(BaseModel):
    """RAGAS metric scores for a single evaluation."""

    context_precision: float = Field(ge=0.0, le=1.0)
    context_recall: float = Field(ge=0.0, le=1.0)
    faithfulness: float = Field(ge=0.0, le=1.0)
    answer_relevancy: float = Field(ge=0.0, le=1.0)


class EvaluationResult(BaseModel):
    """Complete evaluation result for a single Q&A pair."""

    qa_id: str
    question: str
    category: str
    difficulty: Difficulty
    retrieval: RetrievalResult
    generation: GenerationResult
    scores: MetricScores


class AggregateMetrics(BaseModel):
    """Aggregated metrics across all evaluations."""

    total_questions: int
    context_precision_mean: float = Field(ge=0.0, le=1.0)
    context_precision_std: float = Field(ge=0.0)
    context_recall_mean: float = Field(ge=0.0, le=1.0)
    context_recall_std: float = Field(ge=0.0)
    faithfulness_mean: float = Field(ge=0.0, le=1.0)
    faithfulness_std: float = Field(ge=0.0)
    answer_relevancy_mean: float = Field(ge=0.0, le=1.0)
    answer_relevancy_std: float = Field(ge=0.0)
    avg_retrieval_time_ms: float
    avg_generation_time_ms: float

    # Breakdown by category
    metrics_by_category: dict[str, dict[str, float]] = Field(default_factory=dict)
    # Breakdown by difficulty
    metrics_by_difficulty: dict[str, dict[str, float]] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    """Complete evaluation report."""

    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    chunking_strategy: str = Field(..., description="'ast' or 'naive'")
    model_config_summary: dict[str, str] = Field(default_factory=dict)
    aggregate_metrics: AggregateMetrics
    individual_results: list[EvaluationResult] = Field(default_factory=list)
    passed_thresholds: bool = False
    threshold_details: dict[str, dict[str, float]] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    """Comparison between AST and naive chunking strategies."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ast_report: EvaluationReport
    naive_report: EvaluationReport
    improvement: dict[str, float] = Field(default_factory=dict)
    summary: str = ""
