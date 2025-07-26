import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    neo4j_uri: str = ""
    neo4j_username: str = ""
    neo4j_password: str = ""
    astra_db_token: str = ""
    astra_db_endpoint: str = ""

@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    default_recipient: str = ""
    sender_email: str = ""
    mock_mode: bool = True

@dataclass
class APIConfig:
    """API configuration settings"""
    gemini_api_key: str = ""
    openai_api_key: str = ""  # For fallback if needed
    
@dataclass
class AppConfig:
    """Application configuration settings"""
    debug_mode: bool = False
    log_level: str = "INFO"
    data_directory: str = "data"
    logs_directory: str = "logs"
    max_file_size_mb: int = 100
    enable_caching: bool = True

class Config:
    """
    Centralized configuration management for the Multi-Agent GenAI System
    """
    
    def __init__(self):
        self._load_config()
        logger.info("Configuration loaded successfully")
    
    def _load_config(self):
        """Load configuration from environment variables"""
        
        # Database Configuration
        self.database = DatabaseConfig(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
            astra_db_token=os.getenv("ASTRA_DB_TOKEN", ""),
            astra_db_endpoint=os.getenv("ASTRA_DB_ENDPOINT", "")
        )
        
        # Email Configuration
        self.email = EmailConfig(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            default_recipient=os.getenv("DEFAULT_EMAIL_RECIPIENT", "analyst@company.com"),
            sender_email=os.getenv("SENDER_EMAIL", "system@company.com"),
            mock_mode=os.getenv("EMAIL_MOCK_MODE", "true").lower() == "true"
        )
        
        # API Configuration
        self.api = APIConfig(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # Application Configuration
        self.app = AppConfig(
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            data_directory=os.getenv("DATA_DIRECTORY", "data"),
            logs_directory=os.getenv("LOGS_DIRECTORY", "logs"),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100")),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true"
        )
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the configuration and return validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # Validate API Keys
        if not self.api.gemini_api_key:
            validation_results["errors"].append("GEMINI_API_KEY is required")
            validation_results["valid"] = False
        else:
            validation_results["checks"]["gemini_api_key"] = "✅ Present"
        
        # Validate Database Configuration
        if self.database.neo4j_uri:
            validation_results["checks"]["neo4j_uri"] = "✅ Configured"
        else:
            validation_results["warnings"].append("Neo4j URI not configured - using mock mode")
            validation_results["checks"]["neo4j_uri"] = "⚠️ Mock mode"
        
        if self.database.astra_db_token:
            validation_results["checks"]["astra_db"] = "✅ Configured"
        else:
            validation_results["warnings"].append("Astra DB not configured - using mock mode")
            validation_results["checks"]["astra_db"] = "⚠️ Mock mode"
        
        # Validate Email Configuration
        if self.email.mock_mode:
            validation_results["checks"]["email"] = "⚠️ Mock mode"
        elif self.email.smtp_username and self.email.smtp_password:
            validation_results["checks"]["email"] = "✅ SMTP configured"
        else:
            validation_results["warnings"].append("Email SMTP not fully configured")
            validation_results["checks"]["email"] = "⚠️ Incomplete SMTP config"
        
        # Validate File Paths
        try:
            os.makedirs(self.app.data_directory, exist_ok=True)
            validation_results["checks"]["data_directory"] = "✅ Accessible"
        except Exception as e:
            validation_results["errors"].append(f"Cannot access data directory: {str(e)}")
            validation_results["valid"] = False
        
        try:
            os.makedirs(self.app.logs_directory, exist_ok=True)
            validation_results["checks"]["logs_directory"] = "✅ Accessible"
        except Exception as e:
            validation_results["errors"].append(f"Cannot access logs directory: {str(e)}")
            validation_results["valid"] = False
        
        return validation_results
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        if self.database.neo4j_uri and self.database.neo4j_username and self.database.neo4j_password:
            return f"{self.database.neo4j_uri}"
        return ""
    
    def get_email_settings(self) -> Dict[str, Any]:
        """Get email settings as dictionary"""
        return {
            "smtp_server": self.email.smtp_server,
            "smtp_port": self.email.smtp_port,
            "username": self.email.smtp_username,
            "password": self.email.smtp_password,
            "use_tls": self.email.smtp_use_tls,
            "mock_mode": self.email.mock_mode,
            "default_recipient": self.email.default_recipient,
            "sender_email": self.email.sender_email
        }
    
    def get_api_settings(self) -> Dict[str, Any]:
        """Get API settings as dictionary"""
        return {
            "gemini_api_key": self.api.gemini_api_key,
            "openai_api_key": self.api.openai_api_key
        }
    
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        return not self.app.debug_mode and self.api.gemini_api_key != ""
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get important file paths"""
        return {
            "capa_data": os.path.join(self.app.data_directory, "capa_data.txt"),
            "logs_dir": self.app.logs_directory,
            "data_dir": self.app.data_directory
        }
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        Update a configuration value dynamically
        """
        try:
            if section == "database":
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
                    logger.info(f"Updated database.{key}")
                    return True
            elif section == "email":
                if hasattr(self.email, key):
                    setattr(self.email, key, value)
                    logger.info(f"Updated email.{key}")
                    return True
            elif section == "api":
                if hasattr(self.api, key):
                    setattr(self.api, key, value)
                    logger.info(f"Updated api.{key}")
                    return True
            elif section == "app":
                if hasattr(self.app, key):
                    setattr(self.app, key, value)
                    logger.info(f"Updated app.{key}")
                    return True
            
            logger.warning(f"Invalid config section.key: {section}.{key}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating config {section}.{key}: {str(e)}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration
        """
        return {
            "database": {
                "neo4j_configured": bool(self.database.neo4j_uri),
                "astra_configured": bool(self.database.astra_db_token)
            },
            "email": {
                "smtp_configured": bool(self.email.smtp_username and self.email.smtp_password),
                "mock_mode": self.email.mock_mode
            },
            "api": {
                "gemini_configured": bool(self.api.gemini_api_key),
                "openai_configured": bool(self.api.openai_api_key)
            },
            "app": {
                "debug_mode": self.app.debug_mode,
                "log_level": self.app.log_level,
                "caching_enabled": self.app.enable_caching
            }
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        Export configuration as dictionary
        """
        config_dict = {
            "database": {
                "neo4j_uri": self.database.neo4j_uri,
                "neo4j_username": self.database.neo4j_username,
                "astra_db_endpoint": self.database.astra_db_endpoint
            },
            "email": {
                "smtp_server": self.email.smtp_server,
                "smtp_port": self.email.smtp_port,
                "smtp_username": self.email.smtp_username,
                "smtp_use_tls": self.email.smtp_use_tls,
                "default_recipient": self.email.default_recipient,
                "sender_email": self.email.sender_email,
                "mock_mode": self.email.mock_mode
            },
            "app": {
                "debug_mode": self.app.debug_mode,
                "log_level": self.app.log_level,
                "data_directory": self.app.data_directory,
                "logs_directory": self.app.logs_directory,
                "max_file_size_mb": self.app.max_file_size_mb,
                "enable_caching": self.app.enable_caching
            }
        }
        
        if include_secrets:
            config_dict["database"]["neo4j_password"] = self.database.neo4j_password
            config_dict["database"]["astra_db_token"] = self.database.astra_db_token
            config_dict["email"]["smtp_password"] = self.email.smtp_password
            config_dict["api"] = {
                "gemini_api_key": self.api.gemini_api_key,
                "openai_api_key": self.api.openai_api_key
            }
        
        return config_dict

# Global configuration instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """
    Reload the configuration from environment variables
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance
