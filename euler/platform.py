#!/usr/bin/env python3
"""Project Euler platform integration."""

from pathlib import Path
import sys

from solver.core import Platform, Runner, compare_report


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


class EulerPlatform(Platform):
    name = "euler"

    def answer_path(self, problem_id: str) -> Path:
        return self.problem_dir(problem_id) / "answer.txt"

    # Commands
    def cmd_new(self, problem_id: str):
        self.problem_dir(problem_id).mkdir(parents=True, exist_ok=True)
        sol = self.solution_file(problem_id)
        if not sol.exists():
            sol.write_text(EULER_TEMPLATE.format(problem_id=problem_id))
            print(f"Created: {sol}")
        else:
            print(f"Solution file already exists: {sol}")
        ans = self.answer_path(problem_id)
        if not ans.exists():
            ans.write_text("# Put expected answer (single line) here when known.\n")
            print(f"Created: {ans}")
        print(f"Problem directory ready: {self.problem_dir(problem_id)}")

    def cmd_test(self, problem_id: str, **kwargs):
        self.ensure_solution_exists(problem_id)
        ans = self.answer_path(problem_id)
        actual = Runner.run(self.solution_file(problem_id))
        if not ans.exists():
            print("⚠️  No expected answer saved (answer.txt).")
            print(f"Output: {actual}")
            sys.exit(1)
        expected = ans.read_text().strip()
        if expected.startswith("#") or expected == "":
            print("⚠️  Expected answer file has no value yet.")
            print(f"Output: {actual}")
            sys.exit(1)
        compare_report(expected.strip(), actual.strip())

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

    # Extra command specific to Euler
    def cmd_answer(self, problem_id: str, set_value: str | None, show: bool):
        ans = self.answer_path(problem_id)
        if set_value is not None:
            ans.write_text(str(set_value).strip() + "\n")
            print(f"Saved expected answer to {ans}")
        if show or set_value is None:
            if ans.exists():
                print(ans.read_text().strip())
            else:
                print("<no answer saved>")

    def register_cli(self, subparsers):
        p = subparsers.add_parser(self.name, help="Project Euler commands")
        sp = p.add_subparsers(dest="command", required=True)

        new = sp.add_parser("new", help="Create new Euler problem directory")
        new.add_argument("problem_id")
        new.set_defaults(func=lambda a, plat=self: plat.cmd_new(a.problem_id))

        run = sp.add_parser("run", help="Run Euler solution")
        run.add_argument("problem_id", nargs="?")
        run.set_defaults(func=lambda a, plat=self: plat.cmd_run(plat.resolve_problem_id(a.problem_id)))

        test = sp.add_parser("test", help="Run and compare with answer.txt")
        test.add_argument("problem_id", nargs="?")
        test.set_defaults(func=lambda a, plat=self: plat.cmd_test(plat.resolve_problem_id(a.problem_id)))

        ans = sp.add_parser("answer", help="Get/Set expected answer")
        ans.add_argument("problem_id", nargs="?")
        ans.add_argument("--set", dest="set_value", help="Set expected answer")
        ans.add_argument("--show", action="store_true", help="Show saved answer")
        ans.set_defaults(func=lambda a, plat=self: plat.cmd_answer(plat.resolve_problem_id(a.problem_id), a.set_value, a.show))

        submit = sp.add_parser("submit", help="Print answer and problem URL")
        submit.add_argument("problem_id", nargs="?")
        submit.set_defaults(func=lambda a, plat=self: plat.cmd_submit(plat.resolve_problem_id(a.problem_id)))

