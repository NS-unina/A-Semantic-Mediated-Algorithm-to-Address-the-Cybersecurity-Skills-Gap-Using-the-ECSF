#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RES = ROOT / "results" / "generated"
RES.mkdir(parents=True, exist_ok=True)

CFG = json.loads((ROOT / "config" / "parameters.json").read_text(encoding="utf-8"))

nodes = pd.read_csv(DATA / "mappings" / "cybok_nodes.csv")
links = pd.read_csv(DATA / "mappings" / "cybok_to_ecsf.csv").dropna(subset=["ecsf_knowledge"])

alpha = float(CFG["nominal"]["alpha"])
m = float(CFG["nominal"]["m"])

# Compute syllabus -> ECSF knowledge weights from the finalized CyBOK mapping.
node_score = {
    row.mapping_id: m * (float(row.normalized_depth) ** alpha)
    for row in nodes.itertuples()
}

weights = {}
for row in links.itertuples():
    score = node_score[row.mapping_id]
    weights[row.ecsf_knowledge] = max(weights.get(row.ecsf_knowledge, 0.0), score)

pd.DataFrame(
    sorted(weights.items()),
    columns=["ecsf_knowledge", "score"],
).to_csv(RES / "ns_course_knowledge_weights.csv", index=False)


def load_scores(path):
    df = pd.read_csv(path)
    return dict(zip(df["ecsf_knowledge"], df["score"].astype(float)))


def coverage(scores, profiles):
    return {
        role: 100.0 * sum(scores.get(k, 0.0) for k in required) / len(required)
        for role, required in profiles.items()
    }


# IMPORTANT: one canonical ECSF profile definition is used for every method.
profiles = json.loads((DATA / "ecsf" / "profiles.json").read_text(encoding="utf-8"))

student = load_scores(DATA / "ground_truth" / "student_knowledge_scores.csv")
expert = load_scores(DATA / "ground_truth" / "expert_calibrated_knowledge_scores.csv")

outputs = {
    "ns_coverage_result.json": coverage(weights, profiles),
    "ns_survey_coverage_result.json": coverage(student, profiles),
    "ns_survey_coverage_result_expert.json": coverage(expert, profiles),
}

for name, obj in outputs.items():
    (RES / name).write_text(
        json.dumps(obj, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    print(name)
    print(json.dumps(obj, indent=2, ensure_ascii=False))
