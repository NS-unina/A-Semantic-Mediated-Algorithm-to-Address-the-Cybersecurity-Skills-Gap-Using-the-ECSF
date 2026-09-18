# Reproducibility Package: Syllabus-to-ECSF Mapping via CyBOK

This repository contains the complete source code, datasets, and baseline implementations necessary to independently reproduce the workflow, evaluation metrics, and comparative analyses presented in our manuscript.

## Environment Requirements
The pipeline relies on Python 3.x. The required dependencies can be installed via the provided requirements list:
- `scikit-learn` (v1.8.0 or compatible)
- `matplotlib` (v3.10.9 or compatible)
- `seaborn` (v0.13.2 or compatible)
- `sentence-transformers` (v5.5.0 or compatible)

The semantic matching processes utilize the `all-mpnet-base-v2` pre-trained model for generating contextual embeddings.

## Repository Structure and Workflow

### 1. Data and Ground-Truth
- **`Report_Completo_Check(1).xlsx`**: Contains the complete report of the survey results submitted by the students, including the evaluation values expressed in percentages. This file serves as part of the ground-truth construction for bias assessment.

### 2. Baseline Implementations
- **`CSCAM/`**: Contains the source code for the reimplementation of the CSCAM baseline approach, alongside scripts to generate comparative results based on the Network Security (NS) syllabus.
- **`DYCSCOM/`**: Contains the reimplementation of the DYCSCOM baseline and its corresponding execution scripts for performance comparison.

### 3. Core Analysis Scripts
- **`compute_ns_coverage.py`**: Computes the coverage of professional profiles derived from the NS course. The script integrates data from both the student survey and the expert calibration phases.
- **`assess_student_bias.py`**: Executes the Student vs. Expert Bias Analysis, quantifying discrepancies between perceived student competencies and expert ground-truth mapping.

### 4. Validation and Metrics
- **`cybok_validation/semanticSimilarity/`**: Contains the pipeline for Semantic Gap Analysis using CyBOK as an intermediate layer. The script loads the `all-mpnet-base-v2` model and computes distance metrics. Its standard output generates a comparative table across various topics (e.g., Principles & Arch., Wireless Security, Malware Taxonomy), explicitly calculating:
  - **CyBOK Dist**: Semantic distance using the CyBOK intermediate layer.
  - **ECSF Dist**: Standard ECSF semantic distance.
  - **DELTA**: The quantifiable advantage (or gap) introduced by the CyBOK augmentation.
- **`baseline_comparison/`**: Consolidates the outputs from our proposed approach and the baselines. Includes statistical analysis scripts to compute all evaluation metrics and generate the plots and statistical tables reported in the paper.

## Execution
To replicate the core semantic gap analysis:
1. Ensure the virtual environment is active and requirements are installed.
2. Navigate to `cybok_validation/semanticSimilarity/`.
3. Execute the analysis script to load the `all-mpnet-base-v2` weights and generate the DELTA comparison table.