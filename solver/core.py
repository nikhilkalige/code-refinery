#!/usr/bin/env python3
"""
Core utilities shared by competitive programming helpers.
Includes: Runner, Platform base class, and helpers.
"""

import argparse
import io
import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).parent.parent


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)

    def flush(self):
        for f in self.files:
            f.flush()


class Runner:
    @staticmethod
    def run(solution_file: Path, stdin_file: Path | None = None) -> str:
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        output_capture = io.StringIO()
        sys.stdout = Tee(sys.__stdout__, output_capture)
        try:
            if stdin_file is not None:
                with open(stdin_file, "r") as f:
                    sys.stdin = f
                    spec = importlib.util.spec_from_file_location("__main__", solution_file)
                    mod = importlib.util.module_from_spec(spec)
                    assert spec and spec.loader
                    spec.loader.exec_module(mod)
            else:
                spec = importlib.util.spec_from_file_location("__main__", solution_file)
                mod = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(mod)
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
        return output_capture.getvalue().rstrip("\n")


def print_banner(title: str):
    line = "=" * 50
    print(line)
    print(title)
    print(line)


def compare_report(expected: str, actual: str) -> bool:
    if actual == expected:
        print("✅ PASSED")
        return True
    print("❌ FAILED")
    print("\nExpected:")
    print(expected)
    print("\nActual:")
    print(actual)
    return False


class Platform(ABC):
    name: str = ""
    solution_name: str = "solution.py"

    def __init__(self) -> None:
        if not self.name:
            raise ValueError("Platform must define name")
        self.base_dir = repo_root() / self.name

    # Paths
    def problem_dir(self, problem_id: str) -> Path:
        return self.base_dir / problem_id

    def solution_file(self, problem_id: str) -> Path:
        return self.problem_dir(problem_id) / self.solution_name

    # Helpers
    def detect_current_problem(self) -> str:
        cwd = Path.cwd()
        if cwd.parent.name == self.name:
            return cwd.name
        raise ValueError(
            f"Not in a {self.name} problem directory. Specify problem_id or cd into {self.name}/<id>"
        )

    def resolve_problem_id(self, problem_id: str | None) -> str:
        return problem_id if problem_id else self.detect_current_problem()

    def ensure_solution_exists(self, problem_id: str):
        sol = self.solution_file(problem_id)
        if not sol.exists():
            print(f"Error: Solution file not found: {sol}")
            sys.exit(1)

    # Common actions with sensible defaults
    @abstractmethod
    def cmd_new(self, problem_id: str): ...

    def cmd_run(self, problem_id: str, stdin_file: Path | None = None):
        self.ensure_solution_exists(problem_id)
        _ = Runner.run(self.solution_file(problem_id), stdin_file)

    @abstractmethod
    def cmd_test(self, problem_id: str, **kwargs): ...

    @abstractmethod
    def cmd_submit(self, problem_id: str): ...

    # CLI wiring per platform
    @abstractmethod
    def register_cli(self, subparsers: argparse._SubParsersAction): ...

