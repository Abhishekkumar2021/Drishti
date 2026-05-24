# ADR-010: Next.js Frontend

## Status
Approved

## Context & Problem Statement
We need an interactive, responsive web user interface that displays a chat panel, streams responses, renders source code with syntax highlighting, and provides interactive dependency graphs.

## Decision
We select **Next.js 14** (App Router) with React, Styled Components, and Monaco Editor.

## Alternatives Considered
* **Vanilla HTML + JS**: Easy to start but lacks structured state management, reusable components, and routing patterns required for an enterprise-level interface.
* **Python Streamlit**: Fast to build but lacks fine-grained design customization (e.g. glassmorphism design layouts, complex grid styling, side-by-side Monaco editor mapping).

## Consequences
* **Pros**:
  * Rich ecosystem of React UI libraries and Monaco editor components.
  * Server-Side Rendering (SSR) capabilities.
  * Fast Refresh allows quick iterations on UI details.
* **Cons**:
  * Requires a Node.js development runtime environment, adding to the project setup requirements.
