import fnmatch
from pathlib import Path
from typing import List, Set, NewType

ModulePathT = NewType("ModulePathT", str)
FilePathT = NewType("FilePathT", Path)


def match_pattern(module_name: ModulePathT, pattern: str) -> bool:
    """
    Check if module name matches the given pattern.

    Args:
        module_name: Full module name (e.g., 'project.domains.crm.models')
        pattern: Pattern to match (e.g., "project.crm", "project.crm.*", "*.crm", "crm.*", "*.crm.*", "project.*.crm")

    Returns:
        True if the module name matches the pattern, False otherwise

    Examples for pattern
        "project.crm"
        "project.domains.crm"
        "project.domains.crm.*"
        "*.crm",
        "crm.*",
        "*.crm.*",
        "project.*.crm"
    """
    return fnmatch.fnmatch(module_name, pattern)


def find_modules_in_directory(
    directory: FilePathT,
    patterns: List[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> List[tuple[FilePathT, ModulePathT]]:
    """
    Find modules in a directory based on specified inclusion and exclusion patterns.

    This function scans a directory for Python files and retrieves their paths,
    represented as tuples of file paths and module paths. The selection of modules
    is based on user-provided inclusion and exclusion patterns applied to module
    names.

    Parameters:
    directory: str
        The absolute or relative path to the directory to search for Python modules.
    patterns: list[str] or None, optional
        Patterns to include in the module search. If None, all modules are included.
    exclude_patterns: list[str] or None, optional
        Patterns to exclude from the module search. If None, no modules are excluded.

    Returns:
    list[tuple[FilePathT, ModulePathT]]
        FilePathT this is pathlib.Path
        ModulePathT example "project.domains.crm"
        List of tuples containing file paths and corresponding module paths for
        the modules matching the inclusion criteria and not matching the exclusion
        criteria.

    Raises:
    AssertionError
        If the 'patterns' argument is an empty list.
    """
    assert patterns != []

    modules: List[tuple[FilePathT, ModulePathT]] = []
    root_path = Path(directory)

    for file_path in root_path.rglob("*.py"):
        relative_path = file_path.relative_to(root_path.parent)
        parts = list(relative_path.with_suffix("").parts)
        module_name = ModulePathT(".".join(parts))

        if exclude_patterns and any(
            match_pattern(module_name, pattern) for pattern in exclude_patterns
        ):
            continue

        if patterns is None or any(match_pattern(module_name, pattern) for pattern in patterns):
            modules.append((FilePathT(file_path), ModulePathT(module_name)))

    return modules


def find_modules_by_patterns(directory: FilePathT, patterns: List[str]) -> Set[str]:
    """
    Finds and returns a set of module names whose names match the given patterns
    from a specific directory. It searches for all modules within the directory
    and filters them based on the provided patterns.

    Parameters:
    directory: str
        The path to the directory where the search for modules will be performed.
    patterns: List[str]
        A list of patterns to match against the module names.

    Returns:
    Set[str]
        A set of module names from the directory that match any of the given patterns.
    """
    all_modules = find_modules_in_directory(directory)
    matching_modules = set()

    for path, module in all_modules:
        for pattern in patterns:
            if match_pattern(module, pattern):
                matching_modules.add(module)
                break

    return matching_modules
