#!/usr/bin/env python3
"""Calculate exact one-sided binomial acceptance gates for detector validation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scipy.stats import beta, binom


def lower_bound(successes: int, trials: int, alpha: float) -> float:
    if successes == 0:
        return 0.0
    return float(beta.ppf(alpha, successes, trials - successes + 1))


def upper_bound(events: int, trials: int, alpha: float) -> float:
    if events == trials:
        return 1.0
    return float(beta.ppf(1.0 - alpha, events + 1, trials - events))


def minimum_successes(trials: int, target_lower: float, alpha: float) -> int | None:
    return next(
        (successes for successes in range(trials + 1) if lower_bound(successes, trials, alpha) >= target_lower),
        None,
    )


def maximum_events(trials: int, target_upper: float, alpha: float) -> int | None:
    passing = [events for events in range(trials + 1) if upper_bound(events, trials, alpha) <= target_upper]
    return max(passing) if passing else None


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=repo / "phase0/SAMPLE_SIZE_SCENARIOS_V0_1.csv",
    )
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--target-tpr-lower", type=float, default=0.80)
    parser.add_argument("--target-fpr-upper", type=float, default=0.05)
    parser.add_argument("--assumed-true-tpr", type=float, default=0.85)
    parser.add_argument("--assumed-true-fpr", type=float, default=0.02)
    parser.add_argument("--sample-sizes", type=int, nargs="+", default=[50, 100, 150, 200, 250, 300, 400])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    alpha = 1.0 - args.confidence
    if not 0.0 < alpha < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    rows: list[dict[str, str | int | float]] = []
    for trials in args.sample_sizes:
        min_tp = minimum_successes(trials, args.target_tpr_lower, alpha)
        max_fp = maximum_events(trials, args.target_fpr_upper, alpha)
        rows.append(
            {
                "n_per_class": trials,
                "confidence_one_sided": args.confidence,
                "target_tpr_lower": args.target_tpr_lower,
                "minimum_true_positives": "" if min_tp is None else min_tp,
                "observed_tpr_at_gate": "" if min_tp is None else f"{min_tp / trials:.6f}",
                "exact_lower_tpr_at_gate": "" if min_tp is None else f"{lower_bound(min_tp, trials, alpha):.6f}",
                "assumed_true_tpr": args.assumed_true_tpr,
                "power_to_pass_tpr_gate": "" if min_tp is None else f"{binom.sf(min_tp - 1, trials, args.assumed_true_tpr):.6f}",
                "target_fpr_upper": args.target_fpr_upper,
                "maximum_false_positives": "" if max_fp is None else max_fp,
                "observed_fpr_at_gate": "" if max_fp is None else f"{max_fp / trials:.6f}",
                "exact_upper_fpr_at_gate": "" if max_fp is None else f"{upper_bound(max_fp, trials, alpha):.6f}",
                "assumed_true_fpr": args.assumed_true_fpr,
                "power_to_pass_fpr_gate": "" if max_fp is None else f"{binom.cdf(max_fp, trials, args.assumed_true_fpr):.6f}",
                "exact_upper_fpr_if_zero": f"{upper_bound(0, trials, alpha):.6f}",
                "method": "Clopper-Pearson exact one-sided",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} scenarios to {args.output}")


if __name__ == "__main__":
    main()
