"""Comparison runner for AST vs Naive chunking evaluation.

This script orchestrates the comparison between AST-aware chunking and naive
character-based chunking to demonstrate the improvement from structural parsing.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from benchmarks.models import ComparisonReport, EvaluationReport
from benchmarks.report import (
    format_comparison_report,
    save_comparison_report,
)
from benchmarks.runner import DEFAULT_RESULTS_DIR

logger = logging.getLogger(__name__)


def load_report(path: Path) -> EvaluationReport:
    """Load an evaluation report from JSON file.

    Args:
        path: Path to JSON report file.

    Returns:
        Loaded EvaluationReport.
    """
    with open(path) as f:
        data = json.load(f)
    return EvaluationReport.model_validate(data)


def generate_comparison(
    ast_report: EvaluationReport,
    naive_report: EvaluationReport,
) -> ComparisonReport:
    """Generate comparison report from AST and naive evaluations.

    Args:
        ast_report: Evaluation with AST-aware chunking.
        naive_report: Evaluation with naive chunking.

    Returns:
        Comparison report with improvements calculated.
    """
    ast_metrics = ast_report.aggregate_metrics
    naive_metrics = naive_report.aggregate_metrics

    improvement = {
        "context_precision": ast_metrics.context_precision_mean
        - naive_metrics.context_precision_mean,
        "context_recall": ast_metrics.context_recall_mean - naive_metrics.context_recall_mean,
        "faithfulness": ast_metrics.faithfulness_mean - naive_metrics.faithfulness_mean,
        "answer_relevancy": ast_metrics.answer_relevancy_mean - naive_metrics.answer_relevancy_mean,
    }

    # Generate summary
    improvements_list = []
    if improvement["context_precision"] > 0:
        improvements_list.append(
            f"Context precision improved by {improvement['context_precision'] * 100:.1f} percentage points"
        )
    if improvement["context_recall"] > 0:
        improvements_list.append(
            f"Context recall improved by {improvement['context_recall'] * 100:.1f} percentage points"
        )
    if improvement["faithfulness"] > 0:
        improvements_list.append(
            f"Faithfulness improved by {improvement['faithfulness'] * 100:.1f} percentage points"
        )
    if improvement["answer_relevancy"] > 0:
        improvements_list.append(
            f"Answer relevancy improved by {improvement['answer_relevancy'] * 100:.1f} percentage points"
        )

    if all(v > 0 for v in improvement.values()):
        summary = (
            f"AST-aware chunking outperforms naive chunking across all metrics. "
            f"{' '.join(improvements_list)}. "
            f"This validates the core hypothesis that structural code understanding "
            f"leads to better RAG quality."
        )
    elif any(v > 0 for v in improvement.values()):
        positive = [k for k, v in improvement.items() if v > 0]
        summary = (
            f"AST-aware chunking shows improvements in {', '.join(positive)}. "
            f"{' '.join(improvements_list)}."
        )
    else:
        summary = (
            "Results do not show expected improvements. "
            "Further investigation needed into evaluation setup."
        )

    return ComparisonReport(
        timestamp=datetime.utcnow(),
        ast_report=ast_report,
        naive_report=naive_report,
        improvement=improvement,
        summary=summary,
    )


async def main() -> None:
    """CLI entry point for comparison runner."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Compare AST vs Naive chunking evaluation results")
    parser.add_argument(
        "--ast-report",
        type=Path,
        required=True,
        help="Path to AST-aware evaluation report JSON",
    )
    parser.add_argument(
        "--naive-report",
        type=Path,
        required=True,
        help="Path to naive chunking evaluation report JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RESULTS_DIR / "comparison.md",
        help="Output path for comparison report",
    )

    args = parser.parse_args()

    if not args.ast_report.exists():
        logger.error("AST report not found: %s", args.ast_report)
        return

    if not args.naive_report.exists():
        logger.error("Naive report not found: %s", args.naive_report)
        return

    logger.info("Loading AST report: %s", args.ast_report)
    ast_report = load_report(args.ast_report)

    logger.info("Loading naive report: %s", args.naive_report)
    naive_report = load_report(args.naive_report)

    logger.info("Generating comparison...")
    comparison = generate_comparison(ast_report, naive_report)

    # Print to console
    print(format_comparison_report(comparison))

    # Save to file
    save_comparison_report(comparison, args.output)
    logger.info("Saved comparison report to %s", args.output)

    # Also save JSON version
    json_output = args.output.with_suffix(".json")
    with open(json_output, "w") as f:
        f.write(comparison.model_dump_json(indent=2))
    logger.info("Saved JSON comparison to %s", json_output)


if __name__ == "__main__":
    asyncio.run(main())
