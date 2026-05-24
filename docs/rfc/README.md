# Request for Comments (RFC) Process: Drishti (दृष्टि)

This directory manages the Request for Comments (RFC) documents for Drishti.

---

## What is an RFC?

An RFC is a proposal for a major architectural change, feature addition, or design pattern adjustment. It is written to collect feedback from the community and core team before code is written.

### The RFC Flow

```
1. Write Proposal  ──▶ 2. Peer Review  ──▶ 3. Decision
   (RFC Draft)           (Discussions)       (Approve / Decline)
                                                   │
                                                   ▼
                                           4. Document Decision
                                              (Write ADR)
```

For simple library selections or straightforward changes, developers may bypass the RFC step and write an ADR directly. RFCs are reserved for complex, multi-component design challenges (e.g. implementing AST-aware parsers, vector database indexing structures, frontend state flows).

---

## RFC Index

*There are currently no active RFC drafts. All initial architectural decisions have been finalized and documented as [ADRs](file:///Users/abhishek/Dev/Drishti/docs/adr/README.md).*

---

## RFC Markdown Template

When writing a new RFC, create a file named `RFC-NNN-slug-name.md` using the following structure:

```markdown
# RFC-NNN: [Feature / Change Title]

## 1. Executive Summary
Provide a brief 2-3 sentence overview of the proposed change.

## 2. Problem Statement
Explain why this change is necessary and what issues it resolves.

## 3. Proposed Design
* **Architecture**: Explain the components and interfaces.
* **Data Flow**: Detail schemas and sequence steps.
* **Code Example**: Show proposed implementation snippets.

## 4. Alternatives Considered
List 2-3 alternative approaches and explain why they were rejected.

## 5. Drawbacks & Risks
Detail potential security risks, performance regressions, or backwards compatibility issues.
```
