from typing import List
import openai
from chromadb import Client
from chromadb.config import Settings

class EmbeddingsService:
    def __init__(self, openai_api_key: str, chroma_db_url: str):
        openai.api_key = openai_api_key
        self.chroma_client = Client(Settings(chroma_db_url=chroma_db_url))

    def generate_embedding(self, text: str) -> List[float]:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        return response['data'][0]['embedding']

    def store_embedding(self, embedding: List[float], metadata: dict):
        collection = self.chroma_client.get_or_create_collection("embeddings")
        collection.add(embeddings=[embedding], metadatas=[metadata])

    def get_embedding(self, text: str) -> List[float]:
        embedding = self.generate_embedding(text)
        metadata = {"text": text}
        self.store_embedding(embedding, metadata)
        return embedding