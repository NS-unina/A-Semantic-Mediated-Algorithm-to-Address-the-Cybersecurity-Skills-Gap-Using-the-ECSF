#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent
for rel in ['src/compute_ns_coverage.py','src/assess_student_bias.py','src/evaluate.py','src/sensitivity_analysis.py','src/figures/plot_radar.py','src/figures/plot_comparison.py','src/figures/plot_sensitivity.py']:
 print('\n===',rel,'==='); subprocess.run([sys.executable,str(ROOT/rel)],check=True,cwd=ROOT)
print('\nCore reproduction completed. Semantic validation and baseline notebooks are run separately; see README.md.')
