import warnings
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from layers_linter.analyzer import Problem, analyze_dependencies
from layers_linter.config import load_config

try:
    __version__ = version("layers-linter")
except PackageNotFoundError:
    __version__ = "unknown"


class LayersLinter:
    name = "layers-linter"
    version = __version__

    # flake8 calls the plugin once per file, but the analysis covers the whole project,
    # so its result is computed once per (project root, config) and reused.
    _problems_cache: dict[tuple[Path, Path], dict[Path, list[Problem]]] = {}

    def __init__(self, tree, filename, lines, options):
        self.filename = Path(filename).resolve()
        self.options = options

    def run(self):
        config_path = getattr(self.options, "la_config", None)
        if not config_path:
            warnings.warn("Layers check skipped: config path not specified")
            return

        config_path = Path(config_path).resolve()
        if not config_path.exists() or not config_path.is_file():
            warnings.warn(f"Layers check skipped: config file {config_path} does not exist")
            return

        if len(self.options.filenames) == 0:
            warnings.warn("Layers check skipped: no project root to check")
            return

        if len(self.options.filenames) > 1:
            warnings.warn("Layers check skipped: multiple files not supported")
            return

        project_root = Path(self.options.filenames[0])
        problems_by_file = self._get_problems(project_root, config_path)

        for problem in problems_by_file.get(self.filename, []):
            # flake8 line numbers start at 1; module-level problems have line 0.
            line_number = max(problem.line_number, 1)
            yield (line_number, 0, f"{problem.code} {problem.message}", LayersLinter)

    @classmethod
    def _get_problems(cls, project_root: Path, config_path: Path) -> dict[Path, list[Problem]]:
        key = (project_root.resolve(), config_path)
        if key not in cls._problems_cache:
            layers, libs, exclude_modules = load_config(config_path)
            problems_by_file: dict[Path, list[Problem]] = {}
            for problem in analyze_dependencies(
                project_root, layers, libs, exclude_modules, check_no_layer=True
            ):
                file_path = Path(problem.file_path).resolve()
                problems_by_file.setdefault(file_path, []).append(problem)
            cls._problems_cache[key] = problems_by_file

        return cls._problems_cache[key]

    @staticmethod
    def add_options(option_manager):
        option_manager.add_option(
            "--la-config",
            type=str,
            dest="la_config",
            help="Path to layers-linter configuration file (layers.toml)",
            parse_from_config=True,
            default="layers.toml",
        )
