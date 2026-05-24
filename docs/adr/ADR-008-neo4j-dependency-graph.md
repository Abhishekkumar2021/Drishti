# ADR-008: Neo4j Dependency Graph Storage

## Context & Problem Statement
To trace dependencies and execute change impact analysis ("If I change this method, what breaks?"), we need to query relationships. Vector searches are inadequate for multi-hop relationship traversals (e.g. Method A calls Method B, which calls Method C).

## Decision
We select **Neo4j Graph Database** as the relationship store.

## Alternatives Considered
* **Vector DB Metadata Linking**: Storing dependent symbols as string metadata in Qdrant. However, querying multi-hop dependencies requires repeated queries, leading to high latency and complexity.
* **SQL Recursive CTEs**: Can trace hierarchies but SQL schemas are less intuitive for representing dynamic, multi-lingual dependency relationships.

## Consequences
* **Pros**:
  * Cypher query language allows querying complex, multi-hop relationship paths.
  * Native graph visualization capability matches Next.js UI integration patterns.
* **Cons**:
  * Adds another infrastructure component (database container), increasing development footprint.
