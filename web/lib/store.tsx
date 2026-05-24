"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { ChatMessage } from "./api";

export type EditorState = {
  filePath: string;
  content: string;
  language: string;
  highlightStart: number;
  highlightEnd: number;
} | null;

type AppState = {
  repoPath: string;
  setRepoPath: (path: string) => void;
  ingestStatus: string;
  setIngestStatus: (status: string) => void;
  messages: ChatMessage[];
  appendMessage: (message: ChatMessage) => void;
  updateLastAssistant: (content: string) => void;
  editor: EditorState;
  openEditor: (state: NonNullable<EditorState>) => void;
  isAsking: boolean;
  setIsAsking: (value: boolean) => void;
};

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [repoPath, setRepoPath] = useState("");
  const [ingestStatus, setIngestStatus] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [editor, setEditor] = useState<EditorState>(null);
  const [isAsking, setIsAsking] = useState(false);

  const appendMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const updateLastAssistant = useCallback((content: string) => {
    setMessages((prev) => {
      if (prev.length === 0 || prev[prev.length - 1].role !== "assistant") {
        return [...prev, { role: "assistant", content }];
      }
      const next = [...prev];
      next[next.length - 1] = { role: "assistant", content };
      return next;
    });
  }, []);

  const openEditor = useCallback((state: NonNullable<EditorState>) => {
    setEditor(state);
  }, []);

  const value = useMemo(
    () => ({
      repoPath,
      setRepoPath,
      ingestStatus,
      setIngestStatus,
      messages,
      appendMessage,
      updateLastAssistant,
      editor,
      openEditor,
      isAsking,
      setIsAsking,
    }),
    [
      repoPath,
      ingestStatus,
      messages,
      appendMessage,
      updateLastAssistant,
      editor,
      openEditor,
      isAsking,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppStore(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppStore must be used within AppProvider");
  }
  return ctx;
}
