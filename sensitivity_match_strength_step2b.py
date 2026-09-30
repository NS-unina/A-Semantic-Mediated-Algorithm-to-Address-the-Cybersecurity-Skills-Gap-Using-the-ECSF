#!/usr/bin/env python3
"""
Step 2B — Heterogeneous match-strength stress test.

Purpose
-------
The empirical Network Security case study assigned m=1 to all accepted
syllabus-to-CyBOK mappings. Therefore, the lower match-strength coefficients
were not active in the reported case study.

This script performs a *counterfactual robustness analysis* without inventing
which individual mappings should have been classified as Strong/Moderate/etc.

For each scenario:
    - a fraction q of the active CyBOK mappings is randomly selected;
    - selected mappings are downgraded from m=1 to beta;
    - all other mappings remain at m=1;
    - the complete CyBOK -> ECSF knowledge -> ECSF profile pipeline is rerun.

By repeatedly sampling the downgraded subset, the analysis measures how
sensitive the reported role ranking is to the *location* of possible
match-strength overconfidence.

Important:
    - This is a stress test, not an empirical re-labelling of mappings.
    - Random-sample frequencies are robustness frequencies under the specified
      perturbation design; they are NOT probabilities of real-world error.
    - alpha is fixed to 1 here. Joint alpha × match-strength sensitivity should
      be performed only after this step is validated.

The script also checks the published baseline against an ECSF-v1-consistent
baseline. Using the official 13-item Digital Forensics Investigator knowledge
set yields 41.08%, whereas the manuscript table reports 36.2%. The latter is
reproduced if "Computer networks security" is omitted from that role, leaving
12 items. This reconstructed published variant is kept only for diagnostic
comparison; the recommended sensitivity analysis uses the ECSF-consistent set.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# 1. CyBOK nodes produced by the case-study mapping
#    depth = normalized depth reported by the methodology document
#    knowledge = ECSF knowledge items linked to the CyBOK node
# ---------------------------------------------------------------------------

NODES: Dict[str, Tuple[float, List[str]]] = {
    "K1": (1.00, ["Computer systems vulnerabilities",
                  "Cybersecurity recommendations and best practices",
                  "Offensive and defensive security practices",
                  "Offensive and defensive security procedures",
                  "Security architecture reference models"]),
    "K2": (1.00, ["Computer networks security",
                  "Cybersecurity recommendations and best practices",
                  "Offensive and defensive security practices",
                  "Offensive and defensive security procedures",
                  "Security architecture reference models"]),
    "K3": (1.00, ["Cybersecurity recommendations and best practices",
                  "Offensive and defensive security practices",
                  "Offensive and defensive security procedures",
                  "Security architecture reference models"]),
    "K4": (1.00, ["Cybersecurity recommendations and best practices",
                  "Offensive and defensive security practices",
                  "Offensive and defensive security procedures"]),
    "K5": (1.00, ["Cybersecurity recommendations and best practices",
                  "Offensive and defensive security practices",
                  "Offensive and defensive security procedures"]),
    "K6": (1.00, ["Cybersecurity-related technologies"]),
    "K7": (1.00, ["Cybersecurity-related technologies"]),
    "K8": (1.00, ["Cybersecurity-related technologies"]),
    "K9": (1.00, ["Cybersecurity-related technologies"]),
    "K10": (1.00, ["Cybersecurity-related technologies"]),
    "K11": (1.00, ["Cybersecurity controls and solutions"]),
    "K12": (1.00, ["Cybersecurity awareness, education and training programme development"]),
    "K13": (1.00, ["Cybersecurity controls and solutions",
                   "Cybersecurity-related technologies"]),
    "K14": (1.00, ["Cybersecurity controls and solutions",
                   "Cybersecurity-related technologies"]),
    "K15": (1.00, ["Computer networks security"]),
    "K16": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K17": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K18": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K19": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K20": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K21": (1.00, ["Advanced and persistent cyber threats (APT)"]),
    "K22": (0.80, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K23": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation"]),
    "K24": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation",
                   "Cybersecurity controls and solutions",
                   "Cybersecurity-related technologies"]),
    "K25": (1.00, ["Computer Security Incident Response Teams (CSIRTs) operation",
                   "Cybersecurity controls and solutions",
                   "Cybersecurity-related technologies"]),
    "K26": (1.00, ["Offensive and defensive security practices",
                   "Offensive and defensive security procedures",
                   "Penetration testing procedures",
                   "Penetration testing tools",
                   "Testing procedures",
                   "Testing standards, methodologies and frameworks"]),
    "K27": (1.00, ["Penetration testing tools",
                   "Penetration testing procedures",
                   "Testing standards, methodologies and frameworks"]),
    "K28": (1.00, ["Cyber threat actors",
                   "Cyber threats",
                   "Cybersecurity attack procedures",
                   "Cybersecurity risks",
                   "Threat actors Tactics, Techniques and Procedures (TTPs)"]),
    "K29": (0.50, ["Computer systems vulnerabilities",
                   "Penetration testing standards, methodologies and frameworks"]),
    # K30 (VoIP Networks) has no ECSF knowledge association in the mapping table.
    "K30": (1.00, []),
    "K31": (0.34, ["Computer systems vulnerabilities",
                   "Operating systems security",
                   "Penetration testing standards, methodologies and frameworks",
                   "Penetration testing tools",
                   "Testing procedures",
                   "Testing standards, methodologies and frameworks"]),
    "K32": (0.34, ["Computer systems vulnerabilities",
                   "Penetration testing standards, methodologies and frameworks",
                   "Penetration testing tools",
                   "Testing procedures",
                   "Testing standards, methodologies and frameworks"]),
    "K33": (0.67, ["Computer systems vulnerabilities",
                   "Penetration testing standards, methodologies and frameworks",
                   "Penetration testing tools",
                   "Testing procedures",
                   "Testing standards, methodologies and frameworks"]),
    "K34": (0.83, ["Computer systems vulnerabilities",
                   "Penetration testing standards, methodologies and frameworks",
                   "Penetration testing tools",
                   "Testing procedures",
                   "Testing standards, methodologies and frameworks"]),
}


# ---------------------------------------------------------------------------
# 2. ECSF v1 role -> key knowledge sets
# ---------------------------------------------------------------------------

ROLES_ECSF: Dict[str, List[str]] = {
    "Chief Information Security Officer (CISO)": [
        "Cybersecurity policies",
        "Cybersecurity standards, methodologies and frameworks",
        "Cybersecurity recommendations and best practices",
        "Cybersecurity related laws, regulations and legislations",
        "Cybersecurity-related certifications",
        "Ethical cybersecurity organisation requirements",
        "Cybersecurity maturity models",
        "Cybersecurity procedures",
        "Resource management",
        "Management practices",
        "Risk management standards, methodologies and frameworks",
    ],
    "Cyber Incident Responder": [
        "Incident handling standards, methodologies and frameworks",
        "Incident handling recommendations and best practices",
        "Incident handling tools",
        "Incident handling communication procedures",
        "Operating systems security",
        "Computer networks security",
        "Cyber threats",
        "Cybersecurity attack procedures",
        "Computer systems vulnerabilities",
        "Cybersecurity-related certifications",
        "Cybersecurity related laws, regulations and legislations",
        "Secure Operation Centres (SOCs) operation",
        "Computer Security Incident Response Teams (CSIRTs) operation",
    ],
    "Cyber Legal, Policy & Compliance Officer": [
        "Cybersecurity related laws, regulations and legislations",
        "Cybersecurity standards, methodologies and frameworks",
        "Cybersecurity policies",
        "Legal, regulatory and legislative compliance requirements, recommendations and best practices",
        "Privacy impact assessment standards, methodologies and frameworks",
    ],
    "Cyber Threat Intelligence Specialist": [
        "Operating systems security",
        "Computer networks security",
        "Cybersecurity controls and solutions",
        "Computer programming",
        "Cyber Threat Intelligence (CTI) sharing standards, methodologies and frameworks",
        "Responsible information disclosure procedures",
        "Cross-domain and border-domain knowledge related to cybersecurity",
        "Cyber threats",
        "Cyber threat actors",
        "Cybersecurity attack procedures",
        "Advanced and persistent cyber threats (APT)",
        "Threat actors Tactics, Techniques and Procedures (TTPs)",
        "Cybersecurity-related certifications",
    ],
    "Cybersecurity Architect": [
        "Cybersecurity-related certifications",
        "Cybersecurity recommendations and best practices",
        "Cybersecurity standards, methodologies and frameworks",
        "Cybersecurity-related requirements analysis",
        "Secure development lifecycle",
        "Security architecture reference models",
        "Cybersecurity-related technologies",
        "Cybersecurity controls and solutions",
        "Cybersecurity risks",
        "Cyber threats",
        "Cybersecurity trends",
        "Legal, regulatory and legislative compliance requirements, recommendations and best practices",
        "Legacy cybersecurity procedures",
        "Privacy-Enhancing Technologies (PET)",
        "Privacy-by-design standards, methodologies and frameworks",
    ],
    "Cybersecurity Auditor": [
        "Cybersecurity controls and solutions",
        "Legal, regulatory and legislative compliance requirements, recommendations and best practices",
        "Monitoring, testing and evaluating cybersecurity controls' effectiveness",
        "Conformity assessment standards, methodologies and frameworks",
        "Auditing standards, methodologies and frameworks",
        "Cybersecurity standards, methodologies and frameworks",
        "Auditing-related certification",
        "Cybersecurity-related certifications",
    ],
    "Cybersecurity Educator": [
        "Pedagogical standards, methodologies and frameworks",
        "Cybersecurity awareness, education and training programme development",
        "Cybersecurity-related certifications",
        "Cybersecurity education and training standards, methodologies and frameworks",
        "Cybersecurity related laws, regulations and legislations",
        "Cybersecurity recommendations and best practices",
        "Cybersecurity standards, methodologies and frameworks",
        "Cybersecurity controls and solutions",
    ],
    "Cybersecurity Implementer": [
        "Secure development lifecycle",
        "Computer programming",
        "Operating systems security",
        "Computer networks security",
        "Cybersecurity controls and solutions",
        "Offensive and defensive security practices",
        "Secure coding recommendations and best practices",
        "Cybersecurity recommendations and best practices",
        "Testing standards, methodologies and frameworks",
        "Testing procedures",
        "Cybersecurity-related technologies",
    ],
    "Cybersecurity Researcher": [
        "Cybersecurity-related research, development and innovation (RDI)",
        "Cybersecurity standards, methodologies and frameworks",
        "Legal, regulatory and legislative requirements on releasing or using cybersecurity related technologies",
        "Multidiscipline aspect of cybersecurity",
        "Responsible information disclosure procedures",
    ],
    "Cybersecurity Risk Manager": [
        "Risk management standards, methodologies and frameworks",
        "Risk management tools",
        "Risk management recommendations and best practices",
        "Cyber threats",
        "Computer systems vulnerabilities",
        "Cybersecurity controls and solutions",
        "Cybersecurity risks",
        "Monitoring, testing and evaluating cybersecurity controls' effectiveness",
        "Cybersecurity-related certifications",
        "Cybersecurity-related technologies",
    ],
    "Digital Forensics Investigator": [
        "Digital forensics recommendations and best practices",
        "Digital forensics standards, methodologies and frameworks",
        "Digital forensics analysis procedures",
        "Testing procedures",
        "Criminal investigation procedures, standards, methodologies and frameworks",
        "Cybersecurity related laws, regulations and legislations",
        "Malware analysis tools",
        "Cyber threats",
        "Computer systems vulnerabilities",
        "Cybersecurity attack procedures",
        "Operating systems security",
        "Computer networks security",
        "Cybersecurity-related certifications",
    ],
    "Penetration Tester": [
        "Cybersecurity attack procedures",
        "Information technology (IT) and operational technology (OT) appliances",
        "Offensive and defensive security procedures",
        "Operating systems security",
        "Computer networks security",
        "Penetration testing procedures",
        "Penetration testing standards, methodologies and frameworks",
        "Penetration testing tools",
        "Computer programming",
        "Computer systems vulnerabilities",
        "Cybersecurity recommendations and best practices",
        "Cybersecurity-related certifications",
    ],
}


# Diagnostic reconstruction of the manuscript's 36.2% Digital Forensics value:
# removing Computer networks security gives (4 + 0.34)/12 = 36.17%.
ROLES_PUBLISHED_RECONSTRUCTION = {
    role: list(items) for role, items in ROLES_ECSF.items()
}
ROLES_PUBLISHED_RECONSTRUCTION["Digital Forensics Investigator"] = [
    x for x in ROLES_ECSF["Digital Forensics Investigator"]
    if x != "Computer networks security"
]


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

PUBLISHED_ALGORITHM_PERCENT = {
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

ACTIVE_NODES = [k for k, (_, items) in NODES.items() if items]


# ---------------------------------------------------------------------------
# 3. Pipeline
# ---------------------------------------------------------------------------

def compute_knowledge_weights(
    match_strengths: Dict[str, float] | None = None,
    alpha: float = 1.0,
) -> Dict[str, float]:
    if match_strengths is None:
        match_strengths = {k: 1.0 for k in NODES}

    out: Dict[str, float] = {}
    for node, (depth, knowledge_items) in NODES.items():
        score = match_strengths.get(node, 1.0) * (depth ** alpha)
        for knowledge in knowledge_items:
            out[knowledge] = max(out.get(knowledge, 0.0), score)
    return out


def compute_role_coverages(
    roles: Dict[str, List[str]],
    match_strengths: Dict[str, float] | None = None,
    alpha: float = 1.0,
) -> Dict[str, float]:
    knowledge_weights = compute_knowledge_weights(match_strengths, alpha)
    return {
        role: sum(knowledge_weights.get(k, 0.0) for k in items) / len(items)
        for role, items in roles.items()
    }


def kendall_vs_ground_truth(scores: Dict[str, float]) -> float:
    """
    Exact Kendall tau-b against the fixed ground-truth order.

    The ground-truth ranking has no ties; algorithmic scores may contain ties.
    Implemented directly to avoid repeated scipy overhead in Monte Carlo runs.
    """
    vals = [scores[role] for role in GROUND_TRUTH_ORDER]
    concordant = 0
    discordant = 0
    ties_x = 0

    for i in range(len(vals) - 1):
        for j in range(i + 1, len(vals)):
            diff = vals[i] - vals[j]
            if diff > 1e-12:
                concordant += 1
            elif diff < -1e-12:
                discordant += 1
            else:
                ties_x += 1

    comparable_x = concordant + discordant + ties_x
    comparable_y = concordant + discordant  # GT has no ties
    denom = math.sqrt(comparable_x * comparable_y)

    if denom == 0:
        return float("nan")
    return (concordant - discordant) / denom


def ranking(scores: Dict[str, float]) -> List[str]:
    # Ground-truth rank is used only to deterministically break exact score ties.
    return sorted(scores, key=lambda r: (-scores[r], GT_RANK[r]))


def p_at_3(scores: Dict[str, float]) -> float:
    gt_top3 = set(GROUND_TRUTH_ORDER[:3])
    pred_top3 = set(ranking(scores)[:3])
    return len(gt_top3 & pred_top3) / 3.0


# ---------------------------------------------------------------------------
# 4. Baseline validation
# ---------------------------------------------------------------------------

def baseline_comparison_rows() -> List[Dict[str, object]]:
    official = compute_role_coverages(ROLES_ECSF)
    reconstructed = compute_role_coverages(ROLES_PUBLISHED_RECONSTRUCTION)

    rows = []
    for role in GROUND_TRUTH_ORDER:
        rows.append({
            "role": role,
            "published_percent": PUBLISHED_ALGORITHM_PERCENT[role],
            "reconstructed_published_percent": 100 * reconstructed[role],
            "ecsf_consistent_percent": 100 * official[role],
            "published_minus_ecsf_consistent_pp":
                PUBLISHED_ALGORITHM_PERCENT[role] - 100 * official[role],
        })
    return rows


# ---------------------------------------------------------------------------
# 5. Heterogeneous perturbation experiment
# ---------------------------------------------------------------------------

def run_stress_test(
    n_samples: int = 5000,
    seed: int = 20260921,
    q_values: Tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 1.00),
    beta_values: Tuple[float, ...] = (0.85, 0.75, 0.50, 0.30, 0.10),
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:

    rng = np.random.default_rng(seed)

    baseline = compute_role_coverages(ROLES_ECSF)
    baseline_rank = ranking(baseline)
    baseline_top3 = baseline_rank[:3]
    baseline_top3_set = set(baseline_top3)
    baseline_tau = kendall_vs_ground_truth(baseline)

    scenario_rows: List[Dict[str, object]] = []
    role_rows: List[Dict[str, object]] = []

    n_nodes = len(ACTIVE_NODES)

    for q in q_values:
        k = n_nodes if q == 1.0 else max(1, int(round(q * n_nodes)))

        for beta in beta_values:
            taus = []
            p3s = []
            same_top3_set = []
            same_top3_order = []
            same_full_order = []
            coverages_by_role = {r: [] for r in GROUND_TRUTH_ORDER}

            effective_samples = 1 if k == n_nodes else n_samples

            for _ in range(effective_samples):
                if k == n_nodes:
                    downgraded = ACTIVE_NODES
                else:
                    downgraded = rng.choice(ACTIVE_NODES, size=k, replace=False).tolist()

                m = {node: 1.0 for node in NODES}
                for node in downgraded:
                    m[node] = beta

                scores = compute_role_coverages(ROLES_ECSF, m, alpha=1.0)
                rnk = ranking(scores)

                taus.append(kendall_vs_ground_truth(scores))
                p3s.append(p_at_3(scores))
                same_top3_set.append(set(rnk[:3]) == baseline_top3_set)
                same_top3_order.append(rnk[:3] == baseline_top3)
                same_full_order.append(rnk == baseline_rank)

                for role in GROUND_TRUTH_ORDER:
                    coverages_by_role[role].append(scores[role])

            taus_arr = np.asarray(taus, dtype=float)
            p3_arr = np.asarray(p3s, dtype=float)

            scenario_rows.append({
                "q_fraction_downgraded": q,
                "n_nodes_downgraded": k,
                "beta_downgraded_strength": beta,
                "samples": effective_samples,
                "baseline_tau": baseline_tau,
                "tau_mean": float(np.mean(taus_arr)),
                "tau_median": float(np.median(taus_arr)),
                "tau_p05": float(np.quantile(taus_arr, 0.05)),
                "tau_p95": float(np.quantile(taus_arr, 0.95)),
                "tau_min_observed": float(np.min(taus_arr)),
                "tau_max_observed": float(np.max(taus_arr)),
                "mean_p_at_3": float(np.mean(p3_arr)),
                "fraction_p_at_3_equals_1": float(np.mean(p3_arr == 1.0)),
                "fraction_same_top3_set": float(np.mean(same_top3_set)),
                "fraction_same_top3_order": float(np.mean(same_top3_order)),
                "fraction_same_full_ranking": float(np.mean(same_full_order)),
            })

            for role in GROUND_TRUTH_ORDER:
                vals = np.asarray(coverages_by_role[role], dtype=float)
                role_rows.append({
                    "q_fraction_downgraded": q,
                    "n_nodes_downgraded": k,
                    "beta_downgraded_strength": beta,
                    "role": role,
                    "baseline_coverage_percent": 100 * baseline[role],
                    "mean_coverage_percent": 100 * float(np.mean(vals)),
                    "median_coverage_percent": 100 * float(np.median(vals)),
                    "p05_coverage_percent": 100 * float(np.quantile(vals, 0.05)),
                    "p95_coverage_percent": 100 * float(np.quantile(vals, 0.95)),
                    "min_observed_coverage_percent": 100 * float(np.min(vals)),
                    "max_observed_coverage_percent": 100 * float(np.max(vals)),
                })

    return scenario_rows, role_rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_baseline_report() -> None:
    official = compute_role_coverages(ROLES_ECSF)
    reconstructed = compute_role_coverages(ROLES_PUBLISHED_RECONSTRUCTION)

    print("BASELINE VALIDATION")
    print("=" * 82)
    print(f"ECSF-consistent Kendall tau: {kendall_vs_ground_truth(official):.6f}")
    print(f"Reconstructed-published tau: {kendall_vs_ground_truth(reconstructed):.6f}")
    print(f"ECSF-consistent P@3:         {p_at_3(official):.3f}")
    print()
    print(f"{'Role':42} {'Published':>10} {'Reconstr.':>10} {'ECSF-v1':>10}")
    print("-" * 82)
    for role in GROUND_TRUTH_ORDER:
        print(
            f"{role[:42]:42} "
            f"{PUBLISHED_ALGORITHM_PERCENT[role]:9.1f}% "
            f"{100*reconstructed[role]:9.2f}% "
            f"{100*official[role]:9.2f}%"
        )
    print()
    print("Diagnostic discrepancy:")
    print(
        "Digital Forensics Investigator = "
        f"{100*official['Digital Forensics Investigator']:.2f}% with the official "
        "13-item ECSF knowledge set, versus 36.2% reported in the manuscript."
    )


def print_selected_stress_results(rows: List[Dict[str, object]]) -> None:
    print()
    print("HETEROGENEOUS MATCH-STRENGTH STRESS TEST — SELECTED SCENARIOS")
    print("=" * 112)
    print(
        f"{'q':>5} {'beta':>6} {'tau med':>9} {'tau 5%':>9} "
        f"{'P@3=1':>9} {'same top3 set':>14} {'same top3 order':>16}"
    )
    print("-" * 112)

    selected = {(0.10, 0.50), (0.25, 0.50), (0.50, 0.50),
                (0.50, 0.30), (0.75, 0.30), (1.00, 0.10)}

    for row in rows:
        key = (row["q_fraction_downgraded"], row["beta_downgraded_strength"])
        if key in selected:
            print(
                f"{row['q_fraction_downgraded']:5.2f} "
                f"{row['beta_downgraded_strength']:6.2f} "
                f"{row['tau_median']:9.3f} "
                f"{row['tau_p05']:9.3f} "
                f"{row['fraction_p_at_3_equals_1']:9.3f} "
                f"{row['fraction_same_top3_set']:14.3f} "
                f"{row['fraction_same_top3_order']:16.3f}"
            )


def main() -> None:
    root = Path(__file__).resolve().parent

    print_baseline_report()

    baseline_rows = baseline_comparison_rows()
    scenario_rows, role_rows = run_stress_test()

    baseline_path = root / "step2b_baseline_comparison.csv"
    scenario_path = root / "step2b_match_strength_scenarios.csv"
    role_path = root / "step2b_match_strength_role_coverage.csv"

    write_csv(baseline_path, baseline_rows)
    write_csv(scenario_path, scenario_rows)
    write_csv(role_path, role_rows)

    print_selected_stress_results(scenario_rows)

    print("\nOutputs:")
    print(baseline_path)
    print(scenario_path)
    print(role_path)


if __name__ == "__main__":
    main()
