#!/usr/bin/env python3
"""
Problem: knapsack
URL: https://open.kattis.com/problems/knapsack
"""

import sys


def solve(capacity: int, items: list[tuple[int, int]]):
    # dp[item][capacity]
    dp = [[0] * (capacity + 1) for _ in range(len(items) + 1)]

    for item_idx in range(1, len(items) + 1):
        value, weight = items[item_idx - 1]
        for c in range(1, capacity + 1):
            # Item can fit in c
            with_item = 0
            if weight <= c:
                with_item = value + dp[item_idx - 1][c - weight]

            dp[item_idx][c] = max(dp[item_idx - 1][c], with_item)

    choosen_items = []
    idx = len(items)
    c = capacity
    while idx > 0:
        current, prev = dp[idx][c], dp[idx - 1][c]
        if current != prev:  # We picked the item
            choosen_items.append(idx - 1)
            c -= items[idx - 1][1]
        idx -= 1

    # print(dp)
    print(len(choosen_items))
    print(" ".join([str(x) for x in reversed(choosen_items)]))


if __name__ == "__main__":
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        [capacity, N] = [int(n) for n in line.split(" ")]
        items = []
        for _ in range(N):
            values = [int(n) for n in sys.stdin.readline().split(" ")]
            items.append((values[0], values[1]))
        solve(capacity, items)
