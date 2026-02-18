"use client";

import { useState, useEffect } from "react";
import { getDashboard, getQueryAnalytics, getModels, resolveAlert } from "@/lib/api";

export default function DashboardPage() {
    const [dashboard, setDashboard] = useState<any>(null);
    const [analytics, setAnalytics] = useState<any>(null);
    const [models, setModels] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const [dash, anal, mdls] = await Promise.all([
                getDashboard().catch(() => null),
                getQueryAnalytics().catch(() => null),
                getModels().catch(() => null),
            ]);
            setDashboard(dash);
            setAnalytics(anal);
            setModels(mdls);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleResolveAlert = async (id: number) => {
        await resolveAlert(id);
        loadData();
    };

    const metrics = dashboard?.metrics || {};
    const system = metrics.system || {};
    const queryStats = dashboard?.query_stats || {};
    const ingestionStats = dashboard?.ingestion_stats || {};
    const cache = metrics.cache || {};
    const cost = metrics.cost || {};

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>
                        📊 <span className="gradient-text">Ops Dashboard</span>
                    </h1>
                    <p style={{ color: "var(--text-muted)" }}>MLOps • LLMOps • AIOps — Live Monitoring</p>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div className="pulse-live" />
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Auto-refreshing every 30s</span>
                </div>
            </div>

            {loading ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                        <div key={i} className="skeleton" style={{ height: 100 }} />
                    ))}
                </div>
            ) : (
                <>
                    {/* Stat Cards Row 1: System */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                        <div className="stat-card">
                            <div className="stat-value gradient-text">{queryStats.total_queries || 0}</div>
                            <div className="stat-label">Queries (24h)</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--success)" }}>
                                {queryStats.avg_latency_ms?.toFixed(0) || 0}ms
                            </div>
                            <div className="stat-label">Avg Latency</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--warning)" }}>
                                ${queryStats.total_cost_usd?.toFixed(4) || "0.00"}
                            </div>
                            <div className="stat-label">Total Cost (24h)</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--info)" }}>
                                {(cache.hit_rate * 100)?.toFixed(0) || 0}%
                            </div>
                            <div className="stat-label">Cache Hit Rate</div>
                        </div>
                    </div>

                    {/* Stat Cards Row 2: System Health */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 24 }}>
                        <div className="stat-card">
                            <div className="stat-value">{system.cpu_percent || 0}%</div>
                            <div className="stat-label">CPU Usage</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{system.memory_used_mb || 0} MB</div>
                            <div className="stat-label">Memory</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value gradient-text">
                                {metrics.vector_store?.total_vectors || 0}
                            </div>
                            <div className="stat-label">Vectors Indexed</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--success)" }}>
                                {ingestionStats.total_new_papers || 0}
                            </div>
                            <div className="stat-label">Papers (7d)</div>
                        </div>
                    </div>

                    {/* Two Column Layout */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
                        {/* Alerts */}
                        <div className="glass-card">
                            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>🚨 Active Alerts</h3>
                            {dashboard?.alerts?.length > 0 ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                    {dashboard.alerts.map((a: any) => (
                                        <div
                                            key={a.id}
                                            style={{
                                                display: "flex",
                                                justifyContent: "space-between",
                                                alignItems: "center",
                                                padding: "10px 14px",
                                                background: "var(--bg-secondary)",
                                                borderRadius: 10,
                                                borderLeft: `3px solid ${a.severity === "critical" ? "var(--danger)" : a.severity === "warning" ? "var(--warning)" : "var(--info)"
                                                    }`,
                                            }}
                                        >
                                            <div>
                                                <p style={{ fontSize: 13, fontWeight: 600 }}>{a.name}</p>
                                                <p style={{ fontSize: 12, color: "var(--text-muted)" }}>{a.message}</p>
                                            </div>
                                            {!a.resolved && (
                                                <button
                                                    onClick={() => handleResolveAlert(a.id)}
                                                    style={{
                                                        background: "none",
                                                        border: "1px solid var(--border-color)",
                                                        borderRadius: 6,
                                                        padding: "4px 10px",
                                                        color: "var(--text-muted)",
                                                        cursor: "pointer",
                                                        fontSize: 12,
                                                    }}
                                                >
                                                    Resolve
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ color: "var(--text-muted)", fontSize: 13 }}>✅ No active alerts</p>
                            )}
                        </div>

                        {/* Cost Breakdown */}
                        <div className="glass-card">
                            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>💰 LLM Cost Breakdown</h3>
                            <div style={{ marginBottom: 12 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                    <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Hourly Spend</span>
                                    <span
                                        style={{
                                            fontWeight: 600,
                                            color: cost.over_budget ? "var(--danger)" : "var(--success)",
                                        }}
                                    >
                                        ${cost.hourly_spend_usd?.toFixed(4) || "0.00"} / ${cost.hourly_limit_usd || 5}
                                    </span>
                                </div>
                                <div
                                    style={{
                                        height: 6,
                                        background: "var(--bg-secondary)",
                                        borderRadius: 3,
                                        overflow: "hidden",
                                    }}
                                >
                                    <div
                                        style={{
                                            height: "100%",
                                            width: `${Math.min(cost.utilization_pct || 0, 100)}%`,
                                            background: cost.over_budget
                                                ? "var(--danger)"
                                                : `linear-gradient(90deg, var(--success), var(--accent-primary))`,
                                            borderRadius: 3,
                                            transition: "width 0.3s ease",
                                        }}
                                    />
                                </div>
                            </div>
                            {analytics?.cost_by_model?.map((m: any) => (
                                <div
                                    key={m.model}
                                    style={{
                                        display: "flex",
                                        justifyContent: "space-between",
                                        padding: "8px 0",
                                        borderBottom: "1px solid var(--border-color)",
                                        fontSize: 13,
                                    }}
                                >
                                    <span style={{ color: "var(--text-secondary)" }}>{m.model}</span>
                                    <span>
                                        {m.count} calls • ${m.total_cost?.toFixed(4)}
                                    </span>
                                </div>
                            ))}
                            {(!analytics?.cost_by_model || analytics.cost_by_model.length === 0) && (
                                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No LLM usage yet</p>
                            )}
                        </div>
                    </div>

                    {/* Model Registry */}
                    <div className="glass-card" style={{ marginBottom: 24 }}>
                        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>🏗️ Model Registry</h3>
                        {models?.models?.length > 0 ? (
                            <table style={{ width: "100%", fontSize: 13 }}>
                                <thead>
                                    <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                                        <th style={{ textAlign: "left", padding: 10, color: "var(--text-muted)" }}>Model</th>
                                        <th style={{ textAlign: "left", padding: 10, color: "var(--text-muted)" }}>Version</th>
                                        <th style={{ textAlign: "left", padding: 10, color: "var(--text-muted)" }}>Type</th>
                                        <th style={{ textAlign: "left", padding: 10, color: "var(--text-muted)" }}>Status</th>
                                        <th style={{ textAlign: "left", padding: 10, color: "var(--text-muted)" }}>Registered</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {models.models.map((m: any) => (
                                        <tr key={m.id} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                            <td style={{ padding: 10, fontWeight: 600 }}>{m.name}</td>
                                            <td style={{ padding: 10 }}>{m.version}</td>
                                            <td style={{ padding: 10 }}>
                                                <span className="badge badge-primary">{m.model_type}</span>
                                            </td>
                                            <td style={{ padding: 10 }}>
                                                <span className={`badge ${m.is_active ? "badge-success" : "badge-warning"}`}>
                                                    {m.is_active ? "Active" : "Archived"}
                                                </span>
                                            </td>
                                            <td style={{ padding: 10, color: "var(--text-muted)" }}>
                                                {new Date(m.registered_at).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No models registered yet</p>
                        )}
                    </div>

                    {/* Faithfulness + Ingestion Stats */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                        <div className="glass-card">
                            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>🛡️ Quality Metrics</h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Avg Faithfulness</span>
                                    <span style={{ fontWeight: 600, color: "var(--success)" }}>
                                        {(queryStats.avg_faithfulness * 100)?.toFixed(0) || "N/A"}%
                                    </span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Cache Size</span>
                                    <span>{cache.size || 0} / {cache.max_size || 500}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Cache Threshold</span>
                                    <span>{cache.threshold || 0.95}</span>
                                </div>
                            </div>
                        </div>

                        <div className="glass-card">
                            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>📥 Ingestion Stats (7d)</h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Pipeline Runs</span>
                                    <span style={{ fontWeight: 600 }}>{ingestionStats.total_runs || 0}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>New Papers</span>
                                    <span style={{ fontWeight: 600, color: "var(--success)" }}>{ingestionStats.total_new_papers || 0}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Duplicates Filtered</span>
                                    <span>{ingestionStats.total_duplicates || 0}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Avg Duration</span>
                                    <span>{ingestionStats.avg_duration_seconds?.toFixed(1) || 0}s</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
