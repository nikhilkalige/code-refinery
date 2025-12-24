#!/usr/bin/env python3
"""
Problem: magicalcows
URL: https://open.kattis.com/problems/magicalcows
"""

import sys


def parse(lines: list[str]):
    line = lines[0]
    [max_cows, num_farms, num_days] = [int(p) for p in line.split()]

    num_cows_in_farm = [int(line) for line in lines[1 : 1 + num_farms]]
    visitation_days = [
        int(line) for line in lines[num_farms + 1 : num_farms + num_days + 1]
    ]
    return (max_cows, num_farms, num_days, num_cows_in_farm, visitation_days)


def solve(lines: list[str]):
    (max_cows, num_farms, num_days, num_cows_in_farm, visitation_days) = parse(lines)
    last_day = max(visitation_days)
    dp_table = [[0] * (max_cows + 1) for _ in range(last_day + 1)]

    # Count the frequency of farms based on the number of cows
    for count in num_cows_in_farm:
        dp_table[0][count] += 1

    for day in range(0, last_day):
        # Double the number of cows
        for count in range(1, max_cows + 1):
            if count <= max_cows / 2:
                # Cow count on farm with size `count` doubles, but farms remains the same
                dp_table[day + 1][count * 2] += dp_table[day][count]
            else:
                # Cow count exceeds limit, so double the farms. The new `count` will be the same
                # as we double the size, and they get equally divided in the new farms
                dp_table[day + 1][count] += 2 * dp_table[day][count]

    for day in visitation_days:
        print(sum(dp_table[day]))


if __name__ == "__main__":
    data = [line.strip() for line in sys.stdin.readlines()]
    solve(data)
