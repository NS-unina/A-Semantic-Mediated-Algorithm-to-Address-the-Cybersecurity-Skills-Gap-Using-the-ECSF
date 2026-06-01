import json
import pandas as pd
import numpy as np
# from scipy.stats import spearmanr
from scipy.stats import kendalltau

with open('ns_survey_coverage_result_expert.json', 'r') as f:
    survey_data = json.load(f)

with open('ns_coverage_result.json', 'r') as f:
    our_method_data = json.load(f)


with open('DYCSCOM.json', 'r') as f:
    dycscom_data = json.load(f)

with open('CSCOM.json', 'r') as f:
            cscom_data = json.load(f)


methods = {
    "Ground Truth (Expert)": survey_data,
    "Our Approach (CyBOK)": our_method_data,
    "CSCAM (Baseline 1)": cscom_data,
    "DyCSCOM (Baseline 2)": dycscom_data
}

def create_ranking_dataframe(methods_dict):

    df = pd.DataFrame(methods_dict)
    
    ranks_df = df.rank(ascending=False, method='min').astype(int)
    
    display_df = pd.DataFrame()
    for col in df.columns:
        display_df[col] = ranks_df[col].astype(str) + " (" + df[col].round(1).astype(str) + ")"
    
    display_df = display_df.sort_values(by="Ground Truth (Expert)", key=lambda col: ranks_df["Ground Truth (Expert)"])
    
    return ranks_df, display_df

ranks_df, ranking_table_display = create_ranking_dataframe(methods)

def calculate_metrics_table(gt_data, comparators, k=3):
    results = []
    
    sorted_keys = sorted(gt_data.keys())
    gt_values = [gt_data[key] for key in sorted_keys]
    gt_top_k_roles = set(sorted(gt_data, key=gt_data.get, reverse=True)[:k])

    for name, data in comparators.items():
        if name == "Ground Truth (Expert)": continue 
            
        # Spearman
        comp_values = [data.get(key, 0.0) for key in sorted_keys]
        # rho, p_value = spearmanr(gt_values, comp_values)
        tau, tau_p = kendalltau(gt_values, comp_values)
        
        # P@K
        method_top_k_roles = set(sorted(data, key=data.get, reverse=True)[:k])
        intersection = gt_top_k_roles.intersection(method_top_k_roles)
        p_at_k = len(intersection) / k
        
        results.append({
            "Methodology": name,
            f"P@{k} (Top-{k})": p_at_k,
            "Kendall's tau": tau,
            "p-value": tau_p
        })
        
    return pd.DataFrame(results)

metrics_df = calculate_metrics_table(survey_data, methods, k=3)

print("--- METRICS TABLE (DataFrame) ---")
print(metrics_df)

print("\n" + "="*40)
print(" LATEX CODE: METRICS TABLE ")
print("="*40)
print(metrics_df.to_latex(
    index=False, 
    float_format="%.3f",
    caption=f"Comparative Performance Metrics. P@3 measures alignment on the top-3 core roles. Kendall's $\\tau$ quantifies global ranking correlation.",
    label="tab:metrics"
))

print("\n" + "="*40)
print(" LATEX CODE: RANKING COMPARISON (CORRECTED) ")
print("="*40)


latex_ranks = ranking_table_display.to_latex(
    caption="Detailed Role Ranking Comparison. Format: Rank (Score).",
    label="tab:rankings"
)
print(latex_ranks)