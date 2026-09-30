#!/usr/bin/env python3
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'/'ground_truth'; O=ROOT/'results'/'generated'; O.mkdir(parents=True,exist_ok=True)
s=pd.read_csv(D/'student_knowledge_scores.csv').set_index('ecsf_knowledge')['score']
e=pd.read_csv(D/'expert_calibrated_knowledge_scores.csv').set_index('ecsf_knowledge')['score']
common=sorted(set(s.index)&set(e.index)); sv=np.array([s[k]*100 for k in common]); ev=np.array([e[k]*100 for k in common]); diff=sv-ev
W,p=wilcoxon(sv,ev,alternative='greater')
summary={'n_items':len(common),'mean_overestimation_percentage_points':float(diff.mean()),'sd_percentage_points':float(diff.std(ddof=1)),'wilcoxon_W':float(W),'wilcoxon_p_one_sided_greater':float(p)}
(O/'student_bias_summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
