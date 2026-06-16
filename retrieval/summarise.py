from llm.ollama_llm import OllamaLLM
from retrieval.state import IndexingState,SummaryNode

def generate_summaries(state:IndexingState):
    llm=OllamaLLM()
    files=state["files"]
    
    summaries=[]
    
    for file in files:
            prompt = f"""
            You are analyzing a source code file.

            File Path:
            {file.file_path}

            Imports:
            {file.imports}

            Functions:
            {file.functions}

            Classes:
            {file.classes}

            Module Docstring:
            {file.module_docstring}

            Decorators:
            {file.decorators}

            Exception Types:
            {file.exception_types}

            API Routes:
            {file.api_routes}

            Database Models:
            {file.database_models}

            Database Queries:
            {file.database_queries}

            External Dependencies:
            {file.external_dependencies}

            File Size:
            {file.file_size}

            Line Count:
            {file.line_count}

            Generate a concise 2-3 sentence summary describing:
            1. The purpose of this file.
            2. What subsystem it belongs to.
            3. What responsibilities it likely has.

            Return only the summary.
            """
            summary=llm.invoke(prompt)
            summaries.append(SummaryNode(file_path=file.file_path,summary=summary))
    
    return {
        "summaries" : summaries
    }
        