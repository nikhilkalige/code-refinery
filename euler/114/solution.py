#!/usr/bin/env python3
"""
Project Euler Problem 114
URL: https://projecteuler.net/problem=114
"""

import sys


def solve(block_size: int) -> int:
    """
    Calculates the number of ways to fill a row of length N with blocks
    of minimum length 'block_size', separated by at least one gap.

    Logic:
    To find the total ways for a row of length 'n' (dp[n]), we look at
    how the row STARTS on the far left:

    1. It starts with a GREY square:
       - There are n-1 squares remaining.
       - Ways: dp[n-1]

    2. It starts with a RED block of length 'k':
       - 'k' must be between block_size and n.
       - If k == n: The whole row is red (1 way).
       - If k < n: The block MUST be followed by a grey spacer.
         This uses (k + 1) squares total.
         Ways: dp[n - (k + 1)]
    """
    # We don't know the value of N, lets start with a 1000
    N = 1000
    C = 1_000_000

    dp = [0] * (N + 1)
    dp[0] = 1

    for n in range(1, N + 1):
        dp[n] = dp[n - 1]

        for m in range(block_size, n + 1):
            if m == n:
                dp[n] += 1
            else:
                dp[n] += dp[n - (m + 1)]

        if dp[n] > C:
            return n
    return N


if __name__ == "__main__":
    [a] = [int(n) for n in sys.stdin.readline().split(" ")]
    print(solve(a))
