"use client";

import { useState } from "react";
import {
  Plus,
  MessageSquare,
  Trash2,
  Settings,
  FolderOpen,
  Brain,
  Upload,
  Pencil,
  Check,
  X,
  Sparkles,
  ChevronRight,
  Zap,
  Database,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/cn";
import { useAppStore, generateId, type Thread } from "@/lib/storage";

type SidebarTab = "threads" | "memory" | "settings";

export function AppSidebar() {
  const [activeTab, setActiveTab] = useState<SidebarTab>("threads");
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [newWorkspacePath, setNewWorkspacePath] = useState("");
  const [showNewWorkspace, setShowNewWorkspace] = useState(false);

  const {
    workspaces,
    activeWorkspaceId,
    threads,
    activeThreadId,
    setActiveWorkspace,
    addWorkspace,
    setActiveThread,
    addThread,
    updateThread,
    deleteThread,
    getActiveWorkspace,
  } = useAppStore();

  const workspaceThreads = threads.filter(
    (t) => t.workspaceId === activeWorkspaceId
  );

  const handleNewThread = () => {
    if (!activeWorkspaceId) return;
    const thread: Thread = {
      id: generateId(),
      title: "New conversation",
      workspaceId: activeWorkspaceId,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    addThread(thread);
  };

  const handleRenameThread = (threadId: string) => {
    if (editingTitle.trim()) {
      updateThread(threadId, { title: editingTitle.trim() });
    }
    setEditingThreadId(null);
    setEditingTitle("");
  };

  const handleCreateWorkspace = () => {
    if (!newWorkspaceName.trim() || !newWorkspacePath.trim()) return;
    addWorkspace({
      id: generateId(),
      name: newWorkspaceName.trim(),
      repoPath: newWorkspacePath.trim(),
    });
    setNewWorkspaceName("");
    setNewWorkspacePath("");
    setShowNewWorkspace(false);
  };

  const activeWorkspace = getActiveWorkspace();

  return (
    <TooltipProvider delayDuration={0}>
      <aside className="flex h-full w-72 flex-col glass-solid border-r-0">
        {/* Logo Header */}
        <div className="relative overflow-hidden border-b border-surface-border/30 p-5">
          <div className="absolute inset-0 bg-gradient-to-br from-accent/10 via-transparent to-primary/5" />
          <div className="relative flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-primary shadow-glow-sm">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gradient">Drishti</h1>
              <p className="text-xs text-text-muted">दृष्टि — Code Intelligence</p>
            </div>
          </div>
        </div>

        {/* Workspace Selector */}
        <div className="border-b border-surface-border/30 p-3">
          <Dialog open={showNewWorkspace} onOpenChange={setShowNewWorkspace}>
            <div className="flex gap-2">
              <Select
                value={activeWorkspaceId || ""}
                onValueChange={(value) => setActiveWorkspace(value || null)}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select workspace..." />
                </SelectTrigger>
                <SelectContent>
                  {workspaces.map((w) => (
                    <SelectItem key={w.id} value={w.id}>
                      <div className="flex items-center gap-2">
                        <Database className="h-3.5 w-3.5 text-accent" />
                        {w.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <DialogTrigger asChild>
                <Button variant="outline" size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </DialogTrigger>
            </div>

            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Workspace</DialogTitle>
                <DialogDescription>
                  Add a new codebase to index and query with AI.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">
                    Workspace Name
                  </label>
                  <Input
                    placeholder="My Project"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">
                    Repository Path
                  </label>
                  <Input
                    placeholder="/path/to/repository"
                    value={newWorkspacePath}
                    onChange={(e) => setNewWorkspacePath(e.target.value)}
                    icon={<FolderOpen className="h-4 w-4" />}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="secondary" onClick={() => setShowNewWorkspace(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateWorkspace}>
                  <Zap className="mr-2 h-4 w-4" />
                  Create
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-surface-border/30">
          {[
            { id: "threads" as const, icon: MessageSquare, label: "Chats" },
            { id: "memory" as const, icon: Brain, label: "Memory" },
            { id: "settings" as const, icon: Settings, label: "Settings" },
          ].map((tab) => (
            <Tooltip key={tab.id}>
              <TooltipTrigger asChild>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex-1 p-3.5 transition-all duration-200 relative",
                    activeTab === tab.id
                      ? "text-accent"
                      : "text-text-muted hover:text-text-secondary"
                  )}
                >
                  <tab.icon className="mx-auto h-5 w-5" />
                  {activeTab === tab.id && (
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-8 rounded-full bg-gradient-to-r from-accent to-primary" />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">{tab.label}</TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Content Area */}
        <ScrollArea className="flex-1">
          {activeTab === "threads" && (
            <div className="p-3 space-y-2">
              <Button
                onClick={handleNewThread}
                disabled={!activeWorkspaceId}
                className="w-full justify-start"
                variant="secondary"
              >
                <Plus className="mr-2 h-4 w-4" />
                New Chat
              </Button>

              <div className="space-y-1 pt-2">
                {workspaceThreads
                  .sort((a, b) => b.updatedAt - a.updatedAt)
                  .map((thread) => (
                    <div
                      key={thread.id}
                      className={cn(
                        "group flex items-center gap-2 rounded-xl px-3 py-2.5 transition-all duration-200",
                        activeThreadId === thread.id
                          ? "bg-accent-muted border border-accent/20 text-text-primary"
                          : "text-text-tertiary hover:bg-surface-raised/50 hover:text-text-secondary border border-transparent"
                      )}
                    >
                      {editingThreadId === thread.id ? (
                        <div className="flex flex-1 items-center gap-1">
                          <Input
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            className="h-7 text-xs"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleRenameThread(thread.id);
                              if (e.key === "Escape") setEditingThreadId(null);
                            }}
                          />
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={() => handleRenameThread(thread.id)}
                          >
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={() => setEditingThreadId(null)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <button
                            onClick={() => setActiveThread(thread.id)}
                            className="flex-1 truncate text-left text-sm"
                          >
                            {thread.title}
                          </button>
                          <div className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              className="h-6 w-6"
                              onClick={() => {
                                setEditingThreadId(thread.id);
                                setEditingTitle(thread.title);
                              }}
                            >
                              <Pencil className="h-3 w-3" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              className="h-6 w-6 text-danger hover:text-danger hover:bg-danger-muted"
                              onClick={() => deleteThread(thread.id)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
              </div>

              {workspaceThreads.length === 0 && activeWorkspaceId && (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="rounded-full bg-surface-raised p-3 mb-3">
                    <MessageSquare className="h-5 w-5 text-text-muted" />
                  </div>
                  <p className="text-xs text-text-muted">
                    No conversations yet
                  </p>
                  <p className="text-xs text-text-muted/70 mt-1">
                    Start a new chat to begin
                  </p>
                </div>
              )}
              
              {!activeWorkspaceId && (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="rounded-full bg-accent-muted p-3 mb-3">
                    <Database className="h-5 w-5 text-accent" />
                  </div>
                  <p className="text-xs text-text-muted">
                    Select a workspace
                  </p>
                  <p className="text-xs text-text-muted/70 mt-1">
                    Create or select a workspace to start
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "memory" && <MemoryPanel />}
          {activeTab === "settings" && <SettingsPanel />}
        </ScrollArea>

        {/* Workspace Info Footer */}
        {activeWorkspace && (
          <div className="border-t border-surface-border/30 p-3 bg-surface-raised/30">
            <div className="flex items-center gap-2 text-xs">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-muted">
                <FolderOpen className="h-4 w-4 text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="truncate font-medium text-text-secondary">
                  {activeWorkspace.name}
                </p>
                <p className="truncate text-text-muted text-[10px]">
                  {activeWorkspace.repoPath}
                </p>
              </div>
            </div>
            {activeWorkspace.fileCount && (
              <div className="flex gap-2 mt-2">
                <Badge variant="secondary" className="text-[10px]">
                  {activeWorkspace.fileCount} files
                </Badge>
                <Badge variant="secondary" className="text-[10px]">
                  {activeWorkspace.chunkCount} chunks
                </Badge>
              </div>
            )}
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}

function MemoryPanel() {
  const { memories, addMemory, deleteMemory } = useAppStore();
  const [newFact, setNewFact] = useState("");

  const handleAddFact = () => {
    if (!newFact.trim()) return;
    addMemory({
      id: generateId(),
      content: newFact.trim(),
      category: "context",
      createdAt: Date.now(),
    });
    setNewFact("");
  };

  return (
    <div className="p-3 space-y-4">
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Add Memory
        </label>
        <div className="flex gap-2">
          <Input
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            placeholder="I prefer TypeScript..."
            className="flex-1 text-sm"
            onKeyDown={(e) => e.key === "Enter" && handleAddFact()}
          />
          <Button size="sm" onClick={handleAddFact}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-[10px] text-text-muted">
          Memories help the AI understand your preferences and context.
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Stored Memories
          </label>
          <Badge variant="outline">{memories.length}</Badge>
        </div>
        
        <div className="space-y-2">
          {memories.map((fact) => (
            <div
              key={fact.id}
              className="group flex items-start gap-2 rounded-xl bg-surface-raised/50 p-3 border border-surface-border/30 transition-all hover:border-surface-border-light"
            >
              <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-accent-muted">
                <Brain className="h-3 w-3 text-accent" />
              </div>
              <p className="flex-1 text-sm text-text-secondary">{fact.content}</p>
              <Button
                size="icon-sm"
                variant="ghost"
                className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 text-danger hover:text-danger hover:bg-danger-muted"
                onClick={() => deleteMemory(fact.id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>

        {memories.length === 0 && (
          <div className="flex flex-col items-center py-6 text-center">
            <div className="rounded-full bg-surface-raised p-3 mb-3">
              <Brain className="h-5 w-5 text-text-muted" />
            </div>
            <p className="text-xs text-text-muted">No memories yet</p>
            <p className="text-xs text-text-muted/70 mt-1">
              Add facts for personalized responses
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsPanel() {
  const { settings, setSettings, getActiveWorkspace, updateWorkspace, ingestStatus, setIngestStatus } = useAppStore();
  const [isIndexing, setIsIndexing] = useState(false);
  const activeWorkspace = getActiveWorkspace();

  const handleIndex = async () => {
    if (!activeWorkspace) return;
    setIsIndexing(true);
    setIngestStatus("Indexing repository...");
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}/api/v1/ingest`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            repo_root: activeWorkspace.repoPath,
            force: false,
          }),
        }
      );
      
      if (!response.ok) throw new Error("Indexing failed");
      const result = await response.json();
      
      updateWorkspace(activeWorkspace.id, {
        indexedAt: Date.now(),
        fileCount: result.files_indexed || result.total_files,
        chunkCount: result.total_chunks,
      });
      
      setIngestStatus(`Indexed ${result.total_chunks || 0} chunks`);
    } catch (error) {
      setIngestStatus(error instanceof Error ? error.message : "Indexing failed");
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <div className="space-y-5 p-3">
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Model Provider
        </label>
        <Select
          value={settings.modelProvider}
          onValueChange={(value) =>
            setSettings({ modelProvider: value as typeof settings.modelProvider })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="anthropic">
              <div className="flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                Anthropic (Claude)
              </div>
            </SelectItem>
            <SelectItem value="openai">
              <div className="flex items-center gap-2">
                <Zap className="h-3.5 w-3.5 text-success" />
                OpenAI (GPT)
              </div>
            </SelectItem>
            <SelectItem value="ollama">
              <div className="flex items-center gap-2">
                <Database className="h-3.5 w-3.5 text-primary" />
                Ollama (Local)
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Model
        </label>
        <Input
          value={settings.model}
          onChange={(e) => setSettings({ model: e.target.value })}
          placeholder="claude-sonnet-4-20250514"
        />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Temperature
          </label>
          <Badge variant="outline" className="font-mono">
            {settings.temperature.toFixed(1)}
          </Badge>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => setSettings({ temperature: parseFloat(e.target.value) })}
          className="w-full"
        />
        <div className="flex justify-between text-[10px] text-text-muted">
          <span>Precise</span>
          <span>Creative</span>
        </div>
      </div>

      {activeWorkspace && (
        <div className="space-y-3 border-t border-surface-border/30 pt-4">
          <label className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Repository Indexing
          </label>
          <Button
            onClick={handleIndex}
            disabled={isIndexing}
            className="w-full"
            variant={isIndexing ? "secondary" : "default"}
          >
            {isIndexing ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white mr-2" />
                Indexing...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Index Repository
              </>
            )}
          </Button>
          {ingestStatus && (
            <div className="rounded-lg bg-surface-raised/50 p-2 text-xs text-text-tertiary border border-surface-border/30">
              {ingestStatus}
            </div>
          )}
        </div>
      )}

      <div className="border-t border-surface-border/30 pt-4 text-[10px] text-text-muted">
        <p>
          API: {process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}
        </p>
      </div>
    </div>
  );
}
