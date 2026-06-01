#!/usr/bin/env python3
"""Evaluate retrieval quality (context precision and recall).

This script runs retrieval-only evaluation against the golden Q&A dataset,
measuring how well the hybrid search finds relevant code chunks.

Usage:
    python -m benchmarks.eval_retrieval --api-base http://localhost:8000/api/v1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import statistics
import time
from pathlib import Path

import httpx

from benchmarks.metrics import (
    THRESHOLDS,
    _fallback_context_precision,
    _fallback_context_recall,
)
from benchmarks.models import GoldenQA
from benchmarks.runner import DEFAULT_API_BASE, DEFAULT_DATASET_PATH, DEFAULT_RESULTS_DIR

logger = logging.getLogger(__name__)


async def evaluate_retrieval(
    api_base: str,
    dataset_path: Path,
    output_dir: Path,
    max_questions: int | None = None,
) -> dict:
    """Run retrieval-only evaluation.

    Args:
        api_base: Drishti API base URL.
        dataset_path: Path to golden Q&A dataset.
        output_dir: Directory for results.
        max_questions: Optional limit on questions.

    Returns:
        Evaluation results dictionary.
    """
    # Load dataset
    with open(dataset_path) as f:
        data = json.load(f)
    dataset = [GoldenQA.model_validate(item) for item in data]

    if max_questions:
        dataset = dataset[:max_questions]

    logger.info("Evaluating retrieval on %d questions", len(dataset))

    results = []
    questions = []
    contexts_list = []
    ground_truths = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for qa in dataset:
            start = time.perf_counter()
            try:
                response = await client.post(
                    f"{api_base}/search",
                    json={"query": qa.question, "limit": 10},
                )
                response.raise_for_status()
                search_result = response.json()
            except Exception as e:
                logger.error("Search failed for %s: %s", qa.id, e)
                results.append(
                    {
                        "qa_id": qa.id,
                        "question": qa.question,
                        "error": str(e),
                        "precision": 0.0,
                        "recall": 0.0,
                    }
                )
                continue

            elapsed_ms = (time.perf_counter() - start) * 1000
            chunks = search_result.get("results", [])
            retrieved_files = list({c.get("file_path", "") for c in chunks})
            context_texts = [c.get("content", "") for c in chunks]

            # Check file overlap for simple precision/recall
            expected_set = set(qa.expected_files)
            retrieved_set = set(retrieved_files)
            file_precision = (
                len(expected_set & retrieved_set) / len(retrieved_set) if retrieved_set else 0.0
            )
            file_recall = (
                len(expected_set & retrieved_set) / len(expected_set) if expected_set else 1.0
            )

            questions.append(qa.question)
            contexts_list.append(context_texts)
            ground_truths.append(qa.ground_truth_answer)

            results.append(
                {
                    "qa_id": qa.id,
                    "question": qa.question,
                    "expected_files": qa.expected_files,
                    "retrieved_files": retrieved_files,
                    "file_precision": file_precision,
                    "file_recall": file_recall,
                    "retrieval_time_ms": elapsed_ms,
                    "num_chunks": len(chunks),
                }
            )

    # Compute aggregate metrics
    if questions:
        content_precision = _fallback_context_precision(questions, contexts_list, ground_truths)
        content_recall = _fallback_context_recall(questions, contexts_list, ground_truths)

        for i, r in enumerate(results):
            if "error" not in r:
                r["content_precision"] = content_precision[i] if i < len(content_precision) else 0.0
                r["content_recall"] = content_recall[i] if i < len(content_recall) else 0.0

    valid_results = [r for r in results if "error" not in r]
    summary = {
        "total_questions": len(dataset),
        "successful_queries": len(valid_results),
        "file_precision_mean": statistics.mean(r["file_precision"] for r in valid_results)
        if valid_results
        else 0.0,
        "file_recall_mean": statistics.mean(r["file_recall"] for r in valid_results)
        if valid_results
        else 0.0,
        "content_precision_mean": statistics.mean(
            r.get("content_precision", 0.0) for r in valid_results
        )
        if valid_results
        else 0.0,
        "content_recall_mean": statistics.mean(r.get("content_recall", 0.0) for r in valid_results)
        if valid_results
        else 0.0,
        "avg_retrieval_time_ms": statistics.mean(r["retrieval_time_ms"] for r in valid_results)
        if valid_results
        else 0.0,
        "avg_chunks_returned": statistics.mean(r["num_chunks"] for r in valid_results)
        if valid_results
        else 0.0,
    }

    output = {
        "summary": summary,
        "individual_results": results,
        "thresholds": {
            "context_precision": THRESHOLDS["context_precision"],
            "context_recall": THRESHOLDS["context_recall"],
        },
        "passed": (
            summary["content_precision_mean"] >= THRESHOLDS["context_precision"]
            and summary["content_recall_mean"] >= THRESHOLDS["context_recall"]
        ),
    }

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "retrieval_eval.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info("Saved retrieval evaluation to %s", output_path)

    return output


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--max-questions", type=int)

    args = parser.parse_args()

    result = asyncio.run(
        evaluate_retrieval(
            api_base=args.api_base,
            dataset_path=args.dataset,
            output_dir=args.output_dir,
            max_questions=args.max_questions,
        )
    )

    summary = result["summary"]
    print("\n" + "=" * 50)
    print("Retrieval Evaluation Summary")
    print("=" * 50)
    print(f"Questions Evaluated: {summary['total_questions']}")
    print(f"Successful Queries:  {summary['successful_queries']}")
    print("-" * 50)
    print(f"File Precision:      {summary['file_precision_mean']:.1%}")
    print(f"File Recall:         {summary['file_recall_mean']:.1%}")
    print(f"Content Precision:   {summary['content_precision_mean']:.1%}")
    print(f"Content Recall:      {summary['content_recall_mean']:.1%}")
    print("-" * 50)
    print(f"Avg Retrieval Time:  {summary['avg_retrieval_time_ms']:.0f}ms")
    print(f"Avg Chunks Returned: {summary['avg_chunks_returned']:.1f}")
    print("-" * 50)
    status = "✅ PASSED" if result["passed"] else "❌ FAILED"
    print(f"Threshold Check: {status}")
    print("=" * 50)


if __name__ == "__main__":
    main()
