from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field
from typing_extensions import Literal, NotRequired


class BugReport(BaseModel):
    bug_report: str
    bug_report_embedding: list[float] = Field(default_factory=list)


class FileCode(BaseModel):
    file_path: str
    file_content: str


File_Code = FileCode


class RepoTreeNode(BaseModel):
    path: str
    type: Literal["file", "directory"]


class BugLocation(BaseModel):
    file_path: str
    function_name: str
    start_line: int
    end_line: int
    reason: str


class PatchProposal(BaseModel):
    replacement_code: str
    explanation: str = ""
    confidence: float = 0.0


class RepairAttempt(BaseModel):
    iteration: int
    bug_location: BugLocation | None = None
    generated_patch: PatchProposal | None = None
    test_output: str = ""
    validation_error: str | None = None
    passed: bool = False
    applied: bool = False


class AgentState(TypedDict):
    """Represents the mutable LangGraph state used by the repair workflow."""

    bug_report: BugReport
    repo_path: str
    retry_count: int
    repair_history: list[RepairAttempt]

    repo_tree: NotRequired[list[RepoTreeNode]]
    possible_file_paths: NotRequired[list[str]]
    possible_files: NotRequired[list[FileCode]]
    possible_test_paths: NotRequired[list[str]]
    possible_test_files: NotRequired[list[FileCode]]
    file_code: NotRequired[FileCode]
    original_file_code: NotRequired[FileCode]
    bug_location: NotRequired[BugLocation]
    patch_candidate: NotRequired[PatchProposal]
    fixed_code: NotRequired[str]
    patch_applied: NotRequired[bool]
    validation_error: NotRequired[str]
    test_passed: NotRequired[bool]
    test_output: NotRequired[str]
    final_status: NotRequired[str]
