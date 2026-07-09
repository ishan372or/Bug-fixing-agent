from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field


class GetFiles(TypedDict):
    path: str


class FileMetadata(BaseModel):
    file_path: str
    relative_path: str
    imports: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    module_docstring: str | None = None
    decorators: list[str] = Field(default_factory=list)
    exception_types: list[str] = Field(default_factory=list)
    api_routes: list[str] = Field(default_factory=list)
    database_models: list[str] = Field(default_factory=list)
    database_queries: list[str] = Field(default_factory=list)
    external_dependencies: list[str] = Field(default_factory=list)
    file_size: int
    line_count: int
    is_test_file: bool = False
    keywords: list[str] = Field(default_factory=list)


class SummaryNode(BaseModel):
    file_path: str
    summary: str


class RepoEmbedNode(BaseModel):
    file_path: str
    embedding: list[float]


class IndexedFileRecord(BaseModel):
    file_path: str
    relative_path: str
    summary: str
    imports: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    module_docstring: str | None = None
    decorators: list[str] = Field(default_factory=list)
    exception_types: list[str] = Field(default_factory=list)
    api_routes: list[str] = Field(default_factory=list)
    database_models: list[str] = Field(default_factory=list)
    database_queries: list[str] = Field(default_factory=list)
    external_dependencies: list[str] = Field(default_factory=list)
    file_size: int
    line_count: int
    is_test_file: bool = False
    keywords: list[str] = Field(default_factory=list)

    def searchable_terms(self) -> set[str]:
        values = [
            self.relative_path,
            self.summary,
            *self.imports,
            *self.functions,
            *self.classes,
            *self.decorators,
            *self.exception_types,
            *self.api_routes,
            *self.database_models,
            *self.database_queries,
            *self.external_dependencies,
            *self.keywords,
        ]
        return {value.lower() for value in values if value}


class IndexingState(TypedDict):
    repo_path: str
    getfiles: list[GetFiles]
    files: list[FileMetadata]
    summaries: list[SummaryNode]
    repo_embed: list[RepoEmbedNode]
