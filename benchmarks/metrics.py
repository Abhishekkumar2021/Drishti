"""RAGAS metric computation wrappers.

This module provides functions to compute RAG evaluation metrics using the RAGAS library.
Metrics include context precision, context recall, faithfulness, and answer relevancy.
"""

from __future__ import annotations

import logging
from typing import Any

from benchmarks.models import MetricScores

logger = logging.getLogger(__name__)

# Target thresholds from docs/evaluation/metrics.md
THRESHOLDS = {
    "context_precision": 0.85,
    "context_recall": 0.90,
    "faithfulness": 0.95,
    "answer_relevancy": 0.90,
}


def _safe_import_ragas() -> tuple[Any, ...]:
    """Safely import RAGAS components with fallback for missing dependencies."""
    try:
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        return evaluate, context_precision, context_recall, faithfulness, answer_relevancy
    except ImportError as e:
        logger.warning("RAGAS not available: %s. Install with: pip install ragas", e)
        return None, None, None, None, None


def compute_context_precision(
    questions: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> list[float]:
    """Compute context precision scores.

    Context precision measures if the top-ranked retrieved contexts are relevant.

    Args:
        questions: List of questions asked.
        contexts: List of retrieved context lists (one list per question).
        ground_truths: List of expected answers.

    Returns:
        List of precision scores (0.0-1.0) for each question.
    """
    evaluate_fn, context_precision, *_ = _safe_import_ragas()
    if evaluate_fn is None:
        return _fallback_context_precision(questions, contexts, ground_truths)

    try:
        from datasets import Dataset

        data = {
            "question": questions,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)
        result = evaluate_fn(dataset, metrics=[context_precision])
        return [float(result["context_precision"])] * len(questions)
    except Exception as e:
        logger.warning("RAGAS context_precision failed: %s", e)
        return _fallback_context_precision(questions, contexts, ground_truths)


def compute_context_recall(
    questions: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> list[float]:
    """Compute context recall scores.

    Context recall measures if all necessary information was retrieved.

    Args:
        questions: List of questions asked.
        contexts: List of retrieved context lists.
        ground_truths: List of expected answers.

    Returns:
        List of recall scores (0.0-1.0) for each question.
    """
    evaluate_fn, _, context_recall, *_ = _safe_import_ragas()
    if evaluate_fn is None:
        return _fallback_context_recall(questions, contexts, ground_truths)

    try:
        from datasets import Dataset

        data = {
            "question": questions,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
        dataset = Dataset.from_dict(data)
        result = evaluate_fn(dataset, metrics=[context_recall])
        return [float(result["context_recall"])] * len(questions)
    except Exception as e:
        logger.warning("RAGAS context_recall failed: %s", e)
        return _fallback_context_recall(questions, contexts, ground_truths)


def compute_faithfulness(
    questions: list[str],
    contexts: list[list[str]],
    answers: list[str],
) -> list[float]:
    """Compute faithfulness scores.

    Faithfulness measures if the generated answer is supported by the context.

    Args:
        questions: List of questions asked.
        contexts: List of retrieved context lists.
        answers: List of generated answers.

    Returns:
        List of faithfulness scores (0.0-1.0) for each question.
    """
    evaluate_fn, _, _, faithfulness, _ = _safe_import_ragas()
    if evaluate_fn is None:
        return _fallback_faithfulness(questions, contexts, answers)

    try:
        from datasets import Dataset

        data = {
            "question": questions,
            "contexts": contexts,
            "answer": answers,
        }
        dataset = Dataset.from_dict(data)
        result = evaluate_fn(dataset, metrics=[faithfulness])
        return [float(result["faithfulness"])] * len(questions)
    except Exception as e:
        logger.warning("RAGAS faithfulness failed: %s", e)
        return _fallback_faithfulness(questions, contexts, answers)


def compute_answer_relevancy(
    questions: list[str],
    answers: list[str],
) -> list[float]:
    """Compute answer relevancy scores.

    Answer relevancy measures if the answer directly addresses the question.

    Args:
        questions: List of questions asked.
        answers: List of generated answers.

    Returns:
        List of relevancy scores (0.0-1.0) for each question.
    """
    evaluate_fn, *_, answer_relevancy = _safe_import_ragas()
    if evaluate_fn is None:
        return _fallback_answer_relevancy(questions, answers)

    try:
        from datasets import Dataset

        data = {
            "question": questions,
            "answer": answers,
        }
        dataset = Dataset.from_dict(data)
        result = evaluate_fn(dataset, metrics=[answer_relevancy])
        return [float(result["answer_relevancy"])] * len(questions)
    except Exception as e:
        logger.warning("RAGAS answer_relevancy failed: %s", e)
        return _fallback_answer_relevancy(questions, answers)


def compute_all_metrics(
    question: str,
    contexts: list[str],
    generated_answer: str,
    ground_truth: str,
) -> MetricScores:
    """Compute all RAGAS metrics for a single Q&A evaluation.

    Args:
        question: The question asked.
        contexts: Retrieved context strings.
        generated_answer: The LLM-generated answer.
        ground_truth: The expected correct answer.

    Returns:
        MetricScores with all computed metrics.
    """
    precision_scores = compute_context_precision([question], [contexts], [ground_truth])
    recall_scores = compute_context_recall([question], [contexts], [ground_truth])
    faithfulness_scores = compute_faithfulness([question], [contexts], [generated_answer])
    relevancy_scores = compute_answer_relevancy([question], [generated_answer])

    return MetricScores(
        context_precision=precision_scores[0],
        context_recall=recall_scores[0],
        faithfulness=faithfulness_scores[0],
        answer_relevancy=relevancy_scores[0],
    )


def check_thresholds(metrics: MetricScores) -> tuple[bool, dict[str, dict[str, float]]]:
    """Check if metrics meet the defined thresholds.

    Args:
        metrics: Computed metric scores.

    Returns:
        Tuple of (passed, details) where details maps metric name to
        {actual, threshold, passed}.
    """
    details: dict[str, dict[str, float]] = {}
    all_passed = True

    for metric_name, threshold in THRESHOLDS.items():
        actual = getattr(metrics, metric_name)
        passed = actual >= threshold
        details[metric_name] = {
            "actual": actual,
            "threshold": threshold,
            "passed": float(passed),
        }
        if not passed:
            all_passed = False

    return all_passed, details


# Fallback implementations when RAGAS is not available
def _fallback_context_precision(
    questions: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> list[float]:
    """Simple keyword overlap precision when RAGAS unavailable."""
    scores = []
    for _q, ctxs, gt in zip(questions, contexts, ground_truths, strict=True):
        gt_words = set(gt.lower().split())
        if not ctxs:
            scores.append(0.0)
            continue
        relevant_count = 0
        for ctx in ctxs:
            ctx_words = set(ctx.lower().split())
            overlap = len(gt_words & ctx_words) / max(len(gt_words), 1)
            if overlap > 0.1:
                relevant_count += 1
        scores.append(relevant_count / len(ctxs) if ctxs else 0.0)
    return scores


def _fallback_context_recall(
    questions: list[str],
    contexts: list[list[str]],
    ground_truths: list[str],
) -> list[float]:
    """Simple keyword coverage recall when RAGAS unavailable."""
    scores = []
    for _q, ctxs, gt in zip(questions, contexts, ground_truths, strict=True):
        gt_words = set(gt.lower().split())
        if not gt_words:
            scores.append(1.0)
            continue
        all_ctx_words: set[str] = set()
        for ctx in ctxs:
            all_ctx_words.update(ctx.lower().split())
        covered = len(gt_words & all_ctx_words)
        scores.append(covered / len(gt_words))
    return scores


def _fallback_faithfulness(
    questions: list[str],
    contexts: list[list[str]],
    answers: list[str],
) -> list[float]:
    """Simple context support check when RAGAS unavailable."""
    scores = []
    for _q, ctxs, ans in zip(questions, contexts, answers, strict=True):
        if not ans.strip():
            scores.append(0.0)
            continue
        ans_words = set(ans.lower().split())
        all_ctx_words: set[str] = set()
        for ctx in ctxs:
            all_ctx_words.update(ctx.lower().split())
        supported = len(ans_words & all_ctx_words)
        scores.append(supported / max(len(ans_words), 1))
    return scores


def _fallback_answer_relevancy(
    questions: list[str],
    answers: list[str],
) -> list[float]:
    """Simple question-answer overlap when RAGAS unavailable."""
    scores = []
    for q, ans in zip(questions, answers, strict=True):
        q_words = set(q.lower().split())
        ans_words = set(ans.lower().split())
        if not q_words or not ans_words:
            scores.append(0.0)
            continue
        overlap = len(q_words & ans_words)
        scores.append(min(1.0, overlap / max(len(q_words), 1) * 2))
    return scores
