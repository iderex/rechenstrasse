"""Read a mutation report, refuse an unfinished run, and print the score.

Issue #50. The run reports and does not gate, so nothing here compares the score
against a number. What it refuses is a run that could not be completed, because
a broken setup that quietly reports nothing is worse than no run at all.

Two shapes are refused, and they are the two ways a report can be read as a
result when it is not one.

  a report with no total
      The tool printed something this file does not recognise. That is a tool
      that moved or a command that failed, and either way the number underneath
      is not a score.

  a report whose completed count is below its total
      Some mutants were never executed. Their verdicts are unknown, and a
      percentage taken over the ones that did run reads exactly like a
      percentage over all of them.

Standard library only, and run by the runner's own interpreter rather than by
the project environment, because the mutation tool is fetched for the run and
this is the file that reads what it printed.

    python3 tools/mutation_score.py <report file> [survival rate]

Its proof is in the job that calls it, on the same commit: the report of an
enumerated session that has not been executed is handed to it and the step
requires it to refuse. It has no suite of its own beside that.
"""

import pathlib
import re
import sys

TOTAL = re.compile(r"^total jobs:\s*(\d+)\s*$", re.MULTILINE)
COMPLETE = re.compile(r"^complete:\s*(\d+)\s*\(", re.MULTILINE)
SURVIVING = re.compile(r"^surviving mutants:\s*(\d+)\s*\(", re.MULTILINE)


def read(report: str, survival: str | None) -> str:
    """Return the line to print, or raise SystemExit naming what was wrong."""
    total = TOTAL.search(report)
    if total is None:
        raise SystemExit(
            "the report carries no total, so it is not a report this file "
            "knows how to read and the numbers in it are not a score"
        )
    counted = int(total.group(1))

    complete = COMPLETE.search(report)
    executed = int(complete.group(1)) if complete is not None else 0
    if executed != counted:
        raise SystemExit(
            f"{executed} of {counted} mutant(s) were executed, so this run did "
            f"not complete and its numbers are a percentage over the part of "
            f"the work that happened"
        )

    surviving = SURVIVING.search(report)
    survived = int(surviving.group(1)) if surviving is not None else 0
    killed = counted - survived
    rate = f", survival rate {survival.strip()}%" if survival else ""
    return f"{killed} of {counted} mutant(s) killed, {survived} surviving{rate}"


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        raise SystemExit(f"usage: {argv[0] if argv else 'mutation_score.py'} ...")
    report = pathlib.Path(argv[1]).read_text(encoding="utf-8")
    print(read(report, argv[2] if len(argv) == 3 else None))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
