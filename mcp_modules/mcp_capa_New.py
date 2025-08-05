# app/mcp/mcp_capa.py
import os
import logging
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
import asyncio

logger = logging.getLogger(__name__)

class MCPCapaModule:
    """FastMCP module for PostgreSQL CAPA data operations."""
    
    def __init__(self):
        self.module_name = "mcp_capa"
        self.db_config = {
            'dbname': os.getenv('CAPA_DB_NAME', 'CAPA_DB'),
            'user': os.getenv('CAPA_DB_USER', 'postgres'),
            'password': os.getenv('CAPA_DB_PASSWORD', 'Kolkata@2025'),
            'host': os.getenv('CAPA_DB_HOST', 'localhost'),
            'port': os.getenv('CAPA_DB_PORT', '5432')
        }
        self.connection = None
        self.connected = False
        logger.info(f"Initialized {self.module_name} module")
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        logger.info("Connecting to PostgreSQL CAPA database")
        try:
            self.connection = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            self.connected = True
            logger.info("Successfully connected to PostgreSQL CAPA database")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}", exc_info=True)
            self.connected = False
            return False
    
    async def read_capa_data(self, query: str = None) -> List[Dict[str, Any]]:
        """Read CAPA data from PostgreSQL based on an optional query filter."""
        logger.info("Reading CAPA data from PostgreSQL")
        try:
            if not self.connected:
                await self.connect()
            
            async def run_query():
                with self.connection.cursor() as cursor:
                    sql = """
                        SELECT capa_id, title, region, status, date, priority, assigned_to
                        FROM capa
                    """
                    if query:
                        sql += " WHERE " + query
                    cursor.execute(sql)
                    return [dict(row) for row in cursor.fetchall()]
            
            results = await asyncio.get_event_loop().run_in_executor(None, run_query)
            results = [self._validate_capa_record(record) for record in results]
            logger.info(f"Successfully read {len(results)} CAPA records")
            return results
        except Exception as e:
            logger.error(f"Error reading CAPA data: {str(e)}", exc_info=True)
            return []
    
    def _validate_capa_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean a CAPA record."""
        try:
            required_fields = ['capa_id', 'title', 'status', 'date']
            for field in required_fields:
                if field not in record or not record[field]:
                    if field == 'capa_id':
                        record[field] = f"CAPA_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    elif field == 'title':
                        record[field] = 'Untitled CAPA'
                    elif field == 'status':
                        record[field] = 'UNKNOWN'
                    elif field == 'date':
                        record[field] = date.today().isoformat()
            
            # Standardize status
            status = str(record.get('status', '')).upper()
            valid_statuses = ['OPEN', 'CLOSED', 'IN_PROGRESS', 'PENDING', 'CANCELLED']
            if status not in valid_statuses:
                record['status'] = 'OPEN'
            else:
                record['status'] = status
            
            # Ensure date is string in YYYY-MM-DD format
            if isinstance(record.get('date'), date):
                record['date'] = record['date'].isoformat()
            
            # Set defaults for optional fields
            record['region'] = record.get('region', 'Global')
            record['priority'] = record.get('priority', 'Medium')
            return record
        except Exception as e:
            logger.error(f"Error validating CAPA record: {str(e)}")
            return record
    
    async def filter_capa_data(self, capa_data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter CAPA data based on provided criteria (client-side for compatibility)."""
        logger.info(f"Filtering {len(capa_data)} CAPA records with filters: {filters}")
        try:
            filtered_data = []
            for record in capa_data:
                matches = True
                for key, value in filters.items():
                    record_value = str(record.get(key, '')).lower()
                    if isinstance(value, str):
                        if value.lower() not in record_value:
                            matches = False
                            break
                    elif isinstance(value, list):
                        if record_value not in [str(v).lower() for v in value]:
                            matches = False
                            break
                    else:
                        if record_value != str(value).lower():
                            matches = False
                            break
                if matches:
                    filtered_data.append(record)
            logger.info(f"Filtered to {len(filtered_data)} matching CAPA records")
            return filtered_data
        except Exception as e:
            logger.error(f"Error filtering CAPA data: {str(e)}", exc_info=True)
            return capa_data
    
    async def get_capa_statistics(self, capa_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics from CAPA data."""
        logger.info(f"Generating statistics for {len(capa_data)} CAPA records")
        try:
            if not capa_data:
                return {
                    "total_records": 0,
                    "status_distribution": {},
                    "region_distribution": {},
                    "priority_distribution": {}
                }
            
            stats = {
                "total_records": len(capa_data),
                "status_distribution": {},
                "region_distribution": {},
                "priority_distribution": {},
                "date_range": {"earliest": None, "latest": None}
            }
            dates = []
            for record in capa_data:
                status = record.get('status', 'UNKNOWN')
                stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
                region = record.get('region', 'Unknown')
                stats["region_distribution"][region] = stats["region_distribution"].get(region, 0) + 1
                priority = record.get('priority', 'Unknown')
                stats["priority_distribution"][priority] = stats["priority_distribution"].get(priority, 0) + 1
                date_str = record.get('date', '')
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        dates.append(date_obj)
                    except ValueError:
                        pass
            
            if dates:
                stats["date_range"]["earliest"] = min(dates).strftime('%Y-%m-%d')
                stats["date_range"]["latest"] = max(dates).strftime('%Y-%m-%d')
            
            logger.info("Successfully generated CAPA statistics")
            return stats
        except Exception as e:
            logger.error(f"Error generating CAPA statistics: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    async def close_connection(self):
        """Close PostgreSQL connection."""
        if self.connected and self.connection:
            logger.info("Closing PostgreSQL CAPA database connection")
            self.connection.close()
            self.connected = False