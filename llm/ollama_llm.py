from langchain_ollama import ChatOllama


class OllamaLLM:

    def __init__(
        self,
        model: str = "qwen3:8b"
    ):
        self.llm = ChatOllama(
            model=model,
            temperature=0
        )

    def invoke(self, prompt: str) -> str:

        response = self.llm.invoke(prompt)

        return response.content