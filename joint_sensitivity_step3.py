#!/usr/bin/env python3
"""
Step 3 — Joint sensitivity analysis of hierarchical depth (alpha)
and heterogeneous match-strength perturbations (q, beta).

Requires:
    sensitivity_match_strength_step2b.py

Parameters
----------
alpha:
    Controls the contribution of normalized CyBOK depth.
q:
    Fraction of accepted syllabus-to-CyBOK mappings downgraded from m=1.
beta:
    Match strength assigned to downgraded mappings.

The downgraded subset is sampled at random because the empirical case study
assigned m=1 to all accepted mappings and therefore provides no empirical basis
for retrospectively labeling individual mappings as Strong/Moderate/Weak.

The SAME sampled subsets are reused across alpha and beta values. This paired
design ensures that differences across parameterizations are due to the
parameters rather than to different Monte Carlo draws.

Outputs
-------
step3_corrected_alpha_baseline.csv
step3_joint_sensitivity_scenarios.csv
step3_joint_sensitivity_role_coverage.csv
step3_joint_sensitivity_selected_summary.csv
"""

from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
STEP2B = ROOT / "sensitivity_match_strength_step2b.py"

if not STEP2B.exists():
    raise FileNotFoundError(
        "sensitivity_match_strength_step2b.py must be in the same directory."
    )

spec = importlib.util.spec_from_file_location("step2b", STEP2B)
step2b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step2b)

NODES = step2b.NODES
ROLES = step2b.ROLES_ECSF
GT_ORDER = step2b.GROUND_TRUTH_ORDER

ALPHAS = [0.0, 0.5, 1.0, 2.0, 3.0]
Q_VALUES = [0.10, 0.25, 0.50, 0.75, 1.00]
BETAS = [0.85, 0.75, 0.50, 0.30, 0.10]
N_SAMPLES = 5000
SEED = 20260921

active_nodes = [k for k, (_, items) in NODES.items() if items]
node_depth = np.array([NODES[k][0] for k in active_nodes], dtype=float)

knowledge = sorted({item for _, items in NODES.values() for item in items})
k_index = {k:i for i,k in enumerate(knowledge)}

knowledge_node_indices = []
for k in knowledge:
    idxs = [i for i,node in enumerate(active_nodes) if k in NODES[node][1]]
    knowledge_node_indices.append(np.array(idxs, dtype=int))

role_matrix = np.zeros((len(GT_ORDER), len(knowledge)), dtype=float)
for r_idx, role in enumerate(GT_ORDER):
    items = ROLES[role]
    denom = len(items)
    for item in items:
        if item in k_index:
            role_matrix[r_idx, k_index[item]] = 1.0 / denom

PAIR_I, PAIR_J = np.triu_indices(len(GT_ORDER), k=1)
N_PAIRS = len(PAIR_I)

def compute_role_scores(node_scores):
    n = node_scores.shape[0]
    kw = np.zeros((n, len(knowledge)), dtype=float)
    for j, idxs in enumerate(knowledge_node_indices):
        if len(idxs):
            kw[:,j] = node_scores[:,idxs].max(axis=1)
    return kw @ role_matrix.T

def kendall_tau_b_vs_gt(score_matrix):
    diffs = score_matrix[:,PAIR_I] - score_matrix[:,PAIR_J]
    c = (diffs > 1e-12).sum(axis=1)
    d = (diffs < -1e-12).sum(axis=1)
    comparable = c + d
    denom = np.sqrt(N_PAIRS * comparable)
    out = np.full(score_matrix.shape[0], np.nan)
    valid = denom > 0
    out[valid] = (c[valid]-d[valid]) / denom[valid]
    return out

def top3_indices(score_matrix):
    return np.argsort(-score_matrix, axis=1, kind="stable")[:,:3]

gt_top3 = {0,1,2}

nominal_scores = compute_role_scores((node_depth**1.0)[None,:])[0]
nominal_order = np.argsort(-nominal_scores, kind="stable")
nominal_top3 = nominal_order[:3]
nominal_top3_set = set(nominal_top3.tolist())

rng = np.random.default_rng(SEED)
masks = {}
for q in Q_VALUES:
    k = len(active_nodes) if q == 1.0 else max(1, int(round(q*len(active_nodes))))
    if k == len(active_nodes):
        mask = np.ones((1,len(active_nodes)), dtype=bool)
    else:
        mask = np.zeros((N_SAMPLES,len(active_nodes)), dtype=bool)
        for s in range(N_SAMPLES):
            idx = rng.choice(len(active_nodes), size=k, replace=False)
            mask[s,idx] = True
    masks[q] = (k,mask)

scenario_rows = []
role_rows = []
alpha_rows = []

for alpha in ALPHAS:
    rs = compute_role_scores((node_depth**alpha)[None,:])
    tau = kendall_tau_b_vs_gt(rs)[0]
    t3 = top3_indices(rs)[0]
    alpha_rows.append({
        "alpha":alpha,
        "kendall_tau":tau,
        "p_at_3":len(set(t3.tolist()) & gt_top3)/3.0,
        "top_1":GT_ORDER[t3[0]],
        "top_2":GT_ORDER[t3[1]],
        "top_3":GT_ORDER[t3[2]],
        "penetration_tester_percent":100*rs[0,0],
        "implementer_percent":100*rs[0,1],
        "cti_percent":100*rs[0,2],
        "digital_forensics_percent":100*rs[0,4],
    })

for alpha in ALPHAS:
    depth_factor = node_depth**alpha
    for q in Q_VALUES:
        k,mask = masks[q]
        for beta in BETAS:
            strengths = np.where(mask,beta,1.0)
            rs = compute_role_scores(strengths*depth_factor[None,:])
            taus = kendall_tau_b_vs_gt(rs)
            t3 = top3_indices(rs)

            p3 = np.array([len(set(x.tolist()) & gt_top3)/3.0 for x in t3])
            same_set = np.array([set(x.tolist()) == nominal_top3_set for x in t3])
            same_order = np.all(t3 == nominal_top3[None,:], axis=1)

            scenario_rows.append({
                "alpha":alpha,
                "q_fraction_downgraded":q,
                "n_nodes_downgraded":k,
                "beta_downgraded_strength":beta,
                "samples":len(rs),
                "tau_mean":float(np.nanmean(taus)),
                "tau_median":float(np.nanmedian(taus)),
                "tau_p05":float(np.nanquantile(taus,.05)),
                "tau_p95":float(np.nanquantile(taus,.95)),
                "tau_min_observed":float(np.nanmin(taus)),
                "tau_max_observed":float(np.nanmax(taus)),
                "mean_p_at_3":float(np.mean(p3)),
                "fraction_p_at_3_equals_1":float(np.mean(p3 == 1.0)),
                "fraction_same_nominal_top3_set":float(np.mean(same_set)),
                "fraction_same_nominal_top3_order":float(np.mean(same_order)),
            })

            for ridx,role in enumerate(GT_ORDER):
                vals = rs[:,ridx]
                role_rows.append({
                    "alpha":alpha,
                    "q_fraction_downgraded":q,
                    "beta_downgraded_strength":beta,
                    "role":role,
                    "mean_coverage_percent":100*float(np.mean(vals)),
                    "median_coverage_percent":100*float(np.median(vals)),
                    "p05_coverage_percent":100*float(np.quantile(vals,.05)),
                    "p95_coverage_percent":100*float(np.quantile(vals,.95)),
                    "min_coverage_percent":100*float(np.min(vals)),
                    "max_coverage_percent":100*float(np.max(vals)),
                })

scenario_df = pd.DataFrame(scenario_rows)
role_df = pd.DataFrame(role_rows)
alpha_df = pd.DataFrame(alpha_rows)

alpha_df.to_csv(ROOT/"step3_corrected_alpha_baseline.csv", index=False)
scenario_df.to_csv(ROOT/"step3_joint_sensitivity_scenarios.csv", index=False)
role_df.to_csv(ROOT/"step3_joint_sensitivity_role_coverage.csv", index=False)

selected = [
    (0.5,.25,.75),(1.0,.25,.75),(2.0,.25,.75),
    (1.0,.50,.75),(1.0,.25,.50),(2.0,.50,.50)
]
summary = []
for a,q,b in selected:
    summary.append(
        scenario_df[
            (scenario_df.alpha==a) &
            (scenario_df.q_fraction_downgraded==q) &
            (scenario_df.beta_downgraded_strength==b)
        ].iloc[0]
    )
pd.DataFrame(summary).to_csv(
    ROOT/"step3_joint_sensitivity_selected_summary.csv", index=False
)

print("\\nCorrected alpha-only baseline:")
print(alpha_df.to_string(index=False))

print("\\nSelected joint sensitivity scenarios:")
cols = [
    "alpha","q_fraction_downgraded","beta_downgraded_strength",
    "tau_median","tau_p05","fraction_p_at_3_equals_1",
    "fraction_same_nominal_top3_set"
]
print(pd.DataFrame(summary)[cols].to_string(index=False))
