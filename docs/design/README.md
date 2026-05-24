# Design Specifications

Design documents define **contracts** and **data structures** shared across ingestion, storage, search, and the API.

| Document | Description |
|----------|-------------|
| [API Contracts](api-contracts.md) | REST endpoints, WebSocket streaming, error envelopes |
| [Universal Chunk Schema](universal-chunk-schema.md) | Canonical chunk model — fields, types, examples |

---

## Relationship to Other Docs

```mermaid
flowchart LR
    PROD[Product Epics] --> DESIGN[Design specs]
    DESIGN --> LLD[LLD chapters]
    LLD --> CODE[src/drishti]
    ADR[ADRs] --> DESIGN
```

- **Product** defines *what* users need ([epics](../product/epics/)).
- **Design** defines *interfaces* (this folder).
- **LLD** defines *algorithms and class collaborations* ([lld/](../lld/)).
- **ADRs** record *technology choices* ([adr/](../adr/)).
