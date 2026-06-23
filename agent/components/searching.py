from agent.state import AgentState,RepoTreeNode,Possible_file
from pathlib import Path
from llm.ollama_llm import OllamaEmbedLLM,OllamaLLM
import faiss
import pickle
import numpy as np
from pathlib import Path

def read_file(state:AgentState):
    file_path=state["file_path"]
    with open(file_path,"r") as file:
        file_content=file.read()
    
    return {
        "file_code" : Possible_file(
            file_path=file_path,
            file_content=file_content
        )
    }  

def generate_bug_report_embeddings(state:AgentState):
    llm = OllamaEmbedLLM()
    bug_report=state["bug_report"]
    return {
        "bug_report": BugReport(
            bug_report=bug_report.bug_report,
            bug_report_embedding=llm.embed(
                bug_report.bug_report
            )
        )
    }

def semantic_search(state: AgentState):
    index=faiss.index("repo.index")
    with open("metadata.pkl", "rb") as f:
        metadata = pickle.load(f)

    query_embedding = np.array(
        [state["bug_report"].bug_report_embedding],
        dtype=np.float32
    )
    
    total_files=len(state["repo_tree"])

    distances, indices = index.search(
        query_embedding,
        k=total_files/10
    )

    possible_file_paths = []

    for idx in indices[0]:

        if idx == -1:
            continue

        possible_file_paths.append(
            metadata[idx]["file_path"]
        )

    return {
        "possible_file_paths": possible_file_paths
    }
    
def read_possible_files(state:AgentState):
    possible_file_paths=state["possible_file_paths"]
    repo_tree=state["repo_tree"]
    possible_files=[]
    for path in possible_file_paths:
        try:
            code=Path(path).read_text(
                encoding="utf-8",
                errors="ignore"
            )
            possible_files.append(Possible_file(file_path=path,file_content=code))
        except Exception:
            continue
        
    return {
        "Possible_files" : possible_files
    }

def find_exact_file(state:AgentState):
    possible_files=state["possible_files"]
    llm=OllamaLLM()
    final_path=llm.invoke(prompt = f"""
        You are an expert software debugging assistant.

        Bug Report:
        {state["bug_report"].bug_report}

        Candidate Files:

        {possible_files}

        Task:
        Analyze the bug report and the provided source code.

        Determine the SINGLE file most likely responsible for the bug.

        Return ONLY the file path.

        Example output:
        src/auth/login.py

        Do not provide explanations.
        Do not provide markdown.
        Do not return multiple files.
        Return exactly one file path.
        """)
    
    return {
        "file_path" : final_path
    }
    

def get_repo_tree(state: AgentState):
    """Returns the repository tree as a list of RepoTreeNode objects."""
    repo_path = Path(state["repo_path"])

    repo_tree = []

    for path in repo_path.rglob("*"):
        repo_tree.append(RepoTreeNode(path=str(path.relative_to(repo_path)),type="directory" if path.is_dir() else "file"))

    return {
        "repo_tree": repo_tree
    }
    

        
