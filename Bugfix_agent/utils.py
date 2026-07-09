from __future__ import annotations

import re
from pathlib import Path
from typing import Any

IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "site-packages",
    "venv",
}

SUPPORTED_SOURCE_SUFFIXES = {
    ".py",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "bug",
    "by",
    "code",
    "does",
    "file",
    "for",
    "from",
    "function",
    "in",
    "into",
    "is",
    "it",
    "line",
    "lines",
    "module",
    "not",
    "of",
    "on",
    "or",
    "report",
    "should",
    "that",
    "the",
    "this",
    "to",
    "uses",
    "using",
    "when",
    "with",
}


def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def strip_markdown_fences(text: str) -> str:
    stripped = text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    return stripped


def extract_json_object(text: str) -> str:
    stripped = strip_markdown_fences(text).strip()

    if not stripped:
        raise ValueError("Expected JSON content, received an empty response.")

    start = stripped.find("{")
    if start == -1:
        raise ValueError(f"Could not find a JSON object in response: {text!r}")

    depth = 0
    in_string = False
    escaping = False

    for index in range(start, len(stripped)):
        char = stripped[index]

        if escaping:
            escaping = False
            continue

        if char == "\\":
            escaping = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : index + 1]

    raise ValueError(f"Could not find a complete JSON object in response: {text!r}")


def split_identifier(identifier: str) -> list[str]:
    tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", identifier.replace("-", "_"))
    results: list[str] = []

    for token in tokens:
        if token:
            results.append(token.lower())

    return results


def tokenize_text(text: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
    tokens: list[str] = []

    for raw_token in raw_tokens:
        lowered = raw_token.lower()
        if lowered not in STOPWORDS:
            tokens.append(lowered)

        for split_token in split_identifier(raw_token):
            if split_token not in STOPWORDS:
                tokens.append(split_token)

    return sorted(set(tokens))


def is_test_path(path: str | Path) -> bool:
    path_obj = Path(path)
    filename = path_obj.name.lower()
    parts = {part.lower() for part in path_obj.parts}

    return (
        "test" in parts
        or "tests" in parts
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    )


def should_ignore_repo_path(path: str | Path, repo_root: str | Path) -> bool:
    path_obj = Path(path)
    root_obj = Path(repo_root)

    try:
        relative_parts = path_obj.relative_to(root_obj).parts
    except ValueError:
        relative_parts = path_obj.parts

    if any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts):
        return True

    if path_obj.suffix == ".pyc":
        return True

    return False
