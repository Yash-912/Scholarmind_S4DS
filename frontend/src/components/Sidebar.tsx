"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
    { href: "/", icon: "🏠", label: "Home" },
    { href: "/search", icon: "🔍", label: "Search" },
    { href: "/chat", icon: "💬", label: "Chat & Synthesis" },
    { href: "/feed", icon: "📰", label: "My Feed" },
    { href: "/topics", icon: "🗂️", label: "Topics" },
    { href: "/papers", icon: "📄", label: "Papers" },
    { href: "/dashboard", icon: "📊", label: "Ops Dashboard" },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <nav className="sidebar">
            <div style={{ marginBottom: 32 }}>
                <h1 className="gradient-text" style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
                    ScholarMind
                </h1>
                <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Research Discovery Engine</p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {navItems.map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`sidebar-link ${pathname === item.href ? "active" : ""}`}
                    >
                        <span style={{ fontSize: 18 }}>{item.icon}</span>
                        {item.label}
                    </Link>
                ))}
            </div>

            <div style={{ marginTop: "auto", padding: "16px 0", borderTop: "1px solid var(--border-color)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div className="pulse-live" />
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Backend Connected</span>
                </div>
            </div>
        </nav>
    );
}
