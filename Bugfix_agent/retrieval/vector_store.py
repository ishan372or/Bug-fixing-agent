import pickle

import faiss
import numpy as np

from Bugfix_agent.retrieval.state import IndexedFileRecord, IndexingState
from Bugfix_agent.utils import model_to_dict


def store_vector_db(state: IndexingState):
    repo_embed = state["repo_embed"]

    if not repo_embed:
        raise ValueError("No repository embeddings were generated; indexing cannot continue.")

    vectors = np.array([node.embedding for node in repo_embed], dtype=np.float32)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, state["index_path"])

    metadata_by_path = {file.file_path: file for file in state["files"]}
    summary_by_path = {summary.file_path: summary.summary for summary in state["summaries"]}

    records = [
        IndexedFileRecord(
            file_path=file_metadata_by_path.file_path,
            relative_path=file_metadata_by_path.relative_path,
            summary=summary_by_path[file_metadata_by_path.file_path],
            imports=file_metadata_by_path.imports,
            functions=file_metadata_by_path.functions,
            classes=file_metadata_by_path.classes,
            module_docstring=file_metadata_by_path.module_docstring,
            decorators=file_metadata_by_path.decorators,
            exception_types=file_metadata_by_path.exception_types,
            api_routes=file_metadata_by_path.api_routes,
            database_models=file_metadata_by_path.database_models,
            database_queries=file_metadata_by_path.database_queries,
            external_dependencies=file_metadata_by_path.external_dependencies,
            file_size=file_metadata_by_path.file_size,
            line_count=file_metadata_by_path.line_count,
            is_test_file=file_metadata_by_path.is_test_file,
            keywords=file_metadata_by_path.keywords,
        )
        for repo_embed_node in repo_embed
        for file_metadata_by_path in [metadata_by_path[repo_embed_node.file_path]]
    ]

    with open(state["metadata_file_path"], "wb") as file_handle:
        pickle.dump([model_to_dict(record) for record in records], file_handle)

    return {}
