#!/usr/bin/env python3
"""
Project Euler Problem 117
URL: https://projecteuler.net/problem=117
"""

import sys


def solve(N: int, red: int, green: int, blue: int) -> int:
    """
    Calculate the number of ways N blocks can be tiled with any of the choices.
    """

    dp = [0] * (N + 1)
    dp[0] = 1

    for n in range(1, N + 1):
        # 1. Starts with a gray
        dp[n] += dp[n - 1]

        if n >= red:
            dp[n] += dp[n - red]
        if n >= green:
            dp[n] += dp[n - green]
        if n >= blue:
            dp[n] += dp[n - blue]

    return dp[N]


if __name__ == "__main__":
    N = int(sys.stdin.readline())
    print(solve(N, 2, 3, 4))
