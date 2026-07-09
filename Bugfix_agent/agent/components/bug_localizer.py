from __future__ import annotations

import ast
import json

from Bugfix_agent.agent.state import AgentState, BugLocation
from Bugfix_agent.llm.ollama_llm import OllamaLLM
from Bugfix_agent.utils import extract_json_object


def _format_test_context(state: AgentState, max_files: int = 3) -> str:
    test_files = state.get("possible_test_files", [])
    if not test_files:
        return "No relevant tests were retrieved."

    sections = []
    for file_code in test_files[:max_files]:
        sections.append(
            f"""
Test File: {file_code.file_path}
Content:
{file_code.file_content}
""".strip()
        )

    return "\n\n".join(sections)


def _format_repair_history(state: AgentState, max_attempts: int = 3) -> str:
    history = state.get("repair_history", [])
    if not history:
        return "No previous repair attempts."

    sections = []
    for attempt in history[-max_attempts:]:
        patch_code = attempt.generated_patch.replacement_code if attempt.generated_patch else ""
        explanation = attempt.generated_patch.explanation if attempt.generated_patch else ""
        sections.append(
            f"""
Attempt {attempt.iteration}
Applied: {attempt.applied}
Passed: {attempt.passed}
Patch Explanation: {explanation}
Patch Code:
{patch_code}
Validation Error:
{attempt.validation_error or "None"}
Test Output:
{attempt.test_output}
""".strip()
        )

    return "\n\n".join(sections)


def _fallback_location(file_path: str, file_code: str, bug_report: str) -> BugLocation:
    try:
        tree = ast.parse(file_code)
    except SyntaxError:
        total_lines = max(1, len(file_code.splitlines()))
        return BugLocation(
            file_path=file_path,
            function_name="<file>",
            start_line=1,
            end_line=total_lines,
            reason="Fallback localization used the whole file because the current file cannot be parsed.",
        )

    lowered_report = bug_report.lower()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name.lower() in lowered_report:
            return BugLocation(
                file_path=file_path,
                function_name=node.name,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                reason="Fallback localization matched a symbol named in the bug report.",
            )

    total_lines = max(1, len(file_code.splitlines()))
    return BugLocation(
        file_path=file_path,
        function_name="<file>",
        start_line=1,
        end_line=total_lines,
        reason="Fallback localization used the full file because the model response was invalid.",
    )


def find_bug(state: AgentState):
    file_code = state["file_code"].file_content
    bug_report = state["bug_report"].bug_report
    llm = OllamaLLM()

    prompt = f"""
You are localizing a Python bug for an autonomous repair agent.

Bug Report:
{bug_report}

Target File:
{state["file_code"].file_path}

Source Code:
{file_code}

Relevant Tests:
{_format_test_context(state)}

Previous Repair Attempts:
{_format_repair_history(state)}

Task:
- Identify the smallest contiguous block of code that should be replaced to fix the bug.
- Prefer a precise block, but include any lines needed for a production-quality fix.
- Consider hidden tests, edge cases, and previous failures.

Return ONLY valid JSON using this schema:
{{
  "function_name": "<function or class name, or <file>>",
  "start_line": <1-indexed start line>,
  "end_line": <1-indexed end line>,
  "reason": "<why this block should change>"
}}
""".strip()

    response = llm.invoke(prompt).strip()

    try:
        payload = json.loads(extract_json_object(response))
        total_lines = max(1, len(file_code.splitlines()))
        start_line = max(1, min(int(payload["start_line"]), total_lines))
        end_line = max(start_line, min(int(payload["end_line"]), total_lines))
        return {
            "bug_location": BugLocation(
                file_path=state["file_code"].file_path,
                function_name=payload.get("function_name", "<file>"),
                start_line=start_line,
                end_line=end_line,
                reason=payload.get("reason", "Model-selected bug location."),
            )
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {
            "bug_location": _fallback_location(
                file_path=state["file_code"].file_path,
                file_code=file_code,
                bug_report=bug_report,
            )
        }
