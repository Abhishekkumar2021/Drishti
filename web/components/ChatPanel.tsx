"use client";

import { FormEvent, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { askStream, readSourceFile, type ChatMessage } from "@/lib/api";
import { monacoLanguage, splitTextWithCitations } from "@/lib/citations";
import { useAppStore } from "@/lib/store";

function AssistantContent({
  content,
  onCitationClick,
}: {
  content: string;
  onCitationClick: (filePath: string, start: number, end: number) => void;
}) {
  const parts = splitTextWithCitations(content);
  return (
    <div className="prose prose-invert max-w-none text-sm prose-pre:bg-surface-raised">
      {parts.map((part, index) =>
        part.type === "citation" ? (
          <button
            key={`${part.value.filePath}-${index}`}
            type="button"
            onClick={() =>
              onCitationClick(
                part.value.filePath,
                part.value.startLine,
                part.value.endLine,
              )
            }
            className="mx-0.5 inline rounded bg-indigo-900/50 px-1 py-0.5 font-mono text-xs text-indigo-200 hover:bg-indigo-800"
          >
            {part.value.tag}
          </button>
        ) : (
          <ReactMarkdown
            key={`text-${index}`}
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {part.value}
          </ReactMarkdown>
        ),
      )}
    </div>
  );
}

export function ChatPanel() {
  const {
    repoPath,
    messages,
    appendMessage,
    updateLastAssistant,
    openEditor,
    isAsking,
    setIsAsking,
  } = useAppStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  async function handleCitation(filePath: string, start: number, end: number) {
    if (!repoPath.trim()) return;
    try {
      const file = await readSourceFile(repoPath.trim(), filePath);
      openEditor({
        filePath: file.file_path,
        content: file.content,
        language: monacoLanguage(file.file_path, file.language),
        highlightStart: start,
        highlightEnd: end,
      });
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question || isAsking) return;
    if (!repoPath.trim()) {
      appendMessage({
        role: "assistant",
        content: "Set a repository path in the sidebar and run indexing first.",
      });
      return;
    }

    const history: ChatMessage[] = messages.filter(
      (message) => message.role === "user" || message.role === "assistant",
    );
    appendMessage({ role: "user", content: question });
    appendMessage({ role: "assistant", content: "" });
    setInput("");
    setIsAsking(true);

    let answer = "";
    try {
      await askStream(question, repoPath.trim(), history, (event, data) => {
        if (event === "token" && typeof data.text === "string") {
          answer += data.text;
          updateLastAssistant(answer);
        }
      });
    } catch (error) {
      updateLastAssistant(
        error instanceof Error ? error.message : "Failed to get an answer",
      );
    } finally {
      setIsAsking(false);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <header className="border-b border-surface-border px-6 py-4">
        <h2 className="text-sm font-medium text-slate-200">Ask Drishti</h2>
        <p className="text-xs text-slate-500">Streaming answers with file citations</p>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Index a repository, then ask how the codebase works. Citations open in the
            editor on the right.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={
              message.role === "user"
                ? "ml-auto max-w-[85%] rounded-lg bg-accent/20 px-4 py-2 text-sm text-slate-100"
                : "max-w-[95%] rounded-lg bg-surface-raised px-4 py-3"
            }
          >
            {message.role === "user" ? (
              <p className="text-sm">{message.content}</p>
            ) : (
              <AssistantContent content={message.content} onCitationClick={handleCitation} />
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-surface-border p-4">
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-surface-border bg-surface-raised px-4 py-2 text-sm outline-none focus:border-accent"
            placeholder="How does authentication work?"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={isAsking}
          />
          <button
            type="submit"
            disabled={isAsking || !input.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-muted disabled:opacity-50"
          >
            {isAsking ? "…" : "Send"}
          </button>
        </div>
      </form>
    </section>
  );
}
