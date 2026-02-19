interface BadgeProps {
    children: React.ReactNode;
    variant?: "primary" | "success" | "warning" | "danger" | "info" | "neutral";
    size?: "sm" | "md";
}

const VARIANT_STYLES: Record<string, { bg: string; color: string }> = {
    primary: { bg: "rgba(167, 139, 250, 0.15)", color: "#a78bfa" },
    success: { bg: "rgba(52, 211, 153, 0.15)", color: "#34d399" },
    warning: { bg: "rgba(251, 191, 36, 0.15)", color: "#fbbf24" },
    danger: { bg: "rgba(248, 113, 113, 0.15)", color: "#f87171" },
    info: { bg: "rgba(96, 165, 250, 0.15)", color: "#60a5fa" },
    neutral: { bg: "rgba(148, 163, 184, 0.15)", color: "#94a3b8" },
};

export default function Badge({ children, variant = "primary", size = "sm" }: BadgeProps) {
    const s = VARIANT_STYLES[variant] || VARIANT_STYLES.primary;
    return (
        <span
            style={{
                display: "inline-flex",
                alignItems: "center",
                padding: size === "sm" ? "2px 10px" : "4px 14px",
                borderRadius: 20,
                fontSize: size === "sm" ? 11 : 13,
                fontWeight: 600,
                background: s.bg,
                color: s.color,
                letterSpacing: "0.02em",
            }}
        >
            {children}
        </span>
    );
}
