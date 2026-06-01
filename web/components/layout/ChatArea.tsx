"use client";

import { FormEvent, useRef, useState, useEffect, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import {
  Send,
  FileCode,
  Loader2,
  Copy,
  Check,
  Code2,
  X,
  ArrowRight,
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
  const inputRef = useRef<HTMLInputElement>(null);

  const activeThread = getActiveThread();
  const activeWorkspace = getActiveWorkspace();
  const messages = useMemo(() => activeThread?.messages || [], [activeThread?.messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!isAsking && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isAsking]);

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

  const suggestions = [
    "How does authentication work?",
    "What is the main entry point?",
    "Explain the data models",
  ];

  return (
    <div className="flex h-full w-full flex-col min-w-0 bg-bg">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-surface-border h-14 px-6">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">
            {activeThread?.title || "New Conversation"}
          </h2>
          <p className="text-xs text-text-muted">
            {activeWorkspace ? `Querying ${activeWorkspace.name}` : "Select a workspace"}
          </p>
        </div>
        {selectedMessageSources.length > 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowSources(!showSources)}
          >
            <FileCode className="h-4 w-4" />
            {selectedMessageSources.length} Sources
          </Button>
        )}
      </header>

      {/* Chat Area */}
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex flex-col">
          <ScrollArea className="flex-1">
            <div className="max-w-3xl mx-auto px-6 py-6">
              {/* Empty State */}
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-surface border border-surface-border mb-5">
                    <Code2 className="h-7 w-7 text-text-muted" />
                  </div>
                  <h3 className="text-lg font-semibold text-text-primary">
                    Ask about your codebase
                  </h3>
                  <p className="mt-2 text-sm text-text-tertiary text-center max-w-md">
                    {activeWorkspace
                      ? "Ask questions about how the code works. Citations link to source files."
                      : "Select a workspace to start exploring your code with AI."}
                  </p>

                  {activeWorkspace && (
                    <div className="flex flex-wrap justify-center gap-2 mt-6">
                      {suggestions.map((suggestion) => (
                        <button
                          key={suggestion}
                          onClick={() => setInput(suggestion)}
                          className="flex items-center gap-2 px-4 py-2 rounded-full text-sm text-text-secondary bg-surface border border-surface-border hover:bg-surface-hover hover:text-text-primary hover:border-surface-border-light transition-colors"
                        >
                          {suggestion}
                          <ArrowRight className="h-3.5 w-3.5" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Messages */}
              <div className="space-y-5">
                {messages.map((message, index) => (
                  <div
                    key={message.id}
                    className={cn(
                      "animate-slide-up",
                      message.role === "user" && "flex justify-end"
                    )}
                    style={{ animationDelay: `${Math.min(index * 30, 150)}ms` }}
                  >
                    <div
                      className={cn(
                        "max-w-[85%] rounded-2xl px-4 py-3",
                        message.role === "user"
                          ? "bg-accent text-white"
                          : "bg-surface border border-surface-border"
                      )}
                    >
                      {message.role === "user" ? (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                      ) : (
                        <AssistantContent
                          content={message.content}
                          onCitationClick={handleCitationClick}
                        />
                      )}

                      {message.role === "assistant" && message.content && (
                        <div className="flex items-center gap-1 mt-3 pt-3 border-t border-surface-border">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-text-muted hover:text-text-secondary"
                            onClick={() => handleCopyMessage(message)}
                          >
                            {copiedMessageId === message.id ? (
                              <>
                                <Check className="h-3.5 w-3.5 text-success" />
                                Copied
                              </>
                            ) : (
                              <>
                                <Copy className="h-3.5 w-3.5" />
                                Copy
                              </>
                            )}
                          </Button>
                          {message.sources && message.sources.length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-text-muted hover:text-text-secondary"
                              onClick={() => {
                                setSelectedMessageSources(message.sources || []);
                                setShowSources(true);
                              }}
                            >
                              <FileCode className="h-3.5 w-3.5" />
                              {message.sources.length} sources
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading */}
                {isAsking && messages[messages.length - 1]?.content === "" && (
                  <div className="flex items-center gap-2 text-sm text-text-muted animate-fade-in">
                    <div className="flex gap-1">
                      <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" />
                      <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "150ms" }} />
                      <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "300ms" }} />
                    </div>
                    Thinking...
                  </div>
                )}
              </div>

              <div ref={bottomRef} />
            </div>
          </ScrollArea>

          {/* Input - full width */}
          <div className="border-t border-surface-border bg-bg shrink-0">
            <form onSubmit={handleSubmit} className="flex gap-3 px-6 py-4">
              <Input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={activeWorkspace ? "Ask about your codebase..." : "Select a workspace first"}
                disabled={isAsking || !activeWorkspace}
                className="flex-1 h-11"
              />
              <Button
                type="submit"
                disabled={isAsking || !input.trim() || !activeWorkspace}
                className="h-11 w-11 shrink-0"
              >
                {isAsking ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          </div>
        </div>

        {/* Sources Panel */}
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
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <div className="flex gap-1">
          <div className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse" />
          <div className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "150ms" }} />
          <div className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    );
  }

  return (
    <div className="prose prose-sm max-w-none text-text-secondary prose-headings:text-text-primary prose-strong:text-text-primary prose-code:text-text-primary">
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
            className="inline-flex items-center gap-1 mx-0.5 px-2 py-0.5 rounded-md text-xs font-medium text-accent bg-accent-muted hover:bg-accent-muted-hover transition-colors"
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
    <div className="w-80 shrink-0 border-l border-surface-border bg-bg-secondary flex flex-col">
      <div className="flex items-center justify-between border-b border-surface-border h-14 px-4 shrink-0">
        <h3 className="text-sm font-semibold text-text-primary">Sources</h3>
        <Button variant="ghost" size="icon-sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {sources.map((source, index) => (
            <button
              key={`${source.filePath}-${index}`}
              onClick={() => onSourceClick(source)}
              className="w-full text-left rounded-xl bg-surface border border-surface-border p-3 hover:bg-surface-hover hover:border-surface-border-light transition-colors group"
            >
              <div className="flex items-center gap-2 mb-1 overflow-hidden">
                <FileCode className="h-4 w-4 text-accent shrink-0" />
                <span className="text-sm font-medium text-text-primary truncate group-hover:text-accent transition-colors">
                  {source.filePath.split("/").pop()}
                </span>
              </div>
              <p className="text-xs text-text-muted pl-6 truncate" title={source.filePath}>
                {source.filePath}
              </p>
              <p className="text-xs text-text-tertiary pl-6 mt-0.5">
                Lines {source.startLine}-{source.endLine}
              </p>
              {source.score !== undefined && (
                <div className="flex items-center gap-2 mt-2 pl-6">
                  <div className="flex-1 h-1.5 rounded-full bg-surface-border overflow-hidden">
                    <div
                      className="h-full rounded-full bg-accent transition-all"
                      style={{ width: `${source.score * 100}%` }}
                    />
                  </div>
                  <span className="text-2xs text-text-muted font-medium">
                    {(source.score * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
