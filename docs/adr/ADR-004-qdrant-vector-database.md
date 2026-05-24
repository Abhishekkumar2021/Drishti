# ADR-004: Qdrant Vector Database

## Status
Approved

## Context & Problem Statement
We need a storage system capable of holding millions of text and code chunks with their vectors. The database must support fast semantic search, keyword search, payload filtering (scoping queries to files/directories), and hybrid search (combining dense and sparse vector spaces).

## Decision
We select **Qdrant** as our vector database.

## Alternatives Considered
* **pgvector (PostgreSQL)**: Good for general relational + vector search, but lacks native sparse vector support and performance is lower compared to specialized engines.
* **Pinecone**: Cloud-only solution; contradicts requirements for local developer setups and private offline indexing.
* **Chroma**: Easy to set up locally but lacks native hybrid search features and has limited scale performance compared to Qdrant.

## Consequences
* **Pros**:
  * Native support for named vectors, enabling dense and sparse (BM25) vector storage within a single collection.
  * Fast filtering using payload indexes.
  * Easy deployment via lightweight Docker container.
* **Cons**:
  * Custom payload queries require learning Qdrant API formats.
