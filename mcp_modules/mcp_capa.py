import os
import logging
from typing import Dict, Any, List
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPCapaModule:
    """
    FastMCP module for reading and processing CAPA (Corrective and Preventive Action) data
    """
    
    def __init__(self):
        self.module_name = "mcp_capa"
        logger.info(f"Initialized {self.module_name} module")
    
    async def read_capa_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read CAPA data from text file and parse it into structured format
        """
        logger.info(f"Reading CAPA data from: {file_path}")
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"CAPA data file not found: {file_path}")
                return []
            
            capa_data = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read the file content
                content = file.read().strip()
                
                if not content:
                    logger.warning("CAPA data file is empty")
                    return []
                
                # Parse the content (assuming tab-separated or structured format)
                lines = content.split('\n')
                
                # Skip header if present
                if lines and ('CAPA_ID' in lines[0] or 'capa_id' in lines[0].lower()):
                    header_line = lines[0]
                    data_lines = lines[1:]
                    headers = [h.strip().lower() for h in header_line.split('\t')]
                else:
                    # Default headers if not present
                    headers = ['capa_id', 'title', 'region', 'status', 'date', 'priority', 'assigned_to']
                    data_lines = lines
                
                for line_num, line in enumerate(data_lines, 1):
                    if line.strip():
                        try:
                            values = [v.strip() for v in line.split('\t')]
                            
                            # Ensure we have enough values
                            while len(values) < len(headers):
                                values.append('')
                            
                            # Create CAPA record
                            capa_record = {}
                            for i, header in enumerate(headers):
                                if i < len(values):
                                    capa_record[header] = values[i]
                                else:
                                    capa_record[header] = ''
                            
                            # Validate and clean the record
                            capa_record = self._validate_capa_record(capa_record)
                            capa_data.append(capa_record)
                            
                        except Exception as e:
                            logger.warning(f"Error parsing line {line_num}: {line}. Error: {str(e)}")
                            continue
            
            logger.info(f"Successfully read {len(capa_data)} CAPA records")
            return capa_data
            
        except Exception as e:
            logger.error(f"Error reading CAPA data: {str(e)}", exc_info=True)
            return []
    
    def _validate_capa_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean a CAPA record
        """
        try:
            # Ensure required fields exist
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
                        record[field] = datetime.now().strftime('%Y-%m-%d')
            
            # Standardize status
            status = record.get('status', '').upper()
            valid_statuses = ['OPEN', 'CLOSED', 'IN_PROGRESS', 'PENDING', 'CANCELLED']
            if status not in valid_statuses:
                if 'PROGRESS' in status or 'WORKING' in status:
                    record['status'] = 'IN_PROGRESS'
                elif 'COMPLETE' in status or 'DONE' in status:
                    record['status'] = 'CLOSED'
                else:
                    record['status'] = 'OPEN'
            else:
                record['status'] = status
            
            # Validate date format
            date_value = record.get('date', '')
            if date_value:
                record['date'] = self._normalize_date(date_value)
            
            # Set default values for optional fields
            if 'region' not in record or not record['region']:
                record['region'] = 'Global'
            
            if 'priority' not in record or not record['priority']:
                record['priority'] = 'Medium'
            
            return record
            
        except Exception as e:
            logger.error(f"Error validating CAPA record: {str(e)}")
            return record
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format
        """
        try:
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%m-%d-%Y',
                '%d-%m-%Y'
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # If no format matches, return original
            logger.warning(f"Could not normalize date: {date_str}")
            return date_str
            
        except Exception as e:
            logger.error(f"Error normalizing date {date_str}: {str(e)}")
            return date_str
    
    async def write_capa_data(self, file_path: str, capa_data: List[Dict[str, Any]]) -> bool:
        """
        Write CAPA data to file
        """
        logger.info(f"Writing {len(capa_data)} CAPA records to: {file_path}")
        
        try:
            if not capa_data:
                logger.warning("No CAPA data to write")
                return False
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Get all unique headers
            all_headers = set()
            for record in capa_data:
                all_headers.update(record.keys())
            
            headers = sorted(list(all_headers))
            
            with open(file_path, 'w', encoding='utf-8', newline='') as file:
                # Write header
                file.write('\t'.join(headers) + '\n')
                
                # Write data
                for record in capa_data:
                    values = []
                    for header in headers:
                        values.append(str(record.get(header, '')))
                    file.write('\t'.join(values) + '\n')
            
            logger.info(f"Successfully wrote CAPA data to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing CAPA data: {str(e)}", exc_info=True)
            return False
    
    async def filter_capa_data(self, capa_data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter CAPA data based on provided criteria
        """
        logger.info(f"Filtering {len(capa_data)} CAPA records with filters: {filters}")
        
        try:
            filtered_data = []
            
            for record in capa_data:
                matches = True
                
                for filter_key, filter_value in filters.items():
                    record_value = record.get(filter_key, '')
                    
                    if isinstance(filter_value, str):
                        if filter_value.lower() not in str(record_value).lower():
                            matches = False
                            break
                    elif isinstance(filter_value, list):
                        if str(record_value) not in [str(v) for v in filter_value]:
                            matches = False
                            break
                    else:
                        if str(record_value) != str(filter_value):
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
        """
        Generate statistics from CAPA data
        """
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
                # Status distribution
                status = record.get('status', 'UNKNOWN')
                stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
                
                # Region distribution
                region = record.get('region', 'Unknown')
                stats["region_distribution"][region] = stats["region_distribution"].get(region, 0) + 1
                
                # Priority distribution
                priority = record.get('priority', 'Unknown')
                stats["priority_distribution"][priority] = stats["priority_distribution"].get(priority, 0) + 1
                
                # Date range
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
