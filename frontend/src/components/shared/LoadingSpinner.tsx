export default function LoadingSpinner({ size = 24 }: { size?: number }) {
    return (
        <div
            style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
            }}
        >
            <div
                style={{
                    width: size,
                    height: size,
                    border: "3px solid rgba(167, 139, 250, 0.2)",
                    borderTop: "3px solid #a78bfa",
                    borderRadius: "50%",
                    animation: "spin 0.8s linear infinite",
                }}
            />
            <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
        </div>
    );
}
