import logging
import os
from datetime import datetime

def setup_logging(name: str = "invoice_reconciliation", level: int = logging.INFO) -> logging.Logger:
    """
    Setup comprehensive logging system with timestamped files and console output
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamped log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'{timestamp}.log'
    log_filepath = os.path.join(logs_dir, log_filename)
    
    # Configure logger with timestamp suffix to ensure uniqueness
    logger_name = f'{name}_{timestamp}'
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger already exists
    if not logger.handlers:
        # File handler with detailed formatting
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed formatter for file logging
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler for output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Simpler formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log startup information
        logger.info(f'Logging initialized - File: {log_filepath}')
    
    return logger
