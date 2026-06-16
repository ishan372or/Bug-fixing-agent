from retrieval.state import IndexingState,FileMetadata
from pathlib import Path
import ast

def read_files(state:IndexingState):
    repo_path=Path(state['repo_path'])
    files=[]
    for path in repo_path.rglob("*"):
        if path.is_file():
            files.append({'path': str(path)})
    
    return {
        "getfiles": files
    }
    
def generate_metadata(state: IndexingState):

    files_metadata = []

    for file in state["getfiles"]:

        file_path = Path(file["path"])

        try:
            source = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

            imports = []
            functions = []
            classes = []
            decorators = []
            exception_types = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(
                        alias.name
                        for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            decorators.append(dec.id)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            decorators.append(dec.id)
                elif isinstance(node, ast.ExceptHandler):
                    if (
                        node.type
                        and isinstance(node.type, ast.Name)
                    ):
                        exception_types.append(
                            node.type.id
                        )
            files_metadata.append(
                FileMetadata(
                    file_path=str(file_path),
                    imports=list(set(imports)),
                    functions=list(set(functions)),
                    classes=list(set(classes)),
                    module_docstring=ast.get_docstring(tree),
                    decorators=list(set(decorators)),
                    exception_types=list(
                        set(exception_types)
                    ),
                    api_routes=[],
                    database_models=[],
                    database_queries=[],
                    external_dependencies=list(
                        set(imports)
                    ),
                    file_size=file_path.stat().st_size,
                    line_count=len(
                        source.splitlines()
                    ),
                )
            )
        except Exception:
            continue

    return {
        "files": files_metadata
    }