#!/usr/bin/env python3
from pathlib import Path
import json,textwrap,numpy as np,matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; G=ROOT/'results'/'generated'; F=G/'figures'; F.mkdir(parents=True,exist_ok=True); p=G/'ns_coverage_result.json'
if not p.exists(): raise FileNotFoundError(p)
data=json.loads(p.read_text()); cats=list(data); vals=[data[k] for k in cats]; ang=np.linspace(0,2*np.pi,len(cats),endpoint=False).tolist(); ang+=ang[:1]; vals+=vals[:1]
fig,ax=plt.subplots(figsize=(11,11),subplot_kw={'projection':'polar'}); ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1); ax.set_xticks(ang[:-1]); ax.set_xticklabels(['\n'.join(textwrap.wrap(x,22)) for x in cats],fontsize=8); ax.tick_params(axis='x',pad=30); ax.set_ylim(0,100); ax.set_yticks([20,40,60,80]); ax.plot(ang,vals,linewidth=1.7); ax.fill(ang,vals,alpha=.08); fig.tight_layout(); fig.savefig(F/'radar_chart_Q1_NS.pdf',bbox_inches='tight'); fig.savefig(F/'radar_chart_Q1_NS.png',dpi=600,bbox_inches='tight')
