import json
import numpy as np
from scipy.stats import kendalltau

with open('ns_survey_coverage_result_expert.json', 'r') as f:
    survey_data = json.load(f)

with open('ns_coverage_result.json', 'r') as f:
    our_method_data = json.load(f)

with open('DYCSCOM.json', 'r') as f:
    dycscom_data = json.load(f)

with open('CSCAM.json', 'r') as f:
    cscom_data = json.load(f)

sorted_keys = sorted(survey_data.keys())
gt_values = np.array([survey_data[key] for key in sorted_keys])
our_values = np.array([our_method_data[key] for key in sorted_keys])
cscom_values = np.array([cscom_data[key] for key in sorted_keys])
dycscom_values = np.array([dycscom_data[key] for key in sorted_keys])

def get_bootstrap_ci(gt_vals, comp_vals, n_boot=5000):
    taus = []
    n = len(gt_vals)
    for _ in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        tau, _ = kendalltau(gt_vals[idx], comp_vals[idx])
        if not np.isnan(tau):
            taus.append(tau)
    return np.percentile(taus, 2.5), np.percentile(taus, 97.5)

np.random.seed(42)
our_ci = get_bootstrap_ci(gt_values, our_values)
cscom_ci = get_bootstrap_ci(gt_values, cscom_values)
dycscom_ci = get_bootstrap_ci(gt_values, dycscom_values)

print(f"Our Approach (CyBOK): {our_ci}")
print(f"CSCAM (Baseline 1): {cscom_ci}")
print(f"DyCSCOM (Baseline 2): {dycscom_ci}")