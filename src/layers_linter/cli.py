import argparse
import sys
from pathlib import Path

from layers_linter.analyzer import run_linter


def main():
    parser = argparse.ArgumentParser(description="Layer dependency linter")
    parser.add_argument("path", type=Path, help="Path to project root")
    parser.add_argument(
        "--config",
        type=Path,
        nargs="?",
        default="deps.toml",
        help="Path to configuration file (default: deps.toml)",
    )
    args = parser.parse_args()

    problems = run_linter(args.path, args.config)
    for problem in problems:
        print(problem, file=sys.stderr)

    return len(problems)
