import pytest

from src.layers_linter.analyzer import analyze_dependencies
from src.layers_linter.config import load_config


@pytest.fixture
def temp_project(tmp_path):
    def _create_project(toml_config, project_structure):
        config_path = tmp_path / "layers.toml"
        config_path.write_text(toml_config)

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        for file_path, content in project_structure.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        return config_path

    return _create_project


def test_type_checking_import_with_alias(temp_project):
    """
    Tests that the analyzer correctly ignores imports that are inside TYPE_CHECKING blocks
    when TYPE_CHECKING is accessed through an alias (e.g., t.TYPE_CHECKING).
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
depends_on = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
    """

    project_structure = {
        "domain/service.py": """
import typing as t

if t.TYPE_CHECKING:
    from project.infrastructure.db import Database
""",
        "infrastructure/db.py": """
import typing as typ

if typ.TYPE_CHECKING:
    from project.domain.service import Service
""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 0


def test_mixed_type_checking_styles(temp_project):
    """
    Tests that the analyzer correctly handles mixed styles of TYPE_CHECKING
    (both standard and aliased) in the same project.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
depends_on = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
    """

    project_structure = {
        "domain/service.py": """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from project.infrastructure.db import Database
""",
        "domain/repository.py": """
import typing as t

if t.TYPE_CHECKING:
    from project.infrastructure.cache import Cache
""",
        "infrastructure/db.py": """
import typing as typ

if typ.TYPE_CHECKING:
    from project.domain.service import Service
""",
        "infrastructure/cache.py": """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from project.domain.repository import Repository
""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 0


def test_type_checking_alias_with_real_imports(temp_project):
    """
    Tests that the analyzer correctly handles a mix of TYPE_CHECKING imports (which should be ignored)
    and real imports (which should be analyzed) when using aliases.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
depends_on = []

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
    """

    project_structure = {
        "domain/service.py": """
import typing as t
from project.infrastructure.db import Database  # This should cause a violation

if t.TYPE_CHECKING:
    from project.infrastructure.cache import Cache  # This should be ignored
""",
        "infrastructure/db.py": "",
        "infrastructure/cache.py": "",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    # Should find 1 problem: the real import from domain to infrastructure
    # The TYPE_CHECKING import should be ignored
    assert len(problems) == 1
    assert problems[0].imported_module == "project.infrastructure.db"
    assert problems[0].layer_from == "domain"
    assert problems[0].layer_to == "infrastructure"
