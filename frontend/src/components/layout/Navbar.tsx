"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
    const pathname = usePathname();

    return (
        <nav
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                height: 56,
                background: "rgba(10, 10, 20, 0.85)",
                backdropFilter: "blur(20px)",
                borderBottom: "1px solid rgba(167, 139, 250, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0 1.5rem",
                zIndex: 100,
            }}
        >
            <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 24 }}>🎓</span>
                <span
                    style={{
                        fontSize: 18,
                        fontWeight: 700,
                        background: "var(--gradient-primary)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                    }}
                >
                    ScholarMind
                </span>
            </Link>

            <div style={{ display: "flex", gap: 4 }}>
                {[
                    { href: "/search", label: "Search" },
                    { href: "/chat", label: "Chat" },
                    { href: "/feed", label: "Feed" },
                    { href: "/topics", label: "Topics" },
                    { href: "/dashboard", label: "Dashboard" },
                ].map((item) => (
                    <Link
                        key={item.href}
                        href={item.href}
                        style={{
                            padding: "6px 14px",
                            borderRadius: 8,
                            fontSize: 13,
                            fontWeight: 500,
                            color: pathname === item.href ? "#a78bfa" : "var(--text-muted)",
                            background: pathname === item.href ? "rgba(167, 139, 250, 0.1)" : "transparent",
                            textDecoration: "none",
                            transition: "all 0.2s",
                        }}
                    >
                        {item.label}
                    </Link>
                ))}
            </div>
        </nav>
    );
}
