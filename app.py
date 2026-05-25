"""
K-Map Solver & Boolean Simplifier — Streamlit entry point.

Run with:
    streamlit run app.py
"""

import streamlit as st
from solver.parser import parse_minterms, parse_truth_table, parse_csv_upload
from solver.implicants import find_prime_implicants, select_essential_implicants
from solver.expression import build_sop, build_pos, build_verilog
from ui.grid import render_kmap
from ui.components import (
    render_sop_display,
    render_pos_display,
    render_verilog_display,
    render_output_summary,
    render_trace,
    render_truth_table,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="K-Map Solver",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Minimal UI: no custom styling. Focus on functionality only.


# ---------------------------------------------------------------------------
# Sidebar — Input
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🗺️ K-Map Solver")
    st.markdown("*Boolean logic simplifier*")
    st.divider()

    input_mode = st.selectbox(
        "Input Method",
        ["Minterm Notation", "Truth Table (Manual)", "CSV Upload"],
        help="Choose how to provide your Boolean function.",
    )

    minterms, num_vars = None, None
    parse_error = None

    # ------ Minterm Notation ------
    if input_mode == "Minterm Notation":
        st.markdown("**Enter minterms**")
        st.caption("Formats: `Σm(0,1,3,7)` · `m(0,1,3,7)` · `0,1,3,7`")
        minterm_input = st.text_input(
            "Minterms", placeholder="e.g. m(0,1,3,7)", label_visibility="collapsed"
        )
        if minterm_input.strip():
            try:
                minterms, num_vars = parse_minterms(minterm_input)
                st.success(f"✓ {len(minterms)} minterms · {num_vars} variables")
            except ValueError as e:
                parse_error = str(e)

    # ------ Truth Table (Manual) ------
    elif input_mode == "Truth Table (Manual)":
        num_vars_sel = st.selectbox("Number of Variables", [2, 3, 4], index=1)
        st.markdown(f"**Enter truth table ({2**num_vars_sel} rows)**")
        st.caption("Format each row as: `0 0 1` (inputs then output, space-separated)")

        rows_input = st.text_area(
            "Truth Table Rows",
            height=160,
            placeholder="\n".join(
                " ".join(format(i, f"0{num_vars_sel}b")) + " 0"
                for i in range(min(4, 2**num_vars_sel))
            ) + "\n...",
            label_visibility="collapsed",
        )

        if rows_input.strip():
            try:
                rows = [
                    [int(v) for v in line.split()]
                    for line in rows_input.strip().splitlines()
                    if line.strip()
                ]
                minterms, num_vars = parse_truth_table(rows)
                st.success(f"✓ {len(minterms)} minterms · {num_vars} variables")
            except ValueError as e:
                parse_error = str(e)

    # ------ CSV Upload ------
    else:
        st.markdown("**Upload CSV truth table**")
        st.caption("Last column = output. Columns: A, B[, C[, D]], F")
        uploaded = st.file_uploader("CSV File", type=["csv"], label_visibility="collapsed")
        if uploaded:
            try:
                minterms, num_vars = parse_csv_upload(uploaded)
                st.success(f"✓ {len(minterms)} minterms · {num_vars} variables")
            except ValueError as e:
                parse_error = str(e)

    # ------ Output control ------
    st.divider()
    st.markdown("**Output settings**")
    output_name = st.text_input(
        "Output variable name",
        value="F",
        max_chars=1,
        help="Set the final output name shown in the result expression.",
    )
    output_name = output_name.strip() or "F"

    st.markdown(
        "_The final minimized output is always shown after solving."
    )
    show_pos = st.checkbox("Show minimized POS expression", value=False)
    show_verilog = st.checkbox("Show Verilog export", value=False)
    show_truth_table = st.checkbox("Show truth table", value=True)

    st.divider()
    solve_btn = st.button("🚀 Solve", use_container_width=True)


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown("# 🗺️ K-Map Solver & Boolean Simplifier")
st.markdown(
    "Solve and visualize Karnaugh Maps interactively. "
    "Supports 2–4 variable inputs with prime implicant groupings, "
    "SOP/POS output, and step-by-step solution trace."
)

if parse_error:
    st.error(f"**Input Error:** {parse_error}")

elif solve_btn and minterms is not None:
    st.divider()

    # --- Run solver ---
    with st.spinner("Solving K-Map..."):
        prime_imps = find_prime_implicants(minterms, num_vars)
        selected, trace = select_essential_implicants(minterms, prime_imps)
        sop_expr = build_sop(selected, num_vars)

    # --- Layout: K-Map | Results ---
    col_kmap, col_results = st.columns([1.2, 1], gap="large")

    with col_kmap:
        st.markdown("### K-Map Visualization")
        fig = render_kmap(minterms, num_vars, selected)
        st.pyplot(fig, use_container_width=True)

    with col_results:
        st.markdown("### Results")
        render_output_summary(output_name, sop_expr, minterms, num_vars)
        render_sop_display(sop_expr, output_name)

        if show_pos:
            pos_expr = build_pos(minterms, num_vars)
            render_pos_display(pos_expr, output_name)

        if show_verilog:
            verilog_code = build_verilog(sop_expr, num_vars, output_name)
            render_verilog_display(verilog_code)

        st.markdown("#### Prime Implicants Found")
        from solver.expression import group_to_product_term
        for i, pi in enumerate(prime_imps):
            term = group_to_product_term(pi, num_vars)
            is_selected = pi in selected
            icon = "✅" if is_selected else "⬜"
            size_label = f"{len(pi)}-cell"
            minterms_str = ", ".join(str(m) for m in sorted(pi))
            st.markdown(
                f"{icon} `{term}` — {size_label} — minterms: `{{{minterms_str}}}`"
            )

    # --- Truth Table ---
    if show_truth_table:
        st.divider()
        with st.expander("📋 Truth Table", expanded=False):
            render_truth_table(minterms, num_vars)

    # --- Step-by-step trace ---
    st.divider()
    render_trace(trace, num_vars)

elif not solve_btn:
    # Landing state — show examples
    st.info(
        "👈 Enter your Boolean function in the sidebar and click **Solve** to begin.",
        icon="💡",
    )
    st.markdown("### Example Inputs")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    with ex_col1:
        st.markdown(
            """
            **2-Variable**
            m(0, 3)
            Expected: `F = A'B' + AB`
            """
        )
    with ex_col2:
        st.markdown(
            """
            **3-Variable**
        m(0, 1, 2, 4, 5, 6)
        Expected: `F = A'B' + AB' + B'C'` (etc.)
            """
        )
    with ex_col3:
        st.markdown(
            """
            **4-Variable**
            m(0, 1, 2, 3, 8, 9, 10, 11)
            Expected: `F = A'B + AB'` or similar
            """
        )
        
