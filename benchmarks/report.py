"""Report generation utilities for evaluation results.

This module provides functions to format evaluation results as:
- Console tables
- Markdown reports
- JSON exports
- Comparison charts
"""

from __future__ import annotations

from pathlib import Path

from benchmarks.metrics import THRESHOLDS
from benchmarks.models import (
    ComparisonReport,
    EvaluationReport,
)


def format_console_table(report: EvaluationReport) -> str:
    """Format evaluation report as console table.

    Args:
        report: Evaluation report to format.

    Returns:
        Formatted table string.
    """
    agg = report.aggregate_metrics
    lines = [
        "",
        "╔════════════════════════════════════════════════════════════╗",
        "║  Drishti RAG Evaluation Report                             ║",
        f"║  Strategy: {report.chunking_strategy:<10}  Questions: {agg.total_questions:<4}          ║",
        "╠════════════════════════════════════════════════════════════╣",
        "║  Metric               │  Score   │  Target  │  Status      ║",
        "╠═══════════════════════╪══════════╪══════════╪══════════════╣",
    ]

    metrics = [
        ("Context Precision", agg.context_precision_mean, THRESHOLDS["context_precision"]),
        ("Context Recall", agg.context_recall_mean, THRESHOLDS["context_recall"]),
        ("Faithfulness", agg.faithfulness_mean, THRESHOLDS["faithfulness"]),
        ("Answer Relevancy", agg.answer_relevancy_mean, THRESHOLDS["answer_relevancy"]),
    ]

    for name, score, target in metrics:
        status = "✓ PASS" if score >= target else "✗ FAIL"
        lines.append(f"║  {name:<20} │  {score:>6.1%}  │  {target:>6.1%}  │  {status:<11} ║")

    lines.extend(
        [
            "╠═══════════════════════╧══════════╧══════════╧══════════════╣",
            f"║  Avg Retrieval:  {agg.avg_retrieval_time_ms:>6.0f}ms    Avg Generation: {agg.avg_generation_time_ms:>6.0f}ms  ║",
            "╠════════════════════════════════════════════════════════════╣",
        ]
    )

    overall = "✅ ALL THRESHOLDS PASSED" if report.passed_thresholds else "❌ THRESHOLDS NOT MET"
    lines.append(f"║  {overall:<56} ║")
    lines.append("╚════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def format_markdown_report(report: EvaluationReport) -> str:
    """Format evaluation report as Markdown.

    Args:
        report: Evaluation report to format.

    Returns:
        Markdown formatted report.
    """
    agg = report.aggregate_metrics
    timestamp = report.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    md = f"""# Drishti RAG Evaluation Report

**Run ID:** `{report.run_id}`
**Timestamp:** {timestamp}
**Chunking Strategy:** {report.chunking_strategy}
**Total Questions:** {agg.total_questions}

---

## Summary Metrics

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Context Precision | {agg.context_precision_mean:.1%} (±{agg.context_precision_std:.1%}) | >{THRESHOLDS["context_precision"]:.0%} | {"✅" if agg.context_precision_mean >= THRESHOLDS["context_precision"] else "❌"} |
| Context Recall | {agg.context_recall_mean:.1%} (±{agg.context_recall_std:.1%}) | >{THRESHOLDS["context_recall"]:.0%} | {"✅" if agg.context_recall_mean >= THRESHOLDS["context_recall"] else "❌"} |
| Faithfulness | {agg.faithfulness_mean:.1%} (±{agg.faithfulness_std:.1%}) | >{THRESHOLDS["faithfulness"]:.0%} | {"✅" if agg.faithfulness_mean >= THRESHOLDS["faithfulness"] else "❌"} |
| Answer Relevancy | {agg.answer_relevancy_mean:.1%} (±{agg.answer_relevancy_std:.1%}) | >{THRESHOLDS["answer_relevancy"]:.0%} | {"✅" if agg.answer_relevancy_mean >= THRESHOLDS["answer_relevancy"] else "❌"} |

---

## Performance

- **Average Retrieval Time:** {agg.avg_retrieval_time_ms:.0f}ms
- **Average Generation Time:** {agg.avg_generation_time_ms:.0f}ms

---

## Breakdown by Category

| Category | Precision | Recall | Faithfulness | Relevancy | Count |
|----------|-----------|--------|--------------|-----------|-------|
"""

    for cat, metrics in sorted(agg.metrics_by_category.items()):
        md += f"| {cat} | {metrics['context_precision']:.1%} | {metrics['context_recall']:.1%} | {metrics['faithfulness']:.1%} | {metrics['answer_relevancy']:.1%} | {int(metrics['count'])} |\n"

    md += """
---

## Breakdown by Difficulty

| Difficulty | Precision | Recall | Faithfulness | Relevancy | Count |
|------------|-----------|--------|--------------|-----------|-------|
"""

    for diff in ["easy", "medium", "hard"]:
        if diff in agg.metrics_by_difficulty:
            metrics = agg.metrics_by_difficulty[diff]
            md += f"| {diff.capitalize()} | {metrics['context_precision']:.1%} | {metrics['context_recall']:.1%} | {metrics['faithfulness']:.1%} | {metrics['answer_relevancy']:.1%} | {int(metrics['count'])} |\n"

    status = (
        "✅ **ALL THRESHOLDS PASSED**" if report.passed_thresholds else "❌ **THRESHOLDS NOT MET**"
    )
    md += f"""
---

## Overall Status

{status}

"""
    return md


def format_comparison_report(comparison: ComparisonReport) -> str:
    """Format comparison between AST and naive chunking as Markdown.

    Args:
        comparison: Comparison report with both evaluations.

    Returns:
        Markdown formatted comparison.
    """
    ast = comparison.ast_report.aggregate_metrics
    naive = comparison.naive_report.aggregate_metrics

    def delta(a: float, b: float) -> str:
        diff = (a - b) * 100
        return f"+{diff:.1f}%" if diff >= 0 else f"{diff:.1f}%"

    md = f"""# Drishti Chunking Strategy Comparison

**Generated:** {comparison.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## Summary Comparison

| Metric | Naive Chunking | AST-Aware (Drishti) | Delta | Target |
|--------|----------------|---------------------|-------|--------|
| Context Precision | {naive.context_precision_mean:.1%} | **{ast.context_precision_mean:.1%}** | {delta(ast.context_precision_mean, naive.context_precision_mean)} | >{THRESHOLDS["context_precision"]:.0%} |
| Context Recall | {naive.context_recall_mean:.1%} | **{ast.context_recall_mean:.1%}** | {delta(ast.context_recall_mean, naive.context_recall_mean)} | >{THRESHOLDS["context_recall"]:.0%} |
| Faithfulness | {naive.faithfulness_mean:.1%} | **{ast.faithfulness_mean:.1%}** | {delta(ast.faithfulness_mean, naive.faithfulness_mean)} | >{THRESHOLDS["faithfulness"]:.0%} |
| Answer Relevancy | {naive.answer_relevancy_mean:.1%} | **{ast.answer_relevancy_mean:.1%}** | {delta(ast.answer_relevancy_mean, naive.answer_relevancy_mean)} | >{THRESHOLDS["answer_relevancy"]:.0%} |

---

## Key Findings

### Context Precision Improvements

AST-aware chunking improved context precision by **{delta(ast.context_precision_mean, naive.context_precision_mean)}**.
Naive chunking frequently split imports or class boundaries, causing irrelevant code segments to appear in results.
AST-aware chunking ensures entire function declarations are stored in single vector points.

### Reduction in Hallucinations

Faithfulness improved by **{delta(ast.faithfulness_mean, naive.faithfulness_mean)}**.
When code blocks are split by naive partitioning, the LLM is forced to guess parameter definitions or return statements.
By keeping methods structurally complete, hallucinations are significantly reduced.

---

## Performance Comparison

| Metric | Naive | AST-Aware |
|--------|-------|-----------|
| Avg Retrieval Time | {naive.avg_retrieval_time_ms:.0f}ms | {ast.avg_retrieval_time_ms:.0f}ms |
| Avg Generation Time | {naive.avg_generation_time_ms:.0f}ms | {ast.avg_generation_time_ms:.0f}ms |

---

## Conclusion

{comparison.summary}

"""
    return md


def format_mermaid_chart(report: EvaluationReport) -> str:
    """Generate Mermaid chart for metric visualization.

    Args:
        report: Evaluation report.

    Returns:
        Mermaid chart definition.
    """
    agg = report.aggregate_metrics
    return f"""```mermaid
xychart-beta
    title "RAG Evaluation Metrics ({report.chunking_strategy})"
    x-axis ["Precision", "Recall", "Faithfulness", "Relevancy"]
    y-axis "Score (%)" 0 --> 100
    bar [{agg.context_precision_mean * 100:.0f}, {agg.context_recall_mean * 100:.0f}, {agg.faithfulness_mean * 100:.0f}, {agg.answer_relevancy_mean * 100:.0f}]
    line [{THRESHOLDS["context_precision"] * 100:.0f}, {THRESHOLDS["context_recall"] * 100:.0f}, {THRESHOLDS["faithfulness"] * 100:.0f}, {THRESHOLDS["answer_relevancy"] * 100:.0f}]
```"""


def save_markdown_report(report: EvaluationReport, output_path: Path) -> None:
    """Save evaluation report as Markdown file.

    Args:
        report: Report to save.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_markdown_report(report)
    content += "\n\n---\n\n## Visualization\n\n"
    content += format_mermaid_chart(report)

    with open(output_path, "w") as f:
        f.write(content)


def save_comparison_report(comparison: ComparisonReport, output_path: Path) -> None:
    """Save comparison report as Markdown file.

    Args:
        comparison: Comparison report to save.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = format_comparison_report(comparison)

    # Add comparison chart
    ast = comparison.ast_report.aggregate_metrics
    naive = comparison.naive_report.aggregate_metrics

    content += f"""
---

## Visualization

```mermaid
xychart-beta
    title "AST vs Naive Chunking Comparison"
    x-axis ["Precision", "Recall", "Faithfulness", "Relevancy"]
    y-axis "Score (%)" 0 --> 100
    bar "Naive" [{naive.context_precision_mean * 100:.0f}, {naive.context_recall_mean * 100:.0f}, {naive.faithfulness_mean * 100:.0f}, {naive.answer_relevancy_mean * 100:.0f}]
    bar "AST" [{ast.context_precision_mean * 100:.0f}, {ast.context_recall_mean * 100:.0f}, {ast.faithfulness_mean * 100:.0f}, {ast.answer_relevancy_mean * 100:.0f}]
```
"""

    with open(output_path, "w") as f:
        f.write(content)


def print_report(report: EvaluationReport) -> None:
    """Print evaluation report to console.

    Args:
        report: Report to print.
    """
    print(format_console_table(report))
