from __future__ import annotations

import ast
import textwrap
from pathlib import Path

from Bugfix_agent.agent.state import AgentState, FileCode, PatchProposal
from Bugfix_agent.utils import strip_markdown_fences


def clean_generated_code(text: str) -> str:
    return strip_markdown_fences(text).strip("\n")


def _leading_whitespace(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def normalize_replacement_indentation(original_block: list[str], replacement_code: str) -> str:
    cleaned = clean_generated_code(replacement_code)
    if not cleaned:
        return ""

    non_blank_original_lines = [line for line in original_block if line.strip()]
    target_indent = _leading_whitespace(non_blank_original_lines[0]) if non_blank_original_lines else ""
    dedented = textwrap.dedent(cleaned).strip("\n")

    normalized_lines = []
    for line in dedented.splitlines():
        if line.strip():
            normalized_lines.append(f"{target_indent}{line}")
        else:
            normalized_lines.append("")

    return "\n".join(normalized_lines)


def build_updated_source(file_code: str, start_line: int, end_line: int, replacement_code: str) -> tuple[str, str]:
    lines = file_code.splitlines()
    has_trailing_newline = file_code.endswith("\n")
    original_block = lines[start_line - 1 : end_line]
    normalized_replacement = normalize_replacement_indentation(original_block, replacement_code)
    replacement_lines = normalized_replacement.splitlines() if normalized_replacement else []
    lines[start_line - 1 : end_line] = replacement_lines
    updated_code = "\n".join(lines)

    if has_trailing_newline:
        updated_code += "\n"

    return updated_code, normalized_replacement


def validate_python_source(source: str, file_path: str) -> str | None:
    try:
        ast.parse(source, filename=file_path)
        compile(source, file_path, "exec")
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} (line {exc.lineno}, column {exc.offset})"
    except Exception as exc: 
        return f"{type(exc).__name__}: {exc}"

    return None


def _updated_patch_candidate(state: AgentState, normalized_replacement: str) -> PatchProposal:
    patch_candidate = state.get("patch_candidate")
    if patch_candidate is None:
        return PatchProposal(
            replacement_code=normalized_replacement,
            explanation="",
            confidence=0.0,
        )

    return PatchProposal(
        replacement_code=normalized_replacement,
        explanation=patch_candidate.explanation,
        confidence=patch_candidate.confidence,
    )


def apply_patch(state: AgentState):
    file_path = state["file_code"].file_path
    file_code = state["file_code"].file_content
    start_line = state["bug_location"].start_line
    end_line = state["bug_location"].end_line
    replacement_code = state.get("fixed_code", "")

    updated_code, normalized_replacement = build_updated_source(
        file_code=file_code,
        start_line=start_line,
        end_line=end_line,
        replacement_code=replacement_code,
    )

    validation_error = validate_python_source(updated_code, file_path)
    patch_candidate = _updated_patch_candidate(state, normalized_replacement)

    if validation_error:
        return {
            "patch_candidate": patch_candidate,
            "fixed_code": normalized_replacement,
            "patch_applied": False,
            "validation_error": validation_error,
        }

    Path(file_path).write_text(updated_code, encoding="utf-8")

    return {
        "file_code": FileCode(
            file_path=file_path,
            file_content=updated_code,
        ),
        "patch_candidate": patch_candidate,
        "fixed_code": normalized_replacement,
        "patch_applied": True,
        "validation_error": "",
    }
