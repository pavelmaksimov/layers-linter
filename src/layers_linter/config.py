import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LayerConfig:
    contains_modules: List[str]
    depends_on: Optional[List[str]]


@dataclass
class LibConfig:
    allowed_in: Optional[List[str]]  # Layers allowed to use this lib


def load_config(
    config_path: Path,
) -> tuple[Dict[str, LayerConfig], Dict[str, LibConfig], List[str]]:
    with open(config_path, "rb") as f:
        raw_config = tomllib.load(f)

    layers_config = raw_config.get("layers", {})
    libs_config = raw_config.get("libs", {})
    exclude_modules = raw_config.get("exclude_modules", [])

    if not isinstance(exclude_modules, list):
        exclude_modules = []

    layers = {}
    for layer_name, layer_info in layers_config.items():
        depends_on = layer_info.get("depends_on", "none")
        if depends_on == "none":
            depends_on_parsed = None
        elif isinstance(depends_on, list):
            depends_on_parsed = depends_on
        else:
            depends_on_parsed = None

        contains_modules = layer_info.get("contains_modules", [])
        if not isinstance(contains_modules, list):
            contains_modules = []

        layers[layer_name] = LayerConfig(
            contains_modules=contains_modules,
            depends_on=depends_on_parsed,
        )

    libs = {}
    for lib_name, lib_info in libs_config.items():
        # Check for allowed_in or upstream (backward compatibility)
        allowed_in = lib_info.get("allowed_in", lib_info.get("upstream", "none"))
        if allowed_in == "none":
            allowed_in_parsed = None
        elif isinstance(allowed_in, list):
            allowed_in_parsed = allowed_in
        else:
            allowed_in_parsed = None

        libs[lib_name] = LibConfig(allowed_in=allowed_in_parsed)

    return layers, libs, exclude_modules
