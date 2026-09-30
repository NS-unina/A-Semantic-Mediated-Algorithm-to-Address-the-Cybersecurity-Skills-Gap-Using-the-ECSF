# Reproducibility Package: CyBOK-Mediated Syllabus-to-ECSF Mapping

This repository is a cleaned, provenance-oriented release candidate for the Network Security case study. It separates **human-guided mapping/calibration artifacts** from **automated computation**, so an independent researcher can inspect every input used by the reported calculations.

> **Before public release:** read `docs/REPRODUCIBILITY_AUDIT.md`. One profile-definition inconsistency inherited from the current manuscript/repository must still be reconciled.

## Repository structure

```text
config/                     final parameter grids and seeds
data/
  syllabus/                 syllabus text + 25 extracted concepts
  mappings/                 syllabus->CyBOK, augmentation, CyBOK->ECSF, node depth
  ecsf/                     ECSF knowledge + explicit profile definitions
  ground_truth/             raw survey + Student/Expert knowledge-level artifacts
baselines/                  CSCAM and DyCSCOM reimplementation notebooks
validation/                 semantic-similarity validation (script + original notebook)
src/                        canonical automated analysis
  figures/                  paper figure generation
results/reference/          supplied reference outputs
results/generated/          outputs from a fresh run
docs/                       methodology source, audit, migration notes
```

## 1. Environment

Python 3.10+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The SentenceTransformer validation downloads `all-mpnet-base-v2` on first use unless it is already cached.

## 2. Human-guided mapping artifacts

The mapping itself is **not presented as an automated NLP classifier**. The supplied methodology defines a human-guided process. To make that process reproducible/inspectable, its finalized outputs are provided as data:

1. `data/syllabus/network_security_syllabus.txt` — Course Contents/Programme used in the case study.
2. `data/syllabus/extracted_concepts.csv` — 25 concepts C1-C25.
3. `data/mappings/syllabus_to_cybok.csv` — finalized syllabus-to-CyBOK associations.
4. `data/mappings/cybok_augmentation.csv` — the three additions explicitly documented in the methodology: SSH, WebRTC Security, and VoIP Networks.
5. `data/mappings/cybok_nodes.csv` — K1-K34 with normalized depth.
6. `data/mappings/cybok_to_ecsf.csv` — static CyBOK-to-ECSF knowledge associations.

The original methodology document is retained in `docs/course_mapping_methodology.docx`.

All accepted case-study mappings use the nominal Specific state (`m=1`) under the revised formulation.

## 3. Ground truth

The raw student survey summary is in `data/ground_truth/raw/`. The processed Student knowledge scores and final expert-calibrated knowledge scores used by the analysis are explicit CSV files. The expert calibration is a human-consensus stage, so its finalized output is treated as an input artifact for downstream reproducibility.

## 4. Core automated reproduction

Run:

```bash
python src/compute_ns_coverage.py
python src/assess_student_bias.py
python src/evaluate.py
python src/sensitivity_analysis.py
```

`compute_ns_coverage.py` no longer reads a manually hard-coded `K_NS`. It reconstructs the Network Security ECSF knowledge weights from `cybok_nodes.csv` + `cybok_to_ecsf.csv`, applies the nominal `m=1, alpha=1` scoring, uses MAX aggregation, and then computes role coverage.

Generated files are written to `results/generated/`.

## 5. Parameter sensitivity

The final Option-A analysis is consolidated in a single script. Parameters are centralized in `config/parameters.json`:

- alpha: `{0, 0.5, 1, 2, 3}`
- beta: `{0, 0.25, 0.50, 0.75, 1}`
- q: `{0.10, 0.25, 0.50, 0.75, 1.00}`
- 5,000 Monte Carlo samples for stochastic scenarios
- seed `20260921`

`q` is a stress-test parameter, not an algorithm parameter.

## 6. Baselines

The supplied CSCAM and DyCSCOM reimplementations are retained unchanged in `baselines/`. Their reference outputs are in `results/reference/baselines/`. Execute each notebook top-to-bottom in a clean environment to regenerate its output.

## 7. Semantic-gap validation

The original notebook is retained unchanged at `validation/notebooks/semanticSimilarity.ipynb`. A canonical executable version is provided as `validation/semantic_similarity.py`, with the experiment cases separated into `validation/data/semantic_similarity_cases.json`.

Run:

```bash
python validation/semantic_similarity.py
```

This requires the SentenceTransformer model and therefore may need network access on first execution.

## 8. Figures

After running the core analysis:

```bash
python src/figures/plot_radar.py
python src/figures/plot_comparison.py
python src/figures/plot_sensitivity.py
```

These generate the radar, comparison heatmap, and final sensitivity figures used by the revised analysis. Missing inputs cause an explicit failure; no synthetic placeholder data are generated.

## 9. Verification

Run:

```bash
python tests/verify_reproduction.py
```

The script checks the core generated outputs against the supplied current-manuscript references and verifies the reported P@3/Kendall metrics.

## 10. Provenance vs automation

| Stage | Nature | Reproducibility artifact |
|---|---|---|
| Syllabus selection/preprocessing | Human-defined | syllabus text |
| Concept extraction | Human-guided | `extracted_concepts.csv` |
| Syllabus -> CyBOK | Human-guided | `syllabus_to_cybok.csv` |
| CyBOK augmentation | Human-guided | `cybok_augmentation.csv` |
| CyBOK -> ECSF | Static mapping | `cybok_to_ecsf.csv` |
| Hierarchical scoring/aggregation | Automated | `compute_ns_coverage.py` |
| Ground-truth calibration | Human consensus | expert-calibrated CSV |
| Role coverage | Automated | `compute_ns_coverage.py` |
| Metrics/bootstrap | Automated | `evaluate.py` |
| Sensitivity | Automated | `sensitivity_analysis.py` |
| Baselines | Automated notebooks | `baselines/` |
| Semantic-gap validation | Automated | `validation/semantic_similarity.py` |

## Digital Forensics Investigator consistency

All coverage computations use the single canonical ECSF profile file
`data/ecsf/profiles.json`. Digital Forensics Investigator contains 13 knowledge
items, including `Cyber threats`; therefore Proposed, Student and Expert
coverage are evaluated against the same denominator.

## Canonical DFI profile

All computations use `data/ecsf/profiles.json`. The Digital Forensics
Investigator profile contains 13 ECSF knowledge items, including `Cyber threats`.
The same definition is used for the proposed method, Student coverage, Expert
Ground Truth, evaluation metrics, and sensitivity analysis.
