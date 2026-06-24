from agent.state import AgentState
import subprocess

def run_test(state:AgentState):
    repo_path = state["repo_path"]
    
    result = subprocess.run(
        ["pytest"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    return {
        "test_passed": result.returncode == 0,
        "test_output": result.stdout + result.stderr
    }