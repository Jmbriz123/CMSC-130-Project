"""Unit tests for solver/implicants.py"""
import pytest
from solver.implicants import find_prime_implicants, select_essential_implicants


class TestFindPrimeImplicants:
    def test_all_ones_2var(self):
        # F = 1 for all inputs → one group of 4 → PI = {0,1,2,3}
        pis = find_prime_implicants([0, 1, 2, 3], 2)
        assert any(frozenset([0, 1, 2, 3]) == pi for pi in pis)

    def test_single_minterm(self):
        pis = find_prime_implicants([5], 3)
        assert any(5 in pi for pi in pis)

    def test_classic_3var(self):
        # m(0,1,3,7) — known PIs
        pis = find_prime_implicants([0, 1, 3, 7], 3)
        assert len(pis) >= 1


class TestSelectEssentialImplicants:
    def test_full_cover(self):
        minterms = [0, 1, 2, 3]
        pis = find_prime_implicants(minterms, 2)
        selected, trace = select_essential_implicants(minterms, pis)
        covered = set()
        for g in selected:
            covered |= g
        assert set(minterms).issubset(covered)

    def test_trace_has_entries(self):
        minterms = [0, 1, 3, 7]
        pis = find_prime_implicants(minterms, 3)
        _, trace = select_essential_implicants(minterms, pis)
        assert len(trace) >= 1

    def test_empty_minterms(self):
        selected, trace = select_essential_implicants([], [])
        assert selected == []
        assert trace == []