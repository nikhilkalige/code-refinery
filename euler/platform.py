#!/usr/bin/env python3
"""
Project Euler platform integration.

Tests (tests.toml)
- Location: `euler/<id>/tests.toml`
- Each case provides `stdin` and optional `answer` (expected stdout), matching Kattis.
- When `answer` is omitted, the case runs and is reported as unchecked.
"""

from pathlib import Path
import sys

from solver.core import Platform, Runner, load_tests_toml, run_stdin_cases


EULER_TEMPLATE = '''#!/usr/bin/env python3
"""
Project Euler Problem {problem_id}
URL: https://projecteuler.net/problem={problem_id}
"""

def solve() -> int | str:
    # TODO: implement
    return 0


if __name__ == "__main__":
    ans = solve()
    print(ans)
'''

TESTS_TOML_TEMPLATE = (
    "# tests.toml\n"
    "# Each case provides stdin and optional expected answer.\n\n"
    "[[cases]]\n"
    "# name = \"example\"\n"
    "# stdin = \"\"\"input...\"\"\"\n"
    "# answer = \"\"\"output...\"\"\"\n"
)


class EulerPlatform(Platform):
    name = "euler"

    def tests_path(self, problem_id: str) -> Path:
        return self.problem_dir(problem_id) / "tests.toml"

    # Commands
    def cmd_new(self, problem_id: str):
        self.scaffold_solution(problem_id, EULER_TEMPLATE.format(problem_id=problem_id))
        tests = self.tests_path(problem_id)
        self.write_if_absent(tests, TESTS_TOML_TEMPLATE)
        print(f"Problem directory ready: {self.problem_dir(problem_id)}")

    def cmd_test(self, problem_id: str, **kwargs) -> bool:
        self.ensure_solution_exists(problem_id)
        tests_file = self.tests_path(problem_id)
        if not tests_file.exists():
            print("Error: tests.toml not found. Create it to define test cases.")
            print(f"Expected at: {tests_file}")
            sys.exit(1)
        data = load_tests_toml(tests_file)
        cases = data.get("cases", [])
        return run_stdin_cases(self.solution_file(problem_id), cases)

    def cmd_submit(self, problem_id: str):
        self.ensure_solution_exists(problem_id)
        answer = Runner.run(self.solution_file(problem_id))
        url = f"https://projecteuler.net/problem={problem_id}"
        print("Submit this answer on Project Euler:")
        print(f"Problem: {url}")
        print(f"Answer:  {answer}")
        try:
            import pyperclip  # type: ignore

            pyperclip.copy(str(answer))
            print("(Copied answer to clipboard)")
        except Exception:
            pass

    def register_cli(self, subparsers):
        p = subparsers.add_parser(self.name, help="Project Euler commands")
        sp = p.add_subparsers(dest="command", required=True)

        new = sp.add_parser("new", help="Create new Euler problem directory")
        new.add_argument("problem_id")
        new.set_defaults(func=lambda a, plat=self: plat.cmd_new(a.problem_id))

        run = sp.add_parser("run", help="Run Euler solution")
        run.add_argument("problem_id", nargs="?")
        run.set_defaults(func=lambda a, plat=self: plat.cmd_run(plat.resolve_problem_id(a.problem_id)))

        test = sp.add_parser("test", help="Run cases from tests.toml")
        test.add_argument("problem_id", nargs="?")
        test.set_defaults(func=lambda a, plat=self: plat.cmd_test(plat.resolve_problem_id(a.problem_id)))

        submit = sp.add_parser("submit", help="Print answer and problem URL")
        submit.add_argument("problem_id", nargs="?")
        submit.set_defaults(func=lambda a, plat=self: plat.cmd_submit(plat.resolve_problem_id(a.problem_id)))
