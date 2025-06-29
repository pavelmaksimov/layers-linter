import pytest

from src.layers_linter.analyzer import analyze_dependencies
from src.layers_linter.config import load_config


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with the given config."""

    def create_project(toml_config: str, project_structure: dict):
        config_path = tmp_path / "layers.toml"
        with open(config_path, "w") as f:
            f.write(toml_config)

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
depends_on = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
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


def test_valid_dependency_depends_on(temp_project):
    """
    Tests that the analyzer correctly identifies a valid dependency when
    domain imports from infrastructure, which is allowed in the depends_on configuration.
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
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """pass""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 0


def test_invalid_dependency_depends_on(temp_project):
    """
    Tests that the analyzer correctly identifies a dependency violation when
    domain imports from infrastructure, which is not allowed in the configuration
    because infrastructure is not in domain's depends_on list.
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
depends_on = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
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
depends_on = ["infrastructure"]

[layers.infrastructure]
contains_modules = ["project.infrastructure.*"]
depends_on = []
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
    when neither layer has depends_on configurations that allow
    the dependencies between them.
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
        "domain/service.py": """from project.infrastructure.db import Database""",
        "infrastructure/db.py": """from project.domain.service import Service""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert len(problems) == 2


def test_module_in_multiple_layers(temp_project):
    """
    Tests that the analyzer raises ValueError when a module belongs to multiple layers.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.shared.*", "project.domain.*"]
depends_on = []

[layers.infrastructure]
contains_modules = ["project.shared.*", "project.infrastructure.*"]
depends_on = []
"""

    project_structure = {
        "shared/common.py": """# This module belongs to both domain and infrastructure layers""",
        "domain/service.py": """# This module belongs only to domain layer""",
        "infrastructure/db.py": """# This module belongs only to infrastructure layer""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"

    with pytest.raises(ValueError) as excinfo:
        analyze_dependencies(project_root, layers, libs, [])

    # Check that the error message contains the module path and layer names
    assert "project.shared.common" in str(excinfo.value)
    assert "domain" in str(excinfo.value)
    assert "infrastructure" in str(excinfo.value)


def test_layer_exclude_modules(temp_project):
    """
    Tests that the analyzer correctly excludes modules specified in the exclude_modules list
    at the layer level, preventing them from being considered part of that layer.
    """
    toml_config = """
exclude_modules = []

[layers]
[layers.domain]
contains_modules = ["project.domain.*"]
depends_on = ["libs"]
exclude_modules = ["project.domain.base"]

[layers.libs]
contains_modules = ["project.domain.base"]
depends_on = []
"""

    project_structure = {
        "domain/service.py": """from project.domain.base import Database""",
        "domain/base.py": """class Database: pass""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"
    problems = analyze_dependencies(project_root, layers, libs, [])

    assert not problems


def test_check_no_layer(temp_project):
    """
    Tests that the analyzer correctly identifies modules that don't belong to any layer
    when the check_no_layer option is enabled.
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
        "domain/service.py": """# This module belongs to domain layer""",
        "infrastructure/db.py": """# This module belongs to infrastructure layer""",
        "utils/helpers.py": """# This module doesn't belong to any layer""",
    }

    config_path = temp_project(toml_config, project_structure)
    layers, libs, exclude_modules = load_config(config_path)
    project_root = config_path.parent / "project"

    # Without check_no_layer option
    problems = analyze_dependencies(project_root, layers, libs, [])
    assert len(problems) == 0

    # With check_no_layer option
    problems = analyze_dependencies(project_root, layers, libs, [], check_no_layer=True)
    assert len(problems) == 1
    assert problems[0].module_path == "project.utils.helpers"
    assert problems[0].code == "LA002"
