"use client";

import { Component, type ReactNode } from "react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: any) {
        console.error("ErrorBoundary caught:", error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                this.props.fallback || (
                    <div
                        style={{
                            padding: "2rem",
                            textAlign: "center",
                            background: "var(--glass-bg)",
                            border: "1px solid rgba(248, 113, 113, 0.3)",
                            borderRadius: 12,
                            margin: "1rem",
                        }}
                    >
                        <h3 style={{ color: "#f87171", marginBottom: 8 }}>Something went wrong</h3>
                        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>
                            {this.state.error?.message || "An unexpected error occurred."}
                        </p>
                        <button
                            onClick={() => this.setState({ hasError: false, error: null })}
                            style={{
                                marginTop: 12,
                                padding: "8px 20px",
                                background: "var(--gradient-primary)",
                                border: "none",
                                borderRadius: 8,
                                color: "white",
                                cursor: "pointer",
                                fontSize: 14,
                            }}
                        >
                            Try Again
                        </button>
                    </div>
                )
            );
        }
        return this.props.children;
    }
}
