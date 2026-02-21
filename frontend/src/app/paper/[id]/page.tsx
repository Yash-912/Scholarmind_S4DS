"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import type { Paper } from "@/lib/types";

interface RelatedPaper {
    id: number;
    title: string;
    score: number;
    source?: string;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";

export default function PaperDetailPage() {
    const params = useParams();
    const id = params.id;
    const [paper, setPaper] = useState<Paper | null>(null);
    const [related, setRelated] = useState<RelatedPaper[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const [paperRes, relatedRes] = await Promise.all([
                    fetch(`${API}/api/papers/${id}`).then((r) => r.json()),
                    fetch(`${API}/api/papers/${id}/related`).then((r) => r.json()).catch(() => ({ related: [] })),
                ]);
                setPaper(paperRes);
                setRelated(relatedRes.related || []);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        if (id) load();
    }, [id]);

    if (loading)
        return (
            <div style={{ padding: "2rem" }}>
                <div className="skeleton" style={{ height: 40, width: "60%", marginBottom: 16 }} />
                <div className="skeleton" style={{ height: 20, width: "40%", marginBottom: 32 }} />
                <div className="skeleton" style={{ height: 200, marginBottom: 16 }} />
                <div className="skeleton" style={{ height: 200 }} />
            </div>
        );

    if (!paper)
        return (
            <div style={{ padding: "2rem", textAlign: "center" }}>
                <h2 style={{ color: "var(--text-secondary)" }}>Paper not found</h2>
            </div>
        );

    return (
        <div style={{ padding: "1.5rem", maxWidth: 900, margin: "0 auto" }}>
            {/* Header */}
            <div style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                    <span
                        style={{
                            background: "var(--gradient-primary)",
                            color: "white",
                            padding: "4px 12px",
                            borderRadius: 20,
                            fontSize: 12,
                            fontWeight: 600,
                            textTransform: "uppercase",
                        }}
                    >
                        {paper.source || "paper"}
                    </span>
                    {paper.novelty_score > 0.7 && (
                        <span
                            style={{
                                background: "linear-gradient(135deg, #f59e0b, #ef4444)",
                                color: "white",
                                padding: "4px 12px",
                                borderRadius: 20,
                                fontSize: 12,
                                fontWeight: 600,
                            }}
                        >
                            🔥 High Novelty
                        </span>
                    )}
                </div>

                <h1
                    style={{
                        fontSize: "1.75rem",
                        fontWeight: 700,
                        background: "var(--gradient-primary)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                        lineHeight: 1.3,
                        marginBottom: 12,
                    }}
                >
                    {paper.title}
                </h1>

                <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 8 }}>
                    {Array.isArray(paper.authors) ? paper.authors.join(", ") : paper.authors || "Unknown"}
                </p>

                <div style={{ display: "flex", gap: 16, flexWrap: "wrap", fontSize: 13, color: "var(--text-muted)" }}>
                    {paper.published_date && <span>📅 {new Date(paper.published_date).toLocaleDateString()}</span>}
                    {paper.citation_count > 0 && <span>📖 {paper.citation_count} citations</span>}
                    {paper.doi && <span>🔗 DOI: {paper.doi}</span>}
                    {paper.source_id && <span>🆔 {paper.source_id}</span>}
                </div>
            </div>

            {/* Metrics Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: "2rem" }}>
                {[
                    { label: "Novelty", value: ((paper.novelty_score || 0) * 100).toFixed(0) + "%", color: "#f59e0b" },
                    { label: "Citations", value: paper.citation_count || 0, color: "#60a5fa" },
                    { label: "Source", value: paper.source?.toUpperCase() || "N/A", color: "#a78bfa" },
                ].map((m) => (
                    <div
                        key={m.label}
                        style={{
                            background: "var(--glass-bg)",
                            border: "1px solid var(--glass-border)",
                            borderRadius: 12,
                            padding: "14px 16px",
                            textAlign: "center",
                        }}
                    >
                        <div style={{ fontSize: 22, fontWeight: 700, color: m.color }}>{m.value}</div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                            {m.label}
                        </div>
                    </div>
                ))}
            </div>

            {/* Abstract */}
            <div className="glass-card" style={{ padding: "1.5rem", marginBottom: "1.5rem" }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text-primary)" }}>Abstract</h3>
                <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, fontSize: 14 }}>
                    {paper.abstract || "No abstract available."}
                </p>
            </div>

            {/* Categories */}
            {paper.categories && paper.categories.length > 0 && (
                <div className="glass-card" style={{ padding: "1.5rem", marginBottom: "1.5rem" }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text-primary)" }}>Categories</h3>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {paper.categories.map((cat: string) => (
                            <span
                                key={cat}
                                style={{
                                    background: "rgba(167, 139, 250, 0.15)",
                                    color: "#a78bfa",
                                    padding: "4px 12px",
                                    borderRadius: 20,
                                    fontSize: 13,
                                }}
                            >
                                {cat}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Links */}
            <div className="glass-card" style={{ padding: "1.5rem", marginBottom: "1.5rem" }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text-primary)" }}>Links</h3>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    {paper.pdf_url && (
                        <a
                            href={paper.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-glow"
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 6,
                                padding: "8px 20px",
                                fontSize: 14,
                                textDecoration: "none",
                            }}
                        >
                            📄 View PDF
                        </a>
                    )}
                    {paper.doi && (
                        <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 6,
                                padding: "8px 20px",
                                fontSize: 14,
                                color: "var(--text-secondary)",
                                border: "1px solid var(--glass-border)",
                                borderRadius: 8,
                                textDecoration: "none",
                            }}
                        >
                            🔗 DOI Link
                        </a>
                    )}
                </div>
            </div>

            {/* Related Papers */}
            {related.length > 0 && (
                <div className="glass-card" style={{ padding: "1.5rem" }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "var(--text-primary)" }}>Related Papers</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {related.map((r: RelatedPaper, idx: number) => (
                            <a
                                key={idx}
                                href={`/paper/${r.id}`}
                                style={{
                                    display: "block",
                                    padding: 12,
                                    borderRadius: 8,
                                    border: "1px solid var(--glass-border)",
                                    textDecoration: "none",
                                    transition: "background 0.2s",
                                }}
                                onMouseOver={(e) =>
                                    ((e.currentTarget as HTMLElement).style.background = "rgba(167, 139, 250, 0.08)")
                                }
                                onMouseOut={(e) =>
                                    ((e.currentTarget as HTMLElement).style.background = "transparent")
                                }
                            >
                                <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)", marginBottom: 4 }}>
                                    {r.title}
                                </div>
                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                    Score: {(r.score * 100).toFixed(0)}% · {r.source || "paper"}
                                </div>
                            </a>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
