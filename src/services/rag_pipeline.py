import logging
from typing import List, Dict, Optional
try:
    import openai
except ImportError:
    openai = None
from src.services.web_scraper import WebScraper
from src.services.embeddings import EmbeddingsService
from src.services.job_queue import job_queue, JobState
from src.utils.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    
    def __init__(self):
        self.chat_model = settings.openai_chat_model
        self.embeddings_service = EmbeddingsService()
        self.scraper = None
    
    def ingest(self, job_id: str, seed_urls: List[str], domain_allowlist: List[str],
               max_pages: int, max_depth: int) -> bool:
        """
        Ingest pipeline: crawl, clean, chunk, embed, store.
        Runs in background (async context).
        """
        try:
            # Mark job as running
            job_queue.set_running(job_id)
            
            # Initialize scraper
            self.scraper = WebScraper(domain_allowlist, max_pages, max_depth)
            logger.info(f"[Job {job_id}] Starting ingestion: {len(seed_urls)} seed URLs")
            
            # 1. Fetch pages
            pages_data = self.scraper.crawl(seed_urls)
            pages_fetched = len(pages_data)
            logger.info(f"[Job {job_id}] Fetched {pages_fetched} pages")
            job_queue.update_progress(job_id, pages_fetched, 0)
            
            # Add any scraper errors to job
            for error in self.scraper.errors:
                job_queue.add_error(job_id, error)
            
            if pages_fetched == 0:
                logger.warning(f"[Job {job_id}] No pages fetched!")
                job_queue.set_done(job_id, {"pages_indexed": 0})
                return True
            
            # 2. Index in vector store
            pages_indexed, indexing_errors = self.embeddings_service.store_chunks(job_id, pages_data)
            logger.info(f"[Job {job_id}] Indexed {pages_indexed} chunks")
            job_queue.update_progress(job_id, pages_fetched, pages_indexed)
            
            # Add indexing errors
            for error in indexing_errors:
                job_queue.add_error(job_id, error)
            
            # Mark job as complete
            job_queue.set_done(job_id, {
                "pages_fetched": pages_fetched,
                "pages_indexed": pages_indexed,
                "collection_name": f"job_{job_id}"
            })
            
            logger.info(f"[Job {job_id}] Ingestion complete!")
            return True
        
        except Exception as e:
            error_msg = f"Ingestion failed: {str(e)}"
            logger.error(f"[Job {job_id}] {error_msg}")
            job_queue.set_failed(job_id, error_msg)
            return False
    
    def answer(self, job_id: str, question: str) -> Dict:
        """
        Generate grounded answer with citations.
        
        Returns dict with:
        - answer: The grounded answer
        - citations: List of citations (url, title, chunk_id, quote, score)
        - confidence: high/medium/low
        - grounding_notes: Explanation of grounding
        """
        try:
            logger.info(f"[Job {job_id}] Answering: {question}")
            
            # Get job to verify it's done
            job = job_queue.get_job(job_id)
            if not job or job.state != JobState.DONE:
                return {
                    "answer": "Job not found or still processing",
                    "citations": [],
                    "confidence": "low",
                    "grounding_notes": "No valid job state"
                }
            
            # Load or create collection for this job
            collection_name = f"job_{job_id}"
            try:
                collection = self.embeddings_service.get_or_create_collection(collection_name)
                logger.info(f"[Job {job_id}] Collection retrieved/created with name: {collection_name}")
                if collection:
                    logger.info(f"[Job {job_id}] Collection has {collection.count if hasattr(collection, 'count') else '?'} chunks")
            except Exception as e:
                logger.error(f"[Job {job_id}] Failed to get collection: {e}")
                return {
                    "answer": "Could not retrieve indexed content. Job data may not exist or be corrupted.",
                    "citations": [],
                    "confidence": "low",
                    "grounding_notes": f"Collection access error: {str(e)}"
                }
            
            # Check collection has data
            if not self.embeddings_service.collection or (hasattr(self.embeddings_service.collection, 'count') and self.embeddings_service.collection.count == 0):
                logger.warning(f"[Job {job_id}] Collection is empty. Available collections: {list(self.embeddings_service.collections.keys())}")
                return {
                    "answer": "No indexed content found for this job. Please ingest content first.",
                    "citations": [],
                    "confidence": "low",
                    "grounding_notes": "Knowledge base is empty"
                }
            
            # 1. Retrieve relevant chunks
            retrieved_chunks = self.embeddings_service.search(
                question,
                top_k=settings.top_k_chunks
            )
            
            if not retrieved_chunks:
                logger.warning(f"[Job {job_id}] No relevant chunks found")
                return {
                    "answer": "I could not find sufficient information to answer this question.",
                    "citations": [],
                    "confidence": "low",
                    "grounding_notes": "No relevant chunks retrieved from the knowledge base."
                }
            
            # 2. Generate answer with retrieved context
            answer = self._generate_grounded_answer(question, retrieved_chunks)
            
            # 3. Extract and validate citations
            citations = self._extract_citations(retrieved_chunks, answer)
            
            # 4. Estimate confidence
            confidence = self._estimate_confidence(retrieved_chunks, answer, citations)
            
            # 5. Generate grounding notes
            grounding_notes = self._generate_grounding_notes(retrieved_chunks, answer, confidence)
            
            logger.info(f"[Job {job_id}] Answer generated with {len(citations)} citations")
            
            return {
                "answer": answer,
                "citations": citations,
                "confidence": confidence,
                "grounding_notes": grounding_notes
            }
        
        except Exception as e:
            logger.error(f"[Job {job_id}] Answer generation failed: {e}")
            return {
                "answer": "An error occurred while generating the answer.",
                "citations": [],
                "confidence": "low",
                "grounding_notes": f"Error: {str(e)}"
            }
    
    def _generate_grounded_answer(self, question: str, chunks: List[Dict]) -> str:
        """
        Generate answer grounded in retrieved chunks.
        Uses system prompt to enforce factuality and citation.
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Chunk {i}] {chunk['text'][:500]}...")
        context = "\n\n".join(context_parts)
        
        system_prompt = """You are an evidence-based research assistant. You must:
1. Answer ONLY based on the provided evidence/chunks
2. Be factually accurate and never fabricate information
3. If evidence is insufficient, explicitly say so
4. Keep your answer concise but comprehensive
5. Reference chunk numbers where you draw facts from: e.g., "According to [Chunk 0]..."
6. If asked about something not in the evidence, refuse to answer"""
        
        user_message = f"""Evidence/Context:
{context}

Question: {question}

Answer based ONLY on the evidence provided. Reference chunk numbers for each fact."""
        
        try:
            from openai import OpenAI
            from src.utils.config import settings
            
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,  # Lower temp for more factual consistency
                max_tokens=500
            )
            answer = response.choices[0].message.content
            logger.debug(f"Generated answer: {answer[:100]}...")
            return answer
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    def _extract_citations(self, retrieved_chunks: List[Dict], answer: str) -> List[Dict]:
        """
        Extract citations from retrieved chunks.
        Include URL, title, chunk_id, short quote, and similarity score.
        """
        citations = []
        
        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {})
            url = metadata.get("url", "Unknown")
            title = metadata.get("title", "Unknown")
            chunk_id = chunk.get("chunk_id", "Unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0.0)
            
            # Extract short quote (~25 words max)
            quote = text[:150].strip()
            if len(text) > 150:
                quote += "..."
            
            # Convert distance to similarity score (Chroma returns distances)
            # For cosine distance, similarity = 1 - distance
            similarity_score = max(0, 1 - score) if score is not None else 0.0
            
            citations.append({
                "url": url,
                "title": title,
                "chunk_id": chunk_id,
                "quote": quote,
                "score": round(similarity_score, 3)
            })
        
        logger.debug(f"Extracted {len(citations)} citations")
        return citations
    
    def _estimate_confidence(self, chunks: List[Dict], answer: str, citations: List[Dict]) -> str:
        """
        Estimate confidence based on:
        - Number of supporting chunks
        - Relevance scores
        - Answer refusal signals
        """
        if not chunks or not citations:
            return "low"
        
        # Average similarity score
        avg_score = sum(c.get("score", 0) for c in citations) / len(citations) if citations else 0
        
        # Check for refusal signals in answer
        refusal_phrases = [
            "cannot find",
            "insufficient",
            "not mentioned",
            "no evidence",
            "cannot answer",
            "unclear",
            "not available"
        ]
        has_refusal = any(phrase.lower() in answer.lower() for phrase in refusal_phrases)
        
        if has_refusal or avg_score < 0.4:
            return "low"
        elif avg_score < 0.6 or len(chunks) == 1:
            return "medium"
        else:
            return "high"
    
    def _generate_grounding_notes(self, chunks: List[Dict], answer: str, confidence: str) -> str:
        """Generate human-readable notes about grounding."""
        num_chunks = len(chunks)
        avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks) if chunks else 0
        
        if confidence == "high":
            return f"Answer supported by {num_chunks} relevant sources with high confidence (avg similarity: {avg_score:.2f})"
        elif confidence == "medium":
            return f"Answer partially supported by {num_chunks} sources (avg similarity: {avg_score:.2f}). Some details may require additional verification."
        else:
            return f"Limited evidence found. Answer based on {num_chunks} chunks (avg similarity: {avg_score:.2f}). Additional sources recommended."
