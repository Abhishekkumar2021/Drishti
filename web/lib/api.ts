const API_BASE = process.env.NEXT_PUBLIC_DRISHTI_API_URL ?? "http://localhost:8000";

export type ChatMessage = { role: "user" | "assistant" | "system"; content: string };

export type IngestResult = {
  head_commit: string;
  chunks_indexed: number;
  files_parsed: number;
  total_chunks_in_store: number;
  parseable_files: number;
  up_to_date: boolean;
  repo_path?: string;
};

export function formatIngestStatus(result: IngestResult): string {
  const commit = result.head_commit.slice(0, 8);
  if (result.up_to_date && result.total_chunks_in_store > 0) {
    return `Already indexed at ${commit} — ${result.total_chunks_in_store} chunks in store`;
  }
  if (result.chunks_indexed === 0 && result.total_chunks_in_store === 0) {
    return "No chunks indexed — check supported file types or use Force re-index";
  }
  if (result.chunks_indexed > 0) {
    return `Indexed ${result.chunks_indexed} new chunks (${result.total_chunks_in_store} total) · ${commit}`;
  }
  return `Indexed ${result.total_chunks_in_store} chunks from ${result.files_parsed} files · ${commit}`;
}

export type SourceFile = {
  file_path: string;
  content: string;
  language: string | null;
  line_count: number;
};

function authHeaders(): HeadersInit {
  const token = process.env.NEXT_PUBLIC_DRISHTI_API_TOKEN;
  if (!token) return { "Content-Type": "application/json" };
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function ingestRepository(
  repoPath: string,
  forceReindex = false,
): Promise<IngestResult> {
  const response = await fetch(`${API_BASE}/api/v1/ingest`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      repo_path: repoPath,
      force_reindex: forceReindex,
    }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      (body as { error?: { message?: string } }).error?.message ??
      `Ingest failed (${response.status})`;
    throw new Error(message);
  }
  return response.json();
}

export async function readSourceFile(
  repoPath: string,
  filePath: string,
): Promise<SourceFile> {
  const response = await fetch(`${API_BASE}/api/v1/source/read`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ repo_path: repoPath, file_path: filePath }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      (body as { error?: { message?: string } }).error?.message ??
      `Failed to load file (${response.status})`;
    throw new Error(message);
  }
  return response.json();
}

export async function askStream(
  question: string,
  repoPath: string,
  history: ChatMessage[],
  onEvent: (event: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/ask?stream=true`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      question,
      conversation_history: history,
    }),
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => ({}));
    const message =
      (body as { error?: { message?: string } }).error?.message ??
      `Ask failed (${response.status})`;
    throw new Error(message);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      parseSseBlock(part, onEvent);
    }
  }
  if (buffer.trim()) {
    parseSseBlock(buffer, onEvent);
  }
}

function parseSseBlock(
  block: string,
  onEvent: (event: string, data: Record<string, unknown>) => void,
): void {
  let eventName = "message";
  let dataLine = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLine += line.slice(5).trim();
    }
  }
  if (!dataLine) return;
  try {
    onEvent(eventName, JSON.parse(dataLine) as Record<string, unknown>);
  } catch {
    /* ignore malformed chunks */
  }
}
