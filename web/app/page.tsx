import { ChatPanel } from "@/components/ChatPanel";
import { CodePanel } from "@/components/CodePanel";
import { Sidebar } from "@/components/Sidebar";

export default function HomePage() {
  return (
    <main className="flex h-screen overflow-hidden">
      <Sidebar />
      <ChatPanel />
      <CodePanel />
    </main>
  );
}
