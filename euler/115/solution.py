#!/usr/bin/env python3
"""
Project Euler Problem 115
URL: https://projecteuler.net/problem=115
"""

import sys


def ways(N: int, min_len: int) -> int:
    """
    Calculates the number of ways to fill a row of length N with blocks
    of minimum length 'min_len', separated by at least one gap.

    Logic:
    To find the total ways for a row of length 'n' (dp[n]), we look at
    how the row STARTS on the far left:

    1. It starts with a GREY square:
       - There are n-1 squares remaining.
       - Ways: dp[n-1]

    2. It starts with a RED block of length 'k':
       - 'k' must be between min_len and n.
       - If k == n: The whole row is red (1 way).
       - If k < n: The block MUST be followed by a grey spacer.
         This uses (k + 1) squares total.
         Ways: dp[n - (k + 1)]
    """
    # dp[i] stores the number of ways to fill a row of length i
    dp = [0] * (N + 1)

    # Base Case: An empty row has 1 way to be "filled" (doing nothing)
    dp[0] = 1

    # Build the DP table from the bottom up
    for n in range(1, N + 1):
        # Case 1: First square is grey
        dp[n] = dp[n - 1]

        # Case 2: First block is red of length 'bsize'
        for bsize in range(min_len, n + 1):
            if bsize == n:
                dp[n] += 1  # The entire row is one solid red block
            else:
                # Red block (bsize) + Spacer (1) leaves (n - bsize - 1) squares
                dp[n] += dp[n - bsize - 1]

    return dp[N]


def solve(block_size: int):
    for N in range(block_size, 1_000):
        count = ways(N, block_size)
        if count > 1_000_000:
            return N


if __name__ == "__main__":
    block_size = int(sys.stdin.readline())
    print(solve(block_size))
