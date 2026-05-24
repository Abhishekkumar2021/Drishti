"use client";

import { useState } from "react";

import { ingestRepository } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export function Sidebar() {
  const { repoPath, setRepoPath, ingestStatus, setIngestStatus } = useAppStore();
  const [forceReindex, setForceReindex] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleIngest() {
    if (!repoPath.trim()) {
      setIngestStatus("Enter a repository path first.");
      return;
    }
    setLoading(true);
    setIngestStatus("Indexing…");
    try {
      const result = await ingestRepository(repoPath.trim(), forceReindex);
      setIngestStatus(
        `Indexed ${result.chunks_indexed} chunks from ${result.files_parsed} files (${result.head_commit.slice(0, 8)})`,
      );
    } catch (error) {
      setIngestStatus(error instanceof Error ? error.message : "Ingest failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-surface-border bg-surface-raised p-4">
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-white">Drishti</h1>
        <p className="mt-1 text-xs text-slate-400">दृष्टि — code-aware RAG</p>
      </div>

      <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Repository path
      </label>
      <input
        className="mt-2 w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 outline-none focus:border-accent"
        placeholder="/absolute/path/to/repo"
        value={repoPath}
        onChange={(event) => setRepoPath(event.target.value)}
      />

      <label className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <input
          type="checkbox"
          checked={forceReindex}
          onChange={(event) => setForceReindex(event.target.checked)}
          className="rounded border-surface-border"
        />
        Force full re-index
      </label>

      <button
        type="button"
        onClick={handleIngest}
        disabled={loading}
        className="mt-4 w-full rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition hover:bg-accent-muted disabled:opacity-50"
      >
        {loading ? "Indexing…" : "Index repository"}
      </button>

      <p className="mt-3 text-xs leading-relaxed text-slate-500">{ingestStatus}</p>

      <div className="mt-auto pt-6 text-xs text-slate-600">
        API: {process.env.NEXT_PUBLIC_DRISHTI_API_URL ?? "http://localhost:8000"}
      </div>
    </aside>
  );
}
