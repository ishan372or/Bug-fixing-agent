from Bugfix_agent.llm.ollama_llm import OllamaLLM
from Bugfix_agent.retrieval.state import IndexingState, SummaryNode


def generate_summaries(state: IndexingState):
    llm = OllamaLLM()
    files = state["files"]
    summaries: list[SummaryNode] = []

    for file in files:
        prompt = f"""
You are analyzing a Python repository for semantic code retrieval.

File Path:
{file.file_path}

Relative Path:
{file.relative_path}

Functions:
{file.functions}

Classes:
{file.classes}

Imports:
{file.imports}

Decorators:
{file.decorators}

Exception Types:
{file.exception_types}

API Routes:
{file.api_routes}

Database Models:
{file.database_models}

Database Queries:
{file.database_queries}

Is Test File:
{file.is_test_file}

Module Docstring:
{file.module_docstring}

Task:
- Summarize the file in 2-3 sentences.
- Mention the file's role in the repository, key behaviors, and important symbols.
- If it is a test file, mention what it validates.
- Keep the summary factual and retrieval-friendly.

Return only the summary.
""".strip()

        summary = llm.invoke(prompt).strip()
        summaries.append(
            SummaryNode(
                file_path=file.file_path,
                summary=summary,
            )
        )

    return {
        "summaries": summaries,
    }
