import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import textwrap
import os

FILES_CONFIG = [
    {
        "filename": "ns_survey_coverage_result.json",
        "label": "Survey (Target)",
        "color": "#d62728",       
        "linestyle": "--",        
        "fill_alpha": 0.05,
        "is_target": True         
    },
    {
        "filename": "ns_coverage_result.json",
        "label": "Our Methodology",
        "color": "#1f77b4",       
        "linestyle": "-",         
        "fill_alpha": 0.1,
        "is_target": False
    },
    {
        "filename": "DYCSCOM.json",
        "label": "DYCSCOM",
        "color": "#2ca02c",       
        "linestyle": "-.",        
        "fill_alpha": 0.1,
        "is_target": False
    },
    {
        "filename": "CSCOM.json",
        "label": "CSCOM",
        "color": "#60e0f1",      
        "linestyle": ":",         
        "fill_alpha": 0.1,
        "is_target": False
    }
]


plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 12,
    "legend.fontsize": 9,
    "mathtext.fontset": "stix"
})




def load_and_merge_data(config_list):
    dfs = []
    for entry in config_list:
        if not os.path.exists(entry["filename"]):
            print(f" Warning: File {entry['filename']} not found. Skipping.")
            continue
            
        with open(entry["filename"], 'r') as f:
            data = json.load(f)
            
        
        
        s = pd.Series(data, name=entry["label"])
        if s.max() <= 1.0: 
            s = s * 100
            
        dfs.append(s)
    
    if not dfs:
        raise ValueError("Nessun file valido trovato.")
    

    df = pd.concat(dfs, axis=1).fillna(0).sort_index()
    return df

df_data = load_and_merge_data(FILES_CONFIG)

def plot_radar(df, config_list, export_name="radar_comparison_3way"):
    categories = df.index.tolist()
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    def wrap_labels(labels, width=20):
        return ['\n'.join(textwrap.wrap(l, width)) for l in labels]
    
    plt.xticks(angles[:-1], wrap_labels(categories, width=25), size=8)
    ax.tick_params(axis='x', pad=35)
    
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80], ["20", "40", "60", "80"], color="#666666", size=7)
    plt.ylim(0, 100)
    ax.grid(color='#BDC3C7', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.spines['polar'].set_visible(False)
    
    
    for config in config_list:
        label = config["label"]
        if label not in df.columns: continue
        
        values = df[label].tolist()
        values += values[:1]
        
        ax.plot(angles, values, 
                color=config["color"], 
                linewidth=1.5, 
                linestyle=config["linestyle"], 
                label=label)
        
        ax.fill(angles, values, color=config["color"], alpha=config["fill_alpha"])

    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=False)
    
    plt.savefig(f"figs/{export_name}.pdf", format='pdf', bbox_inches='tight')
    plt.savefig(f"figs/{export_name}.png", format='png', dpi=300, bbox_inches='tight')
    print(f"Chart saved as {export_name}.pdf")
    plt.show()

plot_radar(df_data, FILES_CONFIG)


print("\n" + "="*120)
print(f"{'BENCHMARK ANALYSIS (BEST FIT HIGHLIGHTED)':^120}")
print("="*120)

target_col = next((c["label"] for c in FILES_CONFIG if c.get("is_target")), None)

if target_col and target_col in df_data.columns:
    candidate_cols = [c for c in df_data.columns if c != target_col]
    
    
    abs_gaps = pd.DataFrame()
    for cand in candidate_cols:
        abs_gaps[cand] = (df_data[cand] - df_data[target_col]).abs()
    
    best_candidate_per_row = abs_gaps.idxmin(axis=1)

    
    header = f"{'Category':<40} | {target_col[:7]:>7} ||"
    for cand in candidate_cols:
        header += f" {cand[:12]:>12} | {'Gap':>7} ||"
    print(header)
    print("-" * len(header))
    
    for idx, row in df_data.iterrows():
        print(f"{idx:<40} | {row[target_col]:7.1f} ||", end="")
        
        best_cand_name = best_candidate_per_row[idx]
        
        for cand in candidate_cols:
            val = row[cand]
            gap = val - row[target_col]
            
            is_best = (cand == best_cand_name)
            marker = " <<" if is_best else "" 
            
            print(f" {val:12.1f} | {gap:+7.1f}{marker:3} ||", end="")
        print() 

    print("-" * 120)
    print("GLOBAL METRICS (Distance from Survey - Lower is Better):")
    
    for cand in candidate_cols:
        gap_series = df_data[cand] - df_data[target_col]
        mae = gap_series.abs().mean()
        rmse = np.sqrt((gap_series ** 2).mean())
        print(f" > {cand}: MAE = {mae:.2f}, RMSE = {rmse:.2f}")

    
    df_latex = pd.DataFrame(index=df_data.index)
    
    df_latex[target_col] = df_data[target_col].apply(lambda x: f"{x:.1f}")
    
    for cand in candidate_cols:
        col_val_name = f"{cand} (Val)"
        col_gap_name = f"{cand} (Gap)"
        
        latex_vals = []
        latex_gaps = []
        
        for idx, val in df_data[cand].items():
            gap = val - df_data.loc[idx, target_col]
            
            if cand == best_candidate_per_row[idx]:
                gap_str = f"\\textbf{{{gap:+.1f}}}" 
            else:
                gap_str = f"{gap:+.1f}"
            
            latex_vals.append(f"{val:.1f}")
            latex_gaps.append(gap_str)
            
        df_latex[col_val_name] = latex_vals
        df_latex[col_gap_name] = latex_gaps

    latex_code = df_latex.to_latex(
        escape=False, 
        caption=f"Comparison against {target_col} (Best alignment in bold)",
        label="tab:comparative_analysis_best"
    )
    
    with open("tables/table_comparison_best.tex", "w") as f:
        f.write(latex_code)
        
    print(f"\n[INFO] LaTeX table with bold highlights exported to 'table_comparison_best.tex'")

else:
    print("Errore: Impossibile identificare la colonna Target.")