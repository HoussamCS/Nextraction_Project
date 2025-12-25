import logging
from typing import List, Dict, Tuple
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None
try:
    import openai
except ImportError:
    openai = None
from src.utils.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    
    def __init__(self):
        self.embed_model = settings.openai_model
        
        if chromadb:
            chroma_settings = ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.chroma_db_path,
                anonymized_telemetry=False
            )
            self.chroma_client = chromadb.Client(chroma_settings)
        else:
            self.chroma_client = None
        self.collection = None
    
    def get_or_create_collection(self, collection_name: str = "documents"):
        """Get or create a Chroma collection."""
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Using collection: {collection_name}")
            return self.collection
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        """
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("Empty text provided for embedding")
                return None
            
            response = openai.Embedding.create(
                input=text,
                model=self.embed_model
            )
            embedding = response['data'][0]['embedding']
            logger.debug(f"Generated embedding for {len(text)} chars")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """
        Split document content into overlapping chunks.
        Returns list of chunk dicts with metadata.
        """
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_text = content[start:end]
            
            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": end
            })
            
            start = end - overlap if end < len(content) else end
        
        logger.info(f"Split document into {len(chunks)} chunks")
        return chunks
    
    def store_chunks(self, job_id: str, pages: List[Dict]) -> Tuple[int, List[str]]:
        """
        Generate embeddings for document chunks and store in Chroma.
        
        Args:
            job_id: Job identifier for tracking
            pages: List of page dicts with url, title, content, timestamp, chunk_id
        
        Returns:
            (indexed_count, errors)
        """
        if not self.collection:
            self.get_or_create_collection(f"job_{job_id}")
        
        indexed_count = 0
        errors = []
        
        for page in pages:
            try:
                url = page.get("url")
                title = page.get("title")
                content = page.get("content")
                timestamp = page.get("timestamp")
                page_chunk_id = page.get("chunk_id")
                
                # Split into chunks
                chunks = self.chunk_document(content)
                
                for i, chunk in enumerate(chunks):
                    try:
                        # Generate embedding
                        embedding = self.generate_embedding(chunk["text"])
                        if not embedding:
                            continue
                        
                        # Create unique chunk ID
                        chunk_id = f"{page_chunk_id}_chunk_{i}"
                        
                        # Store in Chroma
                        self.collection.add(
                            ids=[chunk_id],
                            embeddings=[embedding],
                            documents=[chunk["text"]],
                            metadatas=[{
                                "url": url,
                                "title": title,
                                "timestamp": timestamp,
                                "page_chunk_id": page_chunk_id,
                                "chunk_idx": i
                            }]
                        )
                        
                        indexed_count += 1
                        logger.info(f"Stored chunk {chunk_id} from {url}")
                        
                    except Exception as e:
                        error_msg = f"Failed to index chunk from {url}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
            
            except Exception as e:
                error_msg = f"Failed to process page {page.get('url')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Indexed {indexed_count} chunks with {len(errors)} errors")
        return indexed_count, errors
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant chunks using semantic similarity.
        
        Returns:
            List of dicts with text, score, and metadata (url, title, etc.)
        """
        if not self.collection:
            logger.warning("No collection available for search")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            formatted = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, chunk_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "chunk_id": chunk_id,
                        "text": results["documents"][0][i],
                        "score": results["distances"][0][i],  # Chroma returns distances, not scores
                        "metadata": results["metadatas"][0][i]
                    })
            
            logger.info(f"Found {len(formatted)} relevant chunks")
            return formatted
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
