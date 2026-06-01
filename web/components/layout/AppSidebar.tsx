"use client";

import { useState, useEffect, useMemo } from "react";
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
  GitBranch,
  FileText,
  Database,
  Clock,
  Menu,
  ChevronLeft,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
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

type SidebarTab = "threads" | "memory" | "settings" | "graph";

interface IndexingProgress {
  status: "idle" | "scanning" | "parsing" | "embedding" | "indexing" | "complete" | "error";
  filesScanned: number;
  filesTotal: number;
  chunksCreated: number;
  currentFile?: string;
  error?: string;
}

interface AppSidebarProps {
  isOpen?: boolean;
  onToggle?: () => void;
}

export function AppSidebar({ isOpen = true, onToggle }: AppSidebarProps) {
  const [activeTab, setActiveTab] = useState<SidebarTab>("threads");
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [newWorkspacePath, setNewWorkspacePath] = useState("");
  const [showNewWorkspace, setShowNewWorkspace] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

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
      <>
        {/* Mobile Toggle Button */}
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-3 left-3 z-50 lg:hidden"
          onClick={onToggle}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Backdrop for mobile */}
        {isOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={onToggle}
          />
        )}

        <aside
          className={cn(
            "flex h-full w-72 flex-col bg-bg-secondary border-r border-surface-border overflow-hidden",
            "fixed lg:relative inset-y-0 left-0 z-40",
            "transition-transform duration-200 lg:translate-x-0",
            isOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between h-14 px-4 border-b border-surface-border shrink-0 overflow-hidden">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent shrink-0">
                <Layers className="h-4 w-4 text-white" />
              </div>
              <div className="min-w-0">
                <h1 className="text-sm font-semibold text-text-primary truncate">Drishti</h1>
                <p className="text-2xs text-text-muted truncate">Code Intelligence</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              className="lg:hidden shrink-0"
              onClick={onToggle}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>

          {/* Workspace Selector */}
          <div className="px-3 py-3 border-b border-surface-border">
            <Dialog open={showNewWorkspace} onOpenChange={setShowNewWorkspace}>
              <div className="flex gap-2 overflow-hidden">
                <Select
                  value={activeWorkspaceId || ""}
                  onValueChange={(value) => setActiveWorkspace(value || null)}
                >
                  <SelectTrigger className="flex-1 h-9 min-w-0">
                    <SelectValue placeholder="Select workspace..." />
                  </SelectTrigger>
                  <SelectContent>
                    {workspaces.map((w) => (
                      <SelectItem key={w.id} value={w.id}>
                        <span className="flex items-center gap-2 truncate">
                          <FolderOpen className="h-3.5 w-3.5 text-text-muted shrink-0" />
                          <span className="truncate">{w.name}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <DialogTrigger asChild>
                  <Button variant="secondary" size="icon" className="h-9 w-9 shrink-0">
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
          <div className="flex gap-0.5 px-3 py-2 border-b border-surface-border">
            {[
              { id: "threads" as const, icon: MessageSquare, label: "Chats" },
              { id: "graph" as const, icon: GitBranch, label: "Graph" },
              { id: "memory" as const, icon: Brain, label: "Memory" },
              { id: "settings" as const, icon: Settings, label: "Settings" },
            ].map((tab) => (
              <Tooltip key={tab.id}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "flex-1 flex items-center justify-center py-2 rounded-lg text-sm font-medium transition-colors",
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
              <ThreadsPanel
                threads={workspaceThreads}
                activeThreadId={activeThreadId}
                activeWorkspaceId={activeWorkspaceId}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                editingThreadId={editingThreadId}
                editingTitle={editingTitle}
                setEditingThreadId={setEditingThreadId}
                setEditingTitle={setEditingTitle}
                onNewThread={handleNewThread}
                onRenameThread={handleRenameThread}
                onSelectThread={setActiveThread}
                onDeleteThread={deleteThread}
              />
            )}
            {activeTab === "graph" && <GraphPanel />}
            {activeTab === "memory" && <MemoryPanel />}
            {activeTab === "settings" && <SettingsPanel />}
          </ScrollArea>

          {/* Footer */}
          {mounted && activeWorkspace && (
            <WorkspaceFooter workspace={activeWorkspace} />
          )}
        </aside>
      </>
    </TooltipProvider>
  );
}

function ThreadsPanel({
  threads,
  activeThreadId,
  activeWorkspaceId,
  searchQuery,
  setSearchQuery,
  editingThreadId,
  editingTitle,
  setEditingThreadId,
  setEditingTitle,
  onNewThread,
  onRenameThread,
  onSelectThread,
  onDeleteThread,
}: {
  threads: Thread[];
  activeThreadId: string | null;
  activeWorkspaceId: string | null;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  editingThreadId: string | null;
  editingTitle: string;
  setEditingThreadId: (id: string | null) => void;
  setEditingTitle: (title: string) => void;
  onNewThread: () => void;
  onRenameThread: (id: string) => void;
  onSelectThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
}) {
  return (
    <div className="p-3 space-y-3">
      <Input
        placeholder="Search conversations..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        icon={<Search className="h-4 w-4" />}
        className="h-9"
      />

      <Button
        onClick={onNewThread}
        disabled={!activeWorkspaceId}
        className="w-full justify-start h-9"
        variant="secondary"
      >
        <Plus className="h-4 w-4" />
        New Chat
      </Button>

      <div className="space-y-1">
        {threads
          .sort((a, b) => b.updatedAt - a.updatedAt)
          .map((thread) => (
            <div
              key={thread.id}
              className={cn(
                "group flex items-center gap-2 rounded-lg px-3 py-2 transition-colors cursor-pointer overflow-hidden",
                activeThreadId === thread.id
                  ? "bg-surface text-text-primary"
                  : "text-text-secondary hover:bg-surface/50 hover:text-text-primary"
              )}
            >
              {editingThreadId === thread.id ? (
                <div className="flex flex-1 items-center gap-1 min-w-0">
                  <Input
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    className="h-7 text-sm flex-1 min-w-0"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") onRenameThread(thread.id);
                      if (e.key === "Escape") setEditingThreadId(null);
                    }}
                  />
                  <Button size="icon-sm" variant="ghost" className="shrink-0" onClick={() => onRenameThread(thread.id)}>
                    <Check className="h-3 w-3" />
                  </Button>
                  <Button size="icon-sm" variant="ghost" className="shrink-0" onClick={() => setEditingThreadId(null)}>
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ) : (
                <>
                  <MessageSquare className="h-4 w-4 shrink-0 text-text-muted" />
                  <button
                    onClick={() => onSelectThread(thread.id)}
                    className="flex-1 min-w-0 truncate text-left text-sm"
                    title={thread.title}
                  >
                    {thread.title}
                  </button>
                  <div className="flex gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
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
                        onDeleteThread(thread.id);
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

      {threads.length === 0 && activeWorkspaceId && !searchQuery && (
        <EmptyState icon={MessageSquare} title="No conversations yet" subtitle="Start a new chat to begin" />
      )}
      {threads.length === 0 && searchQuery && (
        <EmptyState icon={Search} title="No results found" />
      )}
      {!activeWorkspaceId && (
        <EmptyState icon={FolderOpen} title="Select a workspace" subtitle="Create or select a workspace to start" />
      )}
    </div>
  );
}

function GraphPanel() {
  const { getActiveWorkspace } = useAppStore();
  const activeWorkspace = getActiveWorkspace();
  const [graphData, setGraphData] = useState<{ nodes: number; edges: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const workspaceId = activeWorkspace?.id;
  const workspaceRepoPath = activeWorkspace?.repoPath;

  useEffect(() => {
    const loadStats = async () => {
      if (!workspaceRepoPath) return;
      setIsLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000"}/api/v1/graph/stats?repo_root=${encodeURIComponent(workspaceRepoPath)}`
        );
        if (response.ok) {
          const data = await response.json();
          setGraphData(data);
        }
      } catch (error) {
        console.error("Failed to load graph stats:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, [workspaceId, workspaceRepoPath]);

  if (!activeWorkspace) {
    return (
      <div className="p-4">
        <EmptyState icon={GitBranch} title="Select a workspace" subtitle="View dependency graph after indexing" />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-2">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
          Dependency Graph
        </label>
        <p className="text-sm text-text-tertiary">
          Visualize code relationships and dependencies.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="h-6 w-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
        </div>
      ) : graphData ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface rounded-lg p-3 border border-surface-border">
              <p className="text-2xl font-semibold text-text-primary">{graphData.nodes}</p>
              <p className="text-xs text-text-muted">Nodes</p>
            </div>
            <div className="bg-surface rounded-lg p-3 border border-surface-border">
              <p className="text-2xl font-semibold text-text-primary">{graphData.edges}</p>
              <p className="text-xs text-text-muted">Edges</p>
            </div>
          </div>

          <Button variant="secondary" className="w-full h-9" onClick={() => window.open(`/graph?workspace=${activeWorkspace.id}`, '_blank')}>
            <GitBranch className="h-4 w-4" />
            Open Graph Viewer
          </Button>
        </div>
      ) : (
        <div className="text-center py-6">
          <GitBranch className="h-8 w-8 text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-tertiary">No graph data</p>
          <p className="text-xs text-text-muted mt-1">Index the repository first</p>
        </div>
      )}

      <div className="pt-4 border-t border-surface-border space-y-2">
        <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Features</p>
        <ul className="space-y-2 text-sm text-text-tertiary">
          <li className="flex items-center gap-2 overflow-hidden">
            <GitBranch className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">Import/Export relationships</span>
          </li>
          <li className="flex items-center gap-2 overflow-hidden">
            <FileText className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">Function call graphs</span>
          </li>
          <li className="flex items-center gap-2 overflow-hidden">
            <Database className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">Class hierarchies</span>
          </li>
        </ul>
      </div>
    </div>
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
            className="flex-1 h-9"
            onKeyDown={(e) => e.key === "Enter" && handleAddFact()}
          />
          <Button onClick={handleAddFact} className="h-9 w-9" size="icon">
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
              className="group flex items-start gap-2 rounded-lg bg-surface p-3 border border-surface-border overflow-hidden"
            >
              <Brain className="h-4 w-4 shrink-0 text-accent mt-0.5" />
              <p className="flex-1 min-w-0 text-sm text-text-secondary break-words">{fact.content}</p>
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
          <EmptyState icon={Brain} title="No memories yet" subtitle="Add context for better responses" />
        )}
      </div>
    </div>
  );
}

function SettingsPanel() {
  const { settings, setSettings, getActiveWorkspace, updateWorkspace, ingestStatus, setIngestStatus } = useAppStore();
  const [indexingProgress, setIndexingProgress] = useState<IndexingProgress>({
    status: "idle",
    filesScanned: 0,
    filesTotal: 0,
    chunksCreated: 0,
  });
  const activeWorkspace = getActiveWorkspace();

  const handleIndex = async () => {
    if (!activeWorkspace) return;

    setIndexingProgress({
      status: "scanning",
      filesScanned: 0,
      filesTotal: 0,
      chunksCreated: 0,
    });

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

      setIndexingProgress({
        status: "complete",
        filesScanned: result.files_indexed || result.total_files || 0,
        filesTotal: result.files_indexed || result.total_files || 0,
        chunksCreated: result.total_chunks || 0,
      });

      updateWorkspace(activeWorkspace.id, {
        indexedAt: Date.now(),
        fileCount: result.files_indexed || result.total_files,
        chunkCount: result.total_chunks,
      });

      setIngestStatus(`Indexed ${result.total_chunks || 0} chunks from ${result.files_indexed || result.total_files || 0} files`);
    } catch (error) {
      setIndexingProgress({
        status: "error",
        filesScanned: 0,
        filesTotal: 0,
        chunksCreated: 0,
        error: error instanceof Error ? error.message : "Indexing failed",
      });
      setIngestStatus(error instanceof Error ? error.message : "Indexing failed");
    }
  };

  const isIndexing = indexingProgress.status !== "idle" && indexingProgress.status !== "complete" && indexingProgress.status !== "error";

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
          <SelectTrigger className="h-9">
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
          className="h-9"
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
            Temperature
          </label>
          <span className="text-xs text-text-secondary font-mono bg-surface px-2 py-0.5 rounded">
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
            Repository Indexing
          </label>

          <Button
            onClick={handleIndex}
            disabled={isIndexing}
            className="w-full h-9"
            variant={isIndexing ? "secondary" : "default"}
          >
            {isIndexing ? (
              <>
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {indexingProgress.status === "scanning" && "Scanning files..."}
                {indexingProgress.status === "parsing" && "Parsing code..."}
                {indexingProgress.status === "embedding" && "Creating embeddings..."}
                {indexingProgress.status === "indexing" && "Indexing..."}
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Index Repository
              </>
            )}
          </Button>

          {isIndexing && (
            <div className="space-y-2">
              <Progress value={indexingProgress.filesScanned} max={indexingProgress.filesTotal || 100} size="sm" />
              <div className="flex justify-between text-2xs text-text-muted">
                <span>{indexingProgress.filesScanned} files</span>
                <span>{indexingProgress.chunksCreated} chunks</span>
              </div>
            </div>
          )}

          {indexingProgress.status === "complete" && (
            <div className="bg-success-muted rounded-lg p-3 border border-success/20">
              <div className="flex items-center gap-2 text-success text-sm font-medium">
                <Check className="h-4 w-4" />
                Indexing Complete
              </div>
              <p className="text-xs text-text-tertiary mt-1">
                {indexingProgress.filesScanned} files, {indexingProgress.chunksCreated} chunks
              </p>
            </div>
          )}

          {indexingProgress.status === "error" && (
            <div className="bg-danger-muted rounded-lg p-3 border border-danger/20">
              <p className="text-sm text-danger">{indexingProgress.error}</p>
            </div>
          )}

          {activeWorkspace.indexedAt && indexingProgress.status === "idle" && (
            <div className="flex items-center gap-2 text-xs text-text-muted">
              <Clock className="h-3.5 w-3.5" />
              Last indexed: {new Date(activeWorkspace.indexedAt).toLocaleDateString()}
            </div>
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

function WorkspaceFooter({ workspace }: { workspace: { id: string; name: string; repoPath: string; fileCount?: number; chunkCount?: number; indexedAt?: number } }) {
  return (
    <div className="border-t border-surface-border p-3 shrink-0">
      <div className="flex items-center gap-3 overflow-hidden">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface shrink-0">
          <FolderOpen className="h-4 w-4 text-text-muted" />
        </div>
        <div className="flex-1 min-w-0 overflow-hidden">
          <p className="text-sm font-medium text-text-primary truncate">
            {workspace.name}
          </p>
          <p className="text-2xs text-text-muted truncate" title={workspace.repoPath}>
            {workspace.repoPath}
          </p>
        </div>
      </div>
      {workspace.fileCount !== undefined && (
        <div className="flex gap-2 mt-2 flex-wrap">
          <Badge variant="default" className="text-xs">{workspace.fileCount} files</Badge>
          <Badge variant="default" className="text-xs">{workspace.chunkCount || 0} chunks</Badge>
        </div>
      )}
    </div>
  );
}

function EmptyState({ icon: Icon, title, subtitle }: { icon: React.ElementType; title: string; subtitle?: string }) {
  return (
    <div className="flex flex-col items-center py-8 text-center">
      <Icon className="h-8 w-8 text-text-muted mb-3" />
      <p className="text-sm text-text-tertiary">{title}</p>
      {subtitle && <p className="text-xs text-text-muted mt-1">{subtitle}</p>}
    </div>
  );
}
