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
  MoreHorizontal,
  Pencil,
  Check,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
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
      <aside className="flex h-full w-64 flex-col border-r border-surface-border bg-surface-raised">
        <div className="flex items-center justify-between border-b border-surface-border p-4">
          <div>
            <h1 className="text-lg font-semibold text-white">Drishti</h1>
            <p className="text-xs text-slate-500">दृष्टि — Code RAG</p>
          </div>
        </div>

        <div className="border-b border-surface-border p-2">
          <Dialog open={showNewWorkspace} onOpenChange={setShowNewWorkspace}>
            <div className="flex gap-1">
              <select
                value={activeWorkspaceId || ""}
                onChange={(e) => setActiveWorkspace(e.target.value || null)}
                className="flex-1 rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-accent focus:outline-none"
              >
                <option value="">Select workspace...</option>
                {workspaces.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
              <DialogTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </DialogTrigger>
            </div>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Workspace</DialogTitle>
                <DialogDescription>
                  Create a new workspace to index and query a codebase.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200">Name</label>
                  <Input
                    placeholder="My Project"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200">
                    Repository Path
                  </label>
                  <Input
                    placeholder="/path/to/repository"
                    value={newWorkspacePath}
                    onChange={(e) => setNewWorkspacePath(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewWorkspace(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateWorkspace}>Create</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="flex border-b border-surface-border">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setActiveTab("threads")}
                className={cn(
                  "flex-1 p-3 transition-colors",
                  activeTab === "threads"
                    ? "border-b-2 border-accent text-accent"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <MessageSquare className="mx-auto h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Threads</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setActiveTab("memory")}
                className={cn(
                  "flex-1 p-3 transition-colors",
                  activeTab === "memory"
                    ? "border-b-2 border-accent text-accent"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Brain className="mx-auto h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Memory</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setActiveTab("settings")}
                className={cn(
                  "flex-1 p-3 transition-colors",
                  activeTab === "settings"
                    ? "border-b-2 border-accent text-accent"
                    : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Settings className="mx-auto h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Settings</TooltipContent>
          </Tooltip>
        </div>

        <ScrollArea className="flex-1">
          {activeTab === "threads" && (
            <div className="p-2">
              <Button
                onClick={handleNewThread}
                disabled={!activeWorkspaceId}
                className="mb-2 w-full justify-start"
                variant="outline"
              >
                <Plus className="mr-2 h-4 w-4" />
                New Chat
              </Button>

              <div className="space-y-1">
                {workspaceThreads
                  .sort((a, b) => b.updatedAt - a.updatedAt)
                  .map((thread) => (
                    <div
                      key={thread.id}
                      className={cn(
                        "group flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors",
                        activeThreadId === thread.id
                          ? "bg-accent/20 text-slate-100"
                          : "text-slate-400 hover:bg-surface hover:text-slate-200"
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
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6"
                            onClick={() => handleRenameThread(thread.id)}
                          >
                            <Check className="h-3 w-3" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6"
                            onClick={() => setEditingThreadId(null)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <button
                            onClick={() => setActiveThread(thread.id)}
                            className="flex-1 truncate text-left"
                          >
                            {thread.title}
                          </button>
                          <div className="hidden gap-1 group-hover:flex">
                            <Button
                              size="icon"
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
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6 text-red-400 hover:text-red-300"
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
                <p className="mt-4 px-3 text-center text-xs text-slate-500">
                  No conversations yet. Start a new chat!
                </p>
              )}
              {!activeWorkspaceId && (
                <p className="mt-4 px-3 text-center text-xs text-slate-500">
                  Select or create a workspace to start chatting.
                </p>
              )}
            </div>
          )}

          {activeTab === "memory" && <MemoryPanel />}
          {activeTab === "settings" && <SettingsPanel />}
        </ScrollArea>

        {activeWorkspace && (
          <div className="border-t border-surface-border p-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <FolderOpen className="h-4 w-4" />
              <span className="truncate">{activeWorkspace.repoPath}</span>
            </div>
            {activeWorkspace.fileCount && (
              <p className="mt-1 text-xs text-slate-600">
                {activeWorkspace.fileCount} files, {activeWorkspace.chunkCount} chunks
              </p>
            )}
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}

function MemoryPanel() {
  const { memories, addMemory, updateMemory, deleteMemory } = useAppStore();
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
    <div className="p-3 space-y-3">
      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Add Memory
        </label>
        <div className="flex gap-2">
          <Input
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            placeholder="I prefer TypeScript..."
            className="flex-1 text-xs"
            onKeyDown={(e) => e.key === "Enter" && handleAddFact()}
          />
          <Button size="sm" onClick={handleAddFact}>
            Add
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Stored Facts ({memories.length})
        </label>
        {memories.map((fact) => (
          <div
            key={fact.id}
            className="group flex items-start gap-2 rounded-lg bg-surface p-2 text-xs"
          >
            <Brain className="mt-0.5 h-3 w-3 shrink-0 text-accent" />
            <p className="flex-1 text-slate-300">{fact.content}</p>
            <Button
              size="icon"
              variant="ghost"
              className="h-5 w-5 shrink-0 opacity-0 group-hover:opacity-100"
              onClick={() => deleteMemory(fact.id)}
            >
              <Trash2 className="h-3 w-3 text-red-400" />
            </Button>
          </div>
        ))}
        {memories.length === 0 && (
          <p className="text-center text-xs text-slate-600">
            No memories stored yet. Add facts the assistant should remember.
          </p>
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
      
      setIngestStatus(`Indexed ${result.total_chunks || 0} chunks from ${result.files_indexed || result.total_files || 0} files`);
    } catch (error) {
      setIngestStatus(error instanceof Error ? error.message : "Indexing failed");
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <div className="space-y-4 p-3">
      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Model Provider
        </label>
        <select
          value={settings.modelProvider}
          onChange={(e) =>
            setSettings({ modelProvider: e.target.value as typeof settings.modelProvider })
          }
          className="w-full rounded-lg border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-accent focus:outline-none"
        >
          <option value="anthropic">Anthropic (Claude)</option>
          <option value="openai">OpenAI (GPT)</option>
          <option value="ollama">Ollama (Local)</option>
        </select>
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Model
        </label>
        <Input
          value={settings.model}
          onChange={(e) => setSettings({ model: e.target.value })}
          placeholder="claude-sonnet-4-20250514"
        />
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Temperature: {settings.temperature}
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => setSettings({ temperature: parseFloat(e.target.value) })}
          className="w-full accent-accent"
        />
      </div>

      {activeWorkspace && (
        <div className="space-y-2 border-t border-surface-border pt-4">
          <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Indexing
          </label>
          <Button
            onClick={handleIndex}
            disabled={isIndexing}
            className="w-full"
            variant="outline"
          >
            <Upload className="mr-2 h-4 w-4" />
            {isIndexing ? "Indexing..." : "Index Repository"}
          </Button>
          {ingestStatus && (
            <p className="text-xs text-slate-500">{ingestStatus}</p>
          )}
        </div>
      )}

      <div className="border-t border-surface-border pt-4 text-xs text-slate-600">
        <p>API: {process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}</p>
      </div>
    </div>
  );
}
