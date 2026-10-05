import argparse
import sys
from pathlib import Path

from layers_linter.analyzer import run_linter


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer dependency linter")
    parser.add_argument("path", type=Path, help="Path to project root")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("layers.toml"),
        help="Path to configuration file (default: layers.toml)",
    )
    parser.add_argument(
        "--no-check-no-layer",
        action="store_true",
        help="Disable checking for modules that don't belong to any layer",
    )
    args = parser.parse_args()

    if not args.config.is_file():
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 2

    if not args.path.is_dir():
        print(f"Project root is not a directory: {args.path}", file=sys.stderr)
        return 2

    try:
        problems = run_linter(args.path, args.config, check_no_layer=not args.no_check_no_layer)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2

    for problem in problems:
        print(problem, file=sys.stderr)

    # Exit codes are truncated to 0-255, so the number of problems can't be returned as is.
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
