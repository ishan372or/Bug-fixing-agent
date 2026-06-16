from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings


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

class OllamaEmbedLLM:

    def __init__(
        self,
        model: str = "nomic-embed-text"
    ):
        self.embedding_model = OllamaEmbeddings(
            model=model
        )

    def embed(self, text: str):

        return self.embedding_model.embed_query(text)