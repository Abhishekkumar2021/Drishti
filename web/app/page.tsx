import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatArea } from "@/components/layout/ChatArea";
import { CodeViewer } from "@/components/layout/CodeViewer";

export default function HomePage() {
  return (
    <main className="flex h-screen overflow-hidden bg-surface">
      <AppSidebar />
      <ChatArea />
      <CodeViewer />
    </main>
  );
}
