from typing import TypedDict

class AgentState(TypedDict):
    """Represents the state of an agent."""
    
    bug_report:str
    repo_path:str
    possible_file_paths:list[str]
    file_path:str
    fixed_code:str
    possible_test_paths:list[str]
    test_path:str
    test_passed:bool
    test_output:str
    feedback:str