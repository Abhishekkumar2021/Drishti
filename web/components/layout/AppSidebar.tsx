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
  Search,
  Layers,
  Zap,
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
  const [searchQuery, setSearchQuery] = useState("");

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

  const workspaceThreads = threads
    .filter((t) => t.workspaceId === activeWorkspaceId)
    .filter((t) => 
      searchQuery ? t.title.toLowerCase().includes(searchQuery.toLowerCase()) : true
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
      <aside className="flex h-full w-72 flex-col bg-bg-secondary border-r border-surface-border">
        {/* Header */}
        <div className="flex items-center gap-3 h-14 px-4 border-b border-surface-border">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent">
            <Layers className="h-4 w-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-text-primary">Drishti</h1>
            <p className="text-2xs text-text-muted">Code Intelligence</p>
          </div>
        </div>

        {/* Workspace Selector */}
        <div className="px-4 py-3 border-b border-surface-border">
          <Dialog open={showNewWorkspace} onOpenChange={setShowNewWorkspace}>
            <div className="flex gap-2">
              <Select
                value={activeWorkspaceId || ""}
                onValueChange={(value) => setActiveWorkspace(value || null)}
              >
                <SelectTrigger className="flex-1 h-10">
                  <SelectValue placeholder="Select workspace..." />
                </SelectTrigger>
                <SelectContent>
                  {workspaces.map((w) => (
                    <SelectItem key={w.id} value={w.id}>
                      <span className="flex items-center gap-2">
                        <FolderOpen className="h-3.5 w-3.5 text-text-muted" />
                        {w.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <DialogTrigger asChild>
                <Button variant="secondary" size="icon" className="h-10 w-10 shrink-0">
                  <Plus className="h-4 w-4" />
                </Button>
              </DialogTrigger>
            </div>

            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Workspace</DialogTitle>
                <DialogDescription>
                  Add a codebase to index and explore with AI.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">Name</label>
                  <Input
                    placeholder="My Project"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">Path</label>
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
                <Button onClick={handleCreateWorkspace}>Create</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-4 py-2 border-b border-surface-border">
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
                    "flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "bg-surface text-text-primary"
                      : "text-text-tertiary hover:text-text-secondary hover:bg-surface/50"
                  )}
                >
                  <tab.icon className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">{tab.label}</TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          {activeTab === "threads" && (
            <div className="p-3 space-y-3">
              {/* Search */}
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={<Search className="h-4 w-4" />}
                className="h-9"
              />

              {/* New Chat Button */}
              <Button
                onClick={handleNewThread}
                disabled={!activeWorkspaceId}
                className="w-full justify-start h-10"
                variant="secondary"
              >
                <Plus className="h-4 w-4" />
                New Chat
              </Button>

              {/* Thread List */}
              <div className="space-y-1">
                {workspaceThreads
                  .sort((a, b) => b.updatedAt - a.updatedAt)
                  .map((thread) => (
                    <div
                      key={thread.id}
                      className={cn(
                        "group flex items-center gap-2 rounded-lg px-3 py-2.5 transition-colors cursor-pointer",
                        activeThreadId === thread.id
                          ? "bg-surface text-text-primary"
                          : "text-text-secondary hover:bg-surface/50 hover:text-text-primary"
                      )}
                    >
                      {editingThreadId === thread.id ? (
                        <div className="flex flex-1 items-center gap-1">
                          <Input
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            className="h-7 text-sm"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleRenameThread(thread.id);
                              if (e.key === "Escape") setEditingThreadId(null);
                            }}
                          />
                          <Button size="icon-sm" variant="ghost" onClick={() => handleRenameThread(thread.id)}>
                            <Check className="h-3.5 w-3.5" />
                          </Button>
                          <Button size="icon-sm" variant="ghost" onClick={() => setEditingThreadId(null)}>
                            <X className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <MessageSquare className="h-4 w-4 shrink-0 text-text-muted" />
                          <button
                            onClick={() => setActiveThread(thread.id)}
                            className="flex-1 truncate text-left text-sm"
                          >
                            {thread.title}
                          </button>
                          <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              className="h-6 w-6"
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingThreadId(thread.id);
                                setEditingTitle(thread.title);
                              }}
                            >
                              <Pencil className="h-3 w-3" />
                            </Button>
                            <Button
                              size="icon-sm"
                              variant="ghost"
                              className="h-6 w-6 text-danger hover:text-danger"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteThread(thread.id);
                              }}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
              </div>

              {/* Empty States */}
              {workspaceThreads.length === 0 && activeWorkspaceId && !searchQuery && (
                <div className="flex flex-col items-center py-8 text-center">
                  <MessageSquare className="h-8 w-8 text-text-muted mb-3" />
                  <p className="text-sm text-text-tertiary">No conversations yet</p>
                  <p className="text-xs text-text-muted mt-1">Start a new chat to begin</p>
                </div>
              )}

              {workspaceThreads.length === 0 && searchQuery && (
                <div className="flex flex-col items-center py-8 text-center">
                  <Search className="h-8 w-8 text-text-muted mb-3" />
                  <p className="text-sm text-text-tertiary">No results found</p>
                </div>
              )}

              {!activeWorkspaceId && (
                <div className="flex flex-col items-center py-8 text-center">
                  <FolderOpen className="h-8 w-8 text-text-muted mb-3" />
                  <p className="text-sm text-text-tertiary">Select a workspace</p>
                  <p className="text-xs text-text-muted mt-1">Create or select a workspace to start</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "memory" && <MemoryPanel />}
          {activeTab === "settings" && <SettingsPanel />}
        </ScrollArea>

        {/* Footer */}
        {activeWorkspace && (
          <div className="border-t border-surface-border p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface">
                <FolderOpen className="h-4 w-4 text-text-muted" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">
                  {activeWorkspace.name}
                </p>
                <p className="text-2xs text-text-muted truncate">
                  {activeWorkspace.repoPath}
                </p>
              </div>
            </div>
            {activeWorkspace.fileCount && (
              <div className="flex gap-2 mt-3">
                <Badge variant="default">{activeWorkspace.fileCount} files</Badge>
                <Badge variant="default">{activeWorkspace.chunkCount} chunks</Badge>
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
    <div className="p-4 space-y-4">
      <div className="space-y-2">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Add Memory
        </label>
        <div className="flex gap-2">
          <Input
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            placeholder="I prefer TypeScript..."
            className="flex-1 h-10"
            onKeyDown={(e) => e.key === "Enter" && handleAddFact()}
          />
          <Button onClick={handleAddFact} className="h-10">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
            Stored Memories
          </label>
          <Badge variant="outline">{memories.length}</Badge>
        </div>

        <div className="space-y-2">
          {memories.map((fact) => (
            <div
              key={fact.id}
              className="group flex items-start gap-3 rounded-lg bg-surface p-3 border border-surface-border"
            >
              <Brain className="h-4 w-4 shrink-0 text-accent mt-0.5" />
              <p className="flex-1 text-sm text-text-secondary">{fact.content}</p>
              <Button
                size="icon-sm"
                variant="ghost"
                className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 text-danger hover:text-danger"
                onClick={() => deleteMemory(fact.id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>

        {memories.length === 0 && (
          <div className="flex flex-col items-center py-8 text-center">
            <Brain className="h-8 w-8 text-text-muted mb-3" />
            <p className="text-sm text-text-tertiary">No memories yet</p>
            <p className="text-xs text-text-muted mt-1">Add context for better responses</p>
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
    setIngestStatus("Indexing...");

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
    <div className="p-4 space-y-5">
      <div className="space-y-2">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Model Provider
        </label>
        <Select
          value={settings.modelProvider}
          onValueChange={(value) =>
            setSettings({ modelProvider: value as typeof settings.modelProvider })
          }
        >
          <SelectTrigger className="h-10">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
            <SelectItem value="openai">OpenAI (GPT)</SelectItem>
            <SelectItem value="ollama">Ollama (Local)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Model
        </label>
        <Input
          value={settings.model}
          onChange={(e) => setSettings({ model: e.target.value })}
          placeholder="claude-sonnet-4-20250514"
          className="h-10"
        />
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
            Temperature
          </label>
          <span className="text-sm text-text-secondary font-mono">
            {settings.temperature.toFixed(1)}
          </span>
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
        <div className="flex justify-between text-2xs text-text-muted">
          <span>Precise</span>
          <span>Creative</span>
        </div>
      </div>

      {activeWorkspace && (
        <div className="space-y-3 pt-4 border-t border-surface-border">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
            Repository
          </label>
          <Button
            onClick={handleIndex}
            disabled={isIndexing}
            className="w-full h-10"
            variant={isIndexing ? "secondary" : "default"}
          >
            {isIndexing ? (
              <>
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Indexing...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Index Repository
              </>
            )}
          </Button>
          {ingestStatus && (
            <p className="text-xs text-text-tertiary bg-surface rounded-lg px-3 py-2 border border-surface-border">
              {ingestStatus}
            </p>
          )}
        </div>
      )}

      <div className="pt-4 border-t border-surface-border">
        <p className="text-2xs text-text-muted">
          API: {process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}
        </p>
      </div>
    </div>
  );
}
