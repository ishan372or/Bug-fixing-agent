from llm.ollama_llm import OllamaLLM
from agent.state import AgentState


def generate_code(state:AgentState):
    bug_location = state["bug_location"]
    bug_report = state["bug_report"]
    llm = OllamaLLM()
    file_code = state["file_code"].file_content
    prompt = f"""
    You are an expert software engineer.

    Bug Report:
    {bug_report}

    File Path:
    {bug_location.file_path}

    Bug Location:
    Function: {bug_location.function_name}
    Lines: {bug_location.start_line} - {bug_location.end_line}

    Reason:
    {bug_location.reason}

    Source Code:

    {file_code}

    Your task:
    Generate a fix for the bug.

    Rules:
    1. Fix ONLY the identified bug.
    2. Preserve all existing functionality.
    3. Do not modify unrelated code.
    4. Return ONLY the replacement code for the buggy section.
    5. The replacement must be valid code.
    6. Do not return explanations.
    7. Do not return markdown.
    8. Do not return the entire file.

    Return only the replacement code that should replace lines
    {bug_location.start_line} to {bug_location.end_line}.
    """
    replacement_code = llm.invoke(prompt=prompt)
    
    return {
        "fixed_code" : replacement_code
    }