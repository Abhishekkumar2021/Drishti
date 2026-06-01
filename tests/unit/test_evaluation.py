"""Unit tests for the evaluation framework."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.metrics import (
    _fallback_answer_relevancy,
    _fallback_context_precision,
    _fallback_context_recall,
    _fallback_faithfulness,
    check_thresholds,
    compute_all_metrics,
)
from benchmarks.models import (
    AggregateMetrics,
    Difficulty,
    EvaluationReport,
    GoldenQA,
    MetricScores,
)
from benchmarks.report import (
    format_console_table,
    format_markdown_report,
    format_mermaid_chart,
)
from benchmarks.runner import EvaluationRunner


@pytest.mark.unit
class TestGoldenQAModel:
    """Tests for GoldenQA Pydantic model."""

    def test_valid_golden_qa(self) -> None:
        """Test valid GoldenQA instantiation."""
        qa = GoldenQA(
            id="qa_001",
            category="code_structure",
            difficulty=Difficulty.EASY,
            question="What is X?",
            expected_files=["src/x.py"],
            expected_chunks=["ClassX"],
            ground_truth_answer="X is a class that...",
        )
        assert qa.id == "qa_001"
        assert qa.difficulty == Difficulty.EASY

    def test_golden_qa_from_json(self) -> None:
        """Test loading GoldenQA from JSON dict."""
        data = {
            "id": "qa_002",
            "category": "api",
            "difficulty": "medium",
            "question": "How does Y work?",
            "expected_files": ["src/y.py"],
            "ground_truth_answer": "Y works by...",
        }
        qa = GoldenQA.model_validate(data)
        assert qa.difficulty == Difficulty.MEDIUM
        assert qa.expected_chunks == []


@pytest.mark.unit
class TestMetricScores:
    """Tests for MetricScores model."""

    def test_valid_scores(self) -> None:
        """Test valid MetricScores."""
        scores = MetricScores(
            context_precision=0.85,
            context_recall=0.90,
            faithfulness=0.95,
            answer_relevancy=0.88,
        )
        assert scores.context_precision == 0.85

    def test_scores_validation(self) -> None:
        """Test score range validation."""
        with pytest.raises(ValueError):
            MetricScores(
                context_precision=1.5,  # > 1.0
                context_recall=0.90,
                faithfulness=0.95,
                answer_relevancy=0.88,
            )


@pytest.mark.unit
class TestFallbackMetrics:
    """Tests for fallback metric implementations."""

    def test_context_precision_simple(self) -> None:
        """Test fallback context precision with overlapping keywords."""
        questions = ["What is authentication?"]
        contexts = [["authentication is handled by AuthService", "login uses tokens"]]
        ground_truths = ["Authentication is handled by AuthService using JWT tokens"]

        scores = _fallback_context_precision(questions, contexts, ground_truths)
        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_context_precision_empty_contexts(self) -> None:
        """Test context precision with no contexts."""
        questions = ["What is X?"]
        contexts = [[]]
        ground_truths = ["X is a thing"]

        scores = _fallback_context_precision(questions, contexts, ground_truths)
        assert scores[0] == 0.0

    def test_context_recall_full_coverage(self) -> None:
        """Test context recall with full keyword coverage."""
        questions = ["How does search work?"]
        contexts = [["search uses hybrid dense and sparse vectors", "vectors are embedded"]]
        ground_truths = ["search uses hybrid vectors"]

        scores = _fallback_context_recall(questions, contexts, ground_truths)
        assert scores[0] > 0.5

    def test_faithfulness_supported_answer(self) -> None:
        """Test faithfulness when answer is supported by context."""
        questions = ["What is the config?"]
        contexts = [["config uses pydantic settings", "settings read from env"]]
        answers = ["The config uses pydantic settings"]

        scores = _fallback_faithfulness(questions, contexts, answers)
        assert scores[0] > 0.5

    def test_faithfulness_unsupported_answer(self) -> None:
        """Test faithfulness when answer is not in context."""
        questions = ["What is X?"]
        contexts = [["A is blue", "B is red"]]
        answers = ["X is green and yellow with purple stripes"]

        scores = _fallback_faithfulness(questions, contexts, answers)
        assert scores[0] < 0.5

    def test_answer_relevancy_related(self) -> None:
        """Test answer relevancy with related content."""
        questions = ["How does authentication work?"]
        answers = ["Authentication works by verifying tokens"]

        scores = _fallback_answer_relevancy(questions, answers)
        assert scores[0] > 0.0

    def test_answer_relevancy_unrelated(self) -> None:
        """Test answer relevancy with unrelated content."""
        questions = ["What is the database schema configuration?"]
        answers = ["Elephants migrate during winter seasons"]

        scores = _fallback_answer_relevancy(questions, answers)
        # Completely unrelated content should have low overlap
        assert scores[0] < 0.3


@pytest.mark.unit
class TestThresholdChecking:
    """Tests for threshold checking logic."""

    def test_all_thresholds_pass(self) -> None:
        """Test when all thresholds pass."""
        scores = MetricScores(
            context_precision=0.90,
            context_recall=0.95,
            faithfulness=0.98,
            answer_relevancy=0.92,
        )
        passed, details = check_thresholds(scores)
        assert passed is True
        assert all(d["passed"] == 1.0 for d in details.values())

    def test_some_thresholds_fail(self) -> None:
        """Test when some thresholds fail."""
        scores = MetricScores(
            context_precision=0.70,  # Below 0.85
            context_recall=0.95,
            faithfulness=0.98,
            answer_relevancy=0.92,
        )
        passed, details = check_thresholds(scores)
        assert passed is False
        assert details["context_precision"]["passed"] == 0.0
        assert details["context_recall"]["passed"] == 1.0


@pytest.mark.unit
class TestComputeAllMetrics:
    """Tests for combined metric computation."""

    def test_compute_all_metrics(self) -> None:
        """Test computing all metrics for a single Q&A."""
        scores = compute_all_metrics(
            question="What is the search pipeline?",
            contexts=["The search pipeline uses hybrid search with RRF fusion"],
            generated_answer="The search pipeline uses hybrid search",
            ground_truth="The search pipeline uses hybrid search with RRF",
        )
        assert isinstance(scores, MetricScores)
        assert 0.0 <= scores.context_precision <= 1.0
        assert 0.0 <= scores.context_recall <= 1.0
        assert 0.0 <= scores.faithfulness <= 1.0
        assert 0.0 <= scores.answer_relevancy <= 1.0


@pytest.mark.unit
class TestEvaluationRunner:
    """Tests for EvaluationRunner."""

    def test_load_dataset(self, tmp_path: Path) -> None:
        """Test loading golden Q&A dataset."""
        dataset = [
            {
                "id": "qa_001",
                "category": "test",
                "difficulty": "easy",
                "question": "Test question?",
                "expected_files": ["test.py"],
                "ground_truth_answer": "Test answer",
            }
        ]
        dataset_path = tmp_path / "test_qa.json"
        dataset_path.write_text(json.dumps(dataset))

        runner = EvaluationRunner(dataset_path=dataset_path)
        loaded = runner.load_dataset()

        assert len(loaded) == 1
        assert loaded[0].id == "qa_001"

    def test_load_dataset_missing_file(self, tmp_path: Path) -> None:
        """Test error when dataset file doesn't exist."""
        runner = EvaluationRunner(dataset_path=tmp_path / "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            runner.load_dataset()

    def test_compute_aggregates_empty(self) -> None:
        """Test aggregate computation with no results."""
        runner = EvaluationRunner()
        agg = runner.compute_aggregates([])
        assert agg.total_questions == 0


@pytest.mark.unit
class TestReportGeneration:
    """Tests for report generation utilities."""

    def test_format_console_table(self) -> None:
        """Test console table formatting."""
        report = EvaluationReport(
            run_id="test-123",
            chunking_strategy="ast",
            aggregate_metrics=AggregateMetrics(
                total_questions=10,
                context_precision_mean=0.88,
                context_precision_std=0.05,
                context_recall_mean=0.92,
                context_recall_std=0.04,
                faithfulness_mean=0.96,
                faithfulness_std=0.03,
                answer_relevancy_mean=0.91,
                answer_relevancy_std=0.04,
                avg_retrieval_time_ms=150.0,
                avg_generation_time_ms=800.0,
            ),
            passed_thresholds=True,
        )
        table = format_console_table(report)
        assert "Context Precision" in table
        assert "88.0%" in table
        assert "PASS" in table

    def test_format_markdown_report(self) -> None:
        """Test markdown report formatting."""
        report = EvaluationReport(
            run_id="test-456",
            chunking_strategy="ast",
            aggregate_metrics=AggregateMetrics(
                total_questions=5,
                context_precision_mean=0.85,
                context_precision_std=0.05,
                context_recall_mean=0.90,
                context_recall_std=0.04,
                faithfulness_mean=0.95,
                faithfulness_std=0.03,
                answer_relevancy_mean=0.90,
                answer_relevancy_std=0.04,
                avg_retrieval_time_ms=100.0,
                avg_generation_time_ms=500.0,
            ),
            passed_thresholds=True,
        )
        md = format_markdown_report(report)
        assert "# Drishti RAG Evaluation Report" in md
        assert "Context Precision" in md
        assert "test-456" in md

    def test_format_mermaid_chart(self) -> None:
        """Test mermaid chart generation."""
        report = EvaluationReport(
            run_id="test-789",
            chunking_strategy="naive",
            aggregate_metrics=AggregateMetrics(
                total_questions=5,
                context_precision_mean=0.60,
                context_precision_std=0.10,
                context_recall_mean=0.70,
                context_recall_std=0.08,
                faithfulness_mean=0.80,
                faithfulness_std=0.07,
                answer_relevancy_mean=0.75,
                answer_relevancy_std=0.09,
                avg_retrieval_time_ms=100.0,
                avg_generation_time_ms=500.0,
            ),
            passed_thresholds=False,
        )
        chart = format_mermaid_chart(report)
        assert "```mermaid" in chart
        assert "xychart-beta" in chart
        assert "naive" in chart


@pytest.mark.unit
class TestGoldenDatasetValidity:
    """Tests to validate the golden Q&A dataset."""

    def test_golden_dataset_loads(self) -> None:
        """Test that the real golden dataset loads correctly."""
        dataset_path = (
            Path(__file__).parent.parent.parent / "benchmarks" / "datasets" / "golden_qa.json"
        )
        if not dataset_path.exists():
            pytest.skip("Golden dataset not found")

        with open(dataset_path) as f:
            data = json.load(f)

        assert len(data) >= 50, "Dataset should have at least 50 questions"

        for item in data:
            qa = GoldenQA.model_validate(item)
            assert qa.id.startswith("qa_")
            assert len(qa.question) > 10
            assert len(qa.ground_truth_answer) > 20
            assert len(qa.expected_files) > 0

    def test_golden_dataset_categories(self) -> None:
        """Test that dataset covers expected categories."""
        dataset_path = (
            Path(__file__).parent.parent.parent / "benchmarks" / "datasets" / "golden_qa.json"
        )
        if not dataset_path.exists():
            pytest.skip("Golden dataset not found")

        with open(dataset_path) as f:
            data = json.load(f)

        categories = {item["category"] for item in data}
        expected = {"code_structure", "api", "search", "ingestion"}
        assert expected.issubset(categories), f"Missing categories: {expected - categories}"

    def test_golden_dataset_difficulties(self) -> None:
        """Test that dataset has varied difficulties."""
        dataset_path = (
            Path(__file__).parent.parent.parent / "benchmarks" / "datasets" / "golden_qa.json"
        )
        if not dataset_path.exists():
            pytest.skip("Golden dataset not found")

        with open(dataset_path) as f:
            data = json.load(f)

        difficulties = {item["difficulty"] for item in data}
        assert difficulties == {"easy", "medium", "hard"}
