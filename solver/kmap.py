"""
kmap.py
-------
K-Map grid layout, Gray-code ordering, and valid grouping generation.

Gray-code orderings follow standard K-Map convention:
  2-var:  rows=[0,1],       cols=[0,1]        (AB)
  3-var:  rows=[0,1],       cols=[00,01,11,10] (A | BC)
  4-var:  rows=[00,01,11,10], cols=[00,01,11,10] (AB | CD)
"""

from itertools import product as iproduct


# ---------------------------------------------------------------------------
# Gray-code orderings
# ---------------------------------------------------------------------------

GRAY_2 = [0, 1]
GRAY_4 = [0, 1, 3, 2]   # 00, 01, 11, 10

KMAP_LAYOUT = {
    2: {
        "rows": GRAY_2,          # A
        "cols": GRAY_2,          # B
        "row_vars": ["A"],
        "col_vars": ["B"],
    },
    3: {
        "rows": GRAY_2,          # A
        "cols": GRAY_4,          # BC
        "row_vars": ["A"],
        "col_vars": ["B", "C"],
    },
    4: {
        "rows": GRAY_4,          # AB
        "cols": GRAY_4,          # CD
        "row_vars": ["A", "B"],
        "col_vars": ["C", "D"],
    },
}


def get_layout(num_vars: int) -> dict:
    """Return the K-Map layout spec for the given variable count."""
    if num_vars not in KMAP_LAYOUT:
        raise ValueError(f"Unsupported variable count: {num_vars}")
    return KMAP_LAYOUT[num_vars]




def build_grid(minterms: list[int], num_vars: int) -> list[list[int]]:
    """
    Build a 2-D K-Map grid.

    Each cell holds the minterm index (0–15) or -1 if unused.
    Cell value is 1 if the minterm is in the ON-set, 0 otherwise.

    Returns:
        grid[row][col] = 0 or 1
    """
    layout = get_layout(num_vars)
    rows = layout["rows"]
    cols = layout["cols"]

    row_bits = len(layout["row_vars"])
    col_bits = len(layout["col_vars"])

    minterm_set = set(minterms)
    grid = []

    for r in rows:
        row_data = []
        for c in cols:
            # Combine row and col gray indices into a single minterm index
            minterm_idx = (r << col_bits) | c
            row_data.append(1 if minterm_idx in minterm_set else 0)
        grid.append(row_data)

    return grid


def minterm_to_cell(minterm: int, num_vars: int) -> tuple[int, int]:
    """
    Return the (row_idx, col_idx) position in the K-Map grid for a given minterm.
    These are grid indices (0-based), not Gray-code values.
    """
    layout = get_layout(num_vars)
    rows = layout["rows"]
    cols = layout["cols"]
    col_bits = len(layout["col_vars"])

    row_val = minterm >> col_bits
    col_val = minterm & ((1 << col_bits) - 1)

    row_idx = rows.index(row_val)
    col_idx = cols.index(col_val)
    return row_idx, col_idx


def cell_to_minterm(row_idx: int, col_idx: int, num_vars: int) -> int:
    """
    Convert a (row_idx, col_idx) grid position back to its minterm integer.
    """
    layout = get_layout(num_vars)
    rows = layout["rows"]
    cols = layout["cols"]
    col_bits = len(layout["col_vars"])

    row_val = rows[row_idx]
    col_val = cols[col_idx]
    return (row_val << col_bits) | col_val


def generate_all_groups(num_vars: int) -> list[frozenset[int]]:
    """
    Generate all valid K-Map groupings as frozensets of minterm indices.

    Valid groups are rectangular regions whose dimensions are powers of 2,
    including wrap-around at all four edges.

    Returns:
        List of frozensets, each containing the minterm indices in one group.
    """
    layout = get_layout(num_vars)
    num_rows = len(layout["rows"])
    num_cols = len(layout["cols"])

    groups: list[frozenset[int]] = []

    # All valid power-of-2 height/width combinations
    valid_heights = [2**i for i in range(int.bit_length(num_rows))]
    valid_widths  = [2**i for i in range(int.bit_length(num_cols))]

    for h in valid_heights:
        for w in valid_widths:
            # All possible top-left corners
            for start_r in range(num_rows):
                for start_c in range(num_cols):
                    cell_minterms = set()
                    for dr in range(h):
                        for dc in range(w):
                            r = (start_r + dr) % num_rows
                            c = (start_c + dc) % num_cols
                            cell_minterms.add(
                                cell_to_minterm(r, c, num_vars)
                            )
                    groups.append(frozenset(cell_minterms))

    # Deduplicate (same set reached via different starting corners)
    return list(set(groups))