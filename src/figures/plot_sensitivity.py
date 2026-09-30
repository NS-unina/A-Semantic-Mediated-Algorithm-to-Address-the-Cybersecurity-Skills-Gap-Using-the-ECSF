#!/usr/bin/env python3
"""
Generate the sensitivity-analysis figures used in the manuscript.

Expected inputs
---------------
results/generated/sensitivity/alpha_baseline.csv
results/generated/sensitivity/joint_sensitivity.csv

Generated outputs
-----------------
results/generated/figures/fig_parameter_sensitivity_tau_alpha.pdf
results/generated/figures/fig_parameter_sensitivity_tau_alpha.png

results/generated/figures/fig_parameter_sensitivity_top3_worst_alpha.pdf
results/generated/figures/fig_parameter_sensitivity_top3_worst_alpha.png

The joint heatmap is consistent with the manuscript caption:

    Each cell reports the minimum frequency with which the nominal top-three
    ECSF role set is preserved across all tested hierarchical-depth
    configurations, alpha in {0, 0.5, 1, 2, 3}.

Therefore, for each (q, beta) pair, the script takes the minimum top-3
preservation frequency across ALL alpha values present in alpha_baseline.csv.
"""

from pathlib import Path
import os
import tempfile

import matplotlib

# Non-interactive backend: safer for headless/server execution and PDF export.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

SENS_DIR = ROOT / "results" / "generated" / "sensitivity"
FIG_DIR = ROOT / "results" / "generated" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

ALPHA_FILE = SENS_DIR / "alpha_baseline.csv"
JOINT_FILE = SENS_DIR / "joint_sensitivity.csv"


# ---------------------------------------------------------------------------
# Expected alpha configurations
# ---------------------------------------------------------------------------

EXPECTED_ALPHAS = [0.0, 0.5, 1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def require_file(path: Path) -> None:
    """Fail explicitly if an expected input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found:\n  {path}\n\n"
            "Run first:\n"
            "  python src/sensitivity_analysis.py"
        )


def save_figure(fig, pdf_path: Path, png_path: Path) -> None:
    """
    Save PDF and PNG directly to their final destinations.

    Direct saving is more reliable when the repository is located on a
    Windows-mounted filesystem under WSL (/mnt/c/...).
    """
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove previous outputs if present.
    # Make sure the PDF is not open in Acrobat/Edge/Preview Explorer.
    if pdf_path.exists():
        pdf_path.unlink()

    if png_path.exists():
        png_path.unlink()

    fig.savefig(
        pdf_path,
        format="pdf",
        bbox_inches="tight",
    )

    fig.savefig(
        png_path,
        format="png",
        dpi=600,
        bbox_inches="tight",
    )

    # Basic PDF integrity check.
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Generated PDF is empty: {pdf_path}")

    with pdf_path.open("rb") as f:
        header = f.read(4)

    if header != b"%PDF":
        raise RuntimeError(
            f"Generated file does not contain a valid PDF header: {pdf_path}"
        )


def validate_alpha_grid(alpha_df: pd.DataFrame, joint_df: pd.DataFrame) -> None:
    """Ensure that the data contain the alpha configurations stated in the paper."""
    alpha_values = sorted(alpha_df["alpha"].astype(float).unique().tolist())
    joint_values = sorted(joint_df["alpha"].astype(float).unique().tolist())

    if not np.allclose(alpha_values, EXPECTED_ALPHAS):
        raise ValueError(
            "alpha_baseline.csv does not contain the expected alpha grid.\n"
            f"Expected: {EXPECTED_ALPHAS}\n"
            f"Found:    {alpha_values}"
        )

    if not np.allclose(joint_values, EXPECTED_ALPHAS):
        raise ValueError(
            "joint_sensitivity.csv does not contain the expected alpha grid.\n"
            f"Expected: {EXPECTED_ALPHAS}\n"
            f"Found:    {joint_values}"
        )


# ---------------------------------------------------------------------------
# Figure 1: alpha-only sensitivity
# ---------------------------------------------------------------------------

def plot_alpha_sensitivity(alpha_df: pd.DataFrame) -> None:
    """
    Plot Kendall's tau as a function of alpha.

    This figure is useful for the alpha-only sensitivity discussion.
    """
    df = alpha_df.sort_values("alpha").copy()

    fig, ax = plt.subplots(figsize=(6.4, 4.0))

    ax.plot(
        df["alpha"],
        df["kendall_tau"],
        marker="o",
        linewidth=1.6,
    )

    ax.set_xlabel(r"Hierarchical-depth parameter $\alpha$")
    ax.set_ylabel(r"Kendall's $\tau$")
    ax.set_xticks(df["alpha"].tolist())

    # Give a little vertical space around the observed values.
    ymin = float(df["kendall_tau"].min())
    ymax = float(df["kendall_tau"].max())
    margin = max(0.02, (ymax - ymin) * 0.35)

    ax.set_ylim(
        max(-1.0, ymin - margin),
        min(1.0, ymax + margin),
    )

    ax.grid(axis="y", alpha=0.25)

    for x, y in zip(df["alpha"], df["kendall_tau"]):
        ax.annotate(
            f"{y:.3f}",
            (x, y),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )

    fig.tight_layout()

    pdf_path = FIG_DIR / "fig_parameter_sensitivity_tau_alpha.pdf"
    png_path = FIG_DIR / "fig_parameter_sensitivity_tau_alpha.png"

    save_figure(fig, pdf_path, png_path)
    plt.close(fig)

    print(f"[OK] Generated: {pdf_path}")
    print(f"[OK] Generated: {png_path}")


# ---------------------------------------------------------------------------
# Figure 2: worst-alpha top-3 preservation heatmap
# ---------------------------------------------------------------------------

def prepare_worst_alpha_top3(joint_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (q, beta), compute the minimum top-3 preservation frequency across
    ALL tested alpha values.

    This is exactly the aggregation described in the manuscript caption.
    """
    required_columns = {
        "alpha",
        "q_reclassified_specific_to_conceptual",
        "beta_conceptual_weight",
        "fraction_Pat3_equals_1",
        "status",
    }

    missing = required_columns.difference(joint_df.columns)
    if missing:
        raise ValueError(
            "joint_sensitivity.csv is missing required columns:\n"
            + "\n".join(f"  - {x}" for x in sorted(missing))
        )

    df = joint_df.copy()

    # Ranking-based interpretation is undefined for the all-zero degenerate
    # condition. We also exclude q=1 from this visualization, because the
    # manuscript heatmap summarizes stochastic perturbation frequencies.
    df = df[
        (df["status"] == "valid")
        & (df["q_reclassified_specific_to_conceptual"] < 1.0)
    ].copy()

    if df.empty:
        raise ValueError(
            "No valid non-degenerate sensitivity scenarios remain after filtering."
        )

    # Conservative aggregation:
    # minimum top-3 preservation across alpha ∈ {0, 0.5, 1, 2, 3}.
    worst = (
        df.groupby(
            [
                "q_reclassified_specific_to_conceptual",
                "beta_conceptual_weight",
            ],
            as_index=False,
        )["fraction_Pat3_equals_1"]
        .min()
    )

    pivot = worst.pivot(
        index="q_reclassified_specific_to_conceptual",
        columns="beta_conceptual_weight",
        values="fraction_Pat3_equals_1",
    )

    # Manuscript-friendly ordering:
    # q increases bottom-to-top and beta increases left-to-right.
    pivot = pivot.sort_index(ascending=True)
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)

    return pivot


def plot_worst_alpha_top3(joint_df: pd.DataFrame) -> None:
    """
    Generate the heatmap reported in the manuscript.

    Each cell shows the minimum top-3 preservation frequency across
    all tested alpha values:
        alpha ∈ {0, 0.5, 1, 2, 3}

    pcolormesh is deliberately used instead of imshow because it
    produces vector cells that are more reliably rendered in PDF.
    """

    pivot = prepare_worst_alpha_top3(joint_df)

    # Frequencies [0,1] -> percentages [0,100]
    display = pivot.to_numpy(dtype=float) * 100.0

    n_rows, n_cols = display.shape

    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    # Cell boundaries
    x_edges = np.arange(n_cols + 1)
    y_edges = np.arange(n_rows + 1)

    # Vector-based heatmap: more robust than imshow in PDF
    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        display,
        shading="flat",
        vmin=0.0,
        vmax=100.0,
    )

    # Place tick labels at the center of each cell
    ax.set_xticks(np.arange(n_cols) + 0.5)
    ax.set_yticks(np.arange(n_rows) + 0.5)

    ax.set_xticklabels([
        f"{beta:.2f}"
        for beta in pivot.columns
    ])

    ax.set_yticklabels([
        f"{100.0 * q:.0f}%"
        for q in pivot.index
    ])

    ax.set_xlabel(
        r"Conceptual mapping weight $\beta$"
    )

    ax.set_ylabel(
        r"Fraction $q$ of active mapping contributions "
        r"downgraded to Conceptual"
    )

    # Annotate each cell
    for row in range(n_rows):
        for col in range(n_cols):
            value = display[row, col]

            if np.isnan(value):
                label = "NA"
            else:
                label = f"{value:.1f}%"

            ax.text(
                col + 0.5,
                row + 0.5,
                label,
                ha="center",
                va="center",
                fontsize=9,
            )

    # Exact matrix boundaries
    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)

    cbar = fig.colorbar(
        mesh,
        ax=ax,
        pad=0.03,
    )

    cbar.set_label(
        "Minimum top-3 preservation across all tested "
        r"$\alpha$ configurations (%)"
    )

    fig.tight_layout()

    pdf_path = (
        FIG_DIR /
        "fig_parameter_sensitivity_top3_worst_alpha.pdf"
    )

    png_path = (
        FIG_DIR /
        "fig_parameter_sensitivity_top3_worst_alpha.png"
    )

    # Save directly. No temporary/replace step.
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

    plt.close(fig)

    print(f"[OK] Generated: {pdf_path}")
    print(f"[OK] Generated: {png_path}")

    print("\nWorst-alpha top-3 preservation matrix (%):")
    print(
        (pivot * 100.0)
        .round(1)
        .to_string()
    )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    require_file(ALPHA_FILE)
    require_file(JOINT_FILE)

    alpha_df = pd.read_csv(ALPHA_FILE)
    joint_df = pd.read_csv(JOINT_FILE)

    validate_alpha_grid(alpha_df, joint_df)

    print("Sensitivity inputs:")
    print(f"  Alpha baseline: {ALPHA_FILE}")
    print(f"  Joint analysis: {JOINT_FILE}")
    print(f"  Tested alpha values: {EXPECTED_ALPHAS}")
    print()

    plot_alpha_sensitivity(alpha_df)
    plot_worst_alpha_top3(joint_df)

    print("\nSensitivity figures generated successfully.")


if __name__ == "__main__":
    main()
