import ast
from collections import defaultdict
from dataclasses import dataclass
from typing import Set, List, Dict

from layers_linter.search_modules import ModulePathT


@dataclass
class ImportInfo:
    module: ModulePathT
    line_number: int
    is_internal: bool  # True if it's a project module, False if it's a library


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, current_module: ModulePathT, all_project_modules: Set[ModulePathT]):
        self.imports: List[ImportInfo] = []
        self.current_module = current_module
        self.all_project_modules = all_project_modules
        self.inside_type_checking = False

    def process_import(self, node: ast.AST, module_name: ModulePathT):
        if self.inside_type_checking:
            return

        is_internal = module_name in self.all_project_modules
        self.imports.append(ImportInfo(module_name, node.lineno, is_internal))

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.name
            self.process_import(node, ModulePathT(name))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.level > 0:
            if not self.current_module:
                return
            parts = self.current_module.split(".")
            level = node.level
            if level > len(parts):
                return
            base_parts = parts[:-level]
            module = node.module
            if not module:
                return
            new_parts = base_parts + [module]
            module_name = ModulePathT(".".join(new_parts))
        else:
            module_name = ModulePathT(node.module)
        self.process_import(node, module_name)

    def visit_If(self, node: ast.If):
        if isinstance(node.test, ast.Name) and "TYPE_CHECKING" in node.test.id:
            old_flag = self.inside_type_checking
            self.inside_type_checking = True
            for stmt in node.body:
                self.visit(stmt)
            self.inside_type_checking = old_flag
            for stmt in node.orelse:
                self.visit(stmt)
        else:
            self.generic_visit(node)


def collect_imports(all_project_modules, modules_list) -> Dict[ModulePathT, List[ImportInfo]]:
    module_imports: Dict[ModulePathT, List[ImportInfo]] = defaultdict(list)
    for path, module_path in modules_list:
        with open(path) as f:
            content = f.read()
        tree = ast.parse(content)
        visitor = ImportVisitor(module_path, all_project_modules)
        visitor.visit(tree)
        module_imports[module_path].extend(visitor.imports)

    return module_imports
