import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "ScholarMind — Research Paper Discovery & Synthesis",
  description: "AI-powered research paper discovery, multi-paper synthesis, and smart recommendations with MLOps, LLMOps, and AIOps.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Sidebar />
        <main className="main-content">{children}</main>
      </body>
    </html>
  );
}
