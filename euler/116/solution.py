#!/usr/bin/env python3
"""
Project Euler Problem 116
URL: https://projecteuler.net/problem=116
"""

import sys


def solve(N: int, red: int, green: int, blue: int) -> int:
    """
    Calculate the number of ways N blocks can be tiled with one of the choices.
    """

    def tile(block_size: int) -> int:
        dp = [0] * (N + 1)
        dp[0] = 1

        for n in range(1, N + 1):
            # 1. Starts with a gray
            dp[n] += dp[n - 1]

            if n >= block_size:
                dp[n] += dp[n - (block_size)]

        # If we ignore the term 2, it would mean we could all the tiles
        # being gray. This is a invalid case and we need to subtract it
        return dp[N] - 1

    return tile(red) + tile(green) + tile(blue)


if __name__ == "__main__":
    [N, red, green, blue] = [int(n) for n in sys.stdin.readline().split(" ")]
    print(solve(N, red, green, blue))
