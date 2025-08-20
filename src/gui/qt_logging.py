"""
Qt logging handler for real-time log display in GUI.
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal


class QtLogHandler(logging.Handler, QObject):
    """Custom logging handler that emits Qt signals for GUI display."""
    
    log_message = Signal(str, str)  # level, message
    
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        QObject.__init__(self)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(name)s - %(message)s'
        )
        self.setFormatter(formatter)
    
    def emit(self, record):
        """Emit log record as Qt signal."""
        try:
            message = self.format(record)
            level = record.levelname
            self.log_message.emit(level, message)
        except Exception:
            # Silently ignore errors in logging handler to prevent recursion
            pass


class LogCapture:
    """Context manager for capturing logs during processing."""
    
    def __init__(self, log_handler: QtLogHandler, logger_names: list = None):
        self.log_handler = log_handler
        self.logger_names = logger_names or [
            'invoice_reconciliation',
            'core',
            'core.engine', 
            'core.services',
            'gui'
        ]
        self.original_levels = {}
        self.added_handlers = []
    
    def __enter__(self):
        """Start capturing logs."""
        for logger_name in self.logger_names:
            logger = logging.getLogger(logger_name)
            
            # Store original level
            self.original_levels[logger_name] = logger.level
            
            # Set to capture all levels during processing
            logger.setLevel(logging.DEBUG)
            
            # Add our handler if not already present
            if self.log_handler not in logger.handlers:
                logger.addHandler(self.log_handler)
                self.added_handlers.append((logger, self.log_handler))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing logs."""
        # Remove our handlers
        for logger, handler in self.added_handlers:
            if handler in logger.handlers:
                logger.removeHandler(handler)
        
        # Restore original levels
        for logger_name, original_level in self.original_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(original_level)
        
        # Clear tracking lists
        self.added_handlers.clear()
        self.original_levels.clear()
