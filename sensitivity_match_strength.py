#!/usr/bin/env python3
"""
Step 2A — Sensitivity analysis of the match-strength assumption.

Context
-------
In the empirical Network Security case study, all accepted syllabus-to-CyBOK
mappings were assigned match strength m = 1. Therefore, with alpha fixed,
the mapping score is:

    score_{s,j} = d_norm(j)^alpha

This script stress-tests the assumption m=1 through a uniform discount factor
lambda applied to every accepted syllabus-to-CyBOK mapping:

    m_{s,j} = lambda,   lambda in [0, 1]

For lambda > 0, because the same positive multiplicative factor is applied to
every accepted mapping and the ECSF knowledge aggregation uses MAX,

    max(lambda*x_1, ..., lambda*x_n)
      = lambda * max(x_1, ..., x_n)

and therefore every non-zero ECSF profile coverage is multiplied by lambda.

Consequences:
    * absolute coverage values change linearly with lambda;
    * relative ranking is unchanged for every lambda > 0;
    * Kendall's tau against the ground truth is unchanged for every lambda > 0;
    * P@3 is unchanged for every lambda > 0.

lambda = 0 is retained only as a mathematical boundary case. It makes every
profile coverage equal to zero, so the ranking, Kendall's tau and P@3 are not
well-defined and are reported as NA.

This is a robustness/stress test of the global match-strength assumption; it
is NOT an empirical calibration of the six heuristic match-strength levels.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Tuple

try:
    from scipy.stats import kendalltau
except ImportError as exc:
    raise SystemExit("scipy is required. Install with: pip install scipy") from exc


# ---------------------------------------------------------------------------
# 1. Baseline reconstruction from the manuscript (alpha = 1, m = 1)
# ---------------------------------------------------------------------------

ROLES: Dict[str, Dict[str, float | bool]] = {
    "Penetration Tester":
        {"denominator": 12, "constant": 7, "has_os": True, "has_ptstd": True},
    "Cybersecurity Implementer":
        {"denominator": 11, "constant": 7, "has_os": True, "has_ptstd": False},
    "Cyber Threat Intelligence Specialist":
        {"denominator": 13, "constant": 7, "has_os": True, "has_ptstd": False},
    "Cyber Incident Responder":
        {"denominator": 13, "constant": 5, "has_os": True, "has_ptstd": False},
    "Digital Forensics Investigator":
        {"denominator": 12, "constant": 4, "has_os": True, "has_ptstd": False},
    "Cybersecurity Risk Manager":
        {"denominator": 10, "constant": 5, "has_os": False, "has_ptstd": False},
    "Cybersecurity Architect":
        {"denominator": 15, "constant": 6, "has_os": False, "has_ptstd": False},
    "Cybersecurity Auditor":
        {"denominator": 8, "constant": 1, "has_os": False, "has_ptstd": False},
    "Cyber Legal, Policy & Compliance Officer":
        {"denominator": 5, "constant": 0, "has_os": False, "has_ptstd": False},
    "Cybersecurity Educator":
        {"denominator": 8, "constant": 3, "has_os": False, "has_ptstd": False},
    "Chief Information Security Officer (CISO)":
        {"denominator": 11, "constant": 1, "has_os": False, "has_ptstd": False},
    "Cybersecurity Researcher":
        {"denominator": 5, "constant": 0, "has_os": False, "has_ptstd": False},
}

GROUND_TRUTH_ORDER = [
    "Penetration Tester",
    "Cybersecurity Implementer",
    "Cyber Threat Intelligence Specialist",
    "Cyber Incident Responder",
    "Digital Forensics Investigator",
    "Cybersecurity Risk Manager",
    "Cybersecurity Architect",
    "Cybersecurity Auditor",
    "Cyber Legal, Policy & Compliance Officer",
    "Cybersecurity Educator",
    "Chief Information Security Officer (CISO)",
    "Cybersecurity Researcher",
]
GT_RANK = {role: i + 1 for i, role in enumerate(GROUND_TRUTH_ORDER)}

# We include lambda=0 only as a degenerate boundary case.
LAMBDAS = [round(x / 10, 1) for x in range(0, 11)]


def baseline_role_coverage(role: str, alpha: float = 1.0) -> float:
    """Coverage of a role under the manuscript baseline m=1."""
    cfg = ROLES[role]
    numerator = float(cfg["constant"])

    if bool(cfg["has_os"]):
        numerator += 0.34 ** alpha
    if bool(cfg["has_ptstd"]):
        numerator += 0.83 ** alpha

    return numerator / float(cfg["denominator"])


def all_baseline_coverages(alpha: float = 1.0) -> Dict[str, float]:
    return {role: baseline_role_coverage(role, alpha) for role in ROLES}


def discounted_coverages(match_strength: float, alpha: float = 1.0) -> Dict[str, float]:
    """
    Uniformly discount every accepted syllabus-to-CyBOK mapping.

    Because match_strength is common to all accepted mappings, MAX aggregation
    is homogeneous and each final profile coverage is simply scaled by lambda.
    """
    base = all_baseline_coverages(alpha)
    return {role: match_strength * value for role, value in base.items()}


def rank_roles(scores: Dict[str, float]) -> list[str]:
    """
    Descending score with GT rank used ONLY as a deterministic tie-break.

    This function is not used at lambda=0, where all scores are tied and the
    ranking is substantively undefined.
    """
    return sorted(scores, key=lambda role: (-scores[role], GT_RANK[role]))


def kendall_against_ground_truth(scores: Dict[str, float]) -> Tuple[float, float]:
    x = [scores[role] for role in GROUND_TRUTH_ORDER]
    y = [-GT_RANK[role] for role in GROUND_TRUTH_ORDER]
    tau, p_value = kendalltau(x, y)
    return float(tau), float(p_value)


def p_at_3(scores: Dict[str, float]) -> float:
    top3 = set(rank_roles(scores)[:3])
    gt_top3 = set(GROUND_TRUTH_ORDER[:3])
    return len(top3 & gt_top3) / 3.0


def build_results() -> list[dict[str, object]]:
    rows = []

    baseline_scores = discounted_coverages(1.0)
    baseline_tau, _ = kendall_against_ground_truth(baseline_scores)
    baseline_p3 = p_at_3(baseline_scores)

    for lam in LAMBDAS:
        scores = discounted_coverages(lam)

        if lam == 0:
            # All scores are identical: ranking metrics are undefined.
            for role in GROUND_TRUTH_ORDER:
                rows.append({
                    "lambda_match_strength": lam,
                    "role": role,
                    "coverage": scores[role],
                    "coverage_percent": 100.0 * scores[role],
                    "rank": "NA",
                    "gt_rank": GT_RANK[role],
                    "kendall_tau_ground_truth": "NA",
                    "kendall_p_value": "NA",
                    "p_at_3": "NA",
                    "tau_change_vs_lambda_1": "NA",
                    "p3_change_vs_lambda_1": "NA",
                    "status": "degenerate_all_scores_zero",
                })
            continue

        tau, p_value = kendall_against_ground_truth(scores)
        p3 = p_at_3(scores)
        order = rank_roles(scores)
        ranks = {role: i + 1 for i, role in enumerate(order)}

        for role in order:
            rows.append({
                "lambda_match_strength": lam,
                "role": role,
                "coverage": scores[role],
                "coverage_percent": 100.0 * scores[role],
                "rank": ranks[role],
                "gt_rank": GT_RANK[role],
                "kendall_tau_ground_truth": tau,
                "kendall_p_value": p_value,
                "p_at_3": p3,
                "tau_change_vs_lambda_1": tau - baseline_tau,
                "p3_change_vs_lambda_1": p3 - baseline_p3,
                "status": "valid",
            })

    return rows


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_summary() -> None:
    print("Step 2A — Uniform match-strength sensitivity")
    print("=" * 72)

    baseline = discounted_coverages(1.0)
    baseline_tau, _ = kendall_against_ground_truth(baseline)
    baseline_p3 = p_at_3(baseline)
    baseline_order = rank_roles(baseline)

    print(f"Baseline Kendall tau: {baseline_tau:.6f}")
    print(f"Baseline P@3:         {baseline_p3:.3f}")
    print("Baseline top-3:       " + " | ".join(baseline_order[:3]))
    print()

    print(f"{'lambda':>6} {'PT %':>8} {'Impl %':>8} {'CTI %':>8} {'tau':>8} {'P@3':>6}")
    print("-" * 52)

    for lam in LAMBDAS:
        scores = discounted_coverages(lam)

        if lam == 0:
            print(f"{lam:6.1f} {0:8.2f} {0:8.2f} {0:8.2f} {'NA':>8} {'NA':>6}")
            continue

        tau, _ = kendall_against_ground_truth(scores)
        p3 = p_at_3(scores)
        print(
            f"{lam:6.1f} "
            f"{100*scores['Penetration Tester']:8.2f} "
            f"{100*scores['Cybersecurity Implementer']:8.2f} "
            f"{100*scores['Cyber Threat Intelligence Specialist']:8.2f} "
            f"{tau:8.3f} "
            f"{p3:6.2f}"
        )

    print()
    print("Analytical check:")
    print("For every lambda > 0, coverage(lambda) = lambda * coverage(lambda=1).")
    print("Therefore ranks, Kendall's tau and P@3 are invariant to a uniform")
    print("positive rescaling of match strength. lambda=0 is degenerate.")


def main() -> None:
    out = Path(__file__).with_name("match_strength_sensitivity_step2a_results.csv")
    rows = build_results()
    write_csv(rows, out)
    print_summary()
    print(f"\nCSV written to: {out}")


if __name__ == "__main__":
    main()
