"use client";

import { useEffect, useRef } from "react";
import Editor, { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { X, FileCode, ExternalLink, Copy, Check } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useAppStore } from "@/lib/storage";
import { cn } from "@/lib/cn";

export function CodeViewer() {
  const { editor: editorState, setEditor } = useAppStore();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (editorRef.current && editorState) {
      const { highlightStart, highlightEnd } = editorState;
      
      editorRef.current.revealLineInCenter(highlightStart);
      
      editorRef.current.setSelection({
        startLineNumber: highlightStart,
        startColumn: 1,
        endLineNumber: highlightEnd,
        endColumn: 1,
      });

      editorRef.current.deltaDecorations(
        [],
        [
          {
            range: {
              startLineNumber: highlightStart,
              startColumn: 1,
              endLineNumber: highlightEnd,
              endColumn: 1,
            },
            options: {
              isWholeLine: true,
              className: "highlighted-line",
              glyphMarginClassName: "highlighted-glyph",
            },
          },
        ]
      );
    }
  }, [editorState]);

  const handleEditorMount = (
    editor: editor.IStandaloneCodeEditor,
    monaco: Monaco
  ) => {
    editorRef.current = editor;
    
    monaco.editor.defineTheme("drishti-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#0f1419",
        "editor.foreground": "#e2e8f0",
        "editor.lineHighlightBackground": "#1a2332",
        "editor.selectionBackground": "#6366f133",
        "editorLineNumber.foreground": "#4a5568",
        "editorLineNumber.activeForeground": "#a0aec0",
      },
    });
    
    monaco.editor.setTheme("drishti-dark");
  };

  const handleCopy = async () => {
    if (!editorState) return;
    await navigator.clipboard.writeText(editorState.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!editorState) {
    return (
      <div className="flex h-full w-96 flex-col items-center justify-center border-l border-surface-border bg-surface text-center">
        <div className="rounded-full bg-surface-raised p-4">
          <FileCode className="h-8 w-8 text-slate-500" />
        </div>
        <h3 className="mt-4 text-sm font-medium text-slate-400">
          No file selected
        </h3>
        <p className="mt-2 max-w-[200px] text-xs text-slate-600">
          Click a citation in the chat to view the source code here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full w-[500px] flex-col border-l border-surface-border bg-surface">
      <header className="flex items-center justify-between border-b border-surface-border px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <FileCode className="h-4 w-4 shrink-0 text-accent" />
          <span className="truncate text-sm font-medium text-slate-200">
            {editorState.filePath}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleCopy}
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-400" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setEditor(null)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <div className="flex items-center gap-2 border-b border-surface-border bg-surface-raised px-4 py-2 text-xs text-slate-500">
        <span>
          Lines {editorState.highlightStart}-{editorState.highlightEnd}
        </span>
        <span>•</span>
        <span className="uppercase">{editorState.language}</span>
      </div>

      <div className="flex-1">
        <Editor
          height="100%"
          language={editorState.language}
          value={editorState.content}
          onMount={handleEditorMount}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineNumbers: "on",
            renderLineHighlight: "all",
            scrollbar: {
              vertical: "auto",
              horizontal: "auto",
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
            },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            overviewRulerBorder: false,
            guides: {
              indentation: true,
              highlightActiveIndentation: true,
            },
            padding: { top: 16 },
          }}
        />
      </div>

      <style jsx global>{`
        .highlighted-line {
          background-color: rgba(99, 102, 241, 0.15) !important;
          border-left: 3px solid #6366f1 !important;
        }
        .highlighted-glyph {
          background-color: #6366f1;
        }
      `}</style>
    </div>
  );
}
