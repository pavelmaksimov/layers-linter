# File: tests/test_layer_linter.py
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


def test_invalid_dependency(temp_project):
    """
    Tests that the analyzer correctly identifies an invalid dependency where
    infrastructure imports from domain when it's not allowed in the configuration.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = ["domain"]
downstream = []
"""

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """from project.domain.service import Service""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 1
    assert problems[0].layer_to == "domain"
    assert problems[0].layer_from == "infrastructure"


def test_valid_dependency_downstream(temp_project):
    """
    Tests that the analyzer correctly identifies a dependency violation when
    domain imports from infrastructure, which is allowed in the downstream configuration
    but still reported as a problem because it's not in the upstream configuration.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = []
downstream = []
"""

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """pass""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 1
    assert problems[0].layer_to == "infrastructure"
    assert problems[0].layer_from == "domain"


def test_valid_dependency_upstream(temp_project):
    """
    Tests that the analyzer correctly identifies a dependency violation when
    domain imports from infrastructure, which is not allowed in the configuration
    because domain is not in infrastructure's downstream list.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = []

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = ["domain"]
downstream = []
"""

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """pass""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 1


def test_type_checking_import(temp_project):
    """
    Tests that the analyzer correctly ignores imports that are inside TYPE_CHECKING blocks,
    as these are only used for type hints and don't create actual runtime dependencies.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = ["domain"]
downstream = []
    """

    project_structure = {
        "domain/service.py": """
if TYPE_CHECKING:
    from project.infrastructure.db import Database
""",
        "infrastructure/db.py": """
if TYPE_CHECKING:
    from project.domain.service import Service
""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 0


def test_exclude_modules(temp_project):
    """
    Tests that the analyzer correctly excludes modules specified in the exclude_modules list,
    preventing them from being checked for dependency violations.
    """
    toml_config = """
exclude_modules = ["*.db"]

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = ["domain"]
downstream = []
    """

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """from project.domain.service import Service""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, exclude_modules)

    assert len(problems) == 0


def test_invalid_dependency2(temp_project):
    """
    Tests that the analyzer correctly identifies multiple dependency violations
    when neither layer has downstream or upstream configurations that allow
    the dependencies between them.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
upstream = []
downstream = []

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
upstream = []
downstream = []
"""

    project_structure = {
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """from project.domain.service import Service""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 2
