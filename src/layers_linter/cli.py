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
        default="layers.toml",
        help="Path to configuration file (default: layers.toml)",
    )
    parser.add_argument(
        "--no-check-no-layer",
        action="store_true",
        help="Disable checking for modules that don't belong to any layer",
    )
    args = parser.parse_args()

    problems = run_linter(args.path, args.config, check_no_layer=not args.no_check_no_layer)
    for problem in problems:
        print(problem, file=sys.stderr)

    return len(problems)
