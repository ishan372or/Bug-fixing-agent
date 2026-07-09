from __future__ import annotations

import ast
from pathlib import Path

from Bugfix_agent.retrieval.state import FileMetadata, IndexingState
from Bugfix_agent.utils import (
    SUPPORTED_SOURCE_SUFFIXES,
    is_test_path,
    should_ignore_repo_path,
    tokenize_text,
)


def _decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_decorator_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return ast.dump(node, include_attributes=False)


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def read_files(state: IndexingState):
    repo_path = Path(state["repo_path"])
    files = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in SUPPORTED_SOURCE_SUFFIXES:
            continue
        if should_ignore_repo_path(path, repo_path):
            continue

        files.append({"path": str(path)})

    return {
        "getfiles": sorted(files, key=lambda file_node: file_node["path"]),
    }


def generate_metadata(state: IndexingState):
    repo_path = Path(state["repo_path"])
    files_metadata: list[FileMetadata] = []

    for file_node in state["getfiles"]:
        file_path = Path(file_node["path"])

        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        imports: set[str] = set()
        functions: set[str] = set()
        classes: set[str] = set()
        decorators: set[str] = set()
        exception_types: set[str] = set()
        api_routes: set[str] = set()
        database_models: set[str] = set()
        database_queries: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.add(node.name)
                for decorator in node.decorator_list:
                    decorator_name = _decorator_name(decorator)
                    decorators.add(decorator_name)
                    lowered = decorator_name.lower()
                    if any(route_keyword in lowered for route_keyword in ("route", "get", "post", "put", "delete", "patch")):
                        api_routes.add(decorator_name)
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = _decorator_name(child.func).lower()
                        if any(keyword in call_name for keyword in ("select", "insert", "update", "delete", "execute", "query")):
                            database_queries.add(call_name)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
                for decorator in node.decorator_list:
                    decorators.add(_decorator_name(decorator))
                base_names = {_base_name(base).lower() for base in node.bases}
                if any(base_name in {"model", "basemodel", "base"} for base_name in base_names):
                    database_models.add(node.name)
            elif isinstance(node, ast.ExceptHandler) and node.type:
                exception_name = _base_name(node.type)
                if exception_name:
                    exception_types.add(exception_name)

        relative_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
        keyword_text = " ".join(
            [
                relative_path,
                *sorted(functions),
                *sorted(classes),
                *sorted(imports),
                ast.get_docstring(tree) or "",
            ]
        )

        files_metadata.append(
            FileMetadata(
                file_path=str(file_path),
                relative_path=relative_path,
                imports=sorted(imports),
                functions=sorted(functions),
                classes=sorted(classes),
                module_docstring=ast.get_docstring(tree),
                decorators=sorted(decorators),
                exception_types=sorted(exception_types),
                api_routes=sorted(api_routes),
                database_models=sorted(database_models),
                database_queries=sorted(database_queries),
                external_dependencies=sorted(imports),
                file_size=file_path.stat().st_size,
                line_count=len(source.splitlines()),
                is_test_file=is_test_path(relative_path),
                keywords=tokenize_text(keyword_text),
            )
        )

    return {
        "files": files_metadata,
    }
