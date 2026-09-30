#!/usr/bin/env python3
from pathlib import Path
import json,pandas as pd,seaborn as sns,matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; G=ROOT/'results'/'generated'; B=ROOT/'results'/'reference'/'baselines'; F=G/'figures'; F.mkdir(parents=True,exist_ok=True)
files={G/'ns_survey_coverage_result.json':'Student (Raw Survey)',G/'ns_survey_coverage_result_expert.json':'Expert (Ground Truth)',G/'ns_coverage_result.json':'CyBOK (Our Approach)',B/'CSCAM.json':'CSCAM (Baseline 1)',B/'DYCSCOM.json':'DyCSCOM (Baseline 2)'}
data={}
for p,l in files.items():
 if not p.exists(): raise FileNotFoundError(p)
 data[l]=json.loads(p.read_text())
df=pd.DataFrame(data).sort_values('Expert (Ground Truth)',ascending=False); norm=df.copy()
for c in norm:
 lo,hi=norm[c].min(),norm[c].max(); norm[c]=0 if hi==lo else (norm[c]-lo)/(hi-lo)
fig,ax=plt.subplots(figsize=(10,8)); sns.heatmap(norm,annot=df,fmt='.1f',cmap='Blues',cbar=False,linewidths=.2,linecolor='#333333',ax=ax); ax.xaxis.tick_top(); plt.xticks(rotation=45,ha='left'); plt.xlabel(''); plt.ylabel(''); fig.tight_layout(); fig.savefig(F/'Heatmap_comparison.pdf',bbox_inches='tight'); fig.savefig(F/'Heatmap_comparison.png',dpi=300,bbox_inches='tight')
