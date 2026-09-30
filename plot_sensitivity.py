#!/usr/bin/env python3
"""
Publication-quality sensitivity visualizations for the ECSF/CyBOK paper.

Expected input files in the same directory:
    optionA_joint_sensitivity.csv
    step3_corrected_alpha_baseline.csv

Outputs:
    fig_parameter_sensitivity_tau_alpha.pdf/png
    fig_parameter_sensitivity_top3_heatmap.pdf/png
    fig_parameter_sensitivity_tau_heatmap.pdf/png

Design rationale
----------------
Figure 1 isolates alpha and shows how Kendall's tau changes when only
hierarchical-depth weighting is varied.

Figures 2-3 summarize the joint sensitivity at the nominal alpha=1:
    x-axis: beta (Conceptual mapping weight)
    y-axis: q (fraction of observed Specific mappings counterfactually
            reclassified as Conceptual)
    cell:   top-3 preservation frequency or median Kendall's tau.

q is a stress-test parameter, not an algorithm parameter.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
JOINT = ROOT / "optionA_joint_sensitivity.csv"
ALPHA = ROOT / "step3_corrected_alpha_baseline.csv"

OUTDIR = ROOT / "figs"
OUTDIR.mkdir(exist_ok=True)

joint = pd.read_csv(JOINT)
alpha = pd.read_csv(ALPHA)


def save_alpha_tau():
    df = alpha.sort_values("alpha")

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(df["alpha"], df["kendall_tau"], marker="o", linewidth=1.6)

    ax.set_xlabel(r"Hierarchical-depth parameter $\alpha$")
    ax.set_ylabel(r"Kendall's $\tau$")
    ax.set_xticks(df["alpha"])
    ax.set_ylim(0.70, 0.86)
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
    fig.savefig(
        OUTDIR / "fig_parameter_sensitivity_tau_alpha.pdf",
        bbox_inches="tight"
    )
    fig.savefig(
        OUTDIR / "fig_parameter_sensitivity_tau_alpha.png",
        dpi=600,
        bbox_inches="tight"
    )
    plt.close(fig)


def _prepare_nominal_alpha(metric):
    df = joint[
        (joint["alpha"] == 1.0) &
        (joint["q_reclassified_specific_to_conceptual"] < 1.0)
    ].copy()

    pivot = df.pivot(
        index="q_reclassified_specific_to_conceptual",
        columns="beta_conceptual_weight",
        values=metric,
    )

    # More intuitive paper ordering:
    # low -> high perturbation on y, low -> high beta on x.
    pivot = pivot.sort_index(ascending=True)
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    return pivot


def save_heatmap(metric, filename, label, as_percent=False, vmin=None, vmax=None):
    pivot = _prepare_nominal_alpha(metric)

    values = pivot.to_numpy(dtype=float)
    display = values * 100 if as_percent else values

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    image = ax.imshow(
        display,
        origin="lower",
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_xlabel(r"Conceptual mapping weight $\beta$")
    ax.set_ylabel(
        r"Fraction $q$ of Specific mappings reclassified as Conceptual"
    )

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([f"{x:.2f}" for x in pivot.columns])

    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([f"{100*x:.0f}\\%" for x in pivot.index])

    for i in range(display.shape[0]):
        for j in range(display.shape[1]):
            val = display[i, j]
            text = f"{val:.1f}\\%" if as_percent else f"{val:.3f}"
            ax.text(j, i, text, ha="center", va="center", fontsize=8)

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label(label)

    fig.tight_layout()
    fig.savefig(OUTDIR / f"{filename}.pdf", bbox_inches="tight")
    fig.savefig(OUTDIR / f"{filename}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)



def _prepare_conservative_joint(metric):
    """
    Conservative summary over the practically relevant alpha range
    {0.5, 1, 2}: for each (q, beta), retain the minimum robustness value
    observed across alpha.
    """
    df = joint[
        (joint["alpha"].isin([0.0, 0.5, 1.0, 2.0, 3.0])) &
        (joint["q_reclassified_specific_to_conceptual"] < 1.0)
    ].copy()

    conservative = (
        df.groupby(
            [
                "q_reclassified_specific_to_conceptual",
                "beta_conceptual_weight",
            ],
            as_index=False,
        )[metric]
        .min()
    )

    pivot = conservative.pivot(
        index="q_reclassified_specific_to_conceptual",
        columns="beta_conceptual_weight",
        values=metric,
    )
    pivot = pivot.sort_index(ascending=True)
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    return pivot


def save_conservative_heatmap(
    metric,
    filename,
    label,
    as_percent=False,
    vmin=None,
    vmax=None,
):
    pivot = _prepare_conservative_joint(metric)

    values = pivot.to_numpy(dtype=float)
    display = values * 100 if as_percent else values

    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    image = ax.imshow(
        display,
        origin="lower",
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_xlabel(r"Conceptual mapping weight $\beta$")
    ax.set_ylabel(
        r"Fraction $q$ of Specific mappings reclassified as Conceptual"
    )

    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([f"{x:.2f}" for x in pivot.columns])

    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([f"{100*x:.0f}\\%" for x in pivot.index])

    for i in range(display.shape[0]):
        for j in range(display.shape[1]):
            val = display[i, j]
            cell = f"{val:.1f}\\%" if as_percent else f"{val:.3f}"
            ax.text(j, i, cell, ha="center", va="center", fontsize=8)

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label(label)

    fig.tight_layout()
    fig.savefig(OUTDIR / f"{filename}.pdf", bbox_inches="tight")
    fig.savefig(OUTDIR / f"{filename}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    save_alpha_tau()

    save_heatmap(
        metric="fraction_Pat3_equals_1",
        filename="fig_parameter_sensitivity_top3_heatmap",
        label="Top-3 preservation frequency (%)",
        as_percent=True,
        vmin=0,
        vmax=100,
    )

    save_heatmap(
        metric="tau_median",
        filename="fig_parameter_sensitivity_tau_heatmap",
        label=r"Median Kendall's $\tau$",
        as_percent=False,
        vmin=0.45,
        vmax=0.85,
    )

    save_conservative_heatmap(
        metric="fraction_Pat3_equals_1",
        filename="fig_parameter_sensitivity_top3_worst_alpha",
        label=r"Worst-case top-3 preservation over $\alpha\in\{0.5,1,2\}$ (%)",
        as_percent=True,
        vmin=0,
        vmax=100,
    )

    save_conservative_heatmap(
        metric="tau_median",
        filename="fig_parameter_sensitivity_tau_worst_alpha",
        label=r"Worst-case median Kendall's $\tau$ over $\alpha\in\{0.5,1,2\}$",
        as_percent=False,
        vmin=0.45,
        vmax=0.85,
    )

    print("Generated:")
    print(" - figs/fig_parameter_sensitivity_tau_alpha.pdf")
    print(" - figs/fig_parameter_sensitivity_top3_heatmap.pdf")
    print(" - figs/fig_parameter_sensitivity_tau_heatmap.pdf")
    print(" - figs/fig_parameter_sensitivity_top3_worst_alpha.pdf")
    print(" - figs/fig_parameter_sensitivity_tau_worst_alpha.pdf")
