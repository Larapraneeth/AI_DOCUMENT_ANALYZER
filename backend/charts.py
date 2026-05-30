"""
FILE: backend/charts.py
Generates Revenue, EBITDA, and PAT charts using Matplotlib.
Saves as PNG files and returns their paths.
Styled to match Geojit report aesthetics (bar + line combo charts).
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

logger = logging.getLogger(__name__)

# ── Geojit-inspired colour palette ─────────────────────────────────────────
COLORS = {
    "bar_actual":   "#1B5E9B",   # Dark blue – actual years
    "bar_estimate": "#4A90D9",   # Light blue – estimated years
    "line":         "#E8A020",   # Orange – growth line
    "grid":         "#E5E5E5",
    "text":         "#333333",
    "background":   "#FFFFFF",
    "border":       "#CCCCCC",
}

CHART_STYLE = {
    "figure.facecolor":  COLORS["background"],
    "axes.facecolor":    COLORS["background"],
    "axes.edgecolor":    COLORS["border"],
    "axes.labelcolor":   COLORS["text"],
    "xtick.color":       COLORS["text"],
    "ytick.color":       COLORS["text"],
    "grid.color":        COLORS["grid"],
    "grid.linestyle":    "--",
    "grid.linewidth":    0.6,
    "font.family":       "DejaVu Sans",
    "font.size":         9,
}


def _extract_series(series_list: list) -> tuple:
    """Extract (years, values) from [{'year':..., 'value':...}] list."""
    years = []
    values = []
    for item in series_list:
        if isinstance(item, dict):
            years.append(str(item.get("year", "")))
            val = item.get("value")
            try:
                values.append(float(val) if val is not None else 0.0)
            except (TypeError, ValueError):
                values.append(0.0)
    return years, values


def _compute_growth(values: list) -> list:
    """Compute YoY growth percentage for each period."""
    growth = [None]
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if prev and prev != 0:
            growth.append(round((curr - prev) / abs(prev) * 100, 1))
        else:
            growth.append(None)
    return growth


def _bar_colors(years: list) -> list:
    """Actual years = dark blue, estimates (E suffix) = lighter blue."""
    return [
        COLORS["bar_estimate"] if "E" in y or "e" in y else COLORS["bar_actual"]
        for y in years
    ]


def _draw_combo_chart(
    ax_bar,
    ax_line,
    years: list,
    values: list,
    growth: list,
    bar_label: str,
    line_label: str = "Growth (QoQ %)",
):
    """Draws a bar+line combo chart on the provided axes."""
    x = np.arange(len(years))
    bar_w = 0.55
    colors = _bar_colors(years)

    # Bars
    bars = ax_bar.bar(x, values, width=bar_w, color=colors, zorder=3, edgecolor="white", linewidth=0.4)
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(years, fontsize=8, rotation=0)
    ax_bar.set_ylabel(bar_label, fontsize=8, color=COLORS["text"])
    ax_bar.yaxis.grid(True, zorder=0)
    ax_bar.set_axisbelow(True)

    # Value labels on bars
    for bar, val in zip(bars, values):
        if val != 0:
            ax_bar.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.01,
                f"{val:,.0f}",
                ha="center", va="bottom", fontsize=7, color=COLORS["text"]
            )

    # Growth line on secondary axis
    valid_x = [i for i, g in enumerate(growth) if g is not None]
    valid_g = [g for g in growth if g is not None]

    if valid_x:
        ax_line.plot(valid_x, valid_g, color=COLORS["line"], marker="o",
                     markersize=4, linewidth=1.5, zorder=4)
        for xi, gi in zip(valid_x, valid_g):
            ax_line.text(xi, gi + max(abs(v) for v in valid_g if v) * 0.05,
                         f"{gi:.1f}%", ha="center", va="bottom",
                         fontsize=7, color=COLORS["line"])

    ax_line.set_ylabel(line_label, fontsize=8, color=COLORS["line"])
    ax_line.tick_params(axis="y", colors=COLORS["line"])
    ax_line.spines["right"].set_color(COLORS["line"])

    # Legend
    actual_patch = mpatches.Patch(color=COLORS["bar_actual"], label="Actual")
    est_patch = mpatches.Patch(color=COLORS["bar_estimate"], label="Estimate")
    line_patch = mpatches.Patch(color=COLORS["line"], label="YoY Growth %")
    ax_bar.legend(handles=[actual_patch, est_patch, line_patch],
                  loc="upper left", fontsize=7, framealpha=0.8)


def generate_revenue_chart(data: Dict[str, Any], session_id: str, charts_dir: str) -> str:
    """Generate Revenue bar+line chart. Returns PNG file path."""
    years, values = _extract_series(data.get("revenue", []))
    if not years:
        return ""

    growth = _compute_growth(values)

    with plt.style.context(CHART_STYLE):
        fig, ax1 = plt.subplots(figsize=(6, 3.2))
        ax2 = ax1.twinx()
        _draw_combo_chart(ax1, ax2, years, values, growth,
                          bar_label="Revenue (Rs. Cr)", line_label="YoY Growth %")
        ax1.set_title("Revenue", fontsize=10, fontweight="bold",
                      color=COLORS["text"], pad=8)
        plt.tight_layout()

        path = os.path.join(charts_dir, f"revenue_{session_id}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["background"])
        plt.close(fig)

    logger.info(f"Revenue chart saved: {path}")
    return path


def generate_ebitda_chart(data: Dict[str, Any], session_id: str, charts_dir: str) -> str:
    """Generate EBITDA bar+line combo chart. Returns PNG file path."""
    years, values = _extract_series(data.get("ebitda", []))
    if not years:
        return ""

    growth = _compute_growth(values)

    with plt.style.context(CHART_STYLE):
        fig, ax1 = plt.subplots(figsize=(6, 3.2))
        ax2 = ax1.twinx()
        _draw_combo_chart(ax1, ax2, years, values, growth,
                          bar_label="EBITDA (Rs. Cr)", line_label="Margin %")

        # Also overlay EBITDA margin if available
        margin_years, margins = _extract_series(data.get("ebitda_margin", []))
        if margins and any(m != 0 for m in margins):
            x = np.arange(len(years))
            for xi, mi in enumerate(margins[:len(years)]):
                if mi:
                    ax2.text(xi, mi, f"{mi:.1f}%", ha="center", va="top",
                             fontsize=6.5, color="#888888")

        ax1.set_title("EBITDA", fontsize=10, fontweight="bold",
                      color=COLORS["text"], pad=8)
        plt.tight_layout()

        path = os.path.join(charts_dir, f"ebitda_{session_id}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["background"])
        plt.close(fig)

    logger.info(f"EBITDA chart saved: {path}")
    return path


def generate_pat_chart(data: Dict[str, Any], session_id: str, charts_dir: str) -> str:
    """Generate PAT bar+line combo chart. Returns PNG file path."""
    years, values = _extract_series(data.get("pat", []))
    if not years:
        return ""

    growth = _compute_growth(values)

    with plt.style.context(CHART_STYLE):
        fig, ax1 = plt.subplots(figsize=(6, 3.2))
        ax2 = ax1.twinx()
        _draw_combo_chart(ax1, ax2, years, values, growth,
                          bar_label="PAT (Rs. Cr)", line_label="PAT Margin %")
        ax1.set_title("PAT (Profit After Tax)", fontsize=10, fontweight="bold",
                      color=COLORS["text"], pad=8)
        plt.tight_layout()

        path = os.path.join(charts_dir, f"pat_{session_id}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=COLORS["background"])
        plt.close(fig)

    logger.info(f"PAT chart saved: {path}")
    return path


def generate_all_charts(
    data: Dict[str, Any],
    session_id: str,
    charts_dir: str
) -> Dict[str, str]:
    """
    Generate all three charts.
    Returns dict: {'revenue': path, 'ebitda': path, 'pat': path}
    """
    Path(charts_dir).mkdir(parents=True, exist_ok=True)

    return {
        "revenue": generate_revenue_chart(data, session_id, charts_dir),
        "ebitda":  generate_ebitda_chart(data, session_id, charts_dir),
        "pat":     generate_pat_chart(data, session_id, charts_dir),
    }
