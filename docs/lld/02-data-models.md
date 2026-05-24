# LLD Chapter 02: Data Models & Vector Schemas

This chapter defines the schemas, payload filters, and graph database structures that store Drishti's knowledge representation.

---

## Table of Contents

1. [Pydantic Validation Models](#1-pydantic-validation-models)
2. [Qdrant Vector DB Collection Schemas](#2-qdrant-vector-db-collection-schemas)
3. [Qdrant Payload Filtering Definitions](#3-qdrant-payload-filtering-definitions)
4. [Neo4j Graph Database Models](#4-neo4j-graph-database-models)

---

## 1. Pydantic Validation Models

Drishti uses Pydantic v2 to enforce strict runtime type safety, serialize API payloads, and validate configuration environments.

> **Universal Chunk:** Full field reference, ER diagram, and implementation status live in [design/universal-chunk-schema.md](../design/universal-chunk-schema.md).

### Request Payloads

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class IngestionRequest(BaseModel):
    repo_path: str = Field(
        ..., 
        description="Absolute local directory path of repository to index"
    )
    branch: Optional[str] = Field("main", description="Target Git branch")
    recursive: bool = Field(True, description="Recursively walk subdirectories")
    force_reindex: bool = Field(False, description="Ignore state hash and re-index all files")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language query")
    filters: Optional[Dict[str, str]] = Field(
        None, 
        description="Key-value filters (e.g. {'language': 'python', 'file_path': 'src/*'})"
    )
    limit: int = Field(5, ge=1, le=50, description="Max candidates to retrieve")

class AskRequest(BaseModel):
    question: str = Field(..., description="User query for RAG pipeline")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="List of prior messages formatted as [{'role': 'user', 'content': '...'}]"
    )
    filters: Optional[Dict[str, str]] = Field(None, description="Metadata scope filters")
```

---

## 2. Qdrant Vector DB Collection Schemas

We store chunks in a single Qdrant collection named `drishti_chunks`. Points contain two distinct named vectors:

```json
{
  "vectors": {
    "dense": [0.012, -0.045, 0.128, "..."],  // 1536-dimensions (OpenAI text-embedding-3-small)
    "sparse": {                                 // Dynamic dimensions (BM25 sparse tokens)
      "indices": [412, 1024, 8892],
      "values": [0.85, 1.22, 0.45]
    }
  },
  "payload": {
    "id": "uuid4_string",
    "content": "def calculate_complexity(node):\n...",
    "content_type": "code",
    "file_path": "src/utils/metrics.py",
    "source_type": "git_repo",
    "language": "python",
    "start_line": 12,
    "end_line": 35,
    "node_type": "function_definition",
    "name": "calculate_complexity",
    "parent_class": null,
    "parent_module": "src.utils.metrics",
    "context_path": "src/utils/metrics.py::calculate_complexity",
    "parameters": ["node"],
    "return_type": "int",
    "cyclomatic_complexity": 4,
    "dependencies": ["tree_sitter"],
    "last_modified": "2026-05-24T12:00:00Z"
  }
}
```

---

## 3. Qdrant Payload Filtering Definitions

To perform filtered hybrid searches, Drishti translates user-supplied filters into Qdrant filter definitions:

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

def compile_qdrant_filter(filters: Dict[str, str]) -> Filter:
    """
    Compiles key-value queries into Qdrant Filter conditions.
    """
    must_conditions = []
    
    for key, value in filters.items():
        if key in ["language", "content_type", "source_type"]:
            must_conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
            )
        elif key == "file_path":
            # Uses keyword suffix/prefix matching
            must_conditions.append(
                FieldCondition(
                    key="file_path",
                    match=MatchValue(value=value)
                )
            )
            
    return Filter(must=must_conditions)
```

---

## 4. Neo4j Graph Database Models

For code dependencies, Neo4j holds node structures linked via relationship maps.

### Node Attributes
* **`Package`**: `name` (e.g. "drishti.ingestion")
* **`File`**: `path` (e.g. "src/drishti/ingestion/ast_parser.py"), `hash`
* **`Class`**: `name` (e.g. "ASTParser"), `is_interface`
* **`Method`**: `name` (e.g. "parse_node"), `complexity`, `start_line`

### Relationships
* `(Package)-[:CONTAINS]->(File)`
* `(File)-[:CONTAINS]->(Class)`
* `(Class)-[:CONTAINS]->(Method)`
* `(Class)-[:EXTENDS]->(Class)`
* `(Method)-[:CALLS]->(Method)`
* `(File)-[:IMPORTS]->(File)`
