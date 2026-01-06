#!/usr/bin/env python3
"""
Problem: scenes
URL: https://open.kattis.com/problems/scenes
"""

import sys


def recursive_solve(L: int, W: int, H: int):
    def recurse(ribbon: int, w: int):
        if ribbon >= 0 and w == W:
            return 1
        if ribbon < 0:
            return 0

        scenes = 0
        for i in range(min(ribbon, H) + 1):
            v = recurse(ribbon - i, w + 1)
            scenes += v

        return scenes

    # Finds all possible scenes that are available, which also counts scenes
    # where the height of the ribbon is the same.
    # We need (ribbon length = rl)
    #   rl <= H,
    #   W * rl <= L
    # There can only be one valid plain for a value of rl
    #   0 <= rl <= min(H, L/W)
    #   rl  = min(H, L/W) + 1  (1 accounts for rl == 0)
    total = recurse(L, 0)
    plains = min(H, L // W) + 1
    return total - plains


def solve(L: int, W: int, H: int):
    MOD = 10**9 + 7

    dp = [0] * (L + 1)
    dp[0] = 1

    for col in range(1, W + 1):
        # Create a prefix_sum for the current DP state
        prefix_sum = [0] * (L + 2)
        for i in range(0, L + 1):
            prefix_sum[i + 1] = (prefix_sum[i] + dp[i]) % MOD

        # Update dp for the next column using the prefix sums
        new_dp = [0] * (L + 1)
        for s in range(0, L + 1):
            # We want the sum of dp[s-H ... s]
            low = max(0, s - H)
            high = s

            # Range sum using prefix sums: P[high + 1] - P[low]
            new_dp[s] = (prefix_sum[high + 1] - prefix_sum[low]) % MOD

        dp = new_dp
    plains = min(H, L // W) + 1
    return (sum(dp) - plains) % MOD


if __name__ == "__main__":
    [L, W, H] = [int(x) for x in sys.stdin.readline().split(" ")]
    print(solve(L, W, H))
