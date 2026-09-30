#!/usr/bin/env python3
"""
Reproduce the semantic-gap validation experiment and regenerate both figures
used in the manuscript.

Inputs
------
validation/data/semantic_similarity_cases.json

Outputs
-------
results/generated/semantic_similarity/semantic_similarity_results.csv
results/generated/semantic_similarity/statistics.json
results/generated/figures/Fig1_GapAnalysis_Zones.pdf
results/generated/figures/Fig1_GapAnalysis_Zones.png
results/generated/figures/Fig2_Sensitivity_Explicit.pdf
results/generated/figures/Fig2_Sensitivity_Explicit.png
"""

from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import wilcoxon, shapiro, skew, kurtosis
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "validation" / "data" / "semantic_similarity_cases.json"
OUT_DIR = ROOT / "results" / "generated" / "semantic_similarity"
FIG_DIR = ROOT / "results" / "generated" / "figures"

OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "all-mpnet-base-v2"

# Make vector-PDF text broadly compatible.
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def save_figure(fig, stem: str) -> None:
    """Save a figure as both PDF and high-resolution PNG."""
    pdf_path = FIG_DIR / f"{stem}.pdf"
    png_path = FIG_DIR / f"{stem}.png"

    fig.savefig(
        pdf_path,
        format="pdf",
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
    )
    fig.savefig(
        png_path,
        format="png",
        dpi=600,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
    )

    # Basic PDF sanity check.
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Empty PDF generated: {pdf_path}")

    with pdf_path.open("rb") as fh:
        if fh.read(4) != b"%PDF":
            raise RuntimeError(f"Invalid PDF header: {pdf_path}")

    print(f"[OK] Generated: {pdf_path}")
    print(f"[OK] Generated: {png_path}")


# ---------------------------------------------------------------------
# Core experiment
# ---------------------------------------------------------------------

if not CASES_FILE.exists():
    raise FileNotFoundError(f"Missing semantic-similarity input file: {CASES_FILE}")

cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

print(f"Loading sentence-transformer model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

rows = []

for item in cases:
    syllabus = item["syllabus_text"]
    cybok_candidates = item["cybok_candidates"]
    ecsf_candidates = item["ecsf_candidates"]

    # Neural representation.
    syllabus_emb = model.encode(syllabus, convert_to_tensor=True)
    cybok_emb = model.encode(cybok_candidates, convert_to_tensor=True)
    ecsf_emb = model.encode(ecsf_candidates, convert_to_tensor=True)

    d_cybok_emb = 1.0 - util.cos_sim(syllabus_emb, cybok_emb).max().item()
    d_ecsf_emb = 1.0 - util.cos_sim(syllabus_emb, ecsf_emb).max().item()

    # TF-IDF representation.
    texts = [syllabus] + cybok_candidates + ecsf_candidates
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
    )
    X = vectorizer.fit_transform(texts)

    syllabus_vec = X[0]
    cybok_vecs = X[1 : 1 + len(cybok_candidates)]
    ecsf_vecs = X[1 + len(cybok_candidates) :]

    d_cybok_tfidf = 1.0 - cosine_similarity(
        syllabus_vec, cybok_vecs
    ).max()

    d_ecsf_tfidf = 1.0 - cosine_similarity(
        syllabus_vec, ecsf_vecs
    ).max()

    rows.append(
        {
            "Topic": item["label"],
            "CyBOK_Emb": float(d_cybok_emb),
            "ECSF_Emb": float(d_ecsf_emb),
            "Gap_Emb": float(d_ecsf_emb - d_cybok_emb),
            "CyBOK_TFIDF": float(d_cybok_tfidf),
            "ECSF_TFIDF": float(d_ecsf_tfidf),
            "Gap_TFIDF": float(d_ecsf_tfidf - d_cybok_tfidf),
        }
    )

df = pd.DataFrame(rows)
df.to_csv(
    OUT_DIR / "semantic_similarity_results.csv",
    index=False,
)

# Statistical tests.
W, p = wilcoxon(
    df["CyBOK_Emb"],
    df["ECSF_Emb"],
    alternative="less",
)

shapiro_W, shapiro_p = shapiro(df["Gap_Emb"])

stats = {
    "n": int(len(df)),
    "cybok_lower_embedding_distance": int((df["Gap_Emb"] > 0).sum()),
    "cybok_lower_tfidf_distance": int((df["Gap_TFIDF"] > 0).sum()),
    "cybok_embedding_distance_below_0_50": int(
        (df["CyBOK_Emb"] < 0.50).sum()
    ),
    "wilcoxon_W": float(W),
    "wilcoxon_p": float(p),
    "gap_skewness": float(skew(df["Gap_Emb"])),
    "gap_kurtosis": float(kurtosis(df["Gap_Emb"])),
    "shapiro_W": float(shapiro_W),
    "shapiro_p": float(shapiro_p),
    "model_name": MODEL_NAME,
    "tfidf_stop_words": "english",
    "tfidf_ngram_range": [1, 2],
}

(OUT_DIR / "statistics.json").write_text(
    json.dumps(stats, indent=2),
    encoding="utf-8",
)

print("\nSemantic-gap statistics:")
print(json.dumps(stats, indent=2))


# ---------------------------------------------------------------------
# Figure 1 — Semantic Gap Analysis
# ---------------------------------------------------------------------

BLUE = "#005b96"
RED = "#d65a5a"

df_sorted = df.sort_values("Gap_Emb", ascending=True).reset_index(drop=True)
y = np.arange(len(df_sorted))

fig1, ax1 = plt.subplots(figsize=(12, 14))

zones = [
    (0.00, 0.25, "green", "EXCELLENT\n(Strong Match)"),
    (0.25, 0.50, "gold", "GOOD\n(Related)"),
    (0.50, 0.75, "orange", "WEAK\n(Vague)"),
    (0.75, 1.10, "red", "POOR / NONE\n(Unrelated)"),
]

for start, end, color, label in zones:
    ax1.axvspan(
        start,
        end,
        color=color,
        alpha=0.08,
        zorder=0,
        lw=0,
    )
    ax1.text(
        (start + min(end, 1.0)) / 2.0,
        len(df_sorted) + 0.5,
        label,
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

ax1.hlines(
    y=y,
    xmin=df_sorted["CyBOK_Emb"],
    xmax=df_sorted["ECSF_Emb"],
    linewidth=2,
    alpha=0.60,
    zorder=2,
)

ax1.scatter(
    df_sorted["CyBOK_Emb"],
    y,
    label="CyBOK",
    s=130,
    zorder=3,
    edgecolors="white",
    linewidth=1,
)

ax1.scatter(
    df_sorted["ECSF_Emb"],
    y,
    label="ECSF",
    s=130,
    marker="s",
    zorder=3,
    edgecolors="white",
    linewidth=1,
)

for i, row in df_sorted.iterrows():
    gap = row["Gap_Emb"]

    if gap >= 0:
        x_text = row["ECSF_Emb"] + 0.015
        label = f"+{gap:.2f}"
    else:
        x_text = row["CyBOK_Emb"] + 0.015
        label = f"{gap:.2f}"

    ax1.text(
        x_text,
        i,
        label,
        va="center",
        fontsize=9,
        fontweight="bold",
    )

ax1.set_yticks(y)
ax1.set_yticklabels(df_sorted["Topic"], fontsize=11)

ax1.set_xlabel(
    "Semantic distance (1 - cosine similarity)",
    fontsize=12,
    fontweight="bold",
)

ax1.set_title(
    "Semantic Gap Analysis with Interpretation Zones\n"
    f"(one-sided Wilcoxon signed-rank test: p = {p:.4f})",
    loc="left",
    fontweight="bold",
    pad=35,
)

ax1.legend(
    loc="lower right",
    frameon=True,
    fancybox=True,
    framealpha=0.95,
    fontsize=11,
)

ax1.set_xlim(-0.02, 1.10)
ax1.set_ylim(-1, len(df_sorted) + 2)
ax1.grid(axis="x", linestyle="--", alpha=0.3)

fig1.tight_layout()
save_figure(fig1, "Fig1_GapAnalysis_Zones")
plt.close(fig1)


# ---------------------------------------------------------------------
# Figure 2 — Representation robustness / sensitivity
# ---------------------------------------------------------------------

fig2, ax2 = plt.subplots(figsize=(8, 8))

x = df["Gap_Emb"].to_numpy(dtype=float)
y2 = df["Gap_TFIDF"].to_numpy(dtype=float)

ax2.scatter(
    x,
    y2,
    s=100,
    alpha=0.70,
)

# Ordinary least-squares trend line for visualization only.
if len(x) >= 2 and np.ptp(x) > 0:
    slope, intercept = np.polyfit(x, y2, 1)
    xx = np.linspace(x.min(), x.max(), 200)
    ax2.plot(
        xx,
        slope * xx + intercept,
        linestyle="--",
        linewidth=1.5,
    )

ax2.axvline(0, linewidth=1)
ax2.axhline(0, linewidth=1)

ax2.text(
    0.95,
    0.95,
    "Robust advantage:\nCyBOK better in both metrics",
    transform=ax2.transAxes,
    fontsize=11,
    ha="right",
    va="top",
    bbox={
        "facecolor": "white",
        "alpha": 0.9,
        "edgecolor": "gray",
        "boxstyle": "round,pad=0.5",
    },
)

# These are DISTANCE GAPS, not cosine similarities.
ax2.set_xlabel(
    r"Embedding distance gap "
    r"($D_{\mathrm{ECSF}} - D_{\mathrm{CyBOK}}$)"
)
ax2.set_ylabel(
    r"TF-IDF distance gap "
    r"($D_{\mathrm{ECSF}} - D_{\mathrm{CyBOK}}$)"
)

ax2.set_title(
    "Methodological Robustness\n"
    "(comparison of neural and frequency-based representations)",
    loc="left",
    fontweight="bold",
    pad=20,
)

ax2.grid(alpha=0.25)

fig2.tight_layout()
save_figure(fig2, "Fig2_Sensitivity_Explicit")
plt.close(fig2)

print("\nSemantic-similarity experiment completed successfully.")
