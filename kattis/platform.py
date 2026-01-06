#!/usr/bin/env python3
"""
Kattis platform integration.

Tests (tests.toml)
- Location: `kattis/<id>/tests.toml`
- Each case can provide `stdin` and optional `answer` (expected stdout).
- If `tests.toml` exists, `kattis test` runs these cases. Otherwise, it downloads
  samples to a temp directory and runs them directly. `cmd_new` will attempt to
  download samples and convert them into `tests.toml` when possible.
"""

import configparser
import re
import sys
import tempfile
from pathlib import Path

from solver.core import Platform, Runner, compare_report, print_banner, load_tests_toml, run_stdin_cases

try:
    import requests  # type: ignore
except Exception:
    requests = None

try:  # Python 3.11+
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore
    except Exception:  # pragma: no cover
        tomllib = None  # type: ignore


KATTIS_TEMPLATE = '''#!/usr/bin/env python3
"""
Problem: {problem_id}
URL: https://open.kattis.com/problems/{problem_id}
"""

import sys

def solve():
    pass


if __name__ == "__main__":
    print(solve(sys.stdin.readline()))
'''

KATTIS_TESTS_TOML_TEMPLATE = (
    "[[cases]]\n"
    "# name = \"sample-01\"\n"
    "# stdin = \"\"\"input...\"\"\"\n"
    "# answer = \"\"\"output...\"\"\"\n"
)


class KattisPlatform(Platform):
    name = "kattis"

    def get_config(self):
        cfg_path = self.base_dir / ".kattisrc"
        if not cfg_path.exists():
            print(f"Error: {cfg_path} not found.")
            sys.exit(1)
        config = configparser.ConfigParser()
        config.read(cfg_path)
        return config

    def samples_dir(self, problem_id: str) -> Path:
        return Path(tempfile.gettempdir()) / "kattis_samples" / problem_id

    def download_samples(self, problem_id: str) -> Path | None:
        samples_dir = self.samples_dir(problem_id)
        if samples_dir.exists() and list(samples_dir.glob("*.in")):
            return samples_dir
        samples_dir.mkdir(parents=True, exist_ok=True)
        if requests is None:
            print("Error: requests not available; cannot download samples.")
            return None
        url = f"https://open.kattis.com/problems/{problem_id}/file/statement/samples.zip"
        print(f"Downloading samples for {problem_id}...")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error downloading samples: {e}")
            print(f"Check problem: https://open.kattis.com/problems/{problem_id}")
            return None
        zip_path = samples_dir / "samples.zip"
        zip_path.write_bytes(resp.content)
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(samples_dir)
        zip_path.unlink(missing_ok=True)
        print(f"Downloaded {len(list(samples_dir.glob('*.in')))} sample(s) to temp dir")
        return samples_dir

    def tests_path(self, problem_id: str) -> Path:
        return self.problem_dir(problem_id) / "tests.toml"

    def _toml_multiline(self, s: str) -> str:
        # Escape triple quotes inside the string for TOML basic triple-quoted strings
        return '"""' + s.replace('"""', '\\"""') + '"""'

    def write_tests_from_samples(self, problem_id: str, samples_dir: Path) -> Path:
        tests_file = self.tests_path(problem_id)
        lines: list[str] = []
        samples = sorted(samples_dir.glob("*.in"))
        for input_file in samples:
            name = input_file.stem
            output_file = input_file.with_suffix(".ans")
            stdin = input_file.read_text()
            answer = output_file.read_text() if output_file.exists() else None
            lines.append("[[cases]]")
            lines.append(f"name = \"{name}\"")
            lines.append(f"stdin = {self._toml_multiline(stdin)}")
            if answer is not None:
                lines.append(f"answer = {self._toml_multiline(answer)}")
            lines.append("")
        content = "\n".join(lines).rstrip() + "\n"
        tests_file.write_text(content)
        print(f"Created: {tests_file}")
        return tests_file

    # Commands
    def cmd_new(self, problem_id: str):
        self.scaffold_solution(problem_id, KATTIS_TEMPLATE.format(problem_id=problem_id))
        tests = self.tests_path(problem_id)
        if not tests.exists():
            samples = self.download_samples(problem_id)
            if samples and list(samples.glob("*.in")):
                self.write_tests_from_samples(problem_id, samples)
            else:
                # Fall back to an empty template
                self.write_if_absent(tests, KATTIS_TESTS_TOML_TEMPLATE)
        print(f"Problem directory ready: {self.problem_dir(problem_id)}")

    def cmd_test(self, problem_id: str, test_id: int | None = None, **kwargs) -> bool:
        self.ensure_solution_exists(problem_id)
        tests_file = self.tests_path(problem_id)
        if not tests_file.exists():
            # If tests.toml is missing, try to download samples and generate it once
            samples_dir = self.download_samples(problem_id)
            if not samples_dir or not list(samples_dir.glob("*.in")):
                print("Error: no tests.toml and no downloadable samples; cannot run tests.")
                sys.exit(1)
            self.write_tests_from_samples(problem_id, samples_dir)
        data = load_tests_toml(tests_file)
        cases = data.get("cases", [])
        return run_stdin_cases(self.solution_file(problem_id), cases, test_id=test_id)

    def cmd_submit(self, problem_id: str):
        self.ensure_solution_exists(problem_id)
        if requests is None:
            print("Error: requests library required for submit.")
            sys.exit(1)
        config = self.get_config()
        username = config.get("user", "username")
        token = config.get("user", "token")
        submit_url = config.get("kattis", "submissionurl")
        hostname = config.get("kattis", "hostname")
        login_url = config.get("kattis", "loginurl")
        print(f"Submitting {problem_id} to Kattis...")
        session = requests.Session()
        resp = session.post(login_url, data={"user": username, "token": token, "script": "true"})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code}")
            print(resp.text)
            sys.exit(1)
        with open(self.solution_file(problem_id), "rb") as sub_file:
            files = [("sub_file[]", (self.solution_file(problem_id).name, sub_file.read(), "application/octet-stream"))]
        submit_data = {
            "problem": problem_id,
            "language": "Python 3",
            "mainclass": "solution.py",
            "script": "true",
            "submit": "true",
            "submit_ctr": 2,
            "tag": "",
        }
        resp = session.post(submit_url, data=submit_data, files=files)
        if resp.status_code != 200:
            print(f"Submission failed: {resp.status_code}")
            print(resp.text)
            sys.exit(1)
        m = re.search(r"Submission ID: (\d+)", resp.text)
        if m:
            sid = m.group(1)
            print(f"Submitted! ID: {sid}")
            print(f"Track: https://{hostname}/submissions/{sid}")
        else:
            print("Submitted!")
            print(resp.text)

    def register_cli(self, subparsers):
        p = subparsers.add_parser(self.name, help="Kattis commands")
        sp = p.add_subparsers(dest="command", required=True)

        new = sp.add_parser("new", help="Create new problem directory")
        new.add_argument("problem_id")
        new.set_defaults(func=lambda a, plat=self: plat.cmd_new(a.problem_id))

        run = sp.add_parser("run", help="Run solution with input file")
        run.add_argument("problem_id", nargs="?")
        run.add_argument("--file", required=True)
        run.set_defaults(func=lambda a, plat=self: plat.cmd_run(plat.resolve_problem_id(a.problem_id), Path(a.file)))

        test = sp.add_parser("test", help="Download samples and run tests")
        test.add_argument("problem_id", nargs="?")
        test.add_argument("--test-id", nargs="?", default=None)
        test.set_defaults(func=lambda a, plat=self: plat.cmd_test(plat.resolve_problem_id(a.problem_id), test_id=a.test_id))

        submit = sp.add_parser("submit", help="Submit to Kattis")
        submit.add_argument("problem_id", nargs="?")
        submit.set_defaults(func=lambda a, plat=self: plat.cmd_submit(plat.resolve_problem_id(a.problem_id)))
