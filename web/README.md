# Drishti Web UI

Next.js 14 frontend for the Drishti RAG API (EPIC-10).

## Setup

```bash
cp .env.local.example .env.local
npm install
```

## Development

Start the API (`make dev` from repo root) and infrastructure (`make docker-up`), then:

```bash
npm run dev
```

Or from the repository root: `make dev-web`

Open [http://localhost:3000](http://localhost:3000).

## Environment

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_DRISHTI_API_URL` | Backend base URL (default `http://localhost:8000`) |
| `NEXT_PUBLIC_DRISHTI_API_TOKEN` | Optional Bearer token matching backend `API_TOKEN` |

## Workflow

1. Enter an absolute path to a git repository in the sidebar.
2. Click **Index repository** (calls `POST /api/v1/ingest`).
3. Ask questions in the chat pane (streams from `POST /api/v1/ask`).
4. Click citation tags to open files in the Monaco editor (`POST /api/v1/source/read`).
