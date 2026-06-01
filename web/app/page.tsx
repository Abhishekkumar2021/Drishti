"use client";

import { useState } from "react";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatArea } from "@/components/layout/ChatArea";
import { CodeViewer } from "@/components/layout/CodeViewer";

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <main className="flex h-screen overflow-hidden bg-bg">
      <AppSidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <ChatArea />
      <CodeViewer />
    </main>
  );
}
