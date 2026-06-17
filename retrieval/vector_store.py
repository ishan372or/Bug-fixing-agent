import faiss
import pickle
import numpy as np

from retrieval.state import IndexingState

def store_vector_db(state: IndexingState):
    repo_embed = state["repo_embed"]

    vectors = np.array([node.embedding for node in repo_embed],dtype=np.float32)
    index = faiss.IndexFlatL2(vectors.shape[1])
    
    index.add(vectors)

    faiss.write_index(
        index,
        "repo.index"
    )

    with open("paths.pkl", "wb") as f:

        pickle.dump(
            [node.file_path for node in repo_embed],
            f
        )

    return {}