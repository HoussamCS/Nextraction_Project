import logging
from typing import List, Dict, Tuple
import json
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    chromadb = None
    HAS_CHROMADB = False
try:
    import openai
except ImportError:
    openai = None
from src.utils.config import settings

logger = logging.getLogger(__name__)


class SimpleInMemoryVectorStore:
    """Fallback in-memory vector store when chromadb is unavailable"""
    def __init__(self, name):
        self.name = name
        self.embeddings = {}
        self.metadata = {}
        self.documents = {}
        self.count = 0
    
    def add(self, ids, embeddings, documents, metadatas):
        for id_, embedding, doc, meta in zip(ids, embeddings, documents, metadatas):
            self.embeddings[id_] = embedding
            self.documents[id_] = doc
            self.metadata[id_] = meta
            self.count += 1
    
    def query(self, query_embeddings, n_results=5):
        if not self.embeddings:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}
        
        # Simple cosine similarity search
        query_embedding = query_embeddings[0]
        scores = []
        for doc_id, doc_embedding in self.embeddings.items():
            score = self._cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:n_results]
        
        result_ids = [item[0] for item in top_results]
        result_docs = [self.documents.get(id_, "") for id_ in result_ids]
        result_metadata = [self.metadata.get(id_, {}) for id_ in result_ids]
        result_distances = [1 - item[1] for item in top_results]
        
        return {
            "ids": [result_ids],
            "distances": [result_distances],
            "documents": [result_docs],
            "metadatas": [result_metadata]
        }
    
    def _cosine_similarity(self, a, b):
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot_product / (norm_a * norm_b)


class EmbeddingsService:
    
    def __init__(self):
        self.embed_model = settings.openai_model
        self.collection = None
        self.use_memory_store = False
        self.collections = {}  # Dictionary to store multiple in-memory collections by name
        
        if not HAS_CHROMADB:
            logger.warning("chromadb not installed, using in-memory vector store (not persistent)")
            self.chroma_client = None
            self.use_memory_store = True
            return
        
        try:
            chroma_settings = ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.chroma_db_path,
                anonymized_telemetry=False
            )
            self.chroma_client = chromadb.Client(chroma_settings)
            logger.info(f"Chroma initialized at {settings.chroma_db_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize Chroma: {e}, falling back to in-memory store")
            self.chroma_client = None
            self.use_memory_store = True
    
    def get_or_create_collection(self, collection_name: str = "documents"):
        """Get or create a collection (Chroma or in-memory)."""
        logger.info(f"get_or_create_collection called with: {collection_name}")
        logger.info(f"use_memory_store: {self.use_memory_store}, available collections: {list(self.collections.keys()) if self.use_memory_store else 'N/A'}")
        
        if self.use_memory_store:
            # Check if collection already exists in memory
            if collection_name in self.collections:
                self.collection = self.collections[collection_name]
                logger.info(f"Retrieved existing in-memory collection: {collection_name} with {self.collection.count} chunks")
                return self.collection
            
            # Create new collection and store it
            logger.info(f"Creating NEW in-memory collection: {collection_name}")
            self.collection = SimpleInMemoryVectorStore(collection_name)
            self.collections[collection_name] = self.collection
            logger.info(f"Created in-memory collection: {collection_name}. Total collections now: {list(self.collections.keys())}")
            return self.collection
        
        if not self.chroma_client:
            logger.error("Chroma client not initialized and memory store not enabled")
            return None
        
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Using Chroma collection: {collection_name}")
            return self.collection
        except Exception as e:
            logger.error(f"Failed to create/get collection: {e}")
            # Fall back to in-memory
            self.use_memory_store = True
            self.collection = SimpleInMemoryVectorStore(collection_name)
            return self.collection
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        """
        if not openai:
            logger.error("OpenAI module not available")
            return None
        
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("Empty text provided for embedding")
                return None
            
            # Use the new OpenAI API
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            
            response = client.embeddings.create(
                input=text,
                model=self.embed_model
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for {len(text)} chars")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
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
        logger.info(f"[{job_id}] Starting to store {len(pages)} pages")
        
        # Always get or create the collection for this specific job
        collection_name = f"job_{job_id}"
        self.get_or_create_collection(collection_name)
        
        if not self.collection:
            error_msg = "Failed to create vector database collection"
            logger.error(f"[{job_id}] {error_msg}")
            return 0, [error_msg]
        
        logger.info(f"[{job_id}] Collection ready: {self.collection.name}")
        
        indexed_count = 0
        errors = []
        
        for page_idx, page in enumerate(pages):
            try:
                url = page.get("url", "unknown")
                title = page.get("title", "unknown")
                content = page.get("content", "")
                timestamp = page.get("timestamp", "")
                page_chunk_id = page.get("chunk_id", f"page_{page_idx}")
                
                logger.info(f"[{job_id}] Processing page {page_idx + 1}/{len(pages)}: {url}")
                
                if not content or len(content.strip()) == 0:
                    logger.warning(f"[{job_id}] Page {url} has empty content, skipping")
                    continue
                
                # Split into chunks
                chunks = self.chunk_document(content)
                logger.info(f"[{job_id}] Split page into {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    try:
                        logger.debug(f"[{job_id}] Generating embedding for chunk {i + 1}/{len(chunks)}")
                        
                        # Generate embedding
                        embedding = self.generate_embedding(chunk["text"])
                        if not embedding:
                            logger.warning(f"[{job_id}] Failed to generate embedding for chunk {i + 1}")
                            continue
                        
                        logger.debug(f"[{job_id}] Embedding generated (length: {len(embedding)})")
                        
                        # Create unique chunk ID
                        chunk_id = f"{page_chunk_id}_chunk_{i}"
                        
                        logger.debug(f"[{job_id}] Storing chunk {chunk_id}")
                        
                        # Store in vector database
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
                        logger.info(f"[{job_id}] Stored chunk {chunk_id} ({indexed_count} total)")
                        
                    except Exception as e:
                        error_msg = f"Failed to store chunk {i + 1} from {url}: {str(e)}"
                        logger.error(f"[{job_id}] {error_msg}", exc_info=True)
                        errors.append(error_msg)
            
            except Exception as e:
                error_msg = f"Failed to process page {page.get('url', 'unknown')}: {str(e)}"
                logger.error(f"[{job_id}] {error_msg}", exc_info=True)
                errors.append(error_msg)
        
        logger.info(f"[{job_id}] Completed storing chunks: {indexed_count} stored, {len(errors)} errors")
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
            logger.info(f"Searching collection with {self.collection.count if hasattr(self.collection, 'count') else '?'} chunks")
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            logger.info(f"Generated query embedding of length {len(query_embedding)}")
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            logger.info(f"Query returned: {results}")
            
            # Format results
            formatted = []
            if results and results.get("ids") and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
                for i, chunk_id in enumerate(results["ids"][0]):
                    score = results["distances"][0][i]
                    text = results["documents"][0][i] if i < len(results["documents"][0]) else ""
                    metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                    
                    formatted.append({
                        "chunk_id": chunk_id,
                        "text": text,
                        "score": score,
                        "metadata": metadata
                    })
                    logger.info(f"Added chunk {chunk_id} with score {score}")
            else:
                logger.warning(f"Query returned no results. Results structure: {results}")
            
            logger.info(f"Found {len(formatted)} relevant chunks")
            return formatted
        
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        if not self.chroma_client:
            logger.warning("Chroma not initialized, cannot delete collection")
            return False
        
        try:
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
