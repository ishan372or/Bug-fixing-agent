from agent.state import AgentState
from agent.state import RepoTreeNode
from pathlib import Path

def get_repo_tree(state: AgentState):
    """Returns the repository tree as a list of RepoTreeNode objects."""
    repo_path = Path(state["repo_path"])

    repo_tree = []

    for path in repo_path.rglob("*"):
        repo_tree.append(RepoTreeNode(path=str(path.relative_to(repo_path)),type="directory" if path.is_dir() else "file"))

    return {
        "repo_tree": repo_tree
    }
    

        
