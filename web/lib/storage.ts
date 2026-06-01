import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
  createdAt: number;
};

export type Source = {
  filePath: string;
  startLine: number;
  endLine: number;
  content?: string;
  score?: number;
};

export type Thread = {
  id: string;
  title: string;
  workspaceId: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
};

export type Workspace = {
  id: string;
  name: string;
  repoPath: string;
  indexedAt?: number;
  fileCount?: number;
  chunkCount?: number;
};

export type MemoryFact = {
  id: string;
  content: string;
  category: "preference" | "context" | "instruction";
  createdAt: number;
};

export type EditorState = {
  filePath: string;
  content: string;
  language: string;
  highlightStart: number;
  highlightEnd: number;
} | null;

export type ModelProvider = "anthropic" | "openai" | "ollama";

export type Settings = {
  modelProvider: ModelProvider;
  model: string;
  temperature: number;
  theme: "dark" | "light" | "system";
};

interface AppState {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  threads: Thread[];
  activeThreadId: string | null;
  memories: MemoryFact[];
  editor: EditorState;
  settings: Settings;
  isAsking: boolean;
  ingestStatus: string;
  
  setActiveWorkspace: (id: string | null) => void;
  addWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (id: string, updates: Partial<Workspace>) => void;
  deleteWorkspace: (id: string) => void;
  
  setActiveThread: (id: string | null) => void;
  addThread: (thread: Thread) => void;
  updateThread: (id: string, updates: Partial<Thread>) => void;
  deleteThread: (id: string) => void;
  
  addMessage: (threadId: string, message: Message) => void;
  updateMessage: (threadId: string, messageId: string, content: string, sources?: Source[]) => void;
  
  addMemory: (fact: MemoryFact) => void;
  updateMemory: (id: string, content: string) => void;
  deleteMemory: (id: string) => void;
  
  setEditor: (state: EditorState) => void;
  setSettings: (settings: Partial<Settings>) => void;
  setIsAsking: (value: boolean) => void;
  setIngestStatus: (status: string) => void;
  
  getActiveWorkspace: () => Workspace | undefined;
  getActiveThread: () => Thread | undefined;
}

const generateId = () => Math.random().toString(36).substring(2, 15);

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      workspaces: [],
      activeWorkspaceId: null,
      threads: [],
      activeThreadId: null,
      memories: [],
      editor: null,
      settings: {
        modelProvider: "anthropic",
        model: "claude-sonnet-4-20250514",
        temperature: 0.1,
        theme: "dark",
      },
      isAsking: false,
      ingestStatus: "",

      setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),
      
      addWorkspace: (workspace) =>
        set((state) => ({
          workspaces: [...state.workspaces, workspace],
          activeWorkspaceId: workspace.id,
        })),
        
      updateWorkspace: (id, updates) =>
        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.id === id ? { ...w, ...updates } : w
          ),
        })),
        
      deleteWorkspace: (id) =>
        set((state) => ({
          workspaces: state.workspaces.filter((w) => w.id !== id),
          threads: state.threads.filter((t) => t.workspaceId !== id),
          activeWorkspaceId:
            state.activeWorkspaceId === id ? null : state.activeWorkspaceId,
        })),

      setActiveThread: (id) => set({ activeThreadId: id }),
      
      addThread: (thread) =>
        set((state) => ({
          threads: [...state.threads, thread],
          activeThreadId: thread.id,
        })),
        
      updateThread: (id, updates) =>
        set((state) => ({
          threads: state.threads.map((t) =>
            t.id === id ? { ...t, ...updates, updatedAt: Date.now() } : t
          ),
        })),
        
      deleteThread: (id) =>
        set((state) => ({
          threads: state.threads.filter((t) => t.id !== id),
          activeThreadId:
            state.activeThreadId === id ? null : state.activeThreadId,
        })),

      addMessage: (threadId, message) =>
        set((state) => ({
          threads: state.threads.map((t) =>
            t.id === threadId
              ? {
                  ...t,
                  messages: [...t.messages, message],
                  updatedAt: Date.now(),
                  title:
                    t.messages.length === 0 && message.role === "user"
                      ? message.content.slice(0, 50) + (message.content.length > 50 ? "..." : "")
                      : t.title,
                }
              : t
          ),
        })),
        
      updateMessage: (threadId, messageId, content, sources) =>
        set((state) => ({
          threads: state.threads.map((t) =>
            t.id === threadId
              ? {
                  ...t,
                  messages: t.messages.map((m) =>
                    m.id === messageId ? { ...m, content, sources } : m
                  ),
                  updatedAt: Date.now(),
                }
              : t
          ),
        })),

      addMemory: (fact) =>
        set((state) => ({ memories: [...state.memories, fact] })),
        
      updateMemory: (id, content) =>
        set((state) => ({
          memories: state.memories.map((m) =>
            m.id === id ? { ...m, content } : m
          ),
        })),
        
      deleteMemory: (id) =>
        set((state) => ({
          memories: state.memories.filter((m) => m.id !== id),
        })),

      setEditor: (editor) => set({ editor }),
      setSettings: (updates) =>
        set((state) => ({ settings: { ...state.settings, ...updates } })),
      setIsAsking: (isAsking) => set({ isAsking }),
      setIngestStatus: (ingestStatus) => set({ ingestStatus }),

      getActiveWorkspace: () => {
        const state = get();
        return state.workspaces.find((w) => w.id === state.activeWorkspaceId);
      },
      
      getActiveThread: () => {
        const state = get();
        return state.threads.find((t) => t.id === state.activeThreadId);
      },
    }),
    {
      name: "drishti-app-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        workspaces: state.workspaces,
        activeWorkspaceId: state.activeWorkspaceId,
        threads: state.threads,
        activeThreadId: state.activeThreadId,
        memories: state.memories,
        settings: state.settings,
      }),
    }
  )
);

export { generateId };
