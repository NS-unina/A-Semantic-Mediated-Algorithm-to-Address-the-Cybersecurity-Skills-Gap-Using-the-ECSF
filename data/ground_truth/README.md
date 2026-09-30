# Ground-truth artifacts

`student_knowledge_scores.csv` and `expert_calibrated_knowledge_scores.csv` are the knowledge-level values hard-coded in the supplied analysis and used to construct the reported Student/Expert role coverage. The expert-calibrated values are the final output of a human calibration stage; they are not an automated transformation of the raw workbook.

The raw survey workbook is retained in `raw/student_survey_summary.xlsx`. Because individual pre-consensus expert judgments were not retained, the original expert-consensus process cannot be statistically reconstructed retrospectively; this limitation is documented in the manuscript.


## Digital Forensics Investigator consistency

Profile-level Student and Expert coverage is recomputed from the knowledge-level
scores using the same canonical 13-item Digital Forensics Investigator profile
stored in `../ecsf/profiles.json`. The resulting DFI scores are 59.4231% for the
student-derived coverage and 44.2308% for the expert-calibrated ground truth.
