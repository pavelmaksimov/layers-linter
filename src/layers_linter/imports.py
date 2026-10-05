import ast
import warnings
from collections import defaultdict
from dataclasses import dataclass

from layers_linter.search_modules import ModulePathT

TYPING_MODULES = ("typing", "typing_extensions")


@dataclass
class ImportInfo:
    module: ModulePathT
    line_number: int
    is_internal: bool  # True if it's a project module, False if it's a library


def collect_packages(all_project_modules: set[ModulePathT]) -> set[ModulePathT]:
    """Return all packages of the project, e.g. 'project' and 'project.domain'."""
    packages = set()
    for module in all_project_modules:
        parts = module.split(".")
        for i in range(1, len(parts)):
            packages.add(ModulePathT(".".join(parts[:i])))
    return packages


class ImportVisitor(ast.NodeVisitor):
    def __init__(
        self,
        current_module: ModulePathT,
        all_project_modules: set[ModulePathT],
        project_packages: set[ModulePathT] | None = None,
    ):
        self.imports: list[ImportInfo] = []
        self.current_module = current_module
        self.all_project_modules = all_project_modules
        if project_packages is None:
            project_packages = collect_packages(all_project_modules)
        self.project_packages = project_packages
        self.inside_type_checking = False
        # Names TYPE_CHECKING is imported as, e.g. "from typing import TYPE_CHECKING as TC".
        self.type_checking_aliases: set[str] = set()

    def process_import(self, node: ast.AST, module_name: ModulePathT):
        if self.inside_type_checking:
            return

        is_internal = True
        if module_name not in self.all_project_modules:
            package_init = ModulePathT(f"{module_name}.__init__")
            if package_init in self.all_project_modules:
                # Importing a package runs its __init__ module.
                module_name = package_init
            else:
                is_internal = module_name in self.project_packages

        self.imports.append(ImportInfo(module_name, node.lineno, is_internal))

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.process_import(node, ModulePathT(alias.name))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level > 0:
            if not self.current_module:
                return
            parts = self.current_module.split(".")
            level = node.level
            if level > len(parts):
                return
            base_parts = parts[:-level]
            if node.module:
                base_parts.append(node.module)
            if not base_parts:
                return
            module_name = ModulePathT(".".join(base_parts))
        else:
            module_name = ModulePathT(node.module)
            if module_name in TYPING_MODULES:
                for alias in node.names:
                    if alias.name == "TYPE_CHECKING" and alias.asname:
                        self.type_checking_aliases.add(alias.asname)

        # "from package import submodule" depends on the submodule itself,
        # otherwise the dependency is on the module the names are taken from.
        imported_from_module = False
        for alias in node.names:
            submodule = ModulePathT(f"{module_name}.{alias.name}")
            if submodule in self.all_project_modules:
                self.process_import(node, submodule)
            else:
                imported_from_module = True

        if imported_from_module:
            self.process_import(node, module_name)

    def is_type_checking(self, test: ast.expr) -> bool:
        if isinstance(test, ast.Name):
            return "TYPE_CHECKING" in test.id or test.id in self.type_checking_aliases
        if isinstance(test, ast.Attribute):
            return test.attr == "TYPE_CHECKING"
        return False

    def visit_If(self, node: ast.If):
        test = node.test
        negated = isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
        if negated:
            test = test.operand

        if not self.is_type_checking(test):
            self.generic_visit(node)
            return

        # In "if not TYPE_CHECKING: ... else: ..." the else branch is the type-checking one.
        type_checking_body, runtime_body = (
            (node.orelse, node.body) if negated else (node.body, node.orelse)
        )

        old_flag = self.inside_type_checking
        self.inside_type_checking = True
        for stmt in type_checking_body:
            self.visit(stmt)
        self.inside_type_checking = old_flag

        for stmt in runtime_body:
            self.visit(stmt)


def collect_imports(all_project_modules, modules_list) -> dict[ModulePathT, list[ImportInfo]]:
    project_packages = collect_packages(all_project_modules)
    module_imports: dict[ModulePathT, list[ImportInfo]] = defaultdict(list)
    for path, module_path in modules_list:
        # Reading bytes lets ast honour the PEP 263 encoding declaration.
        with open(path, "rb") as f:
            content = f.read()
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            warnings.warn(f"Skipping {path}: {e}", stacklevel=2)
            continue
        visitor = ImportVisitor(module_path, all_project_modules, project_packages)
        visitor.visit(tree)
        module_imports[module_path].extend(visitor.imports)

    return module_imports
