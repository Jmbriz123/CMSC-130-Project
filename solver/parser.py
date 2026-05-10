"""
---------
Handles all input parsing for the K-Map solver.
Accepts:
  - Minterm list notation: Σm(0, 1, 3, 7)
  - Raw integer list: [0, 1, 3, 7]
  - Truth table as list of (output,) rows or pandas DataFrame
  - CSV file (via pandas)
"""

import re
import pandas as pd
from typing import Union


def parse_minterms(raw: str) -> tuple[list[int], int]:
    """
    Parse a minterm expression string into a sorted list of minterm integers
    and auto-detect the number of variables.

    Accepts formats:
      - "Σm(0,1,3,7)"  or  "m(0,1,3,7)"
      - "0,1,3,7"
      - "0 1 3 7"

    Returns:
        (minterms, num_vars): sorted minterm list and variable count (2–4)

    Raises:
        ValueError: on invalid input or out-of-range minterms
    """
    raw = raw.strip()

    # Strip Σm(...) or m(...) wrapper if present
    match = re.match(r"[Σσ]?m\(([^)]+)\)", raw, re.IGNORECASE)
    if match:
        raw = match.group(1)

    # Parse comma or space separated integers
    tokens = re.split(r"[,\s]+", raw.strip())
    try:
        minterms = sorted(set(int(t) for t in tokens if t))
    except ValueError:
        raise ValueError(f"Invalid minterm input: '{raw}'. Expected integers.")

    if not minterms:
        raise ValueError("Minterm list is empty.")

    num_vars = _detect_num_vars(minterms)
    _validate_minterms(minterms, num_vars)

    return minterms, num_vars


def parse_truth_table(rows: list[list[int]]) -> tuple[list[int], int]:
    """
    Parse a truth table given as a list of rows.
    Each row: [A, B, ..., output]
    Rows where output == 1 become minterms.

    Returns:
        (minterms, num_vars)

    Raises:
        ValueError: on malformed rows or unsupported variable count
    """
    if not rows:
        raise ValueError("Truth table is empty.")

    num_vars = len(rows[0]) - 1
    if not (2 <= num_vars <= 4):
        raise ValueError(f"Unsupported variable count: {num_vars}. Must be 2–4.")

    expected_rows = 2 ** num_vars
    if len(rows) != expected_rows:
        raise ValueError(
            f"Truth table must have exactly {expected_rows} rows for {num_vars} variables, "
            f"got {len(rows)}."
        )

    minterms = []
    for i, row in enumerate(rows):
        if len(row) != num_vars + 1:
            raise ValueError(f"Row {i} has {len(row)} columns, expected {num_vars + 1}.")
        if row[-1] == 1:
            minterms.append(i)

    return sorted(minterms), num_vars


def parse_csv(filepath: str) -> tuple[list[int], int]:
    """
    Parse a CSV truth table file.
    Expects columns: A, B[, C[, D]], Output
    The last column is treated as the output.

    Returns:
        (minterms, num_vars)
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    rows = df.values.tolist()
    return parse_truth_table([[int(v) for v in row] for row in rows])


def parse_csv_upload(uploaded_file) -> tuple[list[int], int]:
    """
    Parse a CSV truth table from a Streamlit UploadedFile object.
    """
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        raise ValueError(f"Failed to read uploaded CSV: {e}")

    rows = df.values.tolist()
    return parse_truth_table([[int(v) for v in row] for row in rows])


# 
# Internal helpers
# 

def _detect_num_vars(minterms: list[int]) -> int:
    """
    Infer the minimum number of variables needed to represent all minterms.
    Clamps result to the range [2, 4].
    """
    if not minterms:
        return 2
    max_m = max(minterms)
    if max_m <= 3:
        return 2
    elif max_m <= 7:
        return 3
    elif max_m <= 15:
        return 4
    else:
        raise ValueError(
            f"Minterm {max_m} exceeds the maximum (15) for 4-variable K-Maps."
        )


def _validate_minterms(minterms: list[int], num_vars: int) -> None:
    """Assert all minterms are within the valid range for num_vars."""
    max_valid = (2 ** num_vars) - 1
    invalid = [m for m in minterms if m < 0 or m > max_valid]
    if invalid:
        raise ValueError(
            f"Minterms {invalid} are out of range for {num_vars} variables "
            f"(valid: 0–{max_valid})."
        )