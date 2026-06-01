"use client";

import { useState, useEffect } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatArea } from "@/components/layout/ChatArea";
import { CodeViewer } from "@/components/layout/CodeViewer";
import { useAppStore } from "@/lib/storage";
import { cn } from "@/lib/cn";

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);
  const { editor: editorState } = useAppStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <main className="flex h-screen overflow-hidden bg-bg">
        <div className="w-72 bg-bg-secondary border-r border-surface-border shrink-0" />
        <div className="flex-1" />
      </main>
    );
  }

  return (
    <main className="flex h-screen overflow-hidden bg-bg">
      <AppSidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      <Group
        orientation="horizontal"
        className="flex-1"
        id="main-layout"
      >
        <Panel
          id="chat-panel"
          defaultSize={editorState ? 60 : 100}
          minSize={40}
        >
          <ChatArea />
        </Panel>

        {editorState && (
          <>
            <ResizeHandle />
            <Panel
              id="code-panel"
              defaultSize={40}
              minSize={25}
              maxSize={60}
            >
              <CodeViewer />
            </Panel>
          </>
        )}
      </Group>
    </main>
  );
}

function ResizeHandle() {
  return (
    <Separator
      className={cn(
        "group relative flex items-center justify-center w-1.5",
        "bg-transparent hover:bg-accent/20 active:bg-accent/30",
        "transition-all duration-150 cursor-col-resize"
      )}
    >
      <div
        className={cn(
          "h-12 w-1 rounded-full",
          "bg-surface-border group-hover:bg-accent group-active:bg-accent",
          "transition-all duration-150"
        )}
      />
    </Separator>
  );
}
