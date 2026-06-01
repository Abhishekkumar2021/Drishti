"use client";

import { useEffect, useRef, useState } from "react";
import Editor, { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { X, FileCode, Copy, Check, Code2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/storage";

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
      rules: [
        { token: "comment", foreground: "525252", fontStyle: "italic" },
        { token: "keyword", foreground: "c792ea" },
        { token: "string", foreground: "c3e88d" },
        { token: "number", foreground: "f78c6c" },
        { token: "type", foreground: "82aaff" },
        { token: "function", foreground: "82aaff" },
        { token: "variable", foreground: "a1a1a1" },
      ],
      colors: {
        "editor.background": "#0f0f0f",
        "editor.foreground": "#a1a1a1",
        "editor.lineHighlightBackground": "#1a1a1a",
        "editor.selectionBackground": "#6366f130",
        "editorLineNumber.foreground": "#525252",
        "editorLineNumber.activeForeground": "#717171",
        "editorCursor.foreground": "#ffffff",
        "editor.inactiveSelectionBackground": "#6366f115",
        "editorIndentGuide.background": "#1a1a1a",
        "editorIndentGuide.activeBackground": "#2a2a2a",
        "editorWidget.background": "#141414",
        "editorWidget.border": "#2a2a2a",
        "scrollbarSlider.background": "#2a2a2a80",
        "scrollbarSlider.hoverBackground": "#333333",
        "scrollbarSlider.activeBackground": "#3a3a3a",
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
    return null;
  }

  const fileName = editorState.filePath.split("/").pop();

  return (
    <div className="flex h-full w-full flex-col border-l border-surface-border bg-bg">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-surface-border h-14 px-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface border border-surface-border">
            <FileCode className="h-4 w-4 text-accent" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{fileName}</p>
            <p className="text-2xs text-text-muted truncate">{editorState.filePath}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon-sm" onClick={handleCopy}>
            {copied ? (
              <Check className="h-4 w-4 text-success" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button variant="ghost" size="icon-sm" onClick={() => setEditor(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Info Bar */}
      <div className="flex items-center gap-2 border-b border-surface-border bg-surface/30 px-4 py-2">
        <Badge variant="accent">
          L{editorState.highlightStart}-{editorState.highlightEnd}
        </Badge>
        <Badge variant="default" className="uppercase">
          {editorState.language}
        </Badge>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <Editor
          height="100%"
          language={editorState.language}
          value={editorState.content}
          onMount={handleEditorMount}
          loading={
            <div className="flex h-full items-center justify-center bg-bg">
              <div className="flex gap-1">
                <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" />
                <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 rounded-full bg-text-muted animate-pulse" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          }
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            fontFamily: "var(--font-mono), 'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: true,
            lineNumbers: "on",
            renderLineHighlight: "all",
            scrollbar: {
              vertical: "auto",
              horizontal: "auto",
              verticalScrollbarSize: 6,
              horizontalScrollbarSize: 6,
              useShadows: false,
            },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            overviewRulerBorder: false,
            guides: {
              indentation: true,
              highlightActiveIndentation: true,
            },
            padding: { top: 12, bottom: 12 },
            smoothScrolling: true,
            cursorBlinking: "smooth",
          }}
        />
      </div>

      <style jsx global>{`
        .highlighted-line {
          background-color: rgba(99, 102, 241, 0.1) !important;
          border-left: 2px solid #6366f1 !important;
        }
        .highlighted-glyph {
          background-color: #6366f1;
          width: 2px !important;
          margin-left: 3px;
        }
        .monaco-editor .margin {
          background: transparent !important;
        }
      `}</style>
    </div>
  );
}
