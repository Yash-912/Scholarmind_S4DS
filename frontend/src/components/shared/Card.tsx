interface CardProps {
    children: React.ReactNode;
    title?: string;
    icon?: string;
    className?: string;
    style?: React.CSSProperties;
    onClick?: () => void;
}

export default function Card({ children, title, icon, className, style, onClick }: CardProps) {
    return (
        <div
            className={`glass-card ${className || ""}`}
            onClick={onClick}
            style={{
                padding: "1.25rem",
                cursor: onClick ? "pointer" : undefined,
                transition: "transform 0.2s, box-shadow 0.2s",
                ...style,
            }}
            onMouseOver={(e) => {
                if (onClick) {
                    (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
                    (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 30px rgba(167, 139, 250, 0.15)";
                }
            }}
            onMouseOut={(e) => {
                if (onClick) {
                    (e.currentTarget as HTMLElement).style.transform = "";
                    (e.currentTarget as HTMLElement).style.boxShadow = "";
                }
            }}
        >
            {title && (
                <div
                    style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        marginBottom: 12,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                    }}
                >
                    {icon && <span>{icon}</span>}
                    {title}
                </div>
            )}
            {children}
        </div>
    );
}
