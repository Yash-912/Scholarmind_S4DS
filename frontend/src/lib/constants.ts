// Constants for ScholarMind frontend

export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";

export const ENDPOINTS = {
    papers: "/api/papers",
    search: "/api/search",
    synthesis: "/api/synthesis",
    topics: "/api/topics",
    feed: "/api/feed",
    ingestion: "/api/ingestion",
    mlops: "/api/mlops",
    aiops: "/api/aiops",
    health: "/api/health",
    ops: "/api/ops",
} as const;

export const NAV_ITEMS = [
    { href: "/", label: "Home", icon: "🏠" },
    { href: "/search", label: "Search", icon: "🔍" },
    { href: "/chat", label: "Chat", icon: "💬" },
    { href: "/feed", label: "Feed", icon: "📰" },
    { href: "/topics", label: "Topics", icon: "🗂️" },
    { href: "/papers", label: "Papers", icon: "📄" },
    { href: "/dashboard", label: "Dashboard", icon: "📊" },
] as const;

export const QUERY_TYPES = [
    { value: "", label: "Auto-detect" },
    { value: "synthesis", label: "Synthesis" },
    { value: "comparison", label: "Comparison" },
    { value: "gap_analysis", label: "Gap Analysis" },
    { value: "chat", label: "Chat" },
] as const;

export const THEME = {
    colors: {
        primary: "#a78bfa",
        secondary: "#38bdf8",
        success: "#34d399",
        warning: "#fbbf24",
        danger: "#f87171",
        info: "#60a5fa",
    },
    refreshInterval: 30000, // Dashboard refresh in ms
} as const;
