from __future__ import annotations

import json

from Bugfix_agent.agent.state import AgentState, PatchProposal
from Bugfix_agent.llm.ollama_llm import OllamaLLM
from Bugfix_agent.utils import extract_json_object, strip_markdown_fences


def _format_tests(state: AgentState, max_files: int = 4) -> str:
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
        sections.append(
            f"""
Attempt {attempt.iteration}
Applied: {attempt.applied}
Passed: {attempt.passed}
Explanation: {attempt.generated_patch.explanation if attempt.generated_patch else ""}
Confidence: {attempt.generated_patch.confidence if attempt.generated_patch else 0.0}
Patch:
{attempt.generated_patch.replacement_code if attempt.generated_patch else ""}
Validation Error:
{attempt.validation_error or "None"}
Pytest Output:
{attempt.test_output}
""".strip()
        )

    return "\n\n".join(sections)


def _parse_patch_response(response: str) -> PatchProposal:
    try:
        payload = json.loads(extract_json_object(response))
        confidence = float(payload.get("confidence", 0.0))
        confidence = max(0.0, min(confidence, 1.0))
        return PatchProposal(
            replacement_code=strip_markdown_fences(payload["replacement_code"]).strip("\n"),
            explanation=payload.get("explanation", "").strip(),
            confidence=confidence,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return PatchProposal(
            replacement_code=strip_markdown_fences(response).strip(),
            explanation="The model did not return valid JSON, so the raw response was used as fallback replacement code.",
            confidence=0.15,
        )


def generate_code(state: AgentState):
    bug_location = state["bug_location"]
    llm = OllamaLLM()
    file_code = state["file_code"].file_content
    target_lines = file_code.splitlines()[bug_location.start_line - 1 : bug_location.end_line]
    latest_feedback = state.get("test_output", "") or state.get("validation_error", "")

    prompt = f"""
You are an expert Python software engineer acting as an autonomous bug-fixing agent.

Goal:
- Fix the reported bug.
- Preserve existing behavior unless it is clearly wrong.
- Anticipate hidden tests and edge cases.
- Produce production-quality code, not the smallest possible hack.
- Match the surrounding code style and avoid duplicate logic.
- Return a syntactically correct replacement block that can be inserted directly into the file.

Bug Report:
{state["bug_report"].bug_report}

Target File:
{state["file_code"].file_path}

Full Source Code:
{file_code}

Localized Bug Block:
Function or Class: {bug_location.function_name}
Lines: {bug_location.start_line}-{bug_location.end_line}
Reason: {bug_location.reason}

Current Block To Replace:
{chr(10).join(target_lines)}

Relevant Tests:
{_format_tests(state)}

Previous Repair Attempts:
{_format_repair_history(state)}

Latest Validation or Test Feedback:
{latest_feedback or "No previous validation or test output."}

Requirements:
- Fix the reported issue.
- Preserve indentation relative to the target block.
- Handle obvious edge cases when appropriate for production code.
- Avoid regressions and keep existing public behavior stable.
- Return only the replacement block, not the whole file.
- Do not include markdown fences.

Return ONLY valid JSON using this schema:
{{
  "replacement_code": "<replacement block only>",
  "explanation": "<short explanation of why this fixes the bug and avoids regressions>",
  "confidence": <float between 0 and 1>
}}
""".strip()

    response = llm.invoke(prompt=prompt).strip()
    patch_candidate = _parse_patch_response(response)

    return {
        "patch_candidate": patch_candidate,
        "fixed_code": patch_candidate.replacement_code,
    }
