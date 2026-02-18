"use client";

import { useState, useEffect } from "react";
import { getTopics, getTrendingTopics } from "@/lib/api";

export default function TopicsPage() {
    const [topics, setTopics] = useState<any[]>([]);
    const [trending, setTrending] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [topicsData, trendingData] = await Promise.all([
                getTopics().catch(() => ({ topics: [] })),
                getTrendingTopics().catch(() => ({ trending: [] })),
            ]);
            setTopics(topicsData.topics || []);
            setTrending(trendingData.trending || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const trendIcon = (dir: string) => {
        switch (dir) {
            case "rising": return "🔺";
            case "declining": return "🔻";
            default: return "▬";
        }
    };

    return (
        <div>
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
                🗂️ <span className="gradient-text">Research Topics</span>
            </h1>
            <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
                BERTopic-discovered research themes with trend detection
            </p>

            {/* Trending */}
            {trending.length > 0 && (
                <div style={{ marginBottom: 32 }}>
                    <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>🔥 Trending</h2>
                    <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 8 }}>
                        {trending.map((t: any) => (
                            <div
                                key={t.id}
                                className="glass-card"
                                style={{ minWidth: 250, flexShrink: 0 }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                                    <span style={{ fontWeight: 700 }}>{t.name}</span>
                                    <span className="badge badge-success">🔺 Rising</span>
                                </div>
                                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>{t.paper_count} papers</p>
                                <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                                    {t.keywords?.slice(0, 5).map((kw: string, i: number) => (
                                        <span key={i} className="badge badge-primary" style={{ fontSize: 11 }}>
                                            {kw}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* All Topics */}
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>All Topics</h2>
            {loading ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 120 }} />
                    ))}
                </div>
            ) : topics.length > 0 ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                    {topics.map((t: any) => (
                        <div key={t.id} className="glass-card">
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                                <span style={{ fontWeight: 600, fontSize: 15 }}>{t.name}</span>
                                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                                    {trendIcon(t.trend_direction)}
                                </span>
                            </div>
                            <p style={{ fontSize: 24, fontWeight: 800, color: "var(--accent-secondary)", marginBottom: 8 }}>
                                {t.paper_count}
                            </p>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                                {t.keywords?.slice(0, 6).map((kw: string, i: number) => (
                                    <span key={i} className="badge badge-primary" style={{ fontSize: 11 }}>
                                        {kw}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                    <div style={{ fontSize: 50, marginBottom: 16 }}>🗂️</div>
                    <p>No topics discovered yet. Ingest papers first to enable BERTopic clustering.</p>
                </div>
            )}
        </div>
    );
}
