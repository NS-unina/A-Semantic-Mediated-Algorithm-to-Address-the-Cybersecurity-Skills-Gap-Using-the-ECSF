# Mapping artifacts

These files are machine-readable transcriptions of the finalized mapping artifacts in `docs/course_mapping_methodology.docx`.

- `syllabus_to_cybok.csv`: 39 syllabus-concept -> CyBOK-path associations covering the 25 extracted concepts. The nominal revised mapping state is recorded as `Specific` (`m=1`).
- `cybok_augmentation.csv`: the three additions explicitly documented in the supplied methodology: Secure Shell (SSH), WebRTC Security, and VoIP Networks.
- `cybok_nodes.csv`: K1-K34 with the normalized hierarchical depth used by the scoring procedure.
- `cybok_to_ecsf.csv`: CyBOK-node -> ECSF-knowledge associations. K30 has no ECSF association and therefore contributes nothing downstream.
- `knowledge_aggregation_document.csv`: direct transcription of the aggregation table in the methodology document, retained for auditing. The executable pipeline does **not** use this table as input; it recomputes aggregation from `cybok_nodes.csv` and `cybok_to_ecsf.csv` using MAX, which prevents manual transcription from becoming an implicit computational dependency.

The syllabus-to-CyBOK stage is human-guided. These files reproduce the finalized annotations used by the study; they do not claim to automatically reproduce the human judgment that created them.
