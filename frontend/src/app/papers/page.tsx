"use client";

import { useState, useEffect } from "react";
import { getPapers, triggerIngestion } from "@/lib/api";
import type { Paper } from "@/lib/types";

export default function PapersPage() {
    const [papers, setPapers] = useState<{ papers: Paper[]; total: number } | null>(null);
    const [loading, setLoading] = useState(true);
    const [ingesting, setIngesting] = useState(false);
    const [page, setPage] = useState(0);

    const loadPapers = async () => {
        setLoading(true);
        try {
            const data = await getPapers({ skip: page * 20, limit: 20 });
            setPapers(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPapers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page]);

    const handleIngest = async () => {
        setIngesting(true);
        try {
            await triggerIngestion({ max_arxiv: 30, max_pubmed: 20 });
            alert("Ingestion started in background! Papers will appear in ~2 minutes.");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            alert("Ingestion failed: " + message);
        } finally {
            setIngesting(false);
        }
    };

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>
                        📄 <span className="gradient-text">Papers</span>
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        {papers?.total || 0} papers indexed
                    </p>
                </div>
                <button className="glow-btn" onClick={handleIngest} disabled={ingesting}>
                    {ingesting ? "⏳ Ingesting..." : "🔄 Ingest New Papers"}
                </button>
            </div>

            {loading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 100 }} />
                    ))}
                </div>
            ) : (
                <>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {papers?.papers?.map((p: Paper) => (
                            <div key={p.id} className="glass-card" style={{ padding: 20 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                                    <h3 style={{ fontSize: 15, fontWeight: 600, flex: 1, marginRight: 12 }}>{p.title}</h3>
                                    {(p.novelty_score ?? 0) > 0 && (
                                        <span
                                            className={`badge ${(p.novelty_score ?? 0) > 0.7 ? "badge-danger" : (p.novelty_score ?? 0) > 0.4 ? "badge-warning" : "badge-info"
                                                }`}
                                        >
                                            Novelty: {((p.novelty_score ?? 0) * 100).toFixed(0)}%
                                        </span>
                                    )}
                                </div>
                                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 8 }}>
                                    {p.abstract}
                                </p>
                                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                                    <span className="badge badge-info">{p.source}</span>
                                    {p.published_date && (
                                        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                            📅 {new Date(p.published_date).toLocaleDateString()}
                                        </span>
                                    )}
                                    {(p.citation_count ?? 0) > 0 && (
                                        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                            📌 {p.citation_count} citations
                                        </span>
                                    )}
                                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                        ✍️ {p.authors?.slice(0, 3).join(", ")}{(p.authors?.length ?? 0) > 3 ? "..." : ""}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 24 }}>
                        <button
                            className="glow-btn"
                            disabled={page === 0}
                            onClick={() => setPage((p) => Math.max(0, p - 1))}
                            style={{ padding: "8px 20px", fontSize: 13 }}
                        >
                            ← Previous
                        </button>
                        <span style={{ display: "flex", alignItems: "center", color: "var(--text-muted)" }}>
                            Page {page + 1}
                        </span>
                        <button
                            className="glow-btn"
                            disabled={(papers?.papers?.length || 0) < 20}
                            onClick={() => setPage((p) => p + 1)}
                            style={{ padding: "8px 20px", fontSize: 13 }}
                        >
                            Next →
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
