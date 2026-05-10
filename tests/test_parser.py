"""Unit tests for solver/parser.py"""
import pytest
from solver.parser import parse_minterms, parse_truth_table


class TestParseMinterms:
    def test_sigma_notation(self):
        m, n = parse_minterms("Σm(0,1,3,7)")
        assert m == [0, 1, 3, 7]
        assert n == 3

    def test_m_notation(self):
        m, n = parse_minterms("m(0,1,3,7)")
        assert m == [0, 1, 3, 7]

    def test_plain_csv(self):
        m, n = parse_minterms("0,1,3,7")
        assert m == [0, 1, 3, 7]

    def test_space_separated(self):
        m, n = parse_minterms("0 1 3 7")
        assert m == [0, 1, 3, 7]

    def test_deduplication(self):
        m, _ = parse_minterms("1,1,3,3")
        assert m == [1, 3]

    def test_two_var(self):
        m, n = parse_minterms("0,1")
        assert n == 2

    def test_four_var(self):
        m, n = parse_minterms("0,1,8,15")
        assert n == 4

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_minterms("0,1,16")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_minterms("")


class TestParseTruthTable:
    def test_basic_2var(self):
        rows = [[0, 0, 1], [0, 1, 0], [1, 0, 0], [1, 1, 1]]
        m, n = parse_truth_table(rows)
        assert m == [0, 3]
        assert n == 2

    def test_wrong_row_count_raises(self):
        with pytest.raises(ValueError, match="exactly 4 rows"):
            parse_truth_table([[0, 0, 1], [0, 1, 0]])

    def test_mismatched_cols_raises(self):
        rows = [[0, 0], [0, 1], [1, 0], [1, 1]]  # Missing output column
        with pytest.raises(ValueError):
            parse_truth_table(rows)