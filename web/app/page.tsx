"use client";

import { useState, useEffect } from "react";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatArea } from "@/components/layout/ChatArea";
import { CodeViewer } from "@/components/layout/CodeViewer";

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <main className="flex h-screen overflow-hidden bg-bg">
        <div className="w-72 bg-bg-secondary border-r border-surface-border" />
        <div className="flex-1" />
        <div className="w-[420px] border-l border-surface-border bg-bg" />
      </main>
    );
  }

  return (
    <main className="flex h-screen overflow-hidden bg-bg">
      <AppSidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <ChatArea />
      <CodeViewer />
    </main>
  );
}
