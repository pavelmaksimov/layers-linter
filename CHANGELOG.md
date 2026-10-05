# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Imports between modules of the same layer are no longer reported as LA001
- `from package import submodule` and `from . import submodule` are now checked against the submodule's layer
- Flake8 plugin reports problems only for the file being checked instead of repeating every project problem for each file, and analyzes the project once per run
- CLI exit code is `1` when problems are found (it was the number of problems, which wraps to `0` at 256)
- CLI prints a clear error for a missing config file or invalid configuration instead of a traceback
- Files with syntax errors are skipped with a warning instead of crashing the linter
- Source files are read according to their PEP 263 encoding declaration
- Hidden directories (`.venv`, `.git`, ...) are no longer scanned
- Fixed the `[libs]` example in README

## [3.2.2] - 2025-07-05

### Fixed

- Support TYPE_CHECKING with aliases

## [3.2.1] - 2025-07-05

### Fixed

- Improved TYPE_CHECKING detection to handle more flexible patterns in import conditions

## [3.2.0] - 2025-07-29

### Added

- Added checking for modules without a layer (enabled by default)
- Added `--no-check-no-layer` option to disable checking for modules without a layer
- Added LA002 error code for modules without a layer

## [3.1.0] - 2025-06-23

### Changed

- Improved error reporting and diagnostics
- Enhanced performance for large codebases
- Updated dependencies to latest versions
- Fix Problem.message

### Fixed

- Fixed edge cases in module path resolution
- Improved handling of complex import statements

## [3.0.0] - 2025-06-16

### Changed

- **Breaking**: Renamed configuration file from `deps.toml` to `layers.toml` across code and documentation
- Improved Problem.message formatting for better readability
- Added file_path property to Problem class for better error reporting

## [2.0.0] - 2025-06-16

### Changed

- **Breaking**: Introduced Problem subclasses for more extensible error messaging
- **Breaking**: Renamed `upstream` to `allowed_in` in configuration and related logic
- **Breaking**: Replaced `upstream`/`downstream` terminology with `depends_on` for clearer semantics
- Extracted import processing logic to a separate module for better code organization

## [1.0.1] - 2025-05-29

### Fixed

- Corrected Python version requirement
- Fixed minor bugs and improved stability

### Changed

- Removed redundant comments
- Added detailed docstrings to analyzer test cases
- General code refactoring for better maintainability

## [1.0.0] - 2025-05-20

### Added

- Initial release of Layers Linter
- Static code analysis for enforcing architectural boundaries
- Layer dependency validation
- Library usage restrictions
- CLI tool and Flake8 plugin integration
- Configuration via TOML file
