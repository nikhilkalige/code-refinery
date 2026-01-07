#!/usr/bin/env python3
"""
Problem: narrowartgallery
URL: https://open.kattis.com/problems/narrowartgallery
"""

from math import inf
import sys
from enum import IntEnum
from functools import lru_cache


class State(IntEnum):
    E = 0
    L = 1
    R = 2


def solve(N: int, rooms_to_close: int, rooms: list[tuple[int, int]]):
    """
    Rooms is a N * 2 array of values. We need to minimize the sum of values of all closed rooms.
    """

    dp: list[list[list[int | float | None]]] = [
        [[None] * (rooms_to_close + 1) for _ in range(3)] for _ in range(N + 1)
    ]

    def recurse(row: int, prev_state: State, toclose: int) -> float | int:
        if toclose > N - row:
            return -inf
        if row == N and toclose != 0:
            return -inf
        if row == N and toclose == 0:
            return 0

        if dp[row][prev_state][toclose] is not None:
            return dp[row][prev_state][toclose]

        L = rooms[row][0]
        R = rooms[row][1]

        sE = recurse(row + 1, State.E, toclose) + L + R
        sL = recurse(row + 1, State.L, toclose - 1) + R if toclose > 0 else -inf
        sR = recurse(row + 1, State.R, toclose - 1) + L if toclose > 0 else -inf

        value = 0
        if prev_state == State.E:
            value = max(sE, sL, sR)
        elif prev_state == State.L:
            # We can choose E or L
            value = max(sE, sL)
        elif prev_state == State.R:
            # We can choose E or R
            value = max(sE, sR)

        dp[row][prev_state][toclose] = value
        return value

    return recurse(0, State.E, rooms_to_close)


if __name__ == "__main__":
    [N, k] = [int(n) for n in sys.stdin.readline().split(" ")]
    gallery = []
    for _ in range(N):
        values = [int(n) for n in sys.stdin.readline().split(" ")]
        gallery.append((values[0], values[1]))

    print(solve(N, k, gallery))
