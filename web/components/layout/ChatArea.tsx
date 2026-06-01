"use client";

import { FormEvent, useRef, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import {
  Send,
  FileCode,
  Loader2,
  Copy,
  Check,
  ChevronRight,
  Sparkles,
  Code2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/cn";
import {
  useAppStore,
  generateId,
  type Message,
  type Source,
} from "@/lib/storage";
import { monacoLanguage, splitTextWithCitations } from "@/lib/citations";

type StreamCallback = (event: string, data: Record<string, unknown>) => void;

async function askStream(
  question: string,
  repoPath: string,
  history: { role: string; content: string }[],
  onEvent: StreamCallback
): Promise<void> {
  const url = `${process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}/api/v1/ask`;
  
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      repo_root: repoPath,
      history: history.slice(-10),
      stream: true,
    }),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          onEvent(data.event || "token", data);
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}

async function readSourceFile(
  repoPath: string,
  filePath: string
): Promise<{ content: string; language: string | null; file_path: string }> {
  const url = new URL(
    `${process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}/api/v1/source`
  );
  url.searchParams.set("repo_root", repoPath);
  url.searchParams.set("file_path", filePath);

  const response = await fetch(url.toString());
  if (!response.ok) throw new Error("Failed to read file");
  return response.json();
}

export function ChatArea() {
  const {
    getActiveThread,
    getActiveWorkspace,
    addMessage,
    updateMessage,
    addThread,
    setActiveThread,
    isAsking,
    setIsAsking,
    setEditor,
    activeThreadId,
    activeWorkspaceId,
  } = useAppStore();

  const [input, setInput] = useState("");
  const [showSources, setShowSources] = useState(false);
  const [selectedMessageSources, setSelectedMessageSources] = useState<Source[]>([]);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeThread = getActiveThread();
  const activeWorkspace = getActiveWorkspace();
  const messages = activeThread?.messages || [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleCopyMessage = async (message: Message) => {
    await navigator.clipboard.writeText(message.content);
    setCopiedMessageId(message.id);
    setTimeout(() => setCopiedMessageId(null), 2000);
  };

  const handleCitationClick = async (
    filePath: string,
    start: number,
    end: number
  ) => {
    if (!activeWorkspace) return;
    try {
      const file = await readSourceFile(activeWorkspace.repoPath, filePath);
      setEditor({
        filePath: file.file_path,
        content: file.content,
        language: monacoLanguage(file.file_path, file.language),
        highlightStart: start,
        highlightEnd: end,
      });
    } catch (error) {
      console.error("Failed to load source:", error);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || isAsking) return;

    if (!activeWorkspace) {
      return;
    }

    let threadId = activeThreadId;
    if (!threadId || !activeThread) {
      const newThread = {
        id: generateId(),
        title: question.slice(0, 50) + (question.length > 50 ? "..." : ""),
        workspaceId: activeWorkspaceId!,
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addThread(newThread);
      threadId = newThread.id;
    }

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: question,
      createdAt: Date.now(),
    };

    const assistantMessage: Message = {
      id: generateId(),
      role: "assistant",
      content: "",
      createdAt: Date.now(),
    };

    addMessage(threadId, userMessage);
    addMessage(threadId, assistantMessage);
    setInput("");
    setIsAsking(true);

    const history = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    let answer = "";
    let sources: Source[] = [];

    try {
      await askStream(question, activeWorkspace.repoPath, history, (event, data) => {
        if (event === "token" && typeof data.text === "string") {
          answer += data.text;
          updateMessage(threadId!, assistantMessage.id, answer);
        }
        if (event === "sources" && Array.isArray(data.sources)) {
          sources = data.sources as Source[];
          updateMessage(threadId!, assistantMessage.id, answer, sources);
        }
      });
    } catch (error) {
      updateMessage(
        threadId!,
        assistantMessage.id,
        error instanceof Error ? `Error: ${error.message}` : "Failed to get response"
      );
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-surface-border px-6 py-4">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-medium text-slate-200">
            <Sparkles className="h-4 w-4 text-accent" />
            {activeThread?.title || "New Conversation"}
          </h2>
          <p className="text-xs text-slate-500">
            {activeWorkspace
              ? `Querying ${activeWorkspace.name}`
              : "Select a workspace to start"}
          </p>
        </div>
        {selectedMessageSources.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSources(!showSources)}
          >
            <FileCode className="mr-2 h-4 w-4" />
            Sources ({selectedMessageSources.length})
            <ChevronRight
              className={cn(
                "ml-2 h-4 w-4 transition-transform",
                showSources && "rotate-90"
              )}
            />
          </Button>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="rounded-full bg-accent/10 p-4">
                  <Code2 className="h-8 w-8 text-accent" />
                </div>
                <h3 className="mt-4 text-lg font-medium text-slate-200">
                  Ask about your codebase
                </h3>
                <p className="mt-2 max-w-sm text-sm text-slate-500">
                  {activeWorkspace
                    ? "Ask questions about how the code works. Citations link to source files."
                    : "Select or create a workspace, then index your repository to start."}
                </p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "group relative",
                  message.role === "user" && "flex justify-end"
                )}
              >
                <div
                  className={cn(
                    "relative max-w-[85%] rounded-2xl px-4 py-3",
                    message.role === "user"
                      ? "bg-accent text-white"
                      : "bg-surface-raised"
                  )}
                >
                  {message.role === "user" ? (
                    <p className="text-sm">{message.content}</p>
                  ) : (
                    <AssistantContent
                      content={message.content}
                      onCitationClick={handleCitationClick}
                    />
                  )}

                  {message.role === "assistant" && message.content && (
                    <div className="mt-2 flex items-center gap-2 border-t border-surface-border/50 pt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-slate-500 hover:text-slate-300"
                        onClick={() => handleCopyMessage(message)}
                      >
                        {copiedMessageId === message.id ? (
                          <>
                            <Check className="mr-1 h-3 w-3" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="mr-1 h-3 w-3" />
                            Copy
                          </>
                        )}
                      </Button>
                      {message.sources && message.sources.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs text-slate-500 hover:text-slate-300"
                          onClick={() => {
                            setSelectedMessageSources(message.sources || []);
                            setShowSources(true);
                          }}
                        >
                          <FileCode className="mr-1 h-3 w-3" />
                          {message.sources.length} sources
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isAsking && messages[messages.length - 1]?.content === "" && (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking...
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {showSources && selectedMessageSources.length > 0 && (
          <SourcesPanel
            sources={selectedMessageSources}
            onClose={() => setShowSources(false)}
            onSourceClick={(source) =>
              handleCitationClick(source.filePath, source.startLine, source.endLine)
            }
          />
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t border-surface-border p-4"
      >
        <div className="mx-auto flex max-w-3xl gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              activeWorkspace
                ? "Ask about your codebase..."
                : "Select a workspace first"
            }
            disabled={isAsking || !activeWorkspace}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={isAsking || !input.trim() || !activeWorkspace}
          >
            {isAsking ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

function AssistantContent({
  content,
  onCitationClick,
}: {
  content: string;
  onCitationClick: (filePath: string, start: number, end: number) => void;
}) {
  const parts = splitTextWithCitations(content);

  if (!content) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }

  return (
    <div className="prose prose-invert prose-sm max-w-none prose-pre:bg-surface prose-pre:border prose-pre:border-surface-border">
      {parts.map((part, index) =>
        part.type === "citation" ? (
          <button
            key={`citation-${index}`}
            type="button"
            onClick={() =>
              onCitationClick(
                part.value.filePath,
                part.value.startLine,
                part.value.endLine
              )
            }
            className="mx-0.5 inline-flex items-center gap-1 rounded bg-accent/20 px-1.5 py-0.5 font-mono text-xs text-accent hover:bg-accent/30 transition-colors"
          >
            <FileCode className="h-3 w-3" />
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
        )
      )}
    </div>
  );
}

function SourcesPanel({
  sources,
  onClose,
  onSourceClick,
}: {
  sources: Source[];
  onClose: () => void;
  onSourceClick: (source: Source) => void;
}) {
  return (
    <div className="w-72 border-l border-surface-border bg-surface-raised">
      <div className="flex items-center justify-between border-b border-surface-border p-3">
        <h3 className="text-sm font-medium text-slate-200">Sources</h3>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ×
        </Button>
      </div>
      <ScrollArea className="h-[calc(100%-48px)]">
        <div className="space-y-2 p-3">
          {sources.map((source, index) => (
            <button
              key={`${source.filePath}-${index}`}
              onClick={() => onSourceClick(source)}
              className="w-full rounded-lg bg-surface p-3 text-left transition-colors hover:bg-surface-border"
            >
              <div className="flex items-center gap-2">
                <FileCode className="h-4 w-4 shrink-0 text-accent" />
                <span className="truncate text-xs font-medium text-slate-200">
                  {source.filePath.split("/").pop()}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Lines {source.startLine}-{source.endLine}
              </p>
              {source.score !== undefined && (
                <p className="mt-1 text-xs text-slate-600">
                  Relevance: {(source.score * 100).toFixed(0)}%
                </p>
              )}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
