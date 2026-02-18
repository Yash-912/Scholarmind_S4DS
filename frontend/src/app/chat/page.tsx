"use client";

import { useState, useRef, useEffect } from "react";
import { synthesize } from "@/lib/api";

interface Message {
    role: "user" | "assistant";
    content: string;
    papers?: any[];
    metrics?: any;
    hallucination_check?: any;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [queryType, setQueryType] = useState<string>("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const result = await synthesize({
                query: input,
                query_type: queryType || undefined,
            });

            const assistantMsg: Message = {
                role: "assistant",
                content: result.answer || "No response generated.",
                papers: result.papers,
                metrics: result.metrics,
                hallucination_check: result.hallucination_check,
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (err: any) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: `❌ Error: ${err.message}` },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const suggestedQueries = [
        "Summarize the latest advances in federated learning for healthcare",
        "Compare transformer and LSTM architectures for NLP",
        "What research gaps exist in AI safety?",
        "How has reinforcement learning evolved since 2020?",
    ];

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)" }}>
            <div style={{ marginBottom: 16 }}>
                <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>
                    💬 <span className="gradient-text">Research Chat</span>
                </h1>
                <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
                    RAG-powered multi-paper synthesis with hallucination checking
                </p>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
                {messages.length === 0 && (
                    <div style={{ textAlign: "center", padding: 40 }}>
                        <div style={{ fontSize: 50, marginBottom: 16 }}>🧠</div>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 15 }}>
                            Ask any research question — I&apos;ll retrieve papers, synthesize insights, and cite sources.
                        </p>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
                            {suggestedQueries.map((q) => (
                                <button
                                    key={q}
                                    onClick={() => setInput(q)}
                                    style={{
                                        background: "var(--bg-card)",
                                        border: "1px solid var(--border-color)",
                                        borderRadius: 10,
                                        padding: "10px 16px",
                                        color: "var(--text-secondary)",
                                        fontSize: 13,
                                        cursor: "pointer",
                                        transition: "all 0.2s",
                                        maxWidth: 300,
                                        textAlign: "left",
                                    }}
                                    onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--accent-primary)")}
                                    onMouseOut={(e) => (e.currentTarget.style.borderColor = "var(--border-color)")}
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        style={{
                            marginBottom: 20,
                            display: "flex",
                            justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                        }}
                    >
                        <div
                            style={{
                                maxWidth: msg.role === "user" ? "70%" : "90%",
                                padding: msg.role === "user" ? "12px 18px" : 0,
                                borderRadius: 14,
                                background: msg.role === "user" ? "var(--accent-primary)" : "transparent",
                            }}
                        >
                            {msg.role === "user" ? (
                                <p style={{ fontSize: 15 }}>{msg.content}</p>
                            ) : (
                                <div>
                                    <div className="glass-card prose" style={{ marginBottom: 12 }}>
                                        <div dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }} />
                                    </div>

                                    {/* Source Papers */}
                                    {msg.papers && msg.papers.length > 0 && (
                                        <div style={{ marginBottom: 12 }}>
                                            <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-muted)", marginBottom: 8 }}>
                                                📚 Source Papers ({msg.papers.length})
                                            </p>
                                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                                                {msg.papers.map((p: any, j: number) => (
                                                    <div
                                                        key={j}
                                                        style={{
                                                            background: "var(--bg-card)",
                                                            border: "1px solid var(--border-color)",
                                                            borderRadius: 8,
                                                            padding: "8px 12px",
                                                            fontSize: 12,
                                                            maxWidth: 300,
                                                        }}
                                                    >
                                                        <span style={{ fontWeight: 600 }}>[{j + 1}]</span>{" "}
                                                        <span style={{ color: "var(--text-secondary)" }}>{p.title?.slice(0, 80)}...</span>
                                                        <div style={{ marginTop: 4 }}>
                                                            <span className="badge badge-info" style={{ fontSize: 10 }}>{p.source}</span>
                                                            <span style={{ marginLeft: 8, color: "var(--text-muted)", fontSize: 11 }}>
                                                                Score: {(p.score * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Metrics */}
                                    {msg.metrics && (
                                        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                                            <span className="badge badge-primary">⏱ {msg.metrics.latency_ms?.toFixed(0)}ms</span>
                                            <span className="badge badge-info">📊 {msg.metrics.papers_reranked} papers</span>
                                            <span className="badge badge-success">💰 ${msg.metrics.cost_usd?.toFixed(4)}</span>
                                            {msg.hallucination_check && (
                                                <span
                                                    className={`badge ${msg.hallucination_check.score > 0.7
                                                            ? "badge-success"
                                                            : msg.hallucination_check.score > 0.4
                                                                ? "badge-warning"
                                                                : "badge-danger"
                                                        }`}
                                                >
                                                    🛡️ Faith: {(msg.hallucination_check.score * 100).toFixed(0)}%
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div style={{ display: "flex", gap: 12, alignItems: "center", padding: 16 }}>
                        <div className="skeleton" style={{ width: 100, height: 16 }} />
                        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Synthesizing across papers...</span>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSend} style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <select
                    value={queryType}
                    onChange={(e) => setQueryType(e.target.value)}
                    style={{
                        background: "var(--bg-secondary)",
                        border: "1px solid var(--border-color)",
                        borderRadius: 10,
                        padding: "12px 14px",
                        color: "var(--text-secondary)",
                        fontSize: 13,
                    }}
                >
                    <option value="">Auto-detect</option>
                    <option value="synthesis">Synthesis</option>
                    <option value="comparison">Comparison</option>
                    <option value="gap_analysis">Gap Analysis</option>
                    <option value="chat">Chat</option>
                </select>
                <input
                    className="search-input"
                    placeholder="Ask a research question..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                />
                <button type="submit" className="glow-btn" disabled={loading || !input.trim()}>
                    {loading ? "⏳" : "Send"}
                </button>
            </form>
        </div>
    );
}

function formatMarkdown(text: string): string {
    return text
        .replace(/## (.*)/g, '<h2>$1</h2>')
        .replace(/### (.*)/g, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\[Paper (\d+)\]/g, '<strong style="color: var(--accent-secondary)">[Paper $1]</strong>')
        .replace(/\n/g, '<br/>');
}
