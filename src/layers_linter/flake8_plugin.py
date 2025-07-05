import warnings
from pathlib import Path

from layers_linter.analyzer import analyze_dependencies
from layers_linter.config import load_config


class LayersLinter:
    name = "layers-linter"
    version = "3.2.2"

    def __init__(self, tree, filename, lines, options):
        self.filename = Path(filename).resolve()
        self.options = options

    def run(self):
        config_path = getattr(self.options, "la_config", None)
        if not config_path:
            warnings.warn("Bounded contexts check skipped: config path not specified")
            return

        config_path = Path(config_path).resolve()
        if not config_path.exists() or not config_path.is_file():
            warnings.warn(
                f"Bounded contexts check skipped: config file {config_path} does not exist"
            )
            return

        if len(self.options.filenames) == 0:
            warnings.warn("Bounded contexts check skipped: no project root to check")
            return

        if len(self.options.filenames) > 1:
            warnings.warn("Bounded contexts check skipped: multiple files not supported")
            return

        layers, libs, exclude_modules = load_config(config_path)

        for problem in analyze_dependencies(
            self.options.filenames[0], layers, libs, exclude_modules, check_no_layer=True
        ):
            yield (problem.line_number, 0, f"{problem.code} {problem.message}", LayersLinter)

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
