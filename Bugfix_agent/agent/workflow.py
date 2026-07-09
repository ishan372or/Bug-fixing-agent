from langgraph.graph import END, START, StateGraph

from Bugfix_agent.agent.components.apply_patch import apply_patch
from Bugfix_agent.agent.components.bug_localizer import find_bug
from Bugfix_agent.agent.components.patch_generator import generate_code
from Bugfix_agent.agent.components.searching import (
    find_exact_file,
    generate_bug_report_embeddings,
    read_possible_files,
    semantic_search,
)
from Bugfix_agent.agent.components.test_runner import max_retry_failed, run_test, store_feedback
from Bugfix_agent.agent.state import AgentState

graph_builder = StateGraph(AgentState)

graph_builder.add_node("generate_bug_report_embeddings", generate_bug_report_embeddings)
graph_builder.add_node("semantic_search", semantic_search)
graph_builder.add_node("read_possible_files", read_possible_files)
graph_builder.add_node("find_exact_file", find_exact_file)
graph_builder.add_node("find_bug", find_bug)
graph_builder.add_node("generate_patch", generate_code)
graph_builder.add_node("apply_patch", apply_patch)
graph_builder.add_node("run_test", run_test)
graph_builder.add_node("store_feedback", store_feedback)
graph_builder.add_node("max_retry_failed", max_retry_failed)

MAX_RETRIES = 10

graph_builder.add_edge(START, "generate_bug_report_embeddings")
graph_builder.add_edge("generate_bug_report_embeddings", "semantic_search")
graph_builder.add_edge("semantic_search", "read_possible_files")
graph_builder.add_edge("read_possible_files", "find_exact_file")
graph_builder.add_edge("find_exact_file", "find_bug")
graph_builder.add_edge("find_bug", "generate_patch")
graph_builder.add_edge("generate_patch", "apply_patch")
graph_builder.add_edge("apply_patch", "run_test")
graph_builder.add_edge("run_test", "store_feedback")


def should_continue(state: AgentState):
    if state["retry_count"] >= MAX_RETRIES:
        return "fail"

    if state["test_passed"]:
        return "pass"

    return "retry"


graph_builder.add_conditional_edges(
    "store_feedback",
    should_continue,
    {
        "fail": "max_retry_failed",
        "pass": END,
        "retry": "find_bug",
    },
)

workflow = graph_builder.compile()
