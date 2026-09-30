#!/usr/bin/env python3
"""
Step 1 — Sensitivity analysis of the hierarchical-depth parameter alpha.

Purpose
-------
Reconstruct the alpha-dependent part of the current manuscript's coverage
metric and evaluate the effect of alternative alpha values on the 12 ECSF
role scores, Kendall's tau, and P@3.

Important methodological note
-----------------------------
This script intentionally reconstructs the *reported manuscript instance*
instead of substituting a different ECSF role-to-knowledge matrix. The .tex
manuscript contains the complete knowledge-item weights and the final role
scores, but not the full role/knowledge membership matrix used to generate
those scores.

For the current case study, the only effective knowledge-item weights that are
non-unit at alpha=1 are:
    - Operating systems security: 0.34
    - Penetration testing standards, methodologies and frameworks: 0.83
All other effective knowledge-item weights are 1.0 after the manuscript's
max aggregation. Therefore only roles containing these knowledge items can
change as alpha varies.

The decomposition below is reconstructed from the reported manuscript scores:
    PT:   (7 + 0.34 + 0.83) / 12 = 0.6808  -> 68.1%
    Impl: (7 + 0.34) / 11       = 0.6667  -> 66.7%
    CTI:  (7 + 0.34) / 13       = 0.5646  -> 56.5%
    CIR:  (5 + 0.34) / 13       = 0.4108  -> 41.1%
    DFI:  (4 + 0.34) / 12       = 0.3617  -> 36.2%

This is the correct basis for a Step-1 robustness check. Once the original
role/knowledge matrix is available, replace this compact reconstruction with
that raw matrix and rerun the same analysis.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Tuple

try:
    from scipy.stats import kendalltau
except ImportError as exc:
    raise SystemExit(
        "scipy is required. Install with: pip install scipy"
    ) from exc


# ---------------------------------------------------------------------------
# 1. Manuscript reconstruction
# ---------------------------------------------------------------------------
# For each role:
#   denominator = |K_P|
#   constant = sum of all covered knowledge-item contributions that are 1.0
#   has_os = whether 'Operating systems security' contributes 0.34 at alpha=1
#   has_ptstd = whether 'Penetration testing standards, methodologies and
#               frameworks' contributes 0.83 at alpha=1
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

# Ground-truth ordering reported in the manuscript (rank 1 = highest relevance).
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

# Sensitivity grid proposed for the first reviewer response.
ALPHAS = [0.0, 0.5, 1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# 2. Metric implementation
# ---------------------------------------------------------------------------
def role_coverage(role: str, alpha: float) -> float:
    """Compute the role coverage under the manuscript's alpha-dependent model."""
    cfg = ROLES[role]
    numerator = float(cfg["constant"])

    if bool(cfg["has_os"]):
        numerator += 0.34 ** alpha
    if bool(cfg["has_ptstd"]):
        numerator += 0.83 ** alpha

    return numerator / float(cfg["denominator"])


def all_coverages(alpha: float) -> Dict[str, float]:
    return {role: role_coverage(role, alpha) for role in ROLES}


def rank_roles(scores: Dict[str, float]) -> list[str]:
    """Descending score. GT rank is used only as a deterministic tie-break."""
    return sorted(scores, key=lambda role: (-scores[role], GT_RANK[role]))


def rank_dict(scores: Dict[str, float]) -> Dict[str, int]:
    return {role: i + 1 for i, role in enumerate(rank_roles(scores))}


def kendall_against_ground_truth(scores: Dict[str, float]) -> Tuple[float, float]:
    # Put algorithm scores and GT rank in the same orientation: larger value
    # means more relevant, hence use -rank for the ground truth.
    x = [scores[role] for role in GROUND_TRUTH_ORDER]
    y = [-GT_RANK[role] for role in GROUND_TRUTH_ORDER]
    tau, p_value = kendalltau(x, y)
    return float(tau), float(p_value)


def p_at_3(scores: Dict[str, float]) -> float:
    """
    P@3 against the expert top-3.

    The manuscript has a unique top-3 at alpha=1. For alpha values in this
    sensitivity grid, no tie occurs at the top-3 cutoff, so P@3 is well-defined.
    """
    top3 = set(rank_roles(scores)[:3])
    gt_top3 = set(GROUND_TRUTH_ORDER[:3])
    return len(top3 & gt_top3) / 3.0


# ---------------------------------------------------------------------------
# 3. Baseline consistency check
# ---------------------------------------------------------------------------
REPORTED_BASELINE_PERCENT = {
    "Penetration Tester": 68.1,
    "Cybersecurity Implementer": 66.7,
    "Cyber Threat Intelligence Specialist": 56.5,
    "Cyber Incident Responder": 41.1,
    "Digital Forensics Investigator": 36.2,
    "Cybersecurity Risk Manager": 50.0,
    "Cybersecurity Architect": 40.0,
    "Cybersecurity Auditor": 12.5,
    "Cyber Legal, Policy & Compliance Officer": 0.0,
    "Cybersecurity Educator": 37.5,
    "Chief Information Security Officer (CISO)": 9.1,
    "Cybersecurity Researcher": 0.0,
}


def validate_baseline(tolerance_percent: float = 0.06) -> None:
    """Check alpha=1 reconstruction against the manuscript's one-decimal scores."""
    print("Baseline validation (alpha=1):")
    failures = []
    for role, reported in REPORTED_BASELINE_PERCENT.items():
        computed = 100.0 * role_coverage(role, 1.0)
        delta = computed - reported
        ok = abs(delta) <= tolerance_percent
        print(
            f"  {role:55s} computed={computed:6.3f}% "
            f"reported={reported:5.1f}% delta={delta:+.3f}% "
            f"{'OK' if ok else 'MISMATCH'}"
        )
        if not ok:
            failures.append((role, computed, reported, delta))

    if failures:
        raise AssertionError(
            "The manuscript reconstruction does not reproduce all reported "
            "alpha=1 values within tolerance: " + repr(failures)
        )


def build_results() -> list[dict[str, object]]:
    baseline_scores = all_coverages(1.0)
    baseline_ranks = rank_dict(baseline_scores)
    results = []

    for alpha in ALPHAS:
        scores = all_coverages(alpha)
        ranks = rank_dict(scores)
        tau, p_value = kendall_against_ground_truth(scores)
        tau_vs_baseline, _ = kendalltau(
            [ranks[role] for role in ROLES],
            [baseline_ranks[role] for role in ROLES],
        )
        order = rank_roles(scores)

        for rank, role in enumerate(order, start=1):
            results.append({
                "alpha": alpha,
                "role": role,
                "rank": rank,
                "coverage": scores[role],
                "coverage_percent": 100.0 * scores[role],
                "gt_rank": GT_RANK[role],
                "tau_ground_truth": tau,
                "tau_p_value": p_value,
                "p_at_3": p_at_3(scores),
                "rank_stability_vs_alpha_1": float(tau_vs_baseline),
            })

    return results


# ---------------------------------------------------------------------------
# 4. Output
# ---------------------------------------------------------------------------
def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict[str, object]]) -> None:
    print("\nAlpha sensitivity summary")
    print("=" * 80)

    for alpha in ALPHAS:
        subset = [row for row in rows if float(row["alpha"]) == alpha]
        subset.sort(key=lambda row: int(row["rank"]))
        tau = float(subset[0]["tau_ground_truth"])
        p_value = float(subset[0]["tau_p_value"])
        p3 = float(subset[0]["p_at_3"])
        stability = float(subset[0]["rank_stability_vs_alpha_1"])

        print(
            f"alpha={alpha:<3g} | "
            f"tau={tau:.3f} | p={p_value:.6f} | "
            f"P@3={p3:.3f} | rank-stability={stability:.3f}"
        )

        for row in subset[:3]:
            print(
                f"    {int(row['rank'])}. {row['role']}: "
                f"{float(row['coverage_percent']):.2f}%"
            )
        print()


if __name__ == "__main__":
    validate_baseline()
    results = build_results()

    output_path = Path(__file__).with_name("alpha_sensitivity_step1_results.csv")
    write_csv(results, output_path)
    print_summary(results)
    print(f"Detailed results written to: {output_path}")
