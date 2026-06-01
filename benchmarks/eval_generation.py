#!/usr/bin/env python3
"""Evaluate generation quality (faithfulness and answer relevancy).

This script runs generation evaluation against the golden Q&A dataset,
measuring how well the LLM produces faithful, relevant answers.

Usage:
    python -m benchmarks.eval_generation --api-base http://localhost:8000/api/v1
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
    _fallback_answer_relevancy,
    _fallback_faithfulness,
)
from benchmarks.models import GoldenQA
from benchmarks.runner import DEFAULT_API_BASE, DEFAULT_DATASET_PATH, DEFAULT_RESULTS_DIR

logger = logging.getLogger(__name__)


async def stream_ask(
    client: httpx.AsyncClient, api_base: str, question: str
) -> tuple[str, list[str]]:
    """Execute streaming ask and collect answer + contexts.

    Args:
        client: HTTP client.
        api_base: API base URL.
        question: Question to ask.

    Returns:
        Tuple of (answer, context_strings).
    """
    contexts: list[str] = []
    answer_parts: list[str] = []

    async with client.stream(
        "POST",
        f"{api_base}/ask",
        json={"question": question},
        headers={"Accept": "text/event-stream"},
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.strip():
                continue
            if line.startswith("data: "):
                try:
                    event = json.loads(line[6:])
                    if event.get("event") == "token":
                        answer_parts.append(event.get("data", {}).get("text", ""))
                    elif event.get("event") == "context":
                        chunks = event.get("data", {}).get("chunks", [])
                        contexts = [c.get("content", "") for c in chunks]
                except json.JSONDecodeError:
                    continue

    return "".join(answer_parts), contexts


async def evaluate_generation(
    api_base: str,
    dataset_path: Path,
    output_dir: Path,
    max_questions: int | None = None,
) -> dict:
    """Run generation evaluation.

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

    logger.info("Evaluating generation on %d questions", len(dataset))

    results = []
    questions = []
    contexts_list = []
    answers = []
    ground_truths = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for qa in dataset:
            logger.info("Evaluating: %s", qa.id)
            start = time.perf_counter()

            try:
                answer, contexts = await stream_ask(client, api_base, qa.question)
            except Exception as e:
                logger.error("Ask failed for %s: %s", qa.id, e)
                results.append(
                    {
                        "qa_id": qa.id,
                        "question": qa.question,
                        "error": str(e),
                        "faithfulness": 0.0,
                        "answer_relevancy": 0.0,
                    }
                )
                continue

            elapsed_ms = (time.perf_counter() - start) * 1000

            questions.append(qa.question)
            contexts_list.append(contexts)
            answers.append(answer)
            ground_truths.append(qa.ground_truth_answer)

            results.append(
                {
                    "qa_id": qa.id,
                    "question": qa.question,
                    "generated_answer": answer[:500] + "..." if len(answer) > 500 else answer,
                    "ground_truth_preview": qa.ground_truth_answer[:200] + "...",
                    "generation_time_ms": elapsed_ms,
                    "context_count": len(contexts),
                    "answer_length": len(answer),
                }
            )

    # Compute faithfulness and relevancy
    if questions:
        faithfulness_scores = _fallback_faithfulness(questions, contexts_list, answers)
        relevancy_scores = _fallback_answer_relevancy(questions, answers)

        for i, r in enumerate(results):
            if "error" not in r:
                r["faithfulness"] = faithfulness_scores[i] if i < len(faithfulness_scores) else 0.0
                r["answer_relevancy"] = relevancy_scores[i] if i < len(relevancy_scores) else 0.0

    valid_results = [r for r in results if "error" not in r]
    summary = {
        "total_questions": len(dataset),
        "successful_queries": len(valid_results),
        "faithfulness_mean": statistics.mean(r.get("faithfulness", 0.0) for r in valid_results)
        if valid_results
        else 0.0,
        "answer_relevancy_mean": statistics.mean(
            r.get("answer_relevancy", 0.0) for r in valid_results
        )
        if valid_results
        else 0.0,
        "avg_generation_time_ms": statistics.mean(r["generation_time_ms"] for r in valid_results)
        if valid_results
        else 0.0,
        "avg_answer_length": statistics.mean(r["answer_length"] for r in valid_results)
        if valid_results
        else 0.0,
    }

    if len(valid_results) > 1:
        summary["faithfulness_std"] = statistics.stdev(
            r.get("faithfulness", 0.0) for r in valid_results
        )
        summary["answer_relevancy_std"] = statistics.stdev(
            r.get("answer_relevancy", 0.0) for r in valid_results
        )

    output = {
        "summary": summary,
        "individual_results": results,
        "thresholds": {
            "faithfulness": THRESHOLDS["faithfulness"],
            "answer_relevancy": THRESHOLDS["answer_relevancy"],
        },
        "passed": (
            summary["faithfulness_mean"] >= THRESHOLDS["faithfulness"]
            and summary["answer_relevancy_mean"] >= THRESHOLDS["answer_relevancy"]
        ),
    }

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "generation_eval.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info("Saved generation evaluation to %s", output_path)

    return output


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Evaluate generation quality")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--max-questions", type=int)

    args = parser.parse_args()

    result = asyncio.run(
        evaluate_generation(
            api_base=args.api_base,
            dataset_path=args.dataset,
            output_dir=args.output_dir,
            max_questions=args.max_questions,
        )
    )

    summary = result["summary"]
    print("\n" + "=" * 50)
    print("Generation Evaluation Summary")
    print("=" * 50)
    print(f"Questions Evaluated: {summary['total_questions']}")
    print(f"Successful Queries:  {summary['successful_queries']}")
    print("-" * 50)
    print(f"Faithfulness:        {summary['faithfulness_mean']:.1%}")
    print(f"Answer Relevancy:    {summary['answer_relevancy_mean']:.1%}")
    print("-" * 50)
    print(f"Avg Generation Time: {summary['avg_generation_time_ms']:.0f}ms")
    print(f"Avg Answer Length:   {summary['avg_answer_length']:.0f} chars")
    print("-" * 50)
    status = "✅ PASSED" if result["passed"] else "❌ FAILED"
    print(f"Threshold Check: {status}")
    print("=" * 50)


if __name__ == "__main__":
    main()
