import sys
from types import SimpleNamespace

import pytest

from layers_linter import cli
from layers_linter.analyzer import analyze_dependencies
from layers_linter.config import load_config
from layers_linter.flake8_plugin import LayersLinter

TOML_CONFIG = """
exclude_modules = ["*.__init__"]

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
depends_on = []

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
"""


@pytest.fixture
def temp_project(tmp_path):
    def _create_project(project_structure, toml_config=TOML_CONFIG):
        config_path = tmp_path / "layers.toml"
        config_path.write_text(toml_config)

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        for file_path, content in project_structure.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        return config_path, project_dir

    return _create_project


def analyze(config_path, project_root, check_no_layer=False):
    layers, libs, exclude_modules = load_config(config_path)
    return analyze_dependencies(project_root, layers, libs, exclude_modules, check_no_layer)


def test_same_layer_import_is_allowed(temp_project):
    """Modules of a layer with depends_on = [] can still import each other."""
    config_path, project_root = temp_project(
        {
            "domain/service.py": "from project.domain.entities import User",
            "domain/entities.py": "class User: pass",
        }
    )

    assert analyze(config_path, project_root) == []


@pytest.mark.parametrize(
    "source",
    [
        "from project.infrastructure import db",
        "from project.infrastructure import cache, db",
        "from ..infrastructure import db",
    ],
)
def test_import_of_submodule_from_package(temp_project, source):
    """'from package import submodule' is a dependency on the submodule."""
    config_path, project_root = temp_project(
        {
            "__init__.py": "",
            "domain/__init__.py": "",
            "domain/service.py": source,
            "infrastructure/__init__.py": "",
            "infrastructure/db.py": "",
        }
    )

    problems = analyze(config_path, project_root)

    assert len(problems) == 1
    assert problems[0].imported_module == "project.infrastructure.db"
    assert problems[0].layer_from == "domain"
    assert problems[0].layer_to == "infrastructure"


def test_relative_import_without_module_name(temp_project):
    """'from . import module' is resolved relative to the current package."""
    toml_config = TOML_CONFIG.replace(
        'contains_modules = ["project.domain.*"]', 'contains_modules = ["project.domain.service"]'
    ).replace(
        'contains_modules = ["project.infrastructure.*"]',
        'contains_modules = ["project.domain.db"]',
    )
    config_path, project_root = temp_project(
        {"domain/service.py": "from . import db", "domain/db.py": ""}, toml_config
    )

    problems = analyze(config_path, project_root)

    assert len(problems) == 1
    assert problems[0].imported_module == "project.domain.db"


def test_project_root_given_as_relative_dot(temp_project, monkeypatch):
    """With '.' module names are relative to the current directory (flake8 default)."""
    config_path, project_root = temp_project(
        {
            "domain/service.py": "from project.infrastructure.db import Database",
            "infrastructure/db.py": "",
        }
    )
    monkeypatch.chdir(project_root.parent)

    problems = analyze(config_path, ".", check_no_layer=True)

    assert len(problems) == 1
    assert problems[0].module_path == "project.domain.service"
    assert problems[0].file_path == "project/domain/service.py"


def test_hidden_directories_are_skipped(temp_project):
    config_path, project_root = temp_project(
        {
            "domain/service.py": "",
            ".venv/lib/some_package.py": "import project.domain.service",
        }
    )

    assert analyze(config_path, project_root, check_no_layer=True) == []


def test_file_with_syntax_error_is_skipped(temp_project):
    config_path, project_root = temp_project(
        {
            "domain/broken.py": "def (",
            "domain/service.py": "from project.infrastructure.db import Database",
            "infrastructure/db.py": "",
        }
    )

    with pytest.warns(UserWarning, match="broken.py"):
        problems = analyze(config_path, project_root)

    assert len(problems) == 1


def test_cli_exit_code(temp_project, monkeypatch):
    structure = {"domain/m%d.py" % i: "import project.infrastructure.db" for i in range(256)}
    structure["infrastructure/db.py"] = ""
    config_path, project_root = temp_project(structure)

    monkeypatch.setattr(
        sys, "argv", ["layers-linter", str(project_root), "--config", str(config_path)]
    )
    assert cli.main() == 1

    (project_root / "domain").rename(project_root / "other")
    monkeypatch.setattr(
        sys,
        "argv",
        ["layers-linter", str(project_root), "--config", str(config_path), "--no-check-no-layer"],
    )
    assert cli.main() == 0


def test_cli_missing_config(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["layers-linter", str(tmp_path), "--config", str(tmp_path / "missing.toml")]
    )
    assert cli.main() == 2


def test_flake8_plugin_reports_only_problems_of_checked_file(temp_project, monkeypatch):
    config_path, project_root = temp_project(
        {
            "domain/service.py": "from project.infrastructure.db import Database",
            "infrastructure/db.py": "",
            "stray.py": "",
        }
    )
    monkeypatch.setattr(LayersLinter, "_problems_cache", {})
    options = SimpleNamespace(la_config=str(config_path), filenames=[str(project_root)])

    def run(file_path):
        return list(LayersLinter(None, str(file_path), [], options).run())

    service_problems = run(project_root / "domain/service.py")
    assert [(line, code.split()[0]) for line, _, code, _ in service_problems] == [(1, "LA001")]
    assert run(project_root / "infrastructure/db.py") == []
    assert [(line, code.split()[0]) for line, _, code, _ in run(project_root / "stray.py")] == [
        (1, "LA002")
    ]
