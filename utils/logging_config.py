import os
import logging
import logging.handlers
from typing import Optional
from datetime import datetime

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Setup logging configuration for the Multi-Agent GenAI System
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (auto-generated if None)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        enable_console: Enable console logging
        enable_file: Enable file logging
    """
    
    # Get log level from environment or parameter
    log_level = os.getenv("LOG_LEVEL", log_level).upper()
    
    # Validate log level
    numeric_level = getattr(logging, log_level, logging.INFO)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Create logs directory
    logs_dir = os.getenv("LOGS_DIRECTORY", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(logs_dir, f"multi_agent_system_{timestamp}.log")
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Log the initialization
            logging.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
            
        except Exception as e:
            # If file logging fails, log to console
            logging.error(f"Failed to setup file logging: {str(e)}")
    
    # Set specific loggers for different modules
    _setup_module_loggers(numeric_level)
    
    # Suppress noisy third-party loggers
    _suppress_noisy_loggers()

def _setup_module_loggers(level: int) -> None:
    """
    Setup specific loggers for different modules
    """
    
    # Agent loggers
    logging.getLogger("agents.orchestrator").setLevel(level)
    logging.getLogger("agents.capa_agent").setLevel(level)
    logging.getLogger("agents.neo4j_agent").setLevel(level)
    logging.getLogger("agents.vector_agent").setLevel(level)
    logging.getLogger("agents.email_agent").setLevel(level)
    
    # MCP module loggers
    logging.getLogger("mcp_modules.mcp_capa").setLevel(level)
    logging.getLogger("mcp_modules.mcp_neo4j").setLevel(level)
    logging.getLogger("mcp_modules.mcp_vector").setLevel(level)
    logging.getLogger("mcp_modules.mcp_email").setLevel(level)
    
    # Utility loggers
    logging.getLogger("models.embeddings_handler").setLevel(level)
    logging.getLogger("utils.config").setLevel(level)
    
    # Main application loggers
    logging.getLogger("run_langgraph").setLevel(level)
    logging.getLogger("streamlit_app").setLevel(level)

def _suppress_noisy_loggers() -> None:
    """
    Suppress verbose logging from third-party libraries
    """
    
    # HTTP request libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Database libraries
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("astrapy").setLevel(logging.WARNING)
    
    # ML libraries
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    
    # Google libraries
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    
    # LangGraph and LangChain
    logging.getLogger("langgraph").setLevel(logging.INFO)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    
    # Streamlit
    logging.getLogger("streamlit").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def setup_development_logging() -> None:
    """
    Setup logging configuration optimized for development
    """
    setup_logging(
        log_level="DEBUG",
        enable_console=True,
        enable_file=True
    )

def setup_production_logging() -> None:
    """
    Setup logging configuration optimized for production
    """
    setup_logging(
        log_level="INFO",
        enable_console=False,
        enable_file=True,
        max_bytes=50 * 1024 * 1024,  # 50MB
        backup_count=10
    )

def setup_testing_logging() -> None:
    """
    Setup logging configuration for testing
    """
    setup_logging(
        log_level="WARNING",
        enable_console=True,
        enable_file=False
    )

class StructuredLogger:
    """
    Structured logger for better log analysis
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_agent_action(self, agent_name: str, action: str, **kwargs):
        """Log agent actions with structured data"""
        extra_data = {
            'agent': agent_name,
            'action': action,
            **kwargs
        }
        self.logger.info(f"Agent {agent_name} performed {action}", extra=extra_data)
    
    def log_workflow_step(self, step_name: str, status: str, duration: float = None, **kwargs):
        """Log workflow steps with timing"""
        extra_data = {
            'workflow_step': step_name,
            'status': status,
            'duration_seconds': duration,
            **kwargs
        }
        message = f"Workflow step '{step_name}' {status}"
        if duration:
            message += f" in {duration:.2f}s"
        
        if status == "completed":
            self.logger.info(message, extra=extra_data)
        elif status == "failed":
            self.logger.error(message, extra=extra_data)
        else:
            self.logger.info(message, extra=extra_data)
    
    def log_mcp_operation(self, module: str, operation: str, success: bool, **kwargs):
        """Log MCP module operations"""
        extra_data = {
            'mcp_module': module,
            'operation': operation,
            'success': success,
            **kwargs
        }
        
        message = f"MCP {module} {operation} {'succeeded' if success else 'failed'}"
        
        if success:
            self.logger.info(message, extra=extra_data)
        else:
            self.logger.error(message, extra=extra_data)
    
    def log_api_call(self, api_name: str, endpoint: str, status_code: int = None, 
                     duration: float = None, **kwargs):
        """Log API calls with timing and status"""
        extra_data = {
            'api': api_name,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_seconds': duration,
            **kwargs
        }
        
        message = f"API call to {api_name}/{endpoint}"
        if status_code:
            message += f" returned {status_code}"
        if duration:
            message += f" in {duration:.2f}s"
        
        if status_code and 200 <= status_code < 300:
            self.logger.info(message, extra=extra_data)
        elif status_code and status_code >= 400:
            self.logger.error(message, extra=extra_data)
        else:
            self.logger.info(message, extra=extra_data)

def create_structured_logger(name: str) -> StructuredLogger:
    """
    Create a structured logger instance
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)

# Context manager for timing operations
class LogTimer:
    """Context manager for logging operation timing"""
    
    def __init__(self, logger: logging.Logger, operation_name: str, log_level: int = logging.INFO):
        self.logger = logger
        self.operation_name = operation_name
        self.log_level = log_level
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.log(self.log_level, f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.log(self.log_level, f"Completed {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.2f}s: {exc_val}")
