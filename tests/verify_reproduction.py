#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

subprocess.run(
    [sys.executable, str(ROOT / "src" / "compute_ns_coverage.py")],
    check=True,
    cwd=ROOT,
)
subprocess.run(
    [sys.executable, str(ROOT / "src" / "evaluate.py")],
    check=True,
    cwd=ROOT,
)

G = ROOT / "results" / "generated"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

ours = load(G / "ns_coverage_result.json")
student = load(G / "ns_survey_coverage_result.json")
expert = load(G / "ns_survey_coverage_result_expert.json")

assert abs(ours["Digital Forensics Investigator"] - 41.07692307692308) < 1e-10
assert abs(student["Digital Forensics Investigator"] - 59.42307692307692) < 1e-10
assert abs(expert["Digital Forensics Investigator"] - 44.23076923076923) < 1e-10

metrics = pd.read_csv(G / "evaluation_metrics.csv").set_index("method")
assert abs(metrics.loc["Our Approach (CyBOK)", "P@3"] - 1.0) < 1e-12
assert abs(
    metrics.loc["Our Approach (CyBOK)", "kendall_tau"]
    - 0.8308675641104959
) < 1e-12
assert abs(
    metrics.loc["Our Approach (CyBOK)", "ci95_low"]
    - 0.5789473684210525
) < 1e-12
assert abs(
    metrics.loc["Our Approach (CyBOK)", "ci95_high"]
    - 0.9999999999999999
) < 1e-12

print("Uniform 13-item DFI reproduction: PASS")
