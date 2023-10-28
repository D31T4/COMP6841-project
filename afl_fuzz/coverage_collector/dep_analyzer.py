import ast
import pathlib
from importlib.util import find_spec
from typing import Callable

class _ImportFinder(ast.NodeVisitor):
    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self.imports: set[tuple[str, int]] = set()

    def visit_Import(self, node):
        """
        callback for 'import' statement
        """
        for n in node.names:
            self.imports.add((n.name or '', 0))

        ast.NodeVisitor.generic_visit(self, node)

    def visit_ImportFrom(self, node):
        """
        callback for 'import from' statement
        """
        self.imports.add((node.module or '', node.level)) # handle from . import case
        ast.NodeVisitor.generic_visit(self, node)

def ast_imports(fname: str) -> list[str]:
    '''
    get imported .py files by ast analysis

    Arguments:
    ---
    - fname: filename

    Returns:
    ---
    - imported package names
    '''
    with open(fname, 'r') as f:
        src = f.read()

    src = ast.parse(src)

    visiter = _ImportFinder()
    visiter.visit(src)
    
    return ['.' * lvl + name for name, lvl in visiter.imports]

def get_deps(entry: str, omit: list[Callable[[pathlib.Path], bool]] = None) -> list[str]:
    '''
    get dependencies of a python file

    Arguments:
    ---
    - entry: entry point
    - omit: list of functions. omit a file from analysis if any returns `True`.

    Returns:
    ---
    - list of dependencies
    '''
    omit = omit or []

    entry: pathlib.Path = pathlib.Path(entry).resolve()

    stack: list[tuple[pathlib.Path, str]] = [(entry, '')]
    deps: set[str] = set()
    deps.add(str(entry))

    # dfs
    while stack:
        fname, pkg = stack.pop()
        
        for name in ast_imports(fname):
            spec = find_spec(name, pkg)

            # sys modules: has_location = False
            if spec == None or not spec.has_location:
                continue

            origin = pathlib.Path(spec.origin).resolve()
            is_pkg = origin.name == '__init__.py'

            if any(o(origin) for o in omit):
                continue

            # already visited
            if str(origin) in deps:
                continue
            else:
                deps.add(str(origin))

            if not is_pkg:
                name = spec.parent

            stack.append((str(origin), name))

    return list(deps)