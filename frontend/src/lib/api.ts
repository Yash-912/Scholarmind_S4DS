/**
 * ScholarMind API Client — Typed client for all backend endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            "X-User": "default",
            ...options?.headers,
        },
        ...options,
    });

    if (!res.ok) {
        throw new Error(`API error: ${res.status} ${res.statusText}`);
    }

    return res.json();
}

// === Papers ===
export async function getPapers(params?: { skip?: number; limit?: number; source?: string }) {
    const query = new URLSearchParams();
    if (params?.skip) query.set("skip", String(params.skip));
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.source) query.set("source", params.source);
    return apiFetch<any>(`/api/papers?${query}`);
}

export async function searchPapersTitle(q: string, limit = 20) {
    return apiFetch<any>(`/api/papers/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export async function getPaper(id: number) {
    return apiFetch<any>(`/api/papers/${id}`);
}

export async function getPaperNovelty(id: number) {
    return apiFetch<any>(`/api/papers/${id}/novelty`);
}

// === Search ===
export async function semanticSearch(q: string, topK = 20, useReranker = true) {
    return apiFetch<any>(`/api/search?q=${encodeURIComponent(q)}&top_k=${topK}&use_reranker=${useReranker}`);
}

// === Synthesis ===
export async function synthesize(body: {
    query: string;
    query_type?: string;
    model?: string;
    top_k?: number;
    use_cache?: boolean;
    check_hallucination?: boolean;
}) {
    return apiFetch<any>("/api/synthesis", {
        method: "POST",
        body: JSON.stringify(body),
    });
}

export function synthesizeStream(body: { query: string }) {
    const url = `${API_BASE}/api/synthesis/stream`;
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

export async function getPrompts() {
    return apiFetch<any>("/api/synthesis/prompts");
}

export async function getAvailableModels() {
    return apiFetch<any>("/api/synthesis/models");
}

export async function getCacheStats() {
    return apiFetch<any>("/api/synthesis/cache/stats");
}

// === Topics ===
export async function getTopics(limit = 50) {
    return apiFetch<any>(`/api/topics?limit=${limit}`);
}

export async function getTrendingTopics(limit = 10) {
    return apiFetch<any>(`/api/topics/trending?limit=${limit}`);
}

export async function getTopicPapers(topicId: number, limit = 20) {
    return apiFetch<any>(`/api/topics/${topicId}/papers?limit=${limit}`);
}

// === Feed ===
export async function getFeed() {
    return apiFetch<any>("/api/feed");
}

export async function updateInterests(interests: string[]) {
    return apiFetch<any>("/api/feed/interests", {
        method: "POST",
        body: JSON.stringify({ interests }),
    });
}

export async function addBookmark(paperId: number) {
    return apiFetch<any>(`/api/feed/bookmark/${paperId}`, { method: "POST" });
}

export async function removeBookmark(paperId: number) {
    return apiFetch<any>(`/api/feed/bookmark/${paperId}`, { method: "DELETE" });
}

export async function getBookmarks() {
    return apiFetch<any>("/api/feed/bookmarks");
}

// === Ingestion ===
export async function triggerIngestion(body?: { sources?: string[]; max_arxiv?: number; max_pubmed?: number }) {
    return apiFetch<any>("/api/ingestion/run", {
        method: "POST",
        body: JSON.stringify(body || {}),
    });
}

export async function getIngestionStatus() {
    return apiFetch<any>("/api/ingestion/status");
}

// === MLOps ===
export async function getModels() {
    return apiFetch<any>("/api/mlops/models");
}

export async function getDrift() {
    return apiFetch<any>("/api/mlops/drift");
}

export async function getQueryAnalytics() {
    return apiFetch<any>("/api/mlops/query-analytics");
}

export async function getPromptAnalytics(promptName = "synthesis") {
    return apiFetch<any>(`/api/mlops/prompt-analytics?prompt_name=${promptName}`);
}

// === AIOps ===
export async function getDashboard() {
    return apiFetch<any>("/api/aiops/dashboard");
}

export async function getHealth() {
    return apiFetch<any>("/api/aiops/health");
}

export async function getAlerts(limit = 20) {
    return apiFetch<any>(`/api/aiops/alerts?limit=${limit}`);
}

export async function resolveAlert(alertId: number) {
    return apiFetch<any>(`/api/aiops/alerts/${alertId}/resolve`, { method: "POST" });
}

export async function getLatencyStats() {
    return apiFetch<any>("/api/aiops/latency");
}
