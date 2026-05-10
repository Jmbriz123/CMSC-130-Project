"""Unit tests for solver/kmap.py"""
import pytest
from solver.kmap import (
    build_grid, cell_to_minterm, minterm_to_cell, generate_all_groups
)


class TestBuildGrid:
    def test_2var_all_ones(self):
        grid = build_grid([0, 1, 2, 3], 2)
        assert all(cell == 1 for row in grid for cell in row)

    def test_2var_empty(self):
        grid = build_grid([], 2)
        assert all(cell == 0 for row in grid for cell in row)

    def test_3var_spot_check(self):
        grid = build_grid([0, 1], 3)
        # minterm 0 → A=0,B=0,C=0: row_gray=0→row_idx=0, col_gray=00→col_idx=0
        assert grid[0][0] == 1
        # minterm 1 → A=0,B=0,C=1: col_gray=01→col_idx=1
        assert grid[0][1] == 1


class TestCellMinterm:
    def test_roundtrip_3var(self):
        for m in range(8):
            ri, ci = minterm_to_cell(m, 3)
            assert cell_to_minterm(ri, ci, 3) == m

    def test_roundtrip_4var(self):
        for m in range(16):
            ri, ci = minterm_to_cell(m, 4)
            assert cell_to_minterm(ri, ci, 4) == m


class TestGenerateAllGroups:
    def test_groups_are_power_of_two_size(self):
        groups = generate_all_groups(3)
        for g in groups:
            size = len(g)
            assert size & (size - 1) == 0, f"Group size {size} not a power of 2"

    def test_groups_within_range_4var(self):
        groups = generate_all_groups(4)
        for g in groups:
            assert all(0 <= m <= 15 for m in g)

    def test_single_cell_groups_exist(self):
        groups = generate_all_groups(2)
        single_cells = [g for g in groups if len(g) == 1]
        assert len(single_cells) == 4  # One per cell in 2-var K-Map