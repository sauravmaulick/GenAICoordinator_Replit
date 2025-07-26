import os
import logging
from typing import Dict, Any, List, Optional
from mcp_modules.mcp_neo4j import MCPNeo4jModule

logger = logging.getLogger(__name__)

class Neo4jAgent:
    """
    Agent responsible for querying Neo4j graph database for investigation details,
    brand information, and related data using FastMCP architecture
    """
    
    def __init__(self):
        self.mcp_module = MCPNeo4jModule()
    
    async def get_investigations(self, brand_name: str, capa_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve investigation details for a specific brand, optionally filtered by CAPA IDs
        """
        logger.info(f"Retrieving investigations for brand: {brand_name}, CAPA IDs: {capa_ids}")
        
        try:
            # Use MCP module to query Neo4j
            investigations = await self.mcp_module.query_investigations(brand_name, capa_ids)
            
            if not investigations:
                logger.info(f"No investigations found for brand {brand_name}")
                return {
                    "success": True,
                    "investigations": [],
                    "count": 0,
                    "brand": brand_name,
                    "capa_ids": capa_ids or []
                }
            
            # Enrich investigation data
            enriched_investigations = []
            for inv in investigations:
                enriched_inv = await self._enrich_investigation_data(inv)
                enriched_investigations.append(enriched_inv)
            
            result = {
                "success": True,
                "investigations": enriched_investigations,
                "count": len(enriched_investigations),
                "brand": brand_name,
                "capa_ids": capa_ids or [],
                "query_timestamp": self._get_timestamp()
            }
            
            logger.info(f"Successfully retrieved {len(enriched_investigations)} investigations for {brand_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving investigations: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "investigations": [],
                "count": 0,
                "brand": brand_name,
                "capa_ids": capa_ids or []
            }
    
    async def _enrich_investigation_data(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich investigation data with additional related information
        """
        try:
            # Get related CAPAs
            capa_id = investigation.get('capa_id')
            if capa_id:
                capa_details = await self.mcp_module.get_capa_details(capa_id)
                investigation['capa_details'] = capa_details
            
            # Get batch information
            batch_number = investigation.get('batch_number')
            if batch_number:
                batch_info = await self.mcp_module.get_batch_info(batch_number)
                investigation['batch_info'] = batch_info
            
            # Validate PDF link
            pdf_link = investigation.get('pdf_link')
            if pdf_link:
                investigation['pdf_accessible'] = await self._validate_pdf_link(pdf_link)
            
            return investigation
            
        except Exception as e:
            logger.error(f"Error enriching investigation data: {str(e)}")
            return investigation
    
    async def _validate_pdf_link(self, pdf_link: str) -> bool:
        """
        Validate if PDF link is accessible (mock implementation)
        """
        try:
            # In a real implementation, this would check if the PDF is accessible
            # For now, we'll just check if it's a valid URL format
            return pdf_link.startswith(('http://', 'https://')) and pdf_link.endswith('.pdf')
        except Exception:
            return False
    
    async def get_brand_summary(self, brand_name: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a brand
        """
        logger.info(f"Getting brand summary for: {brand_name}")
        
        try:
            summary = await self.mcp_module.get_brand_summary(brand_name)
            
            return {
                "success": True,
                "brand": brand_name,
                "summary": summary,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting brand summary: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "brand": brand_name
            }
    
    async def get_related_entities(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """
        Get entities related to a specific entity (CAPA, Investigation, etc.)
        """
        logger.info(f"Getting related entities for {entity_type}: {entity_id}")
        
        try:
            related = await self.mcp_module.get_related_entities(entity_id, entity_type)
            
            return {
                "success": True,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "related_entities": related,
                "count": len(related) if related else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting related entities: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "entity_id": entity_id,
                "entity_type": entity_type
            }
    
    async def execute_custom_query(self, cypher_query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a custom Cypher query
        """
        logger.info(f"Executing custom Cypher query")
        
        try:
            results = await self.mcp_module.execute_cypher(cypher_query, parameters or {})
            
            return {
                "success": True,
                "results": results,
                "query": cypher_query,
                "parameters": parameters or {}
            }
            
        except Exception as e:
            logger.error(f"Error executing custom query: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": cypher_query,
                "parameters": parameters or {}
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def get_investigation_count_by_brand(self, brand_name: str) -> Dict[str, Any]:
        """
        Get count of investigations for a specific brand
        """
        logger.info(f"Getting investigation count for brand: {brand_name}")
        
        try:
            count = await self.mcp_module.count_investigations_by_brand(brand_name)
            
            return {
                "success": True,
                "brand": brand_name,
                "investigation_count": count,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting investigation count: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "brand": brand_name,
                "investigation_count": 0
            }
