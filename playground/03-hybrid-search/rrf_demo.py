#!/usr/bin/env python3
"""Hybrid Search & RRF Fusion Demo.

This script demonstrates:
- How dense and sparse search produce different rankings
- Reciprocal Rank Fusion (RRF) algorithm
- Why hybrid outperforms either approach alone

Run with: uv run python playground/03-hybrid-search/rrf_demo.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document:
    """A searchable document."""

    id: str
    title: str
    content: str


# Sample documents about authentication
DOCUMENTS = [
    Document("doc1", "OAuth2 Authentication Flow", "OAuth2 provides secure delegated access using tokens..."),
    Document("doc2", "User Login System", "The login system verifies credentials against the database..."),
    Document("doc3", "JWT Token Validation", "JSON Web Tokens are validated by checking signature..."),
    Document("doc4", "OAuth2 Token Refresh", "When access tokens expire, use refresh tokens to get new ones..."),
    Document("doc5", "Password Hashing", "Passwords are hashed using bcrypt with salt..."),
    Document("doc6", "Session Management", "Sessions track authenticated users across requests..."),
    Document("doc7", "API Key Authentication", "API keys provide simple authentication for services..."),
    Document("doc8", "OAuth2 Scopes", "OAuth2 scopes limit what actions a token can perform..."),
]


def simulate_dense_search(query: str) -> list[tuple[str, float]]:
    """Simulate dense (semantic) search results.

    In reality, this would use embeddings from OpenAI/Cohere.
    """
    # Simulated semantic similarity scores
    # "OAuth2 authentication" finds semantically related docs
    semantic_scores = {
        "doc1": 0.92,  # OAuth2 Authentication Flow
        "doc2": 0.88,  # User Login System (semantically similar)
        "doc3": 0.85,  # JWT Token Validation
        "doc6": 0.82,  # Session Management
        "doc4": 0.78,  # OAuth2 Token Refresh
        "doc7": 0.75,  # API Key Authentication
        "doc5": 0.70,  # Password Hashing
        "doc8": 0.65,  # OAuth2 Scopes
    }
    return sorted(semantic_scores.items(), key=lambda x: -x[1])


def simulate_sparse_search(query: str) -> list[tuple[str, float]]:
    """Simulate sparse (BM25) search results.

    In reality, this would use BM25 term matching.
    """
    # Simulated keyword matching scores
    # "OAuth2 authentication" matches docs with exact terms
    keyword_scores = {
        "doc1": 0.95,  # Contains "OAuth2" and "Authentication"
        "doc4": 0.90,  # Contains "OAuth2"
        "doc8": 0.88,  # Contains "OAuth2"
        "doc3": 0.60,  # No OAuth2, has "validation"
        "doc2": 0.55,  # No OAuth2, has "login"
        "doc7": 0.50,  # Has "Authentication"
        "doc5": 0.30,  # Neither term
        "doc6": 0.25,  # Neither term
    }
    return sorted(keyword_scores.items(), key=lambda x: -x[1])


def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[str, float]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Combine multiple ranked lists using RRF.

    RRF score = Σ (1 / (k + rank_i))

    Args:
        ranked_lists: Multiple lists of (doc_id, score) tuples
        k: Dampening constant (default 60)

    Returns:
        Combined ranking as (doc_id, rrf_score) tuples
    """
    rrf_scores: dict[str, float] = {}

    for ranked_list in ranked_lists:
        for rank, (doc_id, _score) in enumerate(ranked_list, start=1):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
            rrf_scores[doc_id] += 1.0 / (k + rank)

    return sorted(rrf_scores.items(), key=lambda x: -x[1])


def main() -> None:
    """Run the hybrid search demo."""
    print("=" * 70)
    print("Hybrid Search & Reciprocal Rank Fusion (RRF) Demo")
    print("=" * 70)

    query = "OAuth2 authentication"
    print(f"\nQuery: '{query}'")

    # Get individual search results
    dense_results = simulate_dense_search(query)
    sparse_results = simulate_sparse_search(query)

    # Apply RRF
    hybrid_results = reciprocal_rank_fusion(dense_results, sparse_results)

    # Display results
    print("\n" + "─" * 70)
    print(f"{'Rank':<6} {'Dense (Semantic)':<25} {'Sparse (BM25)':<25} {'Hybrid (RRF)':<20}")
    print("─" * 70)

    doc_map = {d.id: d for d in DOCUMENTS}

    for i in range(min(8, len(DOCUMENTS))):
        dense_id = dense_results[i][0] if i < len(dense_results) else "-"
        sparse_id = sparse_results[i][0] if i < len(sparse_results) else "-"
        hybrid_id = hybrid_results[i][0] if i < len(hybrid_results) else "-"

        dense_title = doc_map[dense_id].title[:20] if dense_id != "-" else "-"
        sparse_title = doc_map[sparse_id].title[:20] if sparse_id != "-" else "-"
        hybrid_title = doc_map[hybrid_id].title[:20] if hybrid_id != "-" else "-"

        print(f"{i+1:<6} {dense_title:<25} {sparse_title:<25} {hybrid_title:<20}")

    print("─" * 70)

    # Explain the math
    print("\n📊 RRF CALCULATION EXAMPLE")
    print("-" * 40)
    print("For 'OAuth2 Authentication Flow' (doc1):")
    print(f"  Dense rank: 1  → contribution: 1/(60+1) = {1/61:.4f}")
    print(f"  Sparse rank: 1 → contribution: 1/(60+1) = {1/61:.4f}")
    print(f"  RRF score: {2/61:.4f}")
    print()
    print("For 'User Login System' (doc2):")
    print(f"  Dense rank: 2  → contribution: 1/(60+2) = {1/62:.4f}")
    print(f"  Sparse rank: 5 → contribution: 1/(60+5) = {1/65:.4f}")
    print(f"  RRF score: {1/62 + 1/65:.4f}")

    # Why it works
    print("\n🎯 WHY HYBRID WINS")
    print("-" * 40)
    print("""
Dense-only misses:
  ❌ 'OAuth2 Scopes' ranked 8th (semantically less similar)
  ✅ But it contains exact 'OAuth2' keyword!

Sparse-only misses:
  ❌ 'Session Management' ranked 8th (no keywords)
  ✅ But it's semantically very relevant!

Hybrid captures both:
  ✅ Documents with 'OAuth2' keyword get boosted
  ✅ Semantically similar docs stay in top results
  ✅ RRF balances without requiring score normalization
""")


if __name__ == "__main__":
    main()
