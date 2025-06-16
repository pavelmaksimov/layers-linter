import pytest

from src.layers_linter.analyzer import analyze_dependencies
from src.layers_linter.config import load_config


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with the given config."""

    def create_project(toml_config: str, project_structure: dict):
        # Create config file
        config_path = tmp_path / "deps.toml"
        with open(config_path, "w") as f:
            f.write(toml_config)

        # Create project files
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        for file_path, content in project_structure.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

        return config_path

    return create_project


def test_valid_dependency(temp_project):
    """
    Tests that the analyzer correctly validates dependencies between layers
    and external libraries when they are properly configured in the configuration file.
    Checks that layers can use libraries that are specified in their allowed_in list.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]

[layers.presentation]
contains_modules = ["project.presentation.*"]

[layers.helpers]
contains_modules = ["project.helpers.*"]

[libs]
[libs.sqlalchemy]
allowed_in = ["infrastructure"]

[libs.pydantic]
allowed_in = ["helpers"]

[libs.fastapi]
allowed_in = ["presentation"]

[libs.argparse]
allowed_in = ["presentation"]
"""

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """
# This is allowed to depend on domain
from project.domain.service import Service
import sqlalchemy
        """,
        "helpers/validator.py": """import pydantic""",
        "presentation/controller.py": """
import argparse
import fastapi
        """,
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 0


def test_invalid_library_usage(temp_project):
    """
    Tests that the analyzer correctly identifies invalid library usage
    when a layer imports a library that is not specified in its allowed_in list.
    Verifies that the correct error code (LA020) is reported.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]

[libs]
[libs.sqlalchemy]
allowed_in = ["infrastructure"]
"""

    project_structure = {"domain/service.py": """import sqlalchemy"""}

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 1
    problem = problems[0]
    assert problem.code == "LA020"
