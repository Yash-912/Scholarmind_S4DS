"use client";

import { useState } from "react";
import { semanticSearch } from "@/lib/api";

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError("");
        try {
            const data = await semanticSearch(query);
            setResults(data);
        } catch (err: any) {
            setError(err.message || "Search failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
                🔍 <span className="gradient-text">Semantic Search</span>
            </h1>
            <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
                Hybrid dense + sparse retrieval with cross-encoder re-ranking
            </p>

            <form onSubmit={handleSearch} style={{ display: "flex", gap: 12, marginBottom: 32 }}>
                <input
                    className="search-input"
                    placeholder="Search for papers... (e.g., 'federated learning privacy')"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                />
                <button type="submit" className="glow-btn" disabled={loading} style={{ whiteSpace: "nowrap" }}>
                    {loading ? "Searching..." : "Search"}
                </button>
            </form>

            {error && (
                <div className="glass-card" style={{ borderColor: "var(--danger)", marginBottom: 20 }}>
                    <p style={{ color: "var(--danger)" }}>❌ {error}</p>
                </div>
            )}

            {results && (
                <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                        <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                            {results.count} results for &ldquo;{results.query}&rdquo;
                        </span>
                        {results.reranked && <span className="badge badge-primary">Re-ranked</span>}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {results.results?.map((paper: any, i: number) => (
                            <div key={i} className="glass-card" style={{ padding: 20 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                                    <h3 style={{ fontSize: 16, fontWeight: 600, flex: 1, marginRight: 12 }}>{paper.title}</h3>
                                    <span className="badge badge-primary" style={{ flexShrink: 0 }}>
                                        {(paper.score * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 8 }}>
                                    {paper.snippet}
                                </p>
                                <div style={{ display: "flex", gap: 8 }}>
                                    {paper.source && <span className="badge badge-info">{paper.source}</span>}
                                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>ID: {paper.paper_id}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!results && !loading && (
                <div style={{ textAlign: "center", padding: 60, color: "var(--text-muted)" }}>
                    <div style={{ fontSize: 60, marginBottom: 16 }}>🔬</div>
                    <p>Enter a research query to search across indexed papers</p>
                    <p style={{ fontSize: 13, marginTop: 8 }}>Uses SPECTER2 embeddings + BM25 + Reciprocal Rank Fusion</p>
                </div>
            )}
        </div>
    );
}
