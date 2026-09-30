# ECSF profile definitions

`profiles.json` is the single canonical ECSF profile definition used by every
downstream computation in this reproducibility package.

In particular, **Digital Forensics Investigator** contains 13 knowledge items,
including both `Cyber threats` and `Computer networks security`.

This same profile definition is used consistently for:
- the proposed CyBOK-mediated method;
- student-derived profile coverage;
- expert-calibrated ground-truth profile coverage;
- ranking/evaluation metrics;
- sensitivity analysis.

This removes the historical inconsistency in which Student/Expert coverage used
a 12-item Digital Forensics Investigator profile while the corrected proposed
method used the 13-item definition.
