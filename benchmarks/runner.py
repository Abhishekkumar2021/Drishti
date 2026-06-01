"""Main evaluation runner for RAG pipeline benchmarking.

This module orchestrates the complete evaluation workflow:
1. Load golden Q&A dataset
2. Run retrieval and generation for each question
3. Compute RAGAS metrics
4. Generate aggregate statistics
5. Produce evaluation reports
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from benchmarks.metrics import check_thresholds, compute_all_metrics
from benchmarks.models import (
    AggregateMetrics,
    EvaluationReport,
    EvaluationResult,
    GenerationResult,
    GoldenQA,
    MetricScores,
    RetrievalResult,
)

logger = logging.getLogger(__name__)

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "golden_qa.json"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
DEFAULT_API_BASE = "http://localhost:8000/api/v1"


class EvaluationRunner:
    """Orchestrates RAG evaluation against golden Q&A dataset."""

    def __init__(
        self,
        *,
        api_base: str = DEFAULT_API_BASE,
        dataset_path: Path = DEFAULT_DATASET_PATH,
        results_dir: Path = DEFAULT_RESULTS_DIR,
        repo_path: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Initialize the evaluation runner.

        Args:
            api_base: Base URL for Drishti API.
            dataset_path: Path to golden Q&A JSON file.
            results_dir: Directory to save evaluation results.
            repo_path: Repository path for search/ask queries.
            timeout: HTTP request timeout in seconds.
        """
        self.api_base = api_base.rstrip("/")
        self.dataset_path = dataset_path
        self.results_dir = results_dir
        self.repo_path = repo_path
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> EvaluationRunner:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def load_dataset(self) -> list[GoldenQA]:
        """Load golden Q&A dataset from JSON file.

        Returns:
            List of GoldenQA entries.

        Raises:
            FileNotFoundError: If dataset file doesn't exist.
            ValueError: If dataset is invalid.
        """
        if not self.dataset_path.exists():
            msg = f"Dataset not found: {self.dataset_path}"
            raise FileNotFoundError(msg)

        with open(self.dataset_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            msg = "Dataset must be a JSON array"
            raise ValueError(msg)

        return [GoldenQA.model_validate(item) for item in data]

    async def run_search(self, question: str, filters: dict[str, str] | None = None) -> dict:
        """Execute hybrid search against the API.

        Args:
            question: Search query.
            filters: Optional metadata filters.

        Returns:
            Search response with retrieved chunks.
        """
        if not self._client:
            msg = "Runner must be used as async context manager"
            raise RuntimeError(msg)

        payload = {"query": question, "limit": 10}
        if filters:
            payload["filters"] = filters

        response = await self._client.post(f"{self.api_base}/search", json=payload)
        response.raise_for_status()
        return response.json()

    async def run_ask(
        self,
        question: str,
        filters: dict[str, str] | None = None,
    ) -> tuple[str, list[dict], float]:
        """Execute RAG ask against the API.

        Args:
            question: User question.
            filters: Optional metadata filters.

        Returns:
            Tuple of (answer, contexts, generation_time_ms).
        """
        if not self._client:
            msg = "Runner must be used as async context manager"
            raise RuntimeError(msg)

        payload: dict[str, Any] = {"question": question}
        if filters:
            payload["filters"] = filters

        start = time.perf_counter()
        contexts: list[dict] = []
        answer_parts: list[str] = []

        async with self._client.stream(
            "POST",
            f"{self.api_base}/ask",
            json=payload,
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        event = json.loads(data_str)
                        if event.get("event") == "token":
                            answer_parts.append(event.get("data", {}).get("text", ""))
                        elif event.get("event") == "context":
                            contexts = event.get("data", {}).get("chunks", [])
                    except json.JSONDecodeError:
                        continue

        elapsed_ms = (time.perf_counter() - start) * 1000
        return "".join(answer_parts), contexts, elapsed_ms

    async def evaluate_single(self, qa: GoldenQA) -> EvaluationResult:
        """Evaluate a single Q&A pair.

        Args:
            qa: Golden Q&A entry to evaluate.

        Returns:
            EvaluationResult with scores.
        """
        logger.info("Evaluating: %s - %s", qa.id, qa.question[:50])

        # Run retrieval
        search_start = time.perf_counter()
        search_result = await self.run_search(qa.question)
        retrieval_time_ms = (time.perf_counter() - search_start) * 1000

        retrieved_chunks = search_result.get("results", [])
        retrieved_files = list({c.get("file_path", "") for c in retrieved_chunks})

        retrieval = RetrievalResult(
            qa_id=qa.id,
            question=qa.question,
            retrieved_files=retrieved_files,
            retrieved_chunks=retrieved_chunks,
            expected_files=qa.expected_files,
            retrieval_time_ms=retrieval_time_ms,
        )

        # Run generation
        answer, contexts, generation_time_ms = await self.run_ask(qa.question)
        context_strings = [c.get("content", "") for c in contexts]

        generation = GenerationResult(
            qa_id=qa.id,
            question=qa.question,
            generated_answer=answer,
            ground_truth_answer=qa.ground_truth_answer,
            context_used="\n---\n".join(context_strings),
            generation_time_ms=generation_time_ms,
        )

        # Compute metrics
        scores = compute_all_metrics(
            question=qa.question,
            contexts=context_strings,
            generated_answer=answer,
            ground_truth=qa.ground_truth_answer,
        )

        return EvaluationResult(
            qa_id=qa.id,
            question=qa.question,
            category=qa.category,
            difficulty=qa.difficulty,
            retrieval=retrieval,
            generation=generation,
            scores=scores,
        )

    def compute_aggregates(self, results: list[EvaluationResult]) -> AggregateMetrics:
        """Compute aggregate statistics from individual results.

        Args:
            results: List of individual evaluation results.

        Returns:
            Aggregated metrics with means, std devs, and breakdowns.
        """
        if not results:
            return AggregateMetrics(
                total_questions=0,
                context_precision_mean=0.0,
                context_precision_std=0.0,
                context_recall_mean=0.0,
                context_recall_std=0.0,
                faithfulness_mean=0.0,
                faithfulness_std=0.0,
                answer_relevancy_mean=0.0,
                answer_relevancy_std=0.0,
                avg_retrieval_time_ms=0.0,
                avg_generation_time_ms=0.0,
            )

        precision_vals = [r.scores.context_precision for r in results]
        recall_vals = [r.scores.context_recall for r in results]
        faithfulness_vals = [r.scores.faithfulness for r in results]
        relevancy_vals = [r.scores.answer_relevancy for r in results]
        retrieval_times = [r.retrieval.retrieval_time_ms for r in results]
        generation_times = [r.generation.generation_time_ms for r in results]

        # Breakdown by category
        categories: dict[str, list[EvaluationResult]] = {}
        for r in results:
            categories.setdefault(r.category, []).append(r)

        metrics_by_category: dict[str, dict[str, float]] = {}
        for cat, cat_results in categories.items():
            metrics_by_category[cat] = {
                "context_precision": statistics.mean(
                    r.scores.context_precision for r in cat_results
                ),
                "context_recall": statistics.mean(r.scores.context_recall for r in cat_results),
                "faithfulness": statistics.mean(r.scores.faithfulness for r in cat_results),
                "answer_relevancy": statistics.mean(r.scores.answer_relevancy for r in cat_results),
                "count": float(len(cat_results)),
            }

        # Breakdown by difficulty
        difficulties: dict[str, list[EvaluationResult]] = {}
        for r in results:
            difficulties.setdefault(r.difficulty.value, []).append(r)

        metrics_by_difficulty: dict[str, dict[str, float]] = {}
        for diff, diff_results in difficulties.items():
            metrics_by_difficulty[diff] = {
                "context_precision": statistics.mean(
                    r.scores.context_precision for r in diff_results
                ),
                "context_recall": statistics.mean(r.scores.context_recall for r in diff_results),
                "faithfulness": statistics.mean(r.scores.faithfulness for r in diff_results),
                "answer_relevancy": statistics.mean(
                    r.scores.answer_relevancy for r in diff_results
                ),
                "count": float(len(diff_results)),
            }

        return AggregateMetrics(
            total_questions=len(results),
            context_precision_mean=statistics.mean(precision_vals),
            context_precision_std=statistics.stdev(precision_vals)
            if len(precision_vals) > 1
            else 0.0,
            context_recall_mean=statistics.mean(recall_vals),
            context_recall_std=statistics.stdev(recall_vals) if len(recall_vals) > 1 else 0.0,
            faithfulness_mean=statistics.mean(faithfulness_vals),
            faithfulness_std=statistics.stdev(faithfulness_vals)
            if len(faithfulness_vals) > 1
            else 0.0,
            answer_relevancy_mean=statistics.mean(relevancy_vals),
            answer_relevancy_std=statistics.stdev(relevancy_vals)
            if len(relevancy_vals) > 1
            else 0.0,
            avg_retrieval_time_ms=statistics.mean(retrieval_times),
            avg_generation_time_ms=statistics.mean(generation_times),
            metrics_by_category=metrics_by_category,
            metrics_by_difficulty=metrics_by_difficulty,
        )

    async def run_evaluation(
        self,
        *,
        chunking_strategy: str = "ast",
        max_questions: int | None = None,
        categories: list[str] | None = None,
    ) -> EvaluationReport:
        """Run complete evaluation pipeline.

        Args:
            chunking_strategy: Label for the chunking approach ('ast' or 'naive').
            max_questions: Limit number of questions to evaluate.
            categories: Filter to specific categories.

        Returns:
            Complete evaluation report.
        """
        dataset = self.load_dataset()

        # Filter by category if specified
        if categories:
            dataset = [qa for qa in dataset if qa.category in categories]

        # Limit questions if specified
        if max_questions:
            dataset = dataset[:max_questions]

        logger.info(
            "Running evaluation on %d questions (strategy=%s)", len(dataset), chunking_strategy
        )

        results: list[EvaluationResult] = []
        for qa in dataset:
            try:
                result = await self.evaluate_single(qa)
                results.append(result)
            except Exception as e:
                logger.error("Failed to evaluate %s: %s", qa.id, e)
                # Add failed result with zero scores
                results.append(
                    EvaluationResult(
                        qa_id=qa.id,
                        question=qa.question,
                        category=qa.category,
                        difficulty=qa.difficulty,
                        retrieval=RetrievalResult(
                            qa_id=qa.id,
                            question=qa.question,
                            expected_files=qa.expected_files,
                        ),
                        generation=GenerationResult(
                            qa_id=qa.id,
                            question=qa.question,
                            generated_answer=f"ERROR: {e}",
                            ground_truth_answer=qa.ground_truth_answer,
                            context_used="",
                        ),
                        scores=MetricScores(
                            context_precision=0.0,
                            context_recall=0.0,
                            faithfulness=0.0,
                            answer_relevancy=0.0,
                        ),
                    )
                )

        aggregates = self.compute_aggregates(results)

        # Check thresholds using mean scores
        mean_scores = MetricScores(
            context_precision=aggregates.context_precision_mean,
            context_recall=aggregates.context_recall_mean,
            faithfulness=aggregates.faithfulness_mean,
            answer_relevancy=aggregates.answer_relevancy_mean,
        )
        passed, threshold_details = check_thresholds(mean_scores)

        return EvaluationReport(
            run_id=str(uuid.uuid4()),
            chunking_strategy=chunking_strategy,
            model_config_summary={
                "api_base": self.api_base,
                "dataset": str(self.dataset_path),
            },
            aggregate_metrics=aggregates,
            individual_results=results,
            passed_thresholds=passed,
            threshold_details=threshold_details,
        )

    def save_report(self, report: EvaluationReport, filename: str | None = None) -> Path:
        """Save evaluation report to JSON file.

        Args:
            report: Evaluation report to save.
            filename: Optional custom filename.

        Returns:
            Path to saved report file.
        """
        self.results_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"eval_{report.chunking_strategy}_{timestamp}.json"

        filepath = self.results_dir / filename
        with open(filepath, "w") as f:
            f.write(report.model_dump_json(indent=2))

        logger.info("Saved report to %s", filepath)
        return filepath


async def main() -> None:
    """CLI entry point for evaluation runner."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Run Drishti RAG evaluation")
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        help="Drishti API base URL",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to golden Q&A dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory for evaluation results",
    )
    parser.add_argument(
        "--strategy",
        choices=["ast", "naive"],
        default="ast",
        help="Chunking strategy label",
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        help="Limit number of questions to evaluate",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Filter to specific categories",
    )

    args = parser.parse_args()

    async with EvaluationRunner(
        api_base=args.api_base,
        dataset_path=args.dataset,
        results_dir=args.output_dir,
    ) as runner:
        report = await runner.run_evaluation(
            chunking_strategy=args.strategy,
            max_questions=args.max_questions,
            categories=args.categories,
        )
        runner.save_report(report)

        # Print summary
        agg = report.aggregate_metrics
        print("\n" + "=" * 60)
        print(f"Evaluation Complete: {agg.total_questions} questions")
        print("=" * 60)
        print(
            f"Context Precision:  {agg.context_precision_mean:.1%} (±{agg.context_precision_std:.1%})"
        )
        print(f"Context Recall:     {agg.context_recall_mean:.1%} (±{agg.context_recall_std:.1%})")
        print(f"Faithfulness:       {agg.faithfulness_mean:.1%} (±{agg.faithfulness_std:.1%})")
        print(
            f"Answer Relevancy:   {agg.answer_relevancy_mean:.1%} (±{agg.answer_relevancy_std:.1%})"
        )
        print("-" * 60)
        print(f"Avg Retrieval Time: {agg.avg_retrieval_time_ms:.0f}ms")
        print(f"Avg Generation Time: {agg.avg_generation_time_ms:.0f}ms")
        print("-" * 60)
        status = "✅ PASSED" if report.passed_thresholds else "❌ FAILED"
        print(f"Threshold Check: {status}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
