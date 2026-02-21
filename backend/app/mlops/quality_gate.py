"""
Quality Gate — Automated pass/fail checks on model quality.
Compares current metrics against baseline thresholds.
"""

from dataclasses import dataclass


@dataclass
class GateResult:
    passed: bool
    metric_name: str
    current_value: float
    baseline_value: float
    threshold_pct: float
    message: str


class QualityGate:
    """Automated quality gate for model deployments."""

    # Default baseline metrics (updated as models improve)
    BASELINES = {
        "retrieval_recall@10": 0.65,
        "retrieval_mrr": 0.45,
        "synthesis_faithfulness": 0.70,
        "synthesis_answer_relevance": 0.65,
        "topic_coherence": 0.40,
        "embedding_throughput_docs_per_sec": 10.0,
    }

    def __init__(self, degradation_threshold_pct: float = 5.0):
        self.threshold_pct = degradation_threshold_pct

    def check(self, metric_name: str, current_value: float) -> GateResult:
        """Check if a metric passes the quality gate."""
        baseline = self.BASELINES.get(metric_name)
        if baseline is None:
            return GateResult(
                passed=True,
                metric_name=metric_name,
                current_value=current_value,
                baseline_value=0.0,
                threshold_pct=self.threshold_pct,
                message=f"No baseline for '{metric_name}', auto-pass",
            )

        # Check if degraded more than threshold
        if baseline > 0:
            degradation_pct = ((baseline - current_value) / baseline) * 100
        else:
            degradation_pct = 0.0

        passed = degradation_pct <= self.threshold_pct

        return GateResult(
            passed=passed,
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline,
            threshold_pct=self.threshold_pct,
            message=(
                f"✅ PASSED — {metric_name}: {current_value:.3f} (baseline: {baseline:.3f})"
                if passed
                else f"❌ FAILED — {metric_name}: {current_value:.3f} dropped {degradation_pct:.1f}% from baseline {baseline:.3f} (max allowed: {self.threshold_pct}%)"
            ),
        )

    def check_all(self, metrics: dict[str, float]) -> tuple[bool, list[GateResult]]:
        """Check all provided metrics against baselines."""
        results = [self.check(k, v) for k, v in metrics.items()]
        all_passed = all(r.passed for r in results)
        return all_passed, results

    def update_baseline(self, metric_name: str, new_value: float):
        """Update a baseline metric after a successful deployment."""
        self.BASELINES[metric_name] = new_value


quality_gate = QualityGate()
