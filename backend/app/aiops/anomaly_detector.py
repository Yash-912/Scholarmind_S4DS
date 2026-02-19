"""
Anomaly Detector — IsolationForest-based anomaly detection on operational metrics.
"""

import numpy as np
from collections import deque
from datetime import datetime, timezone
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest


@dataclass
class Anomaly:
    timestamp: str
    metric_name: str
    value: float
    score: float  # -1 = anomaly, 1 = normal
    severity: str  # "low", "medium", "high"
    message: str


class AnomalyDetector:
    """Detects anomalies in operational metrics using IsolationForest."""

    def __init__(self, window_size: int = 200, contamination: float = 0.05):
        self.window_size = window_size
        self.contamination = contamination
        # {metric_name: deque of (timestamp, value)}
        self._history: dict[str, deque] = {}
        self._models: dict[str, IsolationForest] = {}
        self._anomalies: list[Anomaly] = []

    def record(self, metric_name: str, value: float):
        """Record a metric value and check for anomalies."""
        if metric_name not in self._history:
            self._history[metric_name] = deque(maxlen=self.window_size)

        self._history[metric_name].append(
            (datetime.now(timezone.utc).isoformat(), value)
        )

        # Need at least 30 observations to detect anomalies
        if len(self._history[metric_name]) >= 30:
            anomaly = self._check(metric_name, value)
            if anomaly:
                self._anomalies.append(anomaly)
                return anomaly
        return None

    def _check(self, metric_name: str, current_value: float) -> Anomaly | None:
        """Check if the current value is anomalous."""
        values = np.array([v for _, v in self._history[metric_name]]).reshape(-1, 1)

        # Retrain model periodically (every 50 new observations)
        if (
            metric_name not in self._models
            or len(self._history[metric_name]) % 50 == 0
        ):
            self._models[metric_name] = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=50,
            )
            self._models[metric_name].fit(values)

        model = self._models[metric_name]
        score = model.decision_function([[current_value]])[0]
        prediction = model.predict([[current_value]])[0]

        if prediction == -1:  # Anomaly detected
            # Determine severity based on how far from the mean
            mean = values.mean()
            std = values.std()
            if std > 0:
                z_score = abs(current_value - mean) / std
            else:
                z_score = 0

            if z_score > 3:
                severity = "high"
            elif z_score > 2:
                severity = "medium"
            else:
                severity = "low"

            return Anomaly(
                timestamp=datetime.now(timezone.utc).isoformat(),
                metric_name=metric_name,
                value=current_value,
                score=score,
                severity=severity,
                message=f"Anomalous {metric_name}: {current_value:.2f} (mean={mean:.2f}, z={z_score:.1f}σ)",
            )

        return None

    def get_recent_anomalies(self, limit: int = 20) -> list[dict]:
        """Get recent detected anomalies."""
        return [
            {
                "timestamp": a.timestamp,
                "metric": a.metric_name,
                "value": a.value,
                "severity": a.severity,
                "message": a.message,
            }
            for a in self._anomalies[-limit:]
        ]

    def get_metric_stats(self, metric_name: str) -> dict:
        """Get statistics for a tracked metric."""
        if metric_name not in self._history:
            return {}
        values = [v for _, v in self._history[metric_name]]
        return {
            "count": len(values),
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "latest": values[-1] if values else None,
        }


anomaly_detector = AnomalyDetector()
