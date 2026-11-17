"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb, isfinite

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same number of labels")
    if len(human) == 0:
        raise ValueError("calibration requires at least one pair of labels")
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for actual, predicted in zip(human, judge):
        if actual not in ("PASS", "FAIL") or predicted not in ("PASS", "FAIL"):
            raise ValueError("labels must be PASS or FAIL")
        if actual == POS:
            key = "tp" if predicted == POS else "fn"
        else:
            key = "fp" if predicted == POS else "tn"
        counts[key] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    counts = confusion(human, judge)
    predicted_failures = counts["tp"] + counts["fp"]
    actual_failures = counts["tp"] + counts["fn"]
    precision = counts["tp"] / predicted_failures if predicted_failures else 0.0
    recall = counts["tp"] / actual_failures if actual_failures else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    counts = confusion(human, judge)
    n = sum(counts.values())
    expected_agreement = (
        (counts["tp"] + counts["fn"]) * (counts["tp"] + counts["fp"])
        + (counts["tn"] + counts["fp"]) * (counts["tn"] + counts["fn"])
    )
    denominator = n * n - expected_agreement
    if denominator == 0:
        raise ValueError("Cohen's kappa is undefined when expected agreement is 1")
    observed_agreement = n * (counts["tp"] + counts["tn"])
    return (observed_agreement - expected_agreement) / denominator


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    if not all(isfinite(value) and 0.0 <= value <= 1.0
               for value in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be finite probabilities between 0 and 1")
    denominator = sensitivity + specificity - 1.0
    if denominator == 0.0:
        raise ValueError("Rogan-Gladen is undefined when sensitivity + specificity is 1")
    corrected = (observed_rate + specificity - 1.0) / denominator
    return min(1.0, max(0.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    left, right = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if left.ndim != 1 or right.ndim != 1 or left.shape != right.shape or left.size == 0:
        raise ValueError("paired samples must be non-empty one-dimensional arrays of equal length")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("paired samples must contain only finite values")
    if isinstance(n_resamples, bool) or not isinstance(n_resamples, int) or n_resamples < 1:
        raise ValueError("n_resamples must be a positive integer")
    if not isfinite(confidence) or not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if np.array_equal(left, right):
        return 0.0, 0.0, 0.0
    if left.size < 2:
        raise ValueError("bootstrap requires at least two paired items")
    result = bootstrap(
        (left, right), lambda x, y, axis: np.mean(x - y, axis=axis),
        paired=True, vectorized=True, n_resamples=n_resamples,
        confidence_level=confidence, method="percentile", rng=np.random.default_rng(rng),
    )
    return float(np.mean(left - right)), float(result.confidence_interval.low), float(result.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (n, c, k)) or not (n > 0 and 0 <= c <= n and 1 <= k <= n):
        raise ValueError("invalid n, c, k")
    return 1.0 - (comb(n - c, k) / comb(n, k) if n - c >= k else 0.0)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    if any(isinstance(x, bool) or not isinstance(x, int) for x in (n, c, k)) or not (n > 0 and 0 <= c <= n and 1 <= k <= n):
        raise ValueError("invalid n, c, k")
    return comb(c, k) / comb(n, k) if c >= k else 0.0
