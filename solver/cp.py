#!/usr/bin/env python3
"""
Unified helper script for competitive programming with shared abstractions.

Platforms:
  - kattis: new/test/run/submit using kattis/.kattisrc
  - euler:  new/run/test/answer/submit for Project Euler

Highlights of the refactor:
  - Shared Runner and Platform base in cp_core.py
  - Per-platform logic in kattis/platform.py and euler/platform.py

Usage examples:
  # As a script
  ./solver/cp.py kattis new hello
  ./solver/cp.py kattis test hello
  ./solver/cp.py kattis submit hello

  ./solver/cp.py euler new 1
  ./solver/cp.py euler run 1
  ./solver/cp.py euler test 1
  ./solver/cp.py euler submit 1

  # Via flake devShell helper (bin: cph)
  cph kattis test hello
  cph euler test 1
"""

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path when running as a script (./solver/cp.py)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from solver.core import Platform  # noqa: E402
from euler.platform import EulerPlatform  # noqa: E402
from kattis.platform import KattisPlatform  # noqa: E402


def build_parser(platforms: list[Platform]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified CP helper (Kattis + Project Euler)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="platform", required=True)
    for plat in platforms:
        plat.register_cli(subparsers)
    return parser


def main():
    platforms: list[Platform] = [KattisPlatform(), EulerPlatform()]
    parser = build_parser(platforms)
    # Autodetect platform by current directory if not provided
    names = {p.name for p in platforms}
    if len(sys.argv) > 1 and sys.argv[1] not in names:
        parent = Path.cwd().parent.name
        if parent in names:
            sys.argv.insert(1, parent)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
