from __future__ import annotations

import json
import pickle
from pathlib import Path

import faiss
import numpy as np

from Bugfix_agent.agent.state import AgentState, BugReport, FileCode, RepoTreeNode
from Bugfix_agent.llm.ollama_llm import OllamaEmbedLLM, OllamaLLM
from Bugfix_agent.retrieval.state import IndexedFileRecord
from Bugfix_agent.utils import (
    extract_json_object,
    is_test_path,
    should_ignore_repo_path,
    tokenize_text,
)


def _fallback_record(file_path: str) -> IndexedFileRecord:
    path_obj = Path(file_path)
    relative_path = path_obj.name.replace("\\", "/")
    keyword_source = relative_path

    try:
        source = path_obj.read_text(encoding="utf-8", errors="ignore")
        keyword_source = f"{relative_path}\n{source[:1200]}"
        line_count = len(source.splitlines())
        file_size = path_obj.stat().st_size
    except OSError:
        line_count = 0
        file_size = 0

    return IndexedFileRecord(
        file_path=file_path,
        relative_path=relative_path,
        summary="",
        file_size=file_size,
        line_count=line_count,
        is_test_file=is_test_path(relative_path),
        keywords=tokenize_text(keyword_source),
    )


def _load_index_records() -> list[IndexedFileRecord]:
    with open("paths.pkl", "rb") as file_handle:
        raw_metadata = pickle.load(file_handle)

    records: list[IndexedFileRecord] = []

    for item in raw_metadata:
        if isinstance(item, IndexedFileRecord):
            records.append(item)
        elif isinstance(item, str):
            records.append(_fallback_record(item))
        else:
            records.append(IndexedFileRecord(**item))

    return records


def _read_file_code(file_path: str) -> FileCode | None:
    try:
        code = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    return FileCode(file_path=file_path, file_content=code)


def _record_terms(record: IndexedFileRecord) -> set[str]:
    token_groups = [
        record.relative_path,
        record.summary,
        " ".join(record.functions),
        " ".join(record.classes),
        " ".join(record.imports),
        " ".join(record.decorators),
        " ".join(record.exception_types),
        " ".join(record.keywords),
    ]

    terms: set[str] = set()
    for group in token_groups:
        terms.update(tokenize_text(group))
    return terms


def _score_record(
    record: IndexedFileRecord,
    query_terms: set[str],
    vector_rank: int | None,
    vector_distance: float | None,
    prefer_tests: bool,
) -> float:
    record_terms = _record_terms(record)
    overlap = len(query_terms & record_terms)
    symbol_terms = {term for term in tokenize_text(" ".join([*record.functions, *record.classes]))}
    symbol_overlap = len(query_terms & symbol_terms)
    path_overlap = len(query_terms & set(tokenize_text(record.relative_path)))

    score = 0.0

    if vector_rank is not None:
        score += max(0.0, 6.0 - (vector_rank * 0.35))
    if vector_distance is not None:
        score += 2.0 / (1.0 + max(vector_distance, 0.0))

    score += overlap * 1.2
    score += path_overlap * 1.6
    score += symbol_overlap * 1.8

    if prefer_tests and record.is_test_file:
        score += 1.0
    if not prefer_tests and not record.is_test_file:
        score += 0.6

    return score


def _test_relevance_bonus(implementation: IndexedFileRecord, test_record: IndexedFileRecord) -> float:
    impl_terms = set(tokenize_text(implementation.relative_path))
    impl_terms.update(tokenize_text(" ".join(implementation.functions)))
    test_terms = set(tokenize_text(test_record.relative_path))
    test_terms.update(tokenize_text(" ".join(test_record.functions)))

    shared = len(impl_terms & test_terms)
    bonus = shared * 0.9

    impl_stem = Path(implementation.relative_path).stem.lower()
    test_name = Path(test_record.relative_path).name.lower()
    if impl_stem and impl_stem in test_name:
        bonus += 3.0

    impl_parent = Path(implementation.relative_path).parent.name.lower()
    if impl_parent and impl_parent != "." and impl_parent in test_record.relative_path.lower():
        bonus += 1.2

    return bonus


def generate_bug_report_embeddings(state: AgentState):
    llm = OllamaEmbedLLM()
    bug_report = state["bug_report"]
    return {
        "bug_report": BugReport(
            bug_report=bug_report.bug_report,
            bug_report_embedding=llm.embed(bug_report.bug_report),
        )
    }


def semantic_search(state: AgentState):
    records = _load_index_records()
    if not records:
        return {
            "possible_file_paths": [],
            "possible_test_paths": [],
        }

    index = faiss.read_index("repo.index")
    query_embedding = np.array([state["bug_report"].bug_report_embedding], dtype=np.float32)
    search_k = min(len(records), max(12, len(records)))
    distances, indices = index.search(query_embedding, k=search_k)
    query_terms = set(tokenize_text(state["bug_report"].bug_report))

    vector_lookup: dict[int, tuple[int, float]] = {}
    for rank, (record_index, distance) in enumerate(zip(indices[0], distances[0])):
        if record_index != -1:
            vector_lookup[int(record_index)] = (rank, float(distance))

    implementation_scores: list[tuple[float, IndexedFileRecord]] = []
    test_scores: list[tuple[float, IndexedFileRecord]] = []

    for index_position, record in enumerate(records):
        rank, distance = vector_lookup.get(index_position, (None, None))
        score = _score_record(
            record=record,
            query_terms=query_terms,
            vector_rank=rank,
            vector_distance=distance,
            prefer_tests=record.is_test_file,
        )
        if record.is_test_file:
            test_scores.append((score, record))
        else:
            implementation_scores.append((score, record))

    implementation_scores.sort(key=lambda item: (item[0], item[1].relative_path), reverse=True)
    top_implementation = implementation_scores[0][1] if implementation_scores else None

    if top_implementation:
        boosted_test_scores = []
        for score, record in test_scores:
            boosted_test_scores.append((score + _test_relevance_bonus(top_implementation, record), record))
        test_scores = boosted_test_scores

    test_scores.sort(key=lambda item: (item[0], item[1].relative_path), reverse=True)

    return {
        "possible_file_paths": [record.file_path for _, record in implementation_scores[:6]],
        "possible_test_paths": [record.file_path for _, record in test_scores[:6]],
    }


def read_possible_files(state: AgentState):
    possible_files = []
    possible_test_files = []

    for path in state.get("possible_file_paths", []):
        file_code = _read_file_code(path)
        if file_code is not None:
            possible_files.append(file_code)

    for path in state.get("possible_test_paths", []):
        file_code = _read_file_code(path)
        if file_code is not None:
            possible_test_files.append(file_code)

    return {
        "possible_files": possible_files,
        "possible_test_files": possible_test_files,
    }


def _truncate_source(code: str, max_lines: int = 250) -> str:
    lines = code.splitlines()
    if len(lines) <= max_lines:
        return code
    head = "\n".join(lines[: max_lines // 2])
    tail = "\n".join(lines[-(max_lines // 2) :])
    return f"{head}\n...\n{tail}"


def _load_record_map() -> dict[str, IndexedFileRecord]:
    return {record.file_path: record for record in _load_index_records()}


def _select_relevant_test_files(
    selected_file: FileCode,
    state: AgentState,
    records_by_path: dict[str, IndexedFileRecord],
) -> tuple[list[str], list[FileCode]]:
    selected_record = records_by_path.get(selected_file.file_path, _fallback_record(selected_file.file_path))
    candidates = {
        test_record.file_path: test_record
        for test_record in records_by_path.values()
        if test_record.is_test_file
    }

    for file_code in state.get("possible_test_files", []):
        candidates.setdefault(file_code.file_path, records_by_path.get(file_code.file_path, _fallback_record(file_code.file_path)))

    ranked_tests = sorted(
        [
            (
                _test_relevance_bonus(selected_record, record)
                + len(set(tokenize_text(state["bug_report"].bug_report)) & _record_terms(record)) * 0.8,
                record,
            )
            for record in candidates.values()
        ],
        key=lambda item: (item[0], item[1].relative_path),
        reverse=True,
    )

    chosen_paths: list[str] = []
    chosen_files: list[FileCode] = []

    for _, record in ranked_tests[:4]:
        file_code = _read_file_code(record.file_path)
        if file_code is None:
            continue
        chosen_paths.append(record.file_path)
        chosen_files.append(file_code)

    return chosen_paths, chosen_files


def find_exact_file(state: AgentState):
    possible_files = state.get("possible_files", [])
    if not possible_files:
        raise ValueError("Semantic search did not yield any readable implementation candidates.")

    if len(possible_files) == 1:
        selected_file = possible_files[0]
    else:
        llm = OllamaLLM()
        records_by_path = _load_record_map()
        candidate_sections = []

        for file_code in possible_files:
            record = records_by_path.get(file_code.file_path, _fallback_record(file_code.file_path))
            candidate_sections.append(
                f"""
Path: {file_code.file_path}
Summary: {record.summary}
Functions: {record.functions}
Classes: {record.classes}
Imports: {record.imports}
Source Excerpt:
{_truncate_source(file_code.file_content)}
""".strip()
            )

        prompt = f"""
You are selecting the single implementation file most responsible for a reported Python bug.

Bug Report:
{state["bug_report"].bug_report}

Candidate Files:

{chr(10).join(candidate_sections)}

Task:
- Pick the ONE implementation file most likely responsible for the bug.
- Prefer the concrete implementation over tests, mocks, or wrappers.
- Use symbol names, control flow, and path hints from the bug report.

Return ONLY valid JSON using this schema:
{{
  "file_path": "<exact candidate path>"
}}
""".strip()

        response = llm.invoke(prompt).strip()
        payload = json.loads(extract_json_object(response))
        chosen_path = Path(payload["file_path"]).as_posix()

        selected_file = possible_files[0]
        for file_code in possible_files:
            candidate_path = Path(file_code.file_path).as_posix()
            if candidate_path == chosen_path or candidate_path.endswith(chosen_path) or chosen_path.endswith(candidate_path):
                selected_file = file_code
                break

    records_by_path = _load_record_map()
    relevant_test_paths, relevant_test_files = _select_relevant_test_files(selected_file, state, records_by_path)

    return {
        "file_code": selected_file,
        "original_file_code": state.get("original_file_code", selected_file),
        "possible_test_paths": relevant_test_paths,
        "possible_test_files": relevant_test_files,
    }


def get_repo_tree(state: AgentState):
    repo_path = Path(state["repo_path"])
    repo_tree = []

    for path in repo_path.rglob("*"):
        if should_ignore_repo_path(path, repo_path):
            continue
        repo_tree.append(
            RepoTreeNode(
                path=str(path.relative_to(repo_path)).replace("\\", "/"),
                type="directory" if path.is_dir() else "file",
            )
        )

    return {
        "repo_tree": repo_tree,
    }
