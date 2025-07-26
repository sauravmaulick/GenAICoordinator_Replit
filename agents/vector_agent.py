import os
import logging
from typing import Dict, Any, List, Optional
from mcp_modules.mcp_vector import MCPVectorModule
from models.embeddings_handler import EmbeddingsHandler

logger = logging.getLogger(__name__)

class VectorAgent:
    """
    Agent responsible for vector database operations, including searching
    clinical trial summaries and embedded document content using FastMCP architecture
    """
    
    def __init__(self):
        self.mcp_module = MCPVectorModule()
        self.embeddings_handler = EmbeddingsHandler()
    
    async def search_clinical_trials(self, brand_name: str, pdf_links: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for clinical trial summaries for a specific brand
        """
        logger.info(f"Searching clinical trials for brand: {brand_name}")
        
        try:
            # Create search query
            search_query = f"clinical trial summary for brand {brand_name}"
            
            # Generate embeddings for the search query
            query_embedding = await self.embeddings_handler.generate_embedding(search_query)
            
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # Search vector database
            search_results = await self.mcp_module.vector_search(
                query_embedding=query_embedding,
                filter_criteria={"brand": brand_name},
                top_k=5
            )
            
            if not search_results:
                logger.info(f"No clinical trial data found for brand {brand_name}")
                return {
                    "success": True,
                    "summary": "",
                    "brand": brand_name,
                    "pdf_links": pdf_links or [],
                    "documents_found": 0
                }
            
            # Process and summarize results
            summary = await self._generate_summary(search_results, brand_name)
            
            result = {
                "success": True,
                "summary": summary,
                "brand": brand_name,
                "pdf_links": pdf_links or [],
                "documents_found": len(search_results),
                "search_results": search_results,
                "query": search_query
            }
            
            logger.info(f"Successfully found {len(search_results)} clinical trial documents for {brand_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching clinical trials: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "summary": "",
                "brand": brand_name,
                "pdf_links": pdf_links or [],
                "documents_found": 0
            }
    
    async def _generate_summary(self, search_results: List[Dict[str, Any]], brand_name: str) -> str:
        """
        Generate a comprehensive summary from search results
        """
        try:
            # Extract relevant content from search results
            content_pieces = []
            
            for result in search_results:
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                score = result.get('score', 0)
                
                # Only include high-confidence results
                if score > 0.7:
                    content_pieces.append({
                        'content': content,
                        'source': metadata.get('source', 'Unknown'),
                        'page': metadata.get('page', 'N/A'),
                        'score': score
                    })
            
            if not content_pieces:
                return f"No high-confidence clinical trial data found for brand {brand_name}."
            
            # Use embeddings handler to generate summary
            combined_content = "\n\n".join([piece['content'] for piece in content_pieces])
            summary = await self.embeddings_handler.generate_summary(combined_content, brand_name)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating clinical trial summary for {brand_name}: {str(e)}"
    
    async def search_by_pdf_links(self, pdf_links: List[str], query: str) -> Dict[str, Any]:
        """
        Search for content specifically from provided PDF links
        """
        logger.info(f"Searching content from {len(pdf_links)} PDF links")
        
        try:
            # Generate query embedding
            query_embedding = await self.embeddings_handler.generate_embedding(query)
            
            results = []
            for pdf_link in pdf_links:
                # Search within specific PDF
                pdf_results = await self.mcp_module.search_by_source(
                    query_embedding=query_embedding,
                    source_filter=pdf_link,
                    top_k=3
                )
                
                if pdf_results:
                    results.extend(pdf_results)
            
            return {
                "success": True,
                "results": results,
                "pdf_links": pdf_links,
                "query": query,
                "documents_searched": len(pdf_links)
            }
            
        except Exception as e:
            logger.error(f"Error searching PDF links: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "pdf_links": pdf_links,
                "query": query
            }
    
    async def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform semantic search across the vector database
        """
        logger.info(f"Performing semantic search: {query}")
        
        try:
            # Generate query embedding
            query_embedding = await self.embeddings_handler.generate_embedding(query)
            
            # Perform vector search
            results = await self.mcp_module.vector_search(
                query_embedding=query_embedding,
                filter_criteria=filters or {},
                top_k=10
            )
            
            return {
                "success": True,
                "results": results,
                "query": query,
                "filters": filters or {},
                "documents_found": len(results) if results else 0
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "query": query,
                "filters": filters or {}
            }
    
    async def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific document by its ID
        """
        logger.info(f"Retrieving document by ID: {document_id}")
        
        try:
            document = await self.mcp_module.get_document(document_id)
            
            return {
                "success": True,
                "document": document,
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "document": None,
                "document_id": document_id
            }
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new document to the vector database
        """
        logger.info("Adding new document to vector database")
        
        try:
            # Generate embedding for the content
            embedding = await self.embeddings_handler.generate_embedding(content)
            
            if not embedding:
                raise ValueError("Failed to generate embedding for document")
            
            # Add to vector database
            document_id = await self.mcp_module.add_document(
                content=content,
                embedding=embedding,
                metadata=metadata
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "document_id": None
            }
    
    async def get_similar_documents(self, document_id: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Find documents similar to a given document
        """
        logger.info(f"Finding similar documents to: {document_id}")
        
        try:
            similar_docs = await self.mcp_module.find_similar_documents(document_id, top_k)
            
            return {
                "success": True,
                "similar_documents": similar_docs,
                "reference_document_id": document_id,
                "count": len(similar_docs) if similar_docs else 0
            }
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "similar_documents": [],
                "reference_document_id": document_id,
                "count": 0
            }
