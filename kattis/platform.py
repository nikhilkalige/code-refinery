#!/usr/bin/env python3
"""Kattis platform integration."""

import configparser
import re
import sys
import tempfile
from pathlib import Path

from solver.core import Platform, Runner, compare_report, print_banner

try:
    import requests  # type: ignore
except Exception:
    requests = None


KATTIS_TEMPLATE = '''#!/usr/bin/env python3
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

    # Commands
    def cmd_new(self, problem_id: str):
        self.problem_dir(problem_id).mkdir(parents=True, exist_ok=True)
        sol = self.solution_file(problem_id)
        if not sol.exists():
            sol.write_text(KATTIS_TEMPLATE.format(problem_id=problem_id))
            print(f"Created: {sol}")
        else:
            print(f"Solution file already exists: {sol}")
        self.download_samples(problem_id)
        print(f"Problem directory ready: {self.problem_dir(problem_id)}")

    def cmd_test(self, problem_id: str, test_id: int | None = None):
        self.ensure_solution_exists(problem_id)
        samples_dir = self.download_samples(problem_id)
        if not samples_dir:
            sys.exit(1)
        samples = sorted(samples_dir.glob("*.in"))
        if test_id is not None:
            test_id = int(test_id)
            samples = [s for s in samples if s.name.startswith(f"{test_id:02}")]
        passed = failed = 0
        for input_file in samples:
            output_file = input_file.with_suffix(".ans")
            print_banner(f"Test: {input_file.stem}")
            actual = Runner.run(self.solution_file(problem_id), input_file)
            if output_file.exists():
                expected = output_file.read_text().rstrip("\n")
                if compare_report(expected, actual):
                    passed += 1
                else:
                    print("\nInput:")
                    print(input_file.read_text().rstrip("\n"))
                    failed += 1
            else:
                print("⚠️  No expected output file")
                print(f"Output: {actual}")
        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 50)
        return failed == 0

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

