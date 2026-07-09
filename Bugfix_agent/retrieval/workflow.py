from langgraph.graph import StateGraph,START,END
from Bugfix_agent.retrieval.state import IndexingState
from Bugfix_agent.retrieval.file_reader import read_files
from Bugfix_agent.retrieval.file_reader import generate_metadata
from Bugfix_agent.retrieval.summarise import generate_summaries
from Bugfix_agent.retrieval.embedding import generate_embeddings
from Bugfix_agent.retrieval.vector_store import store_vector_db

graph_builder=StateGraph(IndexingState)

graph_builder.add_node("read_files",read_files)
graph_builder.add_node("generate_metadata",generate_metadata)
graph_builder.add_node("generate_summaries",generate_summaries)
graph_builder.add_node("generate_embeddings",generate_embeddings)
graph_builder.add_node("store_vector_db",store_vector_db)

graph_builder.add_edge(
    START,
    "read_files"
)

graph_builder.add_edge(
    "read_files",
    "generate_metadata"
)

graph_builder.add_edge(
    "generate_metadata",
    "generate_summaries"
)

graph_builder.add_edge(
    "generate_summaries",
    "generate_embeddings"
)

graph_builder.add_edge(
    "generate_embeddings",
    "store_vector_db"
)

graph_builder.add_edge(
    "store_vector_db",
    END
)

workflow = graph_builder.compile()

