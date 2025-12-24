#!/usr/bin/env python3
"""
Kattis helper script for competitive programming.

Commands:
    new <problem_id>     Create a new problem directory with template
    test [problem_id]    Run solution against sample test cases
    submit [problem_id]  Submit solution to Kattis
"""

import argparse
import configparser
from contextlib import redirect_stdout
import io
import re
import sys
import tempfile
from pathlib import Path
import importlib.util
import traceback

try:
    import requests
except ImportError:
    print(
        "Error: requests library required. Add 'pythonPackages.requests' to flake.nix"
    )
    sys.exit(1)

TEMPLATE = '''#!/usr/bin/env python3
"""
Problem: {problem_id}
URL: https://open.kattis.com/problems/{problem_id}
"""

import sys
from sys import stdin

def solve():
    pass


if __name__ == "__main__":
    solve()
'''


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)

    def flush(self):
        for f in self.files:
            f.flush()


def get_config():
    """Load Kattis configuration from root git dir/kattis/.kattisrc"""
    kattis_dir = Path(__file__).parent
    config_path = kattis_dir / ".kattisrc"
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_problem_dir(problem_id: str) -> Path:
    """Get the directory path for a problem."""
    return Path(__file__).parent / problem_id


def get_current_problem() -> str:
    """Detect problem ID from current directory."""
    cwd = Path.cwd()
    if cwd.parent.name == "kattis":
        return cwd.name
    raise ValueError(
        "Not in a problem directory. Specify problem_id or cd into kattis/<id>"
    )


def cmd_new(problem_id: str):
    """Create a new problem directory with template."""
    problem_dir = get_problem_dir(problem_id)
    problem_dir.mkdir(parents=True, exist_ok=True)

    solution_file = problem_dir / "solution.py"
    if solution_file.exists():
        print(f"Solution file already exists: {solution_file}")
    else:
        solution_file.write_text(TEMPLATE.format(problem_id=problem_id))
        print(f"Created: {solution_file}")

    # Download samples to temp
    download_samples(problem_id)
    print(f"\nProblem directory ready: {problem_dir}")
    print(f"Edit: {solution_file}")


def get_samples_dir(problem_id: str) -> Path:
    """Get temp directory for sample test cases."""
    return Path(tempfile.gettempdir()) / "kattis_samples" / problem_id


def download_samples(problem_id: str) -> Path:
    """Download sample test cases to temp directory. Returns samples dir."""
    samples_dir = get_samples_dir(problem_id)
    print(samples_dir)

    # Check if already downloaded
    if samples_dir.exists() and list(samples_dir.glob("*.in")):
        return samples_dir

    samples_dir.mkdir(parents=True, exist_ok=True)

    samples_url = (
        f"https://open.kattis.com/problems/{problem_id}/file/statement/samples.zip"
    )

    print(f"Downloading samples for {problem_id}...")

    try:
        response = requests.get(samples_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error downloading samples: {e}")
        print(f"Check if problem exists: https://open.kattis.com/problems/{problem_id}")
        return None

    zip_path = samples_dir / "samples.zip"
    zip_path.write_bytes(response.content)

    # Extract samples
    import zipfile

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(samples_dir)

    zip_path.unlink()

    # List downloaded files
    samples = sorted(samples_dir.glob("*.in"))
    print(f"Downloaded {len(samples)} sample(s) to temp dir")

    return samples_dir


def cmd_test(problem_id: str | None = None, test_id: int | None = None):
    """Run solution against sample test cases."""
    if problem_id is None:
        problem_id = get_current_problem()

    problem_dir = get_problem_dir(problem_id)
    solution_file = problem_dir / "solution.py"

    if not solution_file.exists():
        print(f"Error: Solution file not found: {solution_file}")
        sys.exit(1)

    # Download samples if needed
    samples_dir = download_samples(problem_id)
    if not samples_dir:
        sys.exit(1)

    samples = sorted(samples_dir.glob("*.in"))
    if test_id is not None:
        test_id = int(test_id)
        samples = filter(lambda s: s.name.startswith(f"{test_id:02}"), samples)

    passed = 0
    failed = 0

    original_stdin = sys.stdin
    original_stdout = sys.stdout

    for input_file in samples:
        output_file = input_file.with_suffix(".ans")
        test_name = input_file.stem

        print("=" * 50)
        print(f"Test: {test_name}")
        print("=" * 50)

        output_capture = io.StringIO()
        sys.stdout = Tee(sys.__stdout__, output_capture)

        with open(input_file, "r") as f:
            sys.stdin = f

            spec = importlib.util.spec_from_file_location("__main__", solution_file)
            sol = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sol)

            actual = output_capture.getvalue().rstrip("\n")
            sys.stdout = original_stdout

            if output_file.exists():
                expected = output_file.read_text().rstrip("\n")
                if actual == expected:
                    print("✅ PASSED")
                    passed += 1
                else:
                    print("❌ FAILED")
                    print("\nInput:")
                    print(input_file.read_text().rstrip("\n"))
                    print("\nExpected:")
                    print(expected)
                    print("\nActual:")
                    print(actual)
                    failed += 1
            else:
                print("⚠️  No expected output file")
                print(f"Output: {actual}")

    # Ensure stdin is reset even if an exception occurs
    sys.stdin = original_stdin

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


def cmd_run(problem_id: str | None, file: Path):
    if problem_id is None:
        problem_id = get_current_problem()

    problem_dir = get_problem_dir(problem_id)
    solution_file = problem_dir / "solution.py"

    if not solution_file.exists():
        print(f"Error: Solution file not found: {solution_file}")
        sys.exit(1)

    with open(file, "r") as f:
        sys.stdin = f
        spec = importlib.util.spec_from_file_location("__main__", solution_file)
        sol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sol)


def cmd_submit(problem_id: str = None):
    """Submit solution to Kattis."""
    if problem_id is None:
        problem_id = get_current_problem()

    problem_dir = get_problem_dir(problem_id)
    solution_file = problem_dir / "solution.py"

    if not solution_file.exists():
        print(f"Error: Solution file not found: {solution_file}")
        sys.exit(1)

    config = get_config()

    username = config.get("user", "username")
    token = config.get("user", "token")
    submit_url = config.get("kattis", "submissionurl")
    hostname = config.get("kattis", "hostname")

    print(f"Submitting {problem_id} to Kattis...")

    # Login and submit
    session = requests.Session()

    login_args = {"user": username, "token": token, "script": "true"}

    login_url = config.get("kattis", "loginurl")
    response = session.post(login_url, data=login_args)

    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    # Submit
    submit_data = {
        "problem": problem_id,
        "language": "Python 3",
        "mainclass": "solution.py",
        "script": "true",
        "submit": "true",
        "submit_ctr": 2,
        "tag": "",
    }

    with open(solution_file, "rb") as sub_file:
        files = [
            (
                "sub_file[]",
                (solution_file.name, sub_file.read(), "application/octet-stream"),
            )
        ]

    response = session.post(submit_url, data=submit_data, files=files)
    if response.status_code != 200:
        print(f"Submission failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    # Parse submission ID from response
    match = re.search(r"Submission ID: (\d+)", response.text)
    if match:
        submission_id = match.group(1)
        print(f"Submitted! ID: {submission_id}")
        print(f"Track: https://{hostname}/submissions/{submission_id}")
    else:
        print("Submitted!")
        print(response.text)


def main():
    parser = argparse.ArgumentParser(
        description="Kattis competitive programming helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # new
    new_parser = subparsers.add_parser("new", help="Create new problem directory")
    new_parser.add_argument("problem_id", help="Kattis problem ID")

    run_parser = subparsers.add_parser("run", help="Run tests with input file")
    run_parser.add_argument(
        "problem_id",
        nargs="?",
        help="Problem ID (optional if in problem dir)",
    )
    run_parser.add_argument("--file", required=True)

    # test
    test_parser = subparsers.add_parser("test", help="Download samples and run tests")
    test_parser.add_argument(
        "problem_id",
        nargs="?",
        help="Problem ID (optional if in problem dir)",
    )
    test_parser.add_argument("--test-id", nargs="?", default=None)

    # submit
    submit_parser = subparsers.add_parser("submit", help="Submit to Kattis")
    submit_parser.add_argument(
        "problem_id", nargs="?", help="Problem ID (optional if in problem dir)"
    )

    args = parser.parse_args()

    if args.command == "new":
        cmd_new(args.problem_id)
    elif args.command == "test":
        cmd_test(args.problem_id, args.test_id)
    elif args.command == "submit":
        cmd_submit(args.problem_id)
    elif args.command == "run":
        cmd_run(args.problem_id, Path(args.file))


if __name__ == "__main__":
    main()
