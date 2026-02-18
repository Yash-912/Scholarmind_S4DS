"use client";

import Link from "next/link";

const features = [
  {
    icon: "🔍",
    title: "Semantic Search",
    desc: "Hybrid dense + sparse retrieval with cross-encoder re-ranking for precise paper discovery.",
    href: "/search",
  },
  {
    icon: "💬",
    title: "Multi-Paper Synthesis",
    desc: "RAG-powered synthesis across papers with hallucination checking and source citations.",
    href: "/chat",
  },
  {
    icon: "📰",
    title: "Personalized Feed",
    desc: "Papers recommended based on your interests using SPECTER2 profile embeddings.",
    href: "/feed",
  },
  {
    icon: "🗂️",
    title: "Topic Discovery",
    desc: "BERTopic clustering reveals research themes with trend detection.",
    href: "/topics",
  },
  {
    icon: "🆕",
    title: "Novelty Detection",
    desc: "Identify genuinely novel papers using embedding distance and cross-domain bridge detection.",
    href: "/papers",
  },
  {
    icon: "📊",
    title: "Ops Dashboard",
    desc: "Full MLOps + LLMOps + AIOps monitoring: drift detection, cost tracking, health alerts.",
    href: "/dashboard",
  },
];

const techStack = [
  { name: "SPECTER2", role: "Embeddings" },
  { name: "ChromaDB", role: "Vector Store" },
  { name: "Groq Mixtral", role: "LLM Inference" },
  { name: "BERTopic", role: "Topic Modeling" },
  { name: "MLflow", role: "Experiment Tracking" },
  { name: "FastAPI", role: "Backend API" },
  { name: "Next.js 15", role: "Frontend" },
  { name: "BM25 + RRF", role: "Hybrid Retrieval" },
];

export default function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="hero-gradient" style={{ padding: "60px 0 40px", textAlign: "center" }}>
        <h1
          className="gradient-text"
          style={{ fontSize: 48, fontWeight: 900, marginBottom: 16, lineHeight: 1.1 }}
        >
          ScholarMind
        </h1>
        <p style={{ fontSize: 20, color: "var(--text-secondary)", maxWidth: 600, margin: "0 auto 8px" }}>
          Research Paper Discovery & Synthesis Engine
        </p>
        <p style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 500, margin: "0 auto 32px" }}>
          Powered by real-time scraping, semantic search, and LLM-powered multi-paper synthesis.
          Built with MLOps, LLMOps, and AIOps from the ground up.
        </p>
        <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
          <Link href="/search" className="glow-btn">
            🔍 Start Searching
          </Link>
          <Link
            href="/chat"
            className="glow-btn"
            style={{
              background: "transparent",
              border: "1px solid var(--accent-primary)",
              boxShadow: "none",
            }}
          >
            💬 Ask a Question
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section style={{ padding: "40px 0" }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Features</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 20 }}>
          {features.map((f) => (
            <Link key={f.title} href={f.href} style={{ textDecoration: "none" }}>
              <div className="glass-card" style={{ height: "100%" }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: "var(--text-primary)" }}>
                  {f.title}
                </h3>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section style={{ padding: "40px 0" }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Tech Stack</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          {techStack.map((t) => (
            <div
              key={t.name}
              className="glass-card"
              style={{ padding: "12px 20px", display: "flex", alignItems: "center", gap: 12 }}
            >
              <span style={{ fontWeight: 700, color: "var(--accent-secondary)" }}>{t.name}</span>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{t.role}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section style={{ padding: "40px 0" }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Architecture</h2>
        <div className="glass-card" style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.8, overflowX: "auto" }}>
          <pre style={{ color: "var(--text-secondary)" }}>{`┌─ Ingestion Layer ─────────────────────────────────────┐
│  arXiv API → PubMed → Semantic Scholar → Dedup → DB   │
└───────────────────────┬───────────────────────────────┘
                        ▼
┌─ Core ML Layer ───────────────────────────────────────┐
│  SPECTER2 → ChromaDB → BM25+RRF → Cross-Encoder      │
│  BERTopic → Novelty → Relevance Scoring               │
└───────────────────────┬───────────────────────────────┘
                        ▼
┌─ LLMOps Layer ────────────────────────────────────────┐
│  Groq Gateway → Prompt Registry → Semantic Cache      │
│  RAG Synthesizer → Hallucination Checker              │
└───────────────────────┬───────────────────────────────┘
                        ▼
┌─ Ops Layer ───────────────────────────────────────────┐
│  MLflow Registry → PSI Drift Detection                │
│  Health Monitor → Anomaly Detection → Auto-Alerts     │
└───────────────────────────────────────────────────────┘`}</pre>
        </div>
      </section>
    </div>
  );
}
