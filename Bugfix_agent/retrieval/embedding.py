from Bugfix_agent.llm.ollama_llm import OllamaEmbedLLM
from Bugfix_agent.retrieval.state import IndexingState, RepoEmbedNode


def generate_embeddings(state: IndexingState):
    llm_embed = OllamaEmbedLLM()
    embeddings: list[RepoEmbedNode] = []

    for summary in state["summaries"]:
        embeddings.append(
            RepoEmbedNode(
                file_path=summary.file_path,
                embedding=llm_embed.embed(summary.summary),
            )
        )

    return {
        "repo_embed": embeddings,
    }
