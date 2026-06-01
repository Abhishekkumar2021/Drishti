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
  MessageSquare,
  X,
  ExternalLink,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
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
  const messages = activeThread?.messages || [];

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

  return (
    <div className="flex flex-1 flex-col min-w-0">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-surface-border/30 px-6 py-4 backdrop-blur-sm bg-background/50">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-muted">
            <Sparkles className="h-4 w-4 text-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              {activeThread?.title || "New Conversation"}
            </h2>
            <p className="text-xs text-text-muted">
              {activeWorkspace
                ? `Querying ${activeWorkspace.name}`
                : "Select a workspace to start"}
            </p>
          </div>
        </div>
        {selectedMessageSources.length > 0 && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowSources(!showSources)}
            className="gap-2"
          >
            <FileCode className="h-4 w-4" />
            <span>{selectedMessageSources.length} Sources</span>
            <ChevronRight
              className={cn(
                "h-4 w-4 transition-transform duration-200",
                showSources && "rotate-90"
              )}
            />
          </Button>
        )}
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <ScrollArea className="flex-1 px-6 py-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {/* Empty State */}
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-full bg-gradient-to-r from-accent to-primary opacity-20 blur-xl" />
                  <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-primary shadow-glow">
                    <Code2 className="h-10 w-10 text-white" />
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-text-primary">
                  Ask about your codebase
                </h3>
                <p className="mt-3 max-w-md text-sm text-text-tertiary leading-relaxed">
                  {activeWorkspace
                    ? "Ask questions about how the code works, find implementations, or understand architecture. Citations link directly to source files."
                    : "Select or create a workspace, then index your repository to start exploring your code with AI."}
                </p>
                {activeWorkspace && (
                  <div className="mt-6 flex flex-wrap justify-center gap-2">
                    {[
                      "How does authentication work?",
                      "What is the main entry point?",
                      "Explain the data models",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setInput(suggestion)}
                        className="rounded-full bg-surface-raised/50 px-4 py-2 text-xs text-text-tertiary border border-surface-border/30 transition-all hover:bg-surface-raised hover:text-text-secondary hover:border-surface-border-light"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Messages */}
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={cn(
                  "animate-slide-up",
                  message.role === "user" && "flex justify-end"
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div
                  className={cn(
                    "relative max-w-[85%] rounded-2xl transition-all",
                    message.role === "user"
                      ? "bg-gradient-to-r from-accent to-accent-dark px-5 py-3 text-white shadow-glow-sm"
                      : "glass-card px-5 py-4"
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
                    <div className="mt-3 flex items-center gap-2 border-t border-surface-border/30 pt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-text-muted hover:text-text-secondary"
                        onClick={() => handleCopyMessage(message)}
                      >
                        {copiedMessageId === message.id ? (
                          <>
                            <Check className="mr-1.5 h-3 w-3 text-success" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="mr-1.5 h-3 w-3" />
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
                          <FileCode className="mr-1.5 h-3 w-3" />
                          {message.sources.length} sources
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading State */}
            {isAsking && messages[messages.length - 1]?.content === "" && (
              <div className="flex items-center gap-3 text-sm text-text-tertiary animate-fade-in">
                <div className="flex gap-1">
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: "0ms" }} />
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: "150ms" }} />
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: "300ms" }} />
                </div>
                <span>Thinking...</span>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </ScrollArea>

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

      {/* Input Area */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-surface-border/30 p-4 backdrop-blur-sm bg-background/50"
      >
        <div className="mx-auto flex max-w-3xl gap-3">
          <div className="relative flex-1">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                activeWorkspace
                  ? "Ask about your codebase..."
                  : "Select a workspace first"
              }
              disabled={isAsking || !activeWorkspace}
              className="pr-12 h-12 text-base"
              icon={<MessageSquare className="h-4 w-4" />}
            />
          </div>
          <Button
            type="submit"
            disabled={isAsking || !input.trim() || !activeWorkspace}
            size="lg"
            className="h-12 w-12 shrink-0"
          >
            {isAsking ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
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
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <div className="flex gap-1">
          <div className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
          <div className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: "150ms" }} />
          <div className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    );
  }

  return (
    <div className="prose prose-invert prose-sm max-w-none prose-pre:glass prose-pre:border prose-pre:border-surface-border/30">
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
            className="mx-0.5 inline-flex items-center gap-1.5 rounded-lg bg-accent-muted px-2 py-1 font-mono text-xs text-accent-light border border-accent/20 hover:bg-accent/20 hover:border-accent/40 transition-all"
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
    <div className="w-80 border-l border-surface-border/30 bg-background/50 backdrop-blur-sm animate-slide-left">
      <div className="flex items-center justify-between border-b border-surface-border/30 p-4">
        <h3 className="text-sm font-semibold text-text-primary">Sources</h3>
        <Button variant="ghost" size="icon-sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="h-[calc(100%-57px)]">
        <div className="space-y-2 p-3">
          {sources.map((source, index) => (
            <button
              key={`${source.filePath}-${index}`}
              onClick={() => onSourceClick(source)}
              className="w-full rounded-xl glass-card p-3 text-left transition-all hover:border-accent/30 hover:shadow-glow-sm group"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-muted">
                  <FileCode className="h-4 w-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="block truncate text-sm font-medium text-text-primary group-hover:text-accent-light transition-colors">
                    {source.filePath.split("/").pop()}
                  </span>
                  <span className="text-xs text-text-muted">
                    Lines {source.startLine}-{source.endLine}
                  </span>
                </div>
                <ExternalLink className="h-4 w-4 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              {source.score !== undefined && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-surface-raised overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-gradient-to-r from-accent to-primary"
                      style={{ width: `${source.score * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-text-muted font-medium">
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
