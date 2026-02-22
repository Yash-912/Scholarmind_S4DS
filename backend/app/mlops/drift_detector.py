"""
Drift Detector — Detects data drift and concept drift in the paper stream.
"""

import numpy as np

from app.db.database import async_session
from app.db import crud


class DriftDetector:
    """
    Monitors for:
    1. Data drift — new papers shifting away from training distribution
    2. Concept drift — topic distribution changes over time
    3. Embedding drift — model quality degradation
    """

    def __init__(self):
        self._baseline_mean = None
        self._baseline_std = None
        self._baseline_set = False

    def set_baseline(self, embeddings: np.ndarray):
        """Set baseline embedding statistics for drift comparison."""
        self._baseline_mean = np.mean(embeddings, axis=0)
        self._baseline_std = np.std(embeddings, axis=0)
        # Store actual embeddings for true distribution testing
        np.random.seed(42)
        indices = np.random.choice(len(embeddings), min(300, len(embeddings)), replace=False)
        self._baseline_sample = embeddings[indices]
        self._baseline_set = True
        print(f"✅ Drift baseline set from {len(embeddings)} embeddings")

    def compute_psi(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        buckets: int = 10,
    ) -> float:
        """
        Population Stability Index (PSI) for drift detection.
        PSI < 0.1: No drift
        PSI 0.1-0.2: Moderate drift
        PSI > 0.2: Significant drift
        """
        # Flatten to 1D if needed (use L2 norms as proxy)
        if expected.ndim > 1:
            expected = np.linalg.norm(expected, axis=1)
        if actual.ndim > 1:
            actual = np.linalg.norm(actual, axis=1)

        # Bin the distributions
        breakpoints = np.linspace(
            min(expected.min(), actual.min()),
            max(expected.max(), actual.max()),
            buckets + 1,
        )

        expected_hist, _ = np.histogram(expected, bins=breakpoints)
        actual_hist, _ = np.histogram(actual, bins=breakpoints)

        # Normalize
        expected_pct = (expected_hist + 1) / (len(expected) + buckets)
        actual_pct = (actual_hist + 1) / (len(actual) + buckets)

        # PSI
        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(psi)

    async def check_drift(self, new_embeddings: np.ndarray) -> dict:
        """
        Check for data drift using PSI and cosine distance.

        Args:
            new_embeddings: Embeddings of recently ingested papers

        Returns:
            drift report dict
        """
        if not self._baseline_set:
            return {
                "drifted": False,
                "reason": "No baseline set yet",
                "psi": 0.0,
            }

        if len(new_embeddings) < 5:
            return {
                "drifted": False,
                "reason": "Too few new embeddings for drift analysis",
                "psi": 0.0,
            }

        # Use actual baseline norm stats instead of gaussian sampling
        from app.db.database import async_session

        # If we had actual baseline embeddings stored, we'd use them.
        # But we only have mean/std. Let's use PCA/KMeans approach or just use L2 norms as proxy
        # Since we just want a distribution, we can approximate better by not just using L2,
        # but returning a pseudo-PSI over major dimensions
        # Compute Euclidean distance (L2 norm) using the actual baseline sample, not gaussian randoms
        if hasattr(self, '_baseline_sample'):
            baseline_norms = np.linalg.norm(self._baseline_sample, axis=1)
        else:
            baseline_norms = np.linalg.norm(
                np.random.randn(max(len(new_embeddings), 50), new_embeddings.shape[1])
                * self._baseline_std + self._baseline_mean, axis=1)

        new_norms = np.linalg.norm(new_embeddings, axis=1)
        psi = self.compute_psi(baseline_norms, new_norms)

        # Compute mean cosine distance to baseline
        new_mean = np.mean(new_embeddings, axis=0)
        cos_dist = 1 - np.dot(new_mean, self._baseline_mean) / (
            np.linalg.norm(new_mean) * np.linalg.norm(self._baseline_mean) + 1e-8
        )

        psi_threshold = 0.2
        cos_threshold = 0.3
        is_drifted = psi > psi_threshold or cos_dist > cos_threshold

        result = {
            "drifted": is_drifted,
            "psi": round(psi, 4),
            "psi_threshold": psi_threshold,
            "cosine_distance": round(float(cos_dist), 4),
            "cosine_threshold": cos_threshold,
            "num_new_samples": len(new_embeddings),
        }

        # Log to DB
        async with async_session() as db:
            await crud.create_drift_record(
                db,
                drift_type="data_drift",
                metric_name="psi",
                metric_value=psi,
                threshold=psi_threshold,
                is_drifted=is_drifted,
                details=result,
            )
            await db.commit()

        if is_drifted:
            print(f"🚨 DATA DRIFT DETECTED! PSI={psi:.4f}, cos_dist={cos_dist:.4f}")
        else:
            print(f"✅ No drift detected. PSI={psi:.4f}, cos_dist={cos_dist:.4f}")

        return result

    async def get_drift_history(self, limit: int = 20) -> list[dict]:
        """Get recent drift detection records."""
        async with async_session() as db:
            records = await crud.get_recent_drift_records(db, limit)
            return [
                {
                    "drift_type": r.drift_type,
                    "metric_name": r.metric_name,
                    "metric_value": r.metric_value,
                    "threshold": r.threshold,
                    "is_drifted": r.is_drifted,
                    "detected_at": r.detected_at.isoformat(),
                }
                for r in records
            ]


# Global singleton
drift_detector = DriftDetector()
