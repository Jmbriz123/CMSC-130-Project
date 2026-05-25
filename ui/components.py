"""
Simple Streamlit UI component helpers.

This module intentionally avoids custom HTML/CSS and uses plain Streamlit
widgets so the app focuses on functionality.
"""

import streamlit as st
from solver.expression import group_to_product_term, VAR_NAMES


def render_sop_display(sop_expr: str, output_name: str = "F"):
    """Display the minimized SOP expression plainly."""
    st.subheader("Minimized SOP")
    st.code(f"{output_name} = {sop_expr}")


def render_output_summary(
    output_name: str, sop_expr: str, minterms: list[int], num_vars: int
):
    """Show a concise output summary (always shown after solving)."""
    st.subheader("Output Summary")
    minterm_list = ", ".join(str(m) for m in sorted(minterms)) if minterms else "none"
    st.write(f"Output: {output_name}")
    st.write(f"Minimized: {output_name} = {sop_expr}")
    st.write(f"Variables: {num_vars}")
    st.write(f"Minterms (ON set): {minterm_list}")


def render_pos_display(pos_expr: str, output_name: str = "F"):
    """Display the minimized POS expression plainly."""
    st.subheader("Minimized POS")
    st.code(f"{output_name} = {pos_expr}")


def render_verilog_display(verilog_code: str):
    """Display Verilog export in a code block."""
    st.subheader("Verilog Export")
    st.code(verilog_code, language="verilog")


def render_trace(trace: list[dict], num_vars: int):
    """Render the step-by-step solution trace in simple expanders."""
    if not trace:
        st.info("No grouping steps to display.")
        return

    st.subheader("Step-by-step Trace")
    for i, step in enumerate(trace, 1):
        group = step["group"]
        term = group_to_product_term(group, num_vars)
        covers = ", ".join(str(m) for m in step["covers"]) if step.get("covers") else ""
        group_minterms = ", ".join(str(m) for m in sorted(group))

        label = f"Step {i}: {step.get('step', '')}"
        with st.expander(label, expanded=(i == 1)):
            st.write(f"Product term: {term}")
            st.write(f"Group minterms: {group_minterms}")
            if covers:
                st.write(f"Newly covered: {covers}")
            _render_variable_elimination(group, num_vars)


def render_truth_table(minterms: list[int], num_vars: int):
    """Render a truth table showing all rows with output column."""
    import pandas as pd

    var_names = VAR_NAMES[:num_vars]
    rows = []
    for i in range(2 ** num_vars):
        bits = [int(b) for b in format(i, f"0{num_vars}b")]
        output = 1 if i in minterms else 0
        rows.append(bits + [output])

    df = pd.DataFrame(rows, columns=var_names + ["F"])
    st.dataframe(df, use_container_width=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _render_variable_elimination(group: frozenset[int], num_vars: int):
    """Show which variables are constant vs eliminated in the group."""
    minterms = sorted(group)
    for bit_pos in range(num_vars):
        shift = num_vars - 1 - bit_pos
        bit_vals = set((m >> shift) & 1 for m in minterms)
        var = VAR_NAMES[bit_pos]
        if len(bit_vals) == 1:
            val = bit_vals.pop()
            st.write(f"{var} = {val} (kept)")
        else:
            st.write(f"{var} varies (eliminated)")