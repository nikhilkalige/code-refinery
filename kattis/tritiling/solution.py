#!/usr/bin/env python3
"""
Problem: tritiling
URL: https://open.kattis.com/problems/tritiling
"""

from sys import stdin


def solve(N: int):
    """
    Calculates the number of tiling configurations for a 3xN board.

    Time Complexity: O(N)
    Space Complexity: O(N) - Can be optimized to O(1)
    """
    # N must be even for a valid tiling; odd N always results in 0.
    # The Kattis problem ends input with -1.
    if N < 0:
        return ""
    if N % 2 != 0:
        return 0

    # dp[mask][col]
    # mask: binary representation of rows (0-7)
    # 000 (0) -> All rows empty
    # 111 (7) -> All rows filled
    dp = [[0] * (N + 1) for _ in range(8)]

    # Base Case: An empty board (width 0) is "full" in 1 way.
    dp[7][0] = 1

    for col in range(1, N + 1):
        # State transitions based on how dominoes can be placed:
        # 1. Horizontal dominoes bridge column (col-1) to (col)
        # 2. Vertical dominoes are placed entirely within (col)

        # Current column empty: requires previous col to be full (horizontal)
        dp[0][col] += dp[7][col - 1]

        # Top row only: previous must have middle/bottom (6)
        dp[1][col] += dp[6][col - 1]

        # Middle row only: previous must have top/bottom (5)
        dp[2][col] += dp[5][col - 1]

        # Top + Middle: previous is bottom (4) OR full (7) via vertical
        dp[3][col] += dp[4][col - 1] + dp[7][col - 1]

        # Bottom row only: previous must have top/middle (3)
        dp[4][col] += dp[3][col - 1]

        # Top + Bottom: previous must have middle (2)
        dp[5][col] += dp[2][col - 1]

        # Middle + Bottom: previous is top (1) OR full (7) via vertical
        dp[6][col] += dp[1][col - 1] + dp[7][col - 1]

        # Column Full: previous empty (0) OR through specific vertical combos
        dp[7][col] += dp[6][col - 1] + dp[3][col - 1] + dp[0][col - 1]

    # The answer is the number of ways to have a completely full board at width N
    return dp[7][N]


def solve_trominos(N: int):
    # dp[mask][col] = number of ways to fully tile columns [0 .. col-1],
    # where `mask` describes which cells in column `col` are already filled
    # by tiles extending from column `col-1`.
    #
    # mask meanings (2-bit, top-bottom):
    # 0: [ . ]  no cells filled
    #    [ . ]
    # 1: [ X ]  top filled
    #    [ . ]
    # 2: [ . ]  bottom filled
    #    [ X ]
    # 3: [ X ]  both filled
    #    [ X ]

    dp = [[0] * (N + 1) for _ in range(4)]

    # Base case:
    # Before processing any columns, there are no overhangs
    dp[0][0] = 1

    # Process columns 1..N
    for col in range(1, N + 1):
        # mask 0:
        # - from mask 0: vertical domino fills the column
        # - from mask 3: column was already filled; just advance
        dp[0][col] += dp[0][col - 1] + dp[3][col - 1]

        # mask 1 (top cell filled):
        # - from mask 0: L-tromino creates a top overhang
        # - from mask 2: horizontal domino completes bottom cell
        dp[1][col] += dp[0][col - 1] + dp[2][col - 1]

        # mask 2 (bottom cell filled):
        # - from mask 0: L-tromino creates a bottom overhang
        # - from mask 1: horizontal domino completes top cell
        dp[2][col] += dp[0][col - 1] + dp[1][col - 1]

        # mask 3 (both cells filled):
        # - from mask 0: two horizontal dominoes
        # - from mask 1 or 2: L-tromino fills remainder and both in next column
        dp[3][col] += dp[0][col - 1] + dp[1][col - 1] + dp[2][col - 1]

    # Fully tiled 2×N board means no overhangs past column N
    return dp[0][N]


# print(solve_trominos(10))

if __name__ == "__main__":
    for line in stdin.readlines():
        print(solve(int(line)))
