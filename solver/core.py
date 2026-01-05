#!/usr/bin/env python3
"""
Core utilities shared by competitive programming helpers.
Includes: Runner, Platform base class, and helpers.
"""

import argparse
import io
import importlib.util
import sys
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # Python 3.11+
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except Exception:  # pragma: no cover
        tomllib = None  # type: ignore


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
                    if spec is None or spec.loader is None:
                        raise RuntimeError(f"Failed to load module spec for {solution_file}")
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)  # type: ignore[union-attr]
            else:
                spec = importlib.util.spec_from_file_location("__main__", solution_file)
                if spec is None or spec.loader is None:
                    raise RuntimeError(f"Failed to load module spec for {solution_file}")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
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


def load_tests_toml(tests_file: Path) -> Dict[str, Any]:
    if tomllib is None:
        print("Error: tomllib/tomli not available to read TOML tests.")
        sys.exit(1)
    try:
        data = tomllib.loads(tests_file.read_text())
    except Exception as e:
        print(f"Error reading TOML: {tests_file}\n{e}")
        sys.exit(1)
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        print("Error: tests.toml must define a non-empty [[cases]] array.")
        sys.exit(1)
    return data


def run_stdin_cases(solution_file: Path, cases: List[Dict[str, Any]], test_id: Optional[int] = None) -> bool:
    # Optional filtering by test_id assumes names like 01, 02, ...
    if test_id is not None:
        tid = f"{int(test_id):02}"
        cases = [c for c in cases if str(c.get("name", "")).startswith(tid)]
    passed = failed = unchecked = 0
    for idx, case in enumerate(cases, start=1):
        name = str(case.get("name", "")) or f"case {idx}"
        stdin_val = case.get("stdin", "")
        has_expected = "answer" in case
        expected = case.get("answer") if has_expected else None
        print_banner(f"Test: {name}")
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as tf:
            tf.write(str(stdin_val))
            tf.flush()
            actual = Runner.run(solution_file, Path(tf.name))
        if has_expected:
            if compare_report(str(expected).rstrip("\n"), actual.rstrip("\n")):
                passed += 1
            else:
                failed += 1
                print("\nInput:")
                print(str(stdin_val).rstrip("\n"))
        else:
            unchecked += 1
            print("(no expected answer; output shown above)")
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed, {unchecked} unchecked")
    print("=" * 50)
    return failed == 0


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

    # Small shared scaffolding helpers
    def write_if_absent(self, path: Path, content: str) -> bool:
        if not path.exists():
            path.write_text(content)
            print(f"Created: {path}")
            return True
        else:
            print(f"Already exists: {path}")
            return False

    def scaffold_solution(self, problem_id: str, template: str) -> Path:
        pdir = self.problem_dir(problem_id)
        pdir.mkdir(parents=True, exist_ok=True)
        sol = self.solution_file(problem_id)
        if not sol.exists():
            sol.write_text(template)
            print(f"Created: {sol}")
        else:
            print(f"Solution file already exists: {sol}")
        return sol

    # Common actions with sensible defaults
    @abstractmethod
    def cmd_new(self, problem_id: str): ...

    def cmd_run(self, problem_id: str, stdin_file: Path | None = None):
        self.ensure_solution_exists(problem_id)
        _ = Runner.run(self.solution_file(problem_id), stdin_file)

    @abstractmethod
    def cmd_test(self, problem_id: str, **kwargs) -> bool: ...

    @abstractmethod
    def cmd_submit(self, problem_id: str): ...

    # CLI wiring per platform
    @abstractmethod
    def register_cli(self, subparsers: argparse._SubParsersAction): ...
