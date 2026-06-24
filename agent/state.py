from typing import TypedDict
from typing_extensions import Literal
from pydantic import BaseModel

class BugReport(BaseModel):
        bug_report : str
        bug_report_embedding : list[float]
        
class File_Code(BaseModel):
        file_path : str
        file_content : str

class RepoTreeNode(BaseModel):
        path : str
        type : str[Literal["file", "directory"]]
        
class BugLocation(BaseModel):
    file_path: str
    function_name: str
    start_line: int
    end_line: int
    reason: str

class AgentState(TypedDict):
    """Represents the state of an agent."""
    
    bug_report:BugReport
    repo_path:str
    repo_tree:List[RepoTreeNode]
    possible_file_paths:list[str]
    possible_files:List[Possible_file]
    file_path:str
    file_code : File_Code
    bug_location: BugLocation
    fixed_code:str
    possible_test_paths:list[str]
    test_path:str
    test_passed:bool
    test_output:str
    feedback:str
    
