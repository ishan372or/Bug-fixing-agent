from Bugfix_agent.agent.components.apply_patch import (
    build_updated_source,
    clean_generated_code,
    validate_python_source,
)


def test_clean_generated_code_removes_markdown_fences():
    generated = "```python\nreturn a / b\n```"

    assert clean_generated_code(generated) == "return a / b"


def test_build_updated_source_preserves_indentation():
    source = "def divide(a, b):\n    return a * b\n"

    updated, replacement = build_updated_source(
        file_code=source,
        start_line=2,
        end_line=2,
        replacement_code="return a / b",
    )

    assert replacement == "    return a / b"
    assert updated == "def divide(a, b):\n    return a / b\n"


def test_validate_python_source_rejects_invalid_syntax():
    error = validate_python_source("def broken(:\n    pass\n", "broken.py")

    assert error is not None
    assert "SyntaxError" in error
