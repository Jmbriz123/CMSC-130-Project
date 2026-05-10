"""
grid.py
-------
K-Map grid renderer using Matplotlib.
Draws the Gray-coded grid, fills ON-set cells, and overlays
color-coded prime implicant group rectangles with wrap-around support.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

from solver.kmap import get_layout, cell_to_minterm, minterm_to_cell


# Distinct colors for up to 8 prime implicant groups
GROUP_COLORS = [
    "#E63946", "#2196F3", "#4CAF50", "#FF9800",
    "#9C27B0", "#00BCD4", "#FF5722", "#8BC34A",
]


def render_kmap(
    minterms: list[int],
    num_vars: int,
    selected_groups: list[frozenset[int]],
) -> plt.Figure:
    """
    Render the K-Map grid as a Matplotlib figure.

    Args:
        minterms:        ON-set minterm list
        num_vars:        2, 3, or 4
        selected_groups: prime implicant groups to highlight

    Returns:
        A Matplotlib Figure object (rendered by Streamlit via st.pyplot)
    """
    layout = get_layout(num_vars)
    rows = layout["rows"]
    cols = layout["cols"]
    row_vars = layout["row_vars"]
    col_vars = layout["col_vars"]

    num_rows = len(rows)
    num_cols = len(cols)
    minterm_set = set(minterms)

    # -----------------------------------------------------------------------
    # Figure setup
    # -----------------------------------------------------------------------
    cell_size = 1.1
    fig_w = num_cols * cell_size + 2.0
    fig_h = num_rows * cell_size + 2.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    # -----------------------------------------------------------------------
    # Draw cells
    # -----------------------------------------------------------------------
    for ri, r_gray in enumerate(rows):
        for ci, c_gray in enumerate(cols):
            minterm_idx = cell_to_minterm(ri, ci, num_vars)
            is_on = minterm_idx in minterm_set

            x = ci * cell_size + 1.2
            y = (num_rows - 1 - ri) * cell_size + 0.6

            # Cell background
            bg = "#313244" if is_on else "#1E1E2E"
            rect = FancyBboxPatch(
                (x + 0.05, y + 0.05),
                cell_size - 0.1, cell_size - 0.1,
                boxstyle="round,pad=0.02",
                linewidth=1.2,
                edgecolor="#585B70",
                facecolor=bg,
            )
            ax.add_patch(rect)

            # Cell value (0 or 1)
            cell_val = 1 if is_on else 0
            ax.text(
                x + cell_size / 2, y + cell_size / 2,
                str(cell_val),
                ha="center", va="center",
                fontsize=14, fontweight="bold",
                color="#CDD6F4" if is_on else "#585B70",
            )

            # Minterm index (small, bottom-right)
            ax.text(
                x + cell_size - 0.12, y + 0.18,
                str(minterm_idx),
                ha="right", va="bottom",
                fontsize=7, color="#7F849C",
            )

    # -----------------------------------------------------------------------
    # Draw group overlays
    # -----------------------------------------------------------------------
    for gi, group in enumerate(selected_groups):
        color = GROUP_COLORS[gi % len(GROUP_COLORS)]
        _draw_group_overlay(ax, group, num_vars, num_rows, num_cols,
                             cell_size, color)

    # -----------------------------------------------------------------------
    # Column headers (Gray code + variable labels)
    # -----------------------------------------------------------------------
    col_header_label = "".join(col_vars)
    ax.text(
        1.2 + num_cols * cell_size / 2, 0.6 + num_rows * cell_size + 0.35,
        col_header_label,
        ha="center", va="bottom",
        fontsize=11, fontweight="bold", color="#89B4FA",
    )
    for ci, c_gray in enumerate(cols):
        x = ci * cell_size + 1.2 + cell_size / 2
        y = 0.6 + num_rows * cell_size + 0.05
        bits = format(c_gray, f"0{len(col_vars)}b")
        ax.text(x, y, bits, ha="center", va="bottom",
                fontsize=10, color="#A6E3A1")

    # -----------------------------------------------------------------------
    # Row headers (Gray code + variable labels)
    # -----------------------------------------------------------------------
    row_header_label = "".join(row_vars)
    ax.text(
        0.55, 0.6 + num_rows * cell_size / 2,
        row_header_label,
        ha="center", va="center",
        fontsize=11, fontweight="bold", color="#89B4FA",
        rotation=90,
    )
    for ri, r_gray in enumerate(rows):
        y = (num_rows - 1 - ri) * cell_size + 0.6 + cell_size / 2
        bits = format(r_gray, f"0{len(row_vars)}b")
        ax.text(0.9, y, bits, ha="right", va="center",
                fontsize=10, color="#A6E3A1")

    # -----------------------------------------------------------------------
    # Legend
    # -----------------------------------------------------------------------
    if selected_groups:
        from solver.expression import group_to_product_term
        handles = []
        for gi, group in enumerate(selected_groups):
            color = GROUP_COLORS[gi % len(GROUP_COLORS)]
            term = group_to_product_term(group, num_vars)
            patch = mpatches.Patch(color=color, label=f"Group {gi+1}: {term}")
            handles.append(patch)
        ax.legend(
            handles=handles,
            loc="upper left",
            bbox_to_anchor=(0, -0.05),
            framealpha=0.2,
            facecolor="#313244",
            edgecolor="#585B70",
            labelcolor="#CDD6F4",
            fontsize=9,
        )

    plt.tight_layout(pad=0.5)
    return fig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_group_overlay(
    ax, group: frozenset[int], num_vars: int,
    num_rows: int, num_cols: int,
    cell_size: float, color: str,
):
    """
    Draw a rounded rectangle overlay for a prime implicant group.
    Handles wrap-around groups by splitting them into multiple visual patches.
    """
    # Map each minterm to its (ri, ci) grid position
    cells = [minterm_to_cell(m, num_vars) for m in group]
    ri_set = sorted(set(r for r, _ in cells))
    ci_set = sorted(set(c for _, c in cells))

    # Detect wrap-around in rows or cols
    row_segments = _wrap_segments(ri_set, num_rows)
    col_segments = _wrap_segments(ci_set, num_cols)

    alpha = 0.22
    lw = 2.5
    pad = 0.10

    for r_seg in row_segments:
        for c_seg in col_segments:
            r_min, r_max = min(r_seg), max(r_seg)
            c_min, c_max = min(c_seg), max(c_seg)

            x = c_min * cell_size + 1.2 + pad
            y = (num_rows - 1 - r_max) * cell_size + 0.6 + pad
            w = (c_max - c_min + 1) * cell_size - 2 * pad
            h = (r_max - r_min + 1) * cell_size - 2 * pad

            rect = FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.06",
                linewidth=lw,
                edgecolor=color,
                facecolor=color,
                alpha=alpha,
                zorder=3,
            )
            ax.add_patch(rect)
            # Solid border
            border = FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.06",
                linewidth=lw,
                edgecolor=color,
                facecolor="none",
                zorder=4,
            )
            ax.add_patch(border)


def _wrap_segments(indices: list[int], size: int) -> list[list[int]]:
    """
    Split a sorted list of grid indices into contiguous segments,
    treating the grid as wrapping (toroidal).

    E.g. [0, 1, 2, 3] with size=4 → [[0,1,2,3]]
         [0, 3]        with size=4 → [[3], [0]]  (wrap-around)
    """
    if not indices:
        return []

    # Check if this is a wrap-around group
    is_wrap = (
        len(indices) > 1
        and (max(indices) - min(indices)) > len(indices) - 1
    )

    if not is_wrap:
        return [indices]

    # Split into the "far end" and "near start" segments
    far = [i for i in indices if i > size // 2]
    near = [i for i in indices if i <= size // 2]
    return [seg for seg in [far, near] if seg]