from typing import TypedDict, List
from typing_extensions import Literal
from pydantic import BaseModel

class getfiles(TypedDict):
    path : str

class FileMetadata(BaseModel):
    file_path: str
    imports: list[str]
    functions: list[str]
    classes: list[str]
    module_docstring: str | None
    decorators: list[str]
    exception_types: list[str]
    api_routes: list[str]
    database_models: list[str]
    database_queries: list[str]
    external_dependencies: list[str]
    file_size: int
    line_count: int

class SummaryNode(BaseModel):
    file_path: str
    summary: str

class RepoEmbedNode(BaseModel):
    file_path: str
    embedding: List[float]

class IndexingState(TypedDict):
    repo_path: str
    
    getfiles: List[getfiles]

    files: List[FileMetadata]

    summaries: List[SummaryNode]

    repo_embed: List[RepoEmbedNode]