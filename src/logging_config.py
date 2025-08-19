"""
Centralized logging configuration for the invoice reconciliation tool.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .utils import get_timestamp


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    is_test: bool = False
) -> logging.Logger:
    """
    Set up centralized logging configuration with separate directories for app and tests.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, generates timestamped file.
        console_output: Whether to output logs to console
        is_test: Whether this is for test execution (uses separate directory)
        
    Returns:
        Configured logger instance
    """
    # Create appropriate logs directory
    if is_test:
        logs_dir = Path("logs/tests")
    else:
        logs_dir = Path("logs/app")
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate default log file name if not provided
    if log_file is None:
        timestamp = get_timestamp()
        if is_test:
            log_file = logs_dir / f"test_{timestamp}.log"
        else:
            log_file = logs_dir / f"reconciliation_{timestamp}.log"
    else:
        log_file = Path(log_file)
        if not log_file.is_absolute():
            log_file = logs_dir / log_file
    
    # Create consistent formatter for all handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Only set up if not already configured (prevents duplicate handlers)
    if not root_logger.handlers:
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Add file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    
    # Suppress debug logs from third-party libraries
    if log_level.upper() == "DEBUG":
        # Set third-party loggers to ERROR level to reduce noise
        logging.getLogger('openai').setLevel(logging.ERROR)
        logging.getLogger('httpcore').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('requests').setLevel(logging.ERROR)
    
    # Create application logger that inherits from root
    logger = logging.getLogger('invoice_reconciliator')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}, Test mode: {is_test}")
    
    return logger


def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module that inherits from the root configuration.
    
    Args:
        module_name: Name of the module requesting the logger
        
    Returns:
        Configured logger instance for the module
    """
    return logging.getLogger(f'invoice_reconciliator.{module_name}')


def log_function_entry(logger: logging.Logger, func_name: str, **kwargs) -> None:
    """
    Log function entry with parameters.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being entered
        **kwargs: Function parameters to log
    """
    if kwargs:
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.debug(f"Entering {func_name}({params})")
    else:
        logger.debug(f"Entering {func_name}()")


def log_function_exit(logger: logging.Logger, func_name: str, result=None) -> None:
    """
    Log function exit with optional result.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being exited
        result: Optional result to log
    """
    if result is not None:
        logger.debug(f"Exiting {func_name} -> {type(result).__name__}")
    else:
        logger.debug(f"Exiting {func_name}")
