"use client";

import { useEffect, useRef } from "react";
import Editor, { Monaco } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { X, FileCode, Copy, Check, Code2, Maximize2, Minimize2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/storage";
import { cn } from "@/lib/cn";

export function CodeViewer() {
  const { editor: editorState, setEditor } = useAppStore();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

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
        { token: "comment", foreground: "6b7280", fontStyle: "italic" },
        { token: "keyword", foreground: "a78bfa" },
        { token: "string", foreground: "34d399" },
        { token: "number", foreground: "f59e0b" },
        { token: "type", foreground: "60a5fa" },
        { token: "function", foreground: "f472b6" },
      ],
      colors: {
        "editor.background": "#0a0f1a",
        "editor.foreground": "#e2e8f0",
        "editor.lineHighlightBackground": "#1e293b40",
        "editor.selectionBackground": "#8b5cf640",
        "editorLineNumber.foreground": "#475569",
        "editorLineNumber.activeForeground": "#94a3b8",
        "editorCursor.foreground": "#8b5cf6",
        "editor.inactiveSelectionBackground": "#8b5cf620",
        "editorIndentGuide.background": "#1e293b",
        "editorIndentGuide.activeBackground": "#334155",
        "editorWidget.background": "#0f172a",
        "editorWidget.border": "#334155",
        "scrollbarSlider.background": "#47556560",
        "scrollbarSlider.hoverBackground": "#47556580",
        "scrollbarSlider.activeBackground": "#475565a0",
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
      <div className="flex h-full w-[400px] flex-col items-center justify-center border-l border-surface-border/30 bg-background/50 text-center backdrop-blur-sm">
        <div className="relative mb-6">
          <div className="absolute inset-0 rounded-full bg-surface-raised blur-xl" />
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-raised border border-surface-border/30">
            <Code2 className="h-8 w-8 text-text-muted" />
          </div>
        </div>
        <h3 className="text-sm font-semibold text-text-secondary">
          No file selected
        </h3>
        <p className="mt-2 max-w-[220px] text-xs text-text-muted leading-relaxed">
          Click a citation in the chat to view the source code with syntax highlighting.
        </p>
      </div>
    );
  }

  const fileName = editorState.filePath.split("/").pop();
  const lineCount = editorState.highlightEnd - editorState.highlightStart + 1;

  return (
    <div 
      className={cn(
        "flex h-full flex-col border-l border-surface-border/30 bg-background/50 backdrop-blur-sm transition-all duration-300",
        expanded ? "w-[700px]" : "w-[500px]"
      )}
    >
      {/* Header */}
      <header className="flex items-center justify-between border-b border-surface-border/30 px-4 py-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-muted">
            <FileCode className="h-4 w-4 text-accent" />
          </div>
          <div className="min-w-0">
            <span className="block truncate text-sm font-semibold text-text-primary">
              {fileName}
            </span>
            <span className="text-xs text-text-muted truncate block">
              {editorState.filePath}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setExpanded(!expanded)}
            className="text-text-muted hover:text-text-primary"
          >
            {expanded ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={handleCopy}
            className="text-text-muted hover:text-text-primary"
          >
            {copied ? (
              <Check className="h-4 w-4 text-success" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setEditor(null)}
            className="text-text-muted hover:text-text-primary"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Info Bar */}
      <div className="flex items-center gap-3 border-b border-surface-border/30 bg-surface-raised/30 px-4 py-2">
        <Badge variant="default" className="font-mono">
          L{editorState.highlightStart}-{editorState.highlightEnd}
        </Badge>
        <Badge variant="secondary" className="uppercase">
          {editorState.language}
        </Badge>
        <span className="text-xs text-text-muted">
          {lineCount} line{lineCount !== 1 ? "s" : ""} highlighted
        </span>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <Editor
          height="100%"
          language={editorState.language}
          value={editorState.content}
          onMount={handleEditorMount}
          loading={
            <div className="flex h-full items-center justify-center">
              <div className="flex gap-1">
                <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                <div className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          }
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, monospace",
            fontLigatures: true,
            lineNumbers: "on",
            renderLineHighlight: "all",
            scrollbar: {
              vertical: "auto",
              horizontal: "auto",
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
              useShadows: false,
            },
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
            overviewRulerBorder: false,
            guides: {
              indentation: true,
              highlightActiveIndentation: true,
              bracketPairs: true,
            },
            padding: { top: 16, bottom: 16 },
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            bracketPairColorization: {
              enabled: true,
            },
            renderWhitespace: "selection",
          }}
        />
      </div>

      <style jsx global>{`
        .highlighted-line {
          background: linear-gradient(90deg, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%) !important;
          border-left: 3px solid #8b5cf6 !important;
        }
        .highlighted-glyph {
          background: linear-gradient(180deg, #8b5cf6 0%, #7c3aed 100%);
          width: 3px !important;
          margin-left: 3px;
        }
        .monaco-editor .margin {
          background: transparent !important;
        }
        .monaco-editor .monaco-scrollable-element > .scrollbar > .slider {
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}
