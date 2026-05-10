"""
-------------
Prime implicant identification and essential prime implicant selection.

Algorithm:
  1. Filter valid groups — only those entirely within the ON-set of minterms.
  2. Identify prime implicants — groups not fully contained in any larger valid group.
  3. Find essential prime implicants — the only group covering a given minterm.
  4. Cover remaining minterms greedily (largest group first).
"""

from solver.kmap import generate_all_groups


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_prime_implicants(
    minterms: list[int], num_vars: int
) -> list[frozenset[int]]:
    """
    Identify all prime implicants for the given ON-set minterms.

    A prime implicant is a maximal valid group — no larger valid group
    fully contains it.

    Returns:
        Sorted list of frozensets (each is one prime implicant group).
    """
    minterm_set = frozenset(minterms)
    all_groups = generate_all_groups(num_vars)

    # Keep only groups whose cells are all minterms (ON-set cells only)
    valid = [g for g in all_groups if g.issubset(minterm_set) and len(g) >= 1]

    # A group is prime if no strictly larger valid group contains it
    prime_implicants = []
    for g in valid:
        is_prime = not any(
            g < other for other in valid  # strict subset
        )
        if is_prime:
            prime_implicants.append(g)

    # Deduplicate and sort by descending size for readability
    seen = set()
    result = []
    for pi in sorted(prime_implicants, key=lambda x: -len(x)):
        key = frozenset(pi)
        if key not in seen:
            seen.add(key)
            result.append(pi)

    return result


def select_essential_implicants(
    minterms: list[int],
    prime_implicants: list[frozenset[int]],
) -> tuple[list[frozenset[int]], list[dict]]:
    """
    Select a minimal cover of all minterms using essential prime implicants
    and a greedy fallback for any remaining uncovered minterms.

    Returns:
        (selected, trace)
        - selected: list of chosen prime implicant frozensets
        - trace: list of step dicts for the solution log
          Each step: {"step": str, "group": frozenset, "covers": list[int]}
    """
    uncovered = set(minterms)
    selected: list[frozenset[int]] = []
    trace: list[dict] = []

    # --- Pass 1: Essential prime implicants ---
    essentials = _find_essentials(minterms, prime_implicants)

    for pi in essentials:
        if pi & uncovered:  # Only pick if it still covers something new
            selected.append(pi)
            newly_covered = sorted(pi & uncovered)
            uncovered -= pi
            trace.append({
                "step": "Essential Prime Implicant",
                "group": pi,
                "covers": newly_covered,
            })

    # --- Pass 2: Greedy cover for remaining minterms ---
    remaining_pis = [pi for pi in prime_implicants if pi not in selected]

    while uncovered:
        # Pick the PI that covers the most uncovered minterms
        best = max(
            remaining_pis,
            key=lambda pi: len(pi & uncovered),
            default=None,
        )
        if best is None or not (best & uncovered):
            break  # Should not happen with valid input

        selected.append(best)
        newly_covered = sorted(best & uncovered)
        uncovered -= best
        remaining_pis.remove(best)
        trace.append({
            "step": "Greedy Cover",
            "group": best,
            "covers": newly_covered,
        })

    return selected, trace


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_essentials(
    minterms: list[int],
    prime_implicants: list[frozenset[int]],
) -> list[frozenset[int]]:
    """
    Return prime implicants that are the *only* group covering at least one minterm.
    """
    essentials = []
    for m in minterms:
        covering = [pi for pi in prime_implicants if m in pi]
        if len(covering) == 1:
            pi = covering[0]
            if pi not in essentials:
                essentials.append(pi)
    return essentials