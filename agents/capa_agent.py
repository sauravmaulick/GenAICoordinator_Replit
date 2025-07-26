import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from mcp_modules.mcp_capa import MCPCapaModule

logger = logging.getLogger(__name__)

class CapaAgent:
    """
    Agent responsible for reading and analyzing CAPA (Corrective and Preventive Action) data
    from text files using FastMCP architecture
    """
    
    def __init__(self):
        self.mcp_module = MCPCapaModule()
        self.data_file = "data/capa_data.txt"
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process CAPA-related queries by analyzing the CAPA data file
        """
        logger.info(f"\n\nProcessing CAPA query: {query}")
        
        try:
            # Use MCP module to read and parse CAPA data
            capa_data = await self.mcp_module.read_capa_data(self.data_file)
            
            if not capa_data:
                return {
                    "success": False,
                    "error": "No CAPA data found or file not accessible",
                    "count": 0,
                    "details": []
                }
            
            # Filter for open CAPAs in the last year
            one_year_ago = datetime.now() - timedelta(days=365)
            open_capas = []
            
            for capa in capa_data:
                # Check if CAPA is open and within the last year
                if (capa.get('status', '').upper() == 'OPEN' and 
                    self._is_within_timeframe(capa.get('date'), one_year_ago)):
                    open_capas.append(capa)
            
            result = {
                "success": True,
                "count": len(open_capas),
                "details": open_capas,
                "query_processed": query,
                "analysis_date": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed CAPA query. Found {len(open_capas)} open CAPAs")
            return result
            
        except Exception as e:
            logger.error(f"Error processing CAPA query: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "details": []
            }
    
    def _is_within_timeframe(self, date_str: str, cutoff_date: datetime) -> bool:
        """
        Check if a date string is within the specified timeframe
        """
        try:
            if not date_str:
                return False
            
            # Try different date formats
            date_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y", 
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S"
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    return parsed_date >= cutoff_date
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return False
            
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
            return False
    
    async def get_capa_by_id(self, capa_id: str) -> Dict[str, Any]:
        """
        Retrieve specific CAPA by ID
        """
        logger.info(f"Retrieving CAPA by ID: {capa_id}")
        
        try:
            capa_data = await self.mcp_module.read_capa_data(self.data_file)
            
            for capa in capa_data:
                if capa.get('capa_id') == capa_id:
                    return {
                        "success": True,
                        "capa": capa
                    }
            
            return {
                "success": False,
                "error": f"CAPA with ID {capa_id} not found"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving CAPA {capa_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_capa_statistics(self) -> Dict[str, Any]:
        """
        Get overall CAPA statistics
        """
        logger.info("Generating CAPA statistics")
        
        try:
            capa_data = await self.mcp_module.read_capa_data(self.data_file)
            
            if not capa_data:
                return {
                    "success": False,
                    "error": "No CAPA data available"
                }
            
            stats = {
                "total_capas": len(capa_data),
                "open_capas": 0,
                "closed_capas": 0,
                "in_progress_capas": 0,
                "regions": {},
                "last_updated": datetime.now().isoformat()
            }
            
            for capa in capa_data:
                status = capa.get('status', '').upper()
                region = capa.get('region', 'Unknown')
                
                if status == 'OPEN':
                    stats["open_capas"] += 1
                elif status == 'CLOSED':
                    stats["closed_capas"] += 1
                elif status in ['IN_PROGRESS', 'IN PROGRESS']:
                    stats["in_progress_capas"] += 1
                
                stats["regions"][region] = stats["regions"].get(region, 0) + 1
            
            return {
                "success": True,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Error generating CAPA statistics: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_capas(self, criteria: Dict[str, str]) -> Dict[str, Any]:
        """
        Search CAPAs based on various criteria
        """
        logger.info(f"Searching CAPAs with criteria: {criteria}")
        
        try:
            capa_data = await self.mcp_module.read_capa_data(self.data_file)
            matching_capas = []
            
            for capa in capa_data:
                matches = True
                
                for key, value in criteria.items():
                    if key in capa:
                        if value.lower() not in str(capa[key]).lower():
                            matches = False
                            break
                    else:
                        matches = False
                        break
                
                if matches:
                    matching_capas.append(capa)
            
            return {
                "success": True,
                "count": len(matching_capas),
                "capas": matching_capas,
                "criteria": criteria
            }
            
        except Exception as e:
            logger.error(f"Error searching CAPAs: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "capas": []
            }
