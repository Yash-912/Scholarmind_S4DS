export default function Footer() {
    return (
        <footer
            style={{
                padding: "2rem 1.5rem",
                borderTop: "1px solid var(--glass-border)",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: 13,
                marginTop: "auto",
            }}
        >
            <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 12, flexWrap: "wrap" }}>
                <span>🎓 ScholarMind</span>
                <span>·</span>
                <span>MLOps + LLMOps + AIOps</span>
                <span>·</span>
                <span>Built with SPECTER2 · Groq · ChromaDB · BERTopic</span>
            </div>
            <p style={{ opacity: 0.6 }}>
                Research Paper Discovery &amp; Synthesis Engine — © {new Date().getFullYear()}
            </p>
        </footer>
    );
}
