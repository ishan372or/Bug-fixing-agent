from typing import TypedDict
from typing_extensions import Literal
from pydantic import BaseModel

class RepoTreeNode(BaseModel):
        path : str
        type : str[Literal["file", "directory"]]

class AgentState(TypedDict):
    """Represents the state of an agent."""
    
    bug_report:str
    repo_path:str
    repo_tree:List[RepoTreeNode]
    possible_file_paths:list[str]
    file_path:str
    fixed_code:str
    possible_test_paths:list[str]
    test_path:str
    test_passed:bool
    test_output:str
    feedback:str
    
