from __future__ import annotations

import os
import subprocess
import sys

from Bugfix_agent.agent.state import AgentState, RepairAttempt


def _run_pytest(command: list[str], repo_path: str) -> tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return False, f"Pytest timed out after 300 seconds.\n{output}"

    output = result.stdout + result.stderr
    return result.returncode == 0, output


def run_test(state: AgentState):
    if not state.get("patch_applied", False):
        validation_error = state.get("validation_error", "Patch was not applied.")
        return {
            "test_passed": False,
            "test_output": f"Patch validation failed before pytest execution.\n{validation_error}",
        }

    repo_path = state["repo_path"]
    relevant_tests = state.get("possible_test_paths", [])
    targeted_output = ""

    if relevant_tests:
        targeted_passed, targeted_output = _run_pytest(
            [sys.executable, "-m", "pytest", *relevant_tests],
            repo_path,
        )
        if not targeted_passed:
            return {
                "test_passed": False,
                "test_output": f"Relevant test run failed.\n{targeted_output}",
            }

    full_suite_passed, full_suite_output = _run_pytest([sys.executable, "-m", "pytest"], repo_path)

    return {
        "test_passed": full_suite_passed,
        "test_output": "\n\n".join(part for part in [targeted_output, full_suite_output] if part),
    }


def store_feedback(state: AgentState):
    passed = state["test_passed"]
    test_output = state["test_output"]
    history = list(state.get("repair_history", []))

    history.append(
        RepairAttempt(
            iteration=state["retry_count"] + 1,
            bug_location=state.get("bug_location"),
            generated_patch=state.get("patch_candidate"),
            test_output=test_output,
            validation_error=state.get("validation_error") or None,
            passed=passed,
            applied=state.get("patch_applied", False),
        )
    )

    return {
        "repair_history": history,
        "retry_count": state["retry_count"] + (0 if passed else 1),
        "final_status": "SUCCESS" if passed else state.get("final_status", "RETRYING"),
    }


def max_retry_failed(state: AgentState):
    return {
        "final_status": "FAILED",
    }
