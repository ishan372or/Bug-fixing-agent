from llm.ollama_llm import OllamaEmbedLLM
from retrieval.state import IndexingState,RepoEmbedNode

def generate_embeddings(state:IndexingState):
    llm_embed=OllamaEmbedLLM()
    summaries=state['summaries']
    embeddings=[]
    for summary in summaries:
        file_path=summary.file_path
        embedding=llm_embed.embed(summary.summary)
        embeddings.append(
            RepoEmbedNode(
            file_path=file_path,
            embedding=embedding
        ))
        
    return{
        "repo_embed": embeddings
    }
        
        