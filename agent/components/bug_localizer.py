from agent.components.state import AgentState,BugLocation
from llm.ollama_llm import OllamaLLM
import json

def find_bug(state:AgentState):
    file_code=state["file_code"].file_content
    bug_report=state["bug_report"]
    llm=OllamaLLM()
    prompt = f"""
    You are an expert software debugging assistant.

    Bug Report:
    {bug_report}

    File Path:
    {file_path}

    Source Code:

    {file_code}

    Your task:
    1. Analyze the bug report.
    2. Identify the most likely location of the bug.
    3. Determine the function containing the bug.
    4. Determine the approximate start and end line numbers.
    5. Explain why the bug occurs.

    Return ONLY valid JSON.

    Format:

    {{
        "function_name": "<function_name>",
        "start_line": <line_number>,
        "end_line": <line_number>,
        "reason": "<short explanation>"
    }}

    Rules:
    - Return exactly one function.
    - Use line numbers relative to the provided source file.
    - Do not return markdown.
    - Do not return explanations outside the JSON.
    """
    content=llm.invoke(prompt=prompt)
    response=json.loads(content)
    
    return {
        "bug_location": BugLocation(
            file_path=state["file_path"],
            function_name=result["function_name"],
            start_line=result["start_line"],
            end_line=result["end_line"],
            reason=result["reason"]
        )
    }
    