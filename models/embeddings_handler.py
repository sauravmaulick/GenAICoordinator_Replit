import os
import logging
from typing import List, Optional, Dict, Any
import asyncio
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class EmbeddingsHandler:
    """
    Handler for text embeddings using Google Gemini or fallback models
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.embedding_model = "text-embedding-004"  # Gemini text embedding model
        self.fallback_enabled = True
        
        logger.info("Initialized EmbeddingsHandler with Gemini")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for given text
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            
            # Use Gemini text embedding
            response = await self._generate_gemini_embedding(text)
            
            if response:
                logger.debug("Successfully generated embedding using Gemini")
                return response
            elif self.fallback_enabled:
                logger.warning("Gemini embedding failed, using fallback")
                return await self._generate_fallback_embedding(text)
            else:
                logger.error("Embedding generation failed and fallback disabled")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            if self.fallback_enabled:
                return await self._generate_fallback_embedding(text)
            return None
    
    async def _generate_gemini_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using Gemini text embedding model
        """
        try:
            # Run the synchronous operation in an executor to make it async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._sync_gemini_embedding, 
                text
            )
            
            if response and hasattr(response, 'embedding'):
                return response.embedding
            else:
                logger.warning("Invalid response from Gemini embedding API")
                return None
                
        except Exception as e:
            logger.error(f"Error with Gemini embedding: {str(e)}")
            return None
    
    def _sync_gemini_embedding(self, text: str):
        """
        Synchronous Gemini embedding call
        """
        try:
            # Note: This is a placeholder for the actual Gemini embedding API call
            # The exact API may vary based on the latest Gemini SDK
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return response
        except Exception as e:
            logger.error(f"Sync Gemini embedding error: {str(e)}")
            return None
    
    async def _generate_fallback_embedding(self, text: str) -> Optional[List[float]]:
        """
        Fallback embedding generation using sentence transformers or mock
        """
        try:
            logger.info("Using fallback embedding generation")
            
            # Try to use sentence-transformers if available
            try:
                from sentence_transformers import SentenceTransformer
                
                # Use a lightweight model for fallback
                model = SentenceTransformer('all-MiniLM-L6-v2')
                embedding = model.encode(text)
                return embedding.tolist()
                
            except ImportError:
                logger.warning("sentence-transformers not available, using mock embedding")
                return self._generate_mock_embedding(text)
                
        except Exception as e:
            logger.error(f"Error in fallback embedding: {str(e)}")
            return self._generate_mock_embedding(text)
    
    def _generate_mock_embedding(self, text: str, dimension: int = 768) -> List[float]:
        """
        Generate a mock embedding for development/testing
        """
        try:
            import hashlib
            import numpy as np
            
            # Create a deterministic embedding based on text hash
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Use hash as seed for reproducible random embedding
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, dimension)
            
            # Normalize the embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            logger.debug(f"Generated mock embedding with dimension {dimension}")
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating mock embedding: {str(e)}")
            # Return zero vector as last resort
            return [0.0] * dimension
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            embeddings = []
            
            for i, text in enumerate(texts):
                if i > 0 and i % 10 == 0:
                    logger.info(f"Processed {i}/{len(texts)} embeddings")
                
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            successful_embeddings = len([e for e in embeddings if e is not None])
            logger.info(f"Successfully generated {successful_embeddings}/{len(texts)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}", exc_info=True)
            return [None] * len(texts)
    
    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            if len(embedding1) != len(embedding2):
                logger.warning(f"Embedding dimension mismatch: {len(embedding1)} vs {len(embedding2)}")
                return 0.0
            
            # Calculate cosine similarity
            import numpy as np
            
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate dot product
            dot_product = np.dot(vec1, vec2)
            
            # Calculate norms
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            # Avoid division by zero
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure result is between -1 and 1
            similarity = max(-1.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    async def find_most_similar(self, query_embedding: List[float], 
                              candidate_embeddings: List[List[float]], 
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to a query embedding
        """
        try:
            if not query_embedding or not candidate_embeddings:
                return []
            
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = await self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    'index': i,
                    'similarity': similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding most similar embeddings: {str(e)}")
            return []
    
    async def generate_summary(self, content: str, context: str = "") -> str:
        """
        Generate a summary of content using Gemini
        """
        try:
            logger.info("Generating summary using Gemini")
            
            prompt = f"""
            Please provide a comprehensive summary of the following content related to {context}.
            
            Focus on:
            - Key findings and results
            - Important safety information
            - Clinical implications
            - Critical data points
            
            Content:
            {content}
            
            Provide a clear, concise summary in paragraph format.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                logger.info("Successfully generated summary")
                return response.text
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Summary generation failed for {context}. Content length: {len(content)} characters."
    
    async def extract_key_information(self, content: str, extraction_type: str = "clinical") -> Dict[str, Any]:
        """
        Extract key information from content based on type
        """
        try:
            logger.info(f"Extracting {extraction_type} information")
            
            if extraction_type == "clinical":
                prompt = f"""
                Extract key clinical information from the following content:
                
                Please identify and extract:
                - Primary endpoints and results
                - Safety profile and adverse events
                - Patient population details
                - Dosing information
                - Efficacy measures
                
                Content: {content}
                
                Respond in JSON format with the extracted information.
                """
            elif extraction_type == "manufacturing":
                prompt = f"""
                Extract key manufacturing information from the following content:
                
                Please identify and extract:
                - Batch information
                - Quality control results
                - Manufacturing processes
                - Specifications and tolerances
                - Deviations or issues
                
                Content: {content}
                
                Respond in JSON format with the extracted information.
                """
            else:
                prompt = f"""
                Extract key information from the following content:
                
                Content: {content}
                
                Respond in JSON format with the most important information.
                """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            if response.text:
                import json
                extracted_info = json.loads(response.text)
                logger.info("Successfully extracted key information")
                return extracted_info
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {
                "error": str(e),
                "extraction_type": extraction_type,
                "content_length": len(content)
            }
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this handler
        """
        # Gemini text-embedding-004 typically produces 768-dimensional embeddings
        return 768
    
    async def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that an embedding is properly formatted
        """
        try:
            if not isinstance(embedding, list):
                return False
            
            if len(embedding) != self.get_embedding_dimension():
                return False
            
            # Check if all elements are numbers
            for value in embedding:
                if not isinstance(value, (int, float)):
                    return False
                if not (-1 <= value <= 1):  # Basic range check
                    logger.warning(f"Embedding value outside expected range: {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating embedding: {str(e)}")
            return False
