# Layers Linter

A static code analyzer that enforces architectural boundaries for layers and outher libraries

## Overview

Layers Linter helps you maintain a clean architecture by:

1. **Enforcing layer dependencies**: Ensures that dependencies between modules follow the allowed directions
2. **Restricting library usage**: Verifies that libraries are only used in permitted layers
3. **Integrating with your workflow**: Works as a standalone CLI tool or as a Flake8 plugin

The linter analyzes your project's import structure by parsing the AST (Abstract Syntax Tree) of Python files, building a dependency graph, and validating it against your configuration.

## Installation

```bash
# Install from PyPI
pip install layers-linter

# Or install with Flake8 plugin support
pip install layers-linter[flake8]
```

## Usage

### Command Line Interface

Default path to deps.toml config in the current working directory.

```bash
# Basic usage
layers-linter /path/to/your/project

# With custom configuration file
layers-linter /path/to/your/project --config /path/to/your/deps.toml
```

### Flake8 Plugin

Add to your `.flake8` configuration:

```ini
[flake8]
select = LA
la-config = deps.toml
```

Then run Flake8 as usual:

Default path to deps.toml config in the current working directory.

```bash
flake8 /path/to/your/project [--la-config /path/to/your/config]
```

## Configuration

Layers Linter uses a TOML configuration file to define your project's architecture. By default, it looks for a file named `deps.toml` in the current directory.

### Configuration Format

```toml
# Optional: Modules to exclude from analysis
exclude_modules = ["*.__init__"]

# Layer definitions
[layers]

[layers.dicontainer]
description = ""
# Modules that belong to this layer
contains_modules = [
    "project.container"
]
# Layers that can use this layer (if empty list, no other layers can use it)
upstream = ["presentation"]
# Layers that this layer can use (if empty list, it can't use any other layers)
downstream = ["usecases"]


[layers.usecases]
description = ""
contains_modules = [
    "project.domains.*.use_cases.*",
    "project.domains.*.use_cases",
]
upstream = ["dicontainer", "presentation"]
downstream = []


[layers.presentation]
description = ""
contains_modules = [
    "project.presentation.*",
    "project.domains.*.endpoints"
]
upstream = []
downstream = ["dicontainer"]


# Library restrictions
[libs]

[libs.presentation]
# Layers that can use this library (if not specified, all layers can use it)
upstream = ["fastapi"]
```

### Pattern Matching

The `contains_modules` field supports pattern matching with wildcards:

- `project.module` - Exact match
- `project.module.*` - Module and all submodules
- `project.*.module` - Any module with the specified pattern
- `*.module` - Any module ending with the specified pattern

### Dependency Rules

- **Upstream**: Controls which layers can use this layer
  - Empty list (`[]`): No other layers can use this layer
  - Not specified or `"none"`: No restrictions

- **Downstream**: Controls which layers this layer can use
  - Empty list (`[]`): This layer cannot use any other layers
  - Not specified or `"none"`: No restrictions


## Error Codes

- **LA001**: Invalid dependency between layers
  - Example: `Invalid dependency from layer 'presentation' to layer 'repositories'`

- **LA020**: Restricted library usage
  - Example: `Layers [presentation] cannot use restricted library 'sqlalchemy'`

## Notes

- Imports inside `if typing.TYPE_CHECKING:` blocks are ignored
- The linter builds a complete dependency graph before validation, allowing for comprehensive analysis
