"""
-------------
Reusable Streamlit UI component helpers.
Keeps app.py clean by isolating rendering logic.
"""

import streamlit as st
from solver.expression import group_to_product_term, VAR_NAMES


def render_sop_display(sop_expr: str):
    """Render the SOP result in a styled box."""
    st.markdown(
        f"""
        <div style="
            background: #313244;
            border: 1.5px solid #89B4FA;
            border-radius: 10px;
            padding: 18px 24px;
            margin: 12px 0;
            text-align: center;
        ">
            <div style="color:#A6ADC8; font-size:13px; margin-bottom:6px;">
                Minimized SOP Expression
            </div>
            <div style="
                color:#CDD6F4;
                font-size:28px;
                font-weight:700;
                font-family: 'Courier New', monospace;
                letter-spacing: 2px;
            ">
                F = {sop_expr}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pos_display(pos_expr: str):
    """Render the POS result in a styled box."""
    st.markdown(
        f"""
        <div style="
            background: #313244;
            border: 1.5px solid #A6E3A1;
            border-radius: 10px;
            padding: 18px 24px;
            margin: 12px 0;
            text-align: center;
        ">
            <div style="color:#A6ADC8; font-size:13px; margin-bottom:6px;">
                Minimized POS Expression
            </div>
            <div style="
                color:#CDD6F4;
                font-size:24px;
                font-weight:700;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
            ">
                F = {pos_expr}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_verilog_display(verilog_code: str):
    """Render the Verilog export in a code block."""
    st.markdown("**Verilog Export**")
    st.code(verilog_code, language="verilog")


def render_trace(trace: list[dict], num_vars: int):
    """Render the step-by-step solution trace as an expandable table."""
    if not trace:
        st.info("No grouping steps to display.")
        return

    st.markdown("#### 🔍 Step-by-Step Solution Trace")
    for i, step in enumerate(trace, 1):
        group = step["group"]
        term = group_to_product_term(group, num_vars)
        covers = ", ".join(str(m) for m in step["covers"])
        group_minterms = ", ".join(str(m) for m in sorted(group))

        label = f"Step {i} — **{step['step']}**: `{term}`"
        with st.expander(label, expanded=(i == 1)):
            col1, col2, col3 = st.columns(3)
            col1.metric("Group Size", f"{len(group)} cells")
            col2.markdown(f"**Minterms in group:**<br>`{{{group_minterms}}}`",
                          unsafe_allow_html=True)
            col3.markdown(f"**Newly covered:**<br>`{{{covers}}}`",
                          unsafe_allow_html=True)

            # Show which variables are eliminated
            _render_variable_elimination(group, num_vars)


def render_truth_table(minterms: list[int], num_vars: int):
    """Render a truth table showing all rows with output column highlighted."""
    import pandas as pd

    var_names = VAR_NAMES[:num_vars]
    rows = []
    for i in range(2 ** num_vars):
        bits = [int(b) for b in format(i, f"0{num_vars}b")]
        output = 1 if i in minterms else 0
        rows.append(bits + [output])

    df = pd.DataFrame(rows, columns=var_names + ["F"])
    st.dataframe(
        df.style.apply(
            lambda row: [
                "background-color: #313244; color: #A6E3A1"
                if row["F"] == 1
                else "background-color: transparent; color: #7F849C"
                for _ in row
            ],
            axis=1,
        ),
        use_container_width=True,
        height=min(38 * (2 ** num_vars) + 38, 400),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_variable_elimination(group: frozenset[int], num_vars: int):
    """Show a small table of which variables are constant vs eliminated."""
    minterms = sorted(group)
    rows = []
    for bit_pos in range(num_vars):
        shift = num_vars - 1 - bit_pos
        bit_vals = set((m >> shift) & 1 for m in minterms)
        var = VAR_NAMES[bit_pos]
        if len(bit_vals) == 1:
            val = bit_vals.pop()
            status = f"**{var}** = {val}  →  `{'1' if val else \"0\"}`  (kept as {'`' + var + '`' if val else '`' + var + \"'`\"})"
        else:
            status = f"~~{var}~~ varies (0 and 1)  →  **eliminated**"
        rows.append(status)

    for r in rows:
        st.markdown(f"- {r}")