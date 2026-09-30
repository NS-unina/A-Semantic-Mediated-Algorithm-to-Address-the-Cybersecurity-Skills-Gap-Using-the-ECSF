#!/usr/bin/env python3
from pathlib import Path
import json, numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; G=ROOT/'results'/'generated'; O=G/'sensitivity'; O.mkdir(parents=True,exist_ok=True)
CFG=json.loads((ROOT/'config'/'parameters.json').read_text()); nodes=pd.read_csv(D/'mappings'/'cybok_nodes.csv'); links=pd.read_csv(D/'mappings'/'cybok_to_ecsf.csv').dropna(subset=['ecsf_knowledge'])
profiles=json.loads((D/'ecsf'/'profiles.json').read_text()); gt=json.loads((G/'ns_survey_coverage_result_expert.json').read_text())
gt_order=sorted(gt,key=gt.get,reverse=True); gt_top3=set(gt_order[:3]); role_names=gt_order
active=[x for x in nodes.mapping_id if len(links[links.mapping_id==x])>0]; depth=np.array([float(nodes.loc[nodes.mapping_id==x,'normalized_depth'].iloc[0]) for x in active])
knowledge=sorted(set(links.ecsf_knowledge)); ki={k:i for i,k in enumerate(knowledge)}; kn=[]
for k in knowledge: kn.append(np.array([i for i,n in enumerate(active) if k in set(links.loc[links.mapping_id==n,'ecsf_knowledge'])],dtype=int))
rm=np.zeros((len(role_names),len(knowledge)))
for ri,r in enumerate(role_names):
 for k in profiles[r]:
  if k in ki: rm[ri,ki[k]]=1/len(profiles[r])
pi,pj=np.triu_indices(len(role_names),k=1); N=len(pi)
def scores(ns):
 kw=np.zeros((ns.shape[0],len(knowledge)))
 for j,idx in enumerate(kn):
  if len(idx): kw[:,j]=ns[:,idx].max(axis=1)
 return kw@rm.T
def tau(s):
 d=s[:,pi]-s[:,pj]; c=(d>1e-12).sum(1); dis=(d<-1e-12).sum(1); comp=c+dis; den=np.sqrt(N*comp); out=np.full(len(s),np.nan); ok=den>0; out[ok]=(c[ok]-dis[ok])/den[ok]; return out
def top3(s): return np.argsort(-s,axis=1,kind='stable')[:,:3]
GT3={0,1,2}; alphas=CFG['sensitivity']['alpha']; betas=CFG['sensitivity']['beta']; qs=CFG['sensitivity']['q']; samples=CFG['sensitivity']['samples']; seed=CFG['sensitivity']['seed']
# alpha-only
ar=[]
for a in alphas:
 s=scores((depth**a)[None,:]); t=tau(s)[0]; order=top3(s)[0]
 ar.append({'alpha':a,'kendall_tau':t,'p_at_3':len(set(order)&GT3)/3,'top_1':role_names[order[0]],'top_2':role_names[order[1]],'top_3':role_names[order[2]],'penetration_tester_percent':100*s[0,role_names.index('Penetration Tester')],'implementer_percent':100*s[0,role_names.index('Cybersecurity Implementer')],'cti_percent':100*s[0,role_names.index('Cyber Threat Intelligence Specialist')],'digital_forensics_percent':100*s[0,role_names.index('Digital Forensics Investigator')]})
pd.DataFrame(ar).to_csv(O/'alpha_baseline.csv',index=False)
# paired masks
rng=np.random.default_rng(seed); masks={}
for q in qs:
 n=len(active) if q==1 else max(1,round(q*len(active)))
 if n==len(active): mask=np.ones((1,len(active)),dtype=bool)
 else:
  mask=np.zeros((samples,len(active)),dtype=bool)
  for z in range(samples): mask[z,rng.choice(len(active),size=n,replace=False)]=True
 masks[q]=(n,mask)
nom=scores((depth**1.0)[None,:])[0]; nom3=top3(nom[None,:])[0]; nomset=set(nom3.tolist())
rows=[]
for a in alphas:
 base=depth**a
 for q in qs:
  n,mask=masks[q]
  for b in betas:
   s=scores(np.where(mask,b,1.0)*base[None,:]); ts=tau(s); t3=top3(s); p3=np.array([len(set(x)&GT3)/3 for x in t3]); same=np.array([set(x)==nomset for x in t3]); order=np.all(t3==nom3[None,:],axis=1); valid=ts[~np.isnan(ts)]; deg=len(valid)==0
   rows.append({'alpha':a,'q_reclassified_specific_to_conceptual':q,'n_reclassified_mappings':n,'beta_conceptual_weight':b,'samples':len(s),'tau_mean':np.nan if deg else valid.mean(),'tau_median':np.nan if deg else np.median(valid),'tau_p05':np.nan if deg else np.quantile(valid,.05),'tau_p95':np.nan if deg else np.quantile(valid,.95),'fraction_Pat3_equals_1':np.nan if deg else np.mean(p3==1),'fraction_same_nominal_top3_set':np.nan if deg else np.mean(same),'fraction_same_nominal_top3_order':np.nan if deg else np.mean(order),'status':'degenerate_all_mappings_removed' if deg else 'valid'})
df=pd.DataFrame(rows); df.to_csv(O/'joint_sensitivity.csv',index=False)
selected=[(.5,.25,.75),(1,.25,.75),(2,.25,.75),(1,.50,.75),(1,.25,.50),(2,.50,.50)]
pd.DataFrame([df[(df.alpha==a)&(df.q_reclassified_specific_to_conceptual==q)&(df.beta_conceptual_weight==b)].iloc[0] for a,q,b in selected]).to_csv(O/'selected_scenarios.csv',index=False)
print('Wrote',O)
