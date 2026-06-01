#!/usr/bin/env python3
"""RAG Evaluation Metrics Demo.

This script demonstrates the RAGAS metrics used to evaluate Drishti:
- Context Precision
- Context Recall
- Faithfulness
- Answer Relevancy

Run with: uv run python playground/05-rag-evaluation/evaluation_demo.py
"""

from __future__ import annotations


def context_precision(retrieved: list[str], relevant: list[str]) -> float:
    """Calculate context precision.

    Measures: Of the retrieved documents, how many are relevant?

    Formula: (# relevant in retrieved) / (# retrieved)
    """
    if not retrieved:
        return 0.0
    relevant_set = set(relevant)
    hits = sum(1 for doc in retrieved if doc in relevant_set)
    return hits / len(retrieved)


def context_recall(retrieved: list[str], relevant: list[str]) -> float:
    """Calculate context recall.

    Measures: Of all relevant documents, how many did we retrieve?

    Formula: (# relevant in retrieved) / (# total relevant)
    """
    if not relevant:
        return 1.0  # No relevant docs needed
    relevant_set = set(relevant)
    retrieved_set = set(retrieved)
    hits = len(relevant_set & retrieved_set)
    return hits / len(relevant_set)


def faithfulness_score(answer: str, context: str) -> float:
    """Calculate faithfulness score.

    Measures: Is the answer supported by the context?

    Simplified version: checks keyword overlap.
    Real RAGAS uses LLM to extract claims and verify each against context.
    """
    answer_words = set(answer.lower().split())
    context_words = set(context.lower().split())

    if not answer_words:
        return 0.0

    supported = len(answer_words & context_words)
    return supported / len(answer_words)


def answer_relevancy_score(question: str, answer: str) -> float:
    """Calculate answer relevancy.

    Measures: Does the answer address the question?

    Simplified version: keyword overlap between question and answer.
    Real RAGAS generates hypothetical questions from the answer and
    compares their embeddings to the original question.
    """
    question_words = set(question.lower().split())
    answer_words = set(answer.lower().split())

    # Remove common words
    stop_words = {"the", "a", "is", "are", "what", "how", "does", "in", "to", "and", "of"}
    question_words -= stop_words
    answer_words -= stop_words

    if not question_words:
        return 0.0

    overlap = len(question_words & answer_words)
    return min(1.0, overlap / len(question_words))


def main() -> None:
    """Run the RAG evaluation demo."""
    print("=" * 70)
    print("RAG Evaluation Metrics Demo")
    print("=" * 70)

    # Example 1: Good retrieval
    print("\n📊 EXAMPLE 1: Good Retrieval")
    print("-" * 50)

    question = "How does the authenticate function verify credentials?"
    relevant_docs = ["auth/service.py:authenticate", "auth/validator.py:check_password"]
    retrieved_docs = ["auth/service.py:authenticate", "auth/validator.py:check_password", "auth/utils.py:hash"]

    precision = context_precision(retrieved_docs, relevant_docs)
    recall = context_recall(retrieved_docs, relevant_docs)

    print(f"Question: {question}")
    print(f"Relevant docs: {relevant_docs}")
    print(f"Retrieved docs: {retrieved_docs}")
    print()
    print(f"Context Precision: {precision:.1%} (2/3 retrieved are relevant)")
    print(f"Context Recall:    {recall:.1%} (2/2 relevant were retrieved)")

    # Example 2: Poor retrieval
    print("\n📊 EXAMPLE 2: Poor Retrieval")
    print("-" * 50)

    retrieved_poor = ["utils/helpers.py:format_date", "models/user.py:User", "config.py:Settings"]

    precision_poor = context_precision(retrieved_poor, relevant_docs)
    recall_poor = context_recall(retrieved_poor, relevant_docs)

    print(f"Retrieved docs: {retrieved_poor}")
    print()
    print(f"Context Precision: {precision_poor:.1%} (0/3 retrieved are relevant)")
    print(f"Context Recall:    {recall_poor:.1%} (0/2 relevant were retrieved)")
    print("❌ This indicates retrieval failure!")

    # Example 3: Faithfulness
    print("\n📊 EXAMPLE 3: Faithfulness Check")
    print("-" * 50)

    context = """
    The authenticate function takes username and password parameters.
    It hashes the password using bcrypt and compares against the stored hash.
    Returns True if credentials are valid, False otherwise.
    """

    good_answer = "The authenticate function hashes the password with bcrypt and compares it to the stored hash."
    bad_answer = "The authenticate function uses SHA256 encryption and connects to an LDAP server for validation."

    faithful_good = faithfulness_score(good_answer, context)
    faithful_bad = faithfulness_score(bad_answer, context)

    print("Context:", context[:80] + "...")
    print()
    print(f"Good answer: {good_answer[:60]}...")
    print(f"Faithfulness: {faithful_good:.1%} ✅ (grounded in context)")
    print()
    print(f"Bad answer: {bad_answer[:60]}...")
    print(f"Faithfulness: {faithful_bad:.1%} ❌ (hallucinated details)")

    # Example 4: Answer Relevancy
    print("\n📊 EXAMPLE 4: Answer Relevancy")
    print("-" * 50)

    relevant_answer = "The authenticate function verifies credentials by checking the password hash."
    irrelevant_answer = "The database uses PostgreSQL version 14 with async connections."

    relevancy_good = answer_relevancy_score(question, relevant_answer)
    relevancy_bad = answer_relevancy_score(question, irrelevant_answer)

    print(f"Question: {question}")
    print()
    print(f"Relevant answer: {relevant_answer[:50]}...")
    print(f"Relevancy: {relevancy_good:.1%} ✅")
    print()
    print(f"Irrelevant answer: {irrelevant_answer[:50]}...")
    print(f"Relevancy: {relevancy_bad:.1%} ❌")

    # Summary
    print("\n" + "=" * 70)
    print("DRISHTI TARGET THRESHOLDS")
    print("=" * 70)
    print("""
| Metric              | Target  | Why It Matters                    |
|---------------------|---------|-----------------------------------|
| Context Precision   | > 85%   | Top results should be relevant    |
| Context Recall      | > 90%   | Don't miss important code         |
| Faithfulness        | > 95%   | No hallucinated function names    |
| Answer Relevancy    | > 90%   | Actually answer the question      |

Drishti achieves these through:
1. AST-aware chunking (complete semantic units)
2. Hybrid search (dense + sparse + RRF)
3. Cohere re-ranking (cross-encoder precision)
4. LangGraph retry loop (grade and expand query)
""")


if __name__ == "__main__":
    main()
