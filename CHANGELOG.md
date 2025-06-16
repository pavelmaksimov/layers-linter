# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
