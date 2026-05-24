/** Citation tag pattern: [path/to/file.py:L10-15] */
const CITATION_RE = /\[([^\]:\n]+):L(\d+)(?:-(\d+))?\]/g;

export type ParsedCitation = {
  tag: string;
  filePath: string;
  startLine: number;
  endLine: number;
};

export function parseCitationTag(tag: string): ParsedCitation | null {
  const match = /\[([^\]:\n]+):L(\d+)(?:-(\d+))?\]/.exec(tag);
  if (!match) return null;
  const start = Number.parseInt(match[2], 10);
  const end = match[3] ? Number.parseInt(match[3], 10) : start;
  return {
    tag: match[0],
    filePath: match[1],
    startLine: start,
    endLine: end,
  };
}

export function splitTextWithCitations(text: string): Array<
  | { type: "text"; value: string }
  | { type: "citation"; value: ParsedCitation }
> {
  const parts: Array<
    | { type: "text"; value: string }
    | { type: "citation"; value: ParsedCitation }
  > = [];
  let lastIndex = 0;
  for (const match of text.matchAll(CITATION_RE)) {
    const index = match.index ?? 0;
    if (index > lastIndex) {
      parts.push({ type: "text", value: text.slice(lastIndex, index) });
    }
    const parsed = parseCitationTag(match[0]);
    if (parsed) {
      parts.push({ type: "citation", value: parsed });
    }
    lastIndex = index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push({ type: "text", value: text.slice(lastIndex) });
  }
  return parts;
}

export function monacoLanguage(filePath: string, backendLang: string | null): string {
  if (backendLang) return backendLang;
  const ext = filePath.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    py: "python",
    java: "java",
    js: "javascript",
    jsx: "javascript",
    ts: "typescript",
    tsx: "typescript",
    go: "go",
  };
  return ext ? (map[ext] ?? "plaintext") : "plaintext";
}
