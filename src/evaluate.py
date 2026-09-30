#!/usr/bin/env python3
from pathlib import Path
import json, numpy as np, pandas as pd
from scipy.stats import kendalltau
ROOT=Path(__file__).resolve().parents[1]; G=ROOT/'results'/'generated'; R=ROOT/'results'/'reference'/'baselines'
def load(p): return json.loads(p.read_text())
methods={'Ground Truth (Expert)':load(G/'ns_survey_coverage_result_expert.json'),'Our Approach (CyBOK)':load(G/'ns_coverage_result.json'),'CSCAM (Baseline 1)':load(R/'CSCAM.json'),'DyCSCOM (Baseline 2)':load(R/'DYCSCOM.json')}
gt=methods['Ground Truth (Expert)']; keys=sorted(gt); gtv=np.array([gt[k] for k in keys]); gt_top=set(sorted(gt,key=gt.get,reverse=True)[:3])
rng=np.random.RandomState(42)
def ci(comp,nboot=5000):
 vals=[]; n=len(gtv)
 for _ in range(nboot):
  idx=rng.choice(n,n,replace=True); tau,_=kendalltau(gtv[idx],comp[idx])
  if not np.isnan(tau): vals.append(tau)
 return np.percentile(vals,[2.5,97.5])
rows=[]
for name,data in methods.items():
 if name.startswith('Ground Truth'): continue
 cv=np.array([data[k] for k in keys]); tau,p=kendalltau(gtv,cv); lo,hi=ci(cv); top=set(sorted(data,key=data.get,reverse=True)[:3])
 rows.append({'method':name,'P@3':len(gt_top&top)/3,'kendall_tau':tau,'ci95_low':lo,'ci95_high':hi,'p_value':p})
pd.DataFrame(rows).to_csv(G/'evaluation_metrics.csv',index=False)
# ranking table
scores=pd.DataFrame(methods); ranks=scores.rank(ascending=False,method='min').astype(int); out=[]
for role in scores.index:
 row={'role':role}
 for m in scores.columns: row[m+'__score']=scores.loc[role,m]; row[m+'__rank']=ranks.loc[role,m]
 out.append(row)
pd.DataFrame(out).to_csv(G/'role_rankings.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
