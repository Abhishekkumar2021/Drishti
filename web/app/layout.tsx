import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AppProvider } from "@/lib/store";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Drishti — दृष्टि",
  description: "AST-aware RAG for code understanding",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
