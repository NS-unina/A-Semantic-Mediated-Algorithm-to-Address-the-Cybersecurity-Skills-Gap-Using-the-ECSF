import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.colors as mcolors


plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['figure.dpi'] = 300
plt.rcParams['axes.grid'] = False 

# caricamento dati
filenames = {
    "ns_survey_coverage_result.json":        "Student (Raw Survey)",
    "ns_survey_coverage_result_expert.json": "Expert (Ground Truth)",
    "ns_coverage_result.json":               "CyBOK (Our Approach)", # Nome breve e tecnico
    "CSCOM.json":                            "CSCAM (Baseline 1)",
    "DYCSCOM.json":                          "DyCSCOM (Baseline 2)"
}

def load_data_rigorous(file_map):
    data = {}
    for fname, label in file_map.items():
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                raw = json.load(f)
                clean_dict = {
                    k.replace("Cybersecurity ", "").replace("Chief Information Security Officer (CISO)", "CISO").split(" (")[0]: v 
                    for k,v in raw.items()
                }
                data[label] = clean_dict
        else:
            print(f"[WARNING] Missing {fname}, generating placeholder data.")
            roles = ["Pentester", "Implementer", "Threat Intel", "Responder", "Risk Mgr", "Architect", "Forensics", "Researcher", "Educator", "Legal", "CISO", "Auditor"]
            scale = 5 if "DyCSCOM" in label else 100
            np.random.seed(42) 
            data[label] = {r: np.random.randint(0, scale) for r in roles}
    return pd.DataFrame(data)

df = load_data_rigorous(filenames)


if "Expert (Ground Truth)" in df.columns:
    df_sorted = df.sort_values("Expert (Ground Truth)", ascending=False)
else:
    df_sorted = df

col_order = [
    "Student (Raw Survey)", 
    "Expert (Ground Truth)", 
    "CyBOK (Our Approach)", 
    "CSCAM (Baseline 1)", 
    "DyCSCOM (Baseline 2)"
]
final_cols = [c for c in col_order if c in df_sorted.columns]
df_final = df_sorted[final_cols]


def plot_rigorous_matrix():
    df_norm = df_final.copy()
    for col in df_norm.columns:
        max_val = df_norm[col].max()
        min_val = df_norm[col].min()
        if max_val > min_val:
            df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)
        else:
            df_norm[col] = 0 

    
    fig, ax = plt.subplots(figsize=(10, 8)) 
    
    # Heatmap
    sns.heatmap(df_norm, 
                annot=df_final,      
                fmt=".1f",           
                cmap="Blues",        
                cbar=False,          
                linewidths=0.2,      
                linecolor="#333333",   
                annot_kws={"size": 11, "weight": "medium", "fontfamily": "serif"},
                ax=ax)

    
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    
    plt.xticks(rotation=45, ha='left', fontsize=11, fontweight='bold') 
    plt.yticks(fontsize=11)
    plt.xlabel("") 
    plt.ylabel("")

    # plt.title(
    #     r"$\bf{Comparative\ Relevance\ Density\ Matrix}$" + "\n" +
    #     r"Color intensity denotes column-normalized relative importance ($I_{rel} \in [0,1]$)." + "\n" +
    #     r"Annotated values represent absolute raw scores ($S_{raw}$)." + "\n",
    #     loc='left', fontsize=10, pad=20
    # )
    
    
    ax.axhline(y=0, color='k', linewidth=2)
    ax.axhline(y=df_final.shape[0], color='k', linewidth=2)
    
    plt.tight_layout()
    plt.savefig("figs/Heatmap_comparison.pdf", format='pdf', bbox_inches='tight')
    plt.savefig("figs/Heatmap_comparison.png", dpi=300, bbox_inches='tight')
    print("Generated: Heatmap_comparison.pdf (Vector) & .png (Raster)")

if __name__ == "__main__":
    plot_rigorous_matrix()