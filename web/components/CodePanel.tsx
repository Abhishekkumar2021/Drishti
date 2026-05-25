"use client";

import dynamic from "next/dynamic";
import type { editor as MonacoEditorType } from "monaco-editor";
import { useEffect, useRef } from "react";

import { useAppStore } from "@/lib/store";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export function CodePanel() {
  const { editor } = useAppStore();
  const editorRef = useRef<MonacoEditorType.IStandaloneCodeEditor | null>(null);

  useEffect(() => {
    if (!editor || !editorRef.current) return;
    const start = editor.highlightStart;
    const end = editor.highlightEnd;
    editorRef.current.deltaDecorations(
      [],
      [
        {
          range: {
            startLineNumber: start,
            startColumn: 1,
            endLineNumber: end,
            endColumn: 1,
          },
          options: {
            isWholeLine: true,
            className: "drishti-line-highlight",
          },
        },
      ],
    );
    editorRef.current.revealLineInCenter(start);
  }, [editor]);

  return (
    <aside className="flex w-[42%] shrink-0 flex-col border-l border-surface-border bg-surface-raised">
      <header className="border-b border-surface-border px-4 py-3">
        <h2 className="text-sm font-medium text-slate-200">Source</h2>
        <p className="truncate font-mono text-xs text-slate-500">
          {editor?.filePath ?? "Click a citation to open a file"}
        </p>
      </header>
      <div className="relative min-h-0 flex-1">
        {editor ? (
          <MonacoEditor
            height="100%"
            language={editor.language}
            value={editor.content}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              scrollBeyondLastLine: false,
              lineNumbers: "on",
            }}
            onMount={(instance) => {
              editorRef.current = instance;
              instance.revealLineInCenter(editor.highlightStart);
            }}
          />
        ) : (
          <div className="flex h-full items-center justify-center p-6 text-center text-sm text-slate-500">
            Citations in answers link here. Select a file to view highlighted lines.
          </div>
        )}
      </div>
      <style jsx global>{`
        .drishti-line-highlight {
          background: rgba(99, 102, 241, 0.25);
        }
      `}</style>
    </aside>
  );
}
