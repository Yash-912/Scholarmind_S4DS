"use client";

import { useState, useEffect } from "react";
import { getFeed, updateInterests, addBookmark } from "@/lib/api";

export default function FeedPage() {
    const [feed, setFeed] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [interests, setInterests] = useState<string[]>([]);
    const [newInterest, setNewInterest] = useState("");

    useEffect(() => {
        loadFeed();
    }, []);

    const loadFeed = async () => {
        setLoading(true);
        try {
            const data = await getFeed();
            setFeed(data);
            setInterests(data.interests || []);
        } catch (err) {
            console.error("Feed load failed:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleAddInterest = async () => {
        if (!newInterest.trim()) return;
        const updated = [...interests, newInterest.trim()];
        setInterests(updated);
        setNewInterest("");
        await updateInterests(updated);
        loadFeed();
    };

    const handleRemoveInterest = async (idx: number) => {
        const updated = interests.filter((_, i) => i !== idx);
        setInterests(updated);
        await updateInterests(updated);
        loadFeed();
    };

    const handleBookmark = async (paperId: number) => {
        await addBookmark(paperId);
        alert("Paper bookmarked!");
    };

    return (
        <div>
            <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8 }}>
                📰 <span className="gradient-text">My Feed</span>
            </h1>
            <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
                Personalized recommendations based on your research interests
            </p>

            {/* Interests */}
            <div className="glass-card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>🎯 Your Interests</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
                    {interests.map((int, i) => (
                        <span
                            key={i}
                            className="badge badge-primary"
                            style={{ cursor: "pointer", fontSize: 13, padding: "6px 14px" }}
                            onClick={() => handleRemoveInterest(i)}
                            title="Click to remove"
                        >
                            {int} ×
                        </span>
                    ))}
                    {interests.length === 0 && (
                        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>No interests set. Add some below!</span>
                    )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <input
                        className="search-input"
                        placeholder="Add an interest (e.g., 'graph neural networks')"
                        value={newInterest}
                        onChange={(e) => setNewInterest(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleAddInterest()}
                        style={{ flex: 1 }}
                    />
                    <button className="glow-btn" onClick={handleAddInterest}>
                        Add
                    </button>
                </div>
            </div>

            {/* Feed */}
            {loading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 100, width: "100%" }} />
                    ))}
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {feed?.feed?.map((paper: any, i: number) => (
                        <div key={i} className="glass-card" style={{ padding: 20 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                <div style={{ flex: 1 }}>
                                    <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>{paper.title}</h3>
                                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                        <span className="badge badge-success">
                                            Relevance: {(paper.relevance_score * 100).toFixed(0)}%
                                        </span>
                                        {paper.source && <span className="badge badge-info">{paper.source}</span>}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleBookmark(Number(paper.paper_id))}
                                    style={{
                                        background: "none",
                                        border: "1px solid var(--border-color)",
                                        borderRadius: 8,
                                        padding: "6px 12px",
                                        color: "var(--text-secondary)",
                                        cursor: "pointer",
                                        fontSize: 13,
                                    }}
                                >
                                    🔖 Save
                                </button>
                            </div>
                        </div>
                    ))}
                    {(!feed?.feed || feed.feed.length === 0) && (
                        <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                            <p>No recommendations yet. Add interests and ingest some papers first!</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
