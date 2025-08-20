"""
Service manager for invoice reconciliation components.

Manages initialization and lifecycle of core services.
"""

from pathlib import Path
from typing import Optional

from .services import PDFProcessor, LLMExtractor, FileManager
from .validator import InvoiceValidator
from ..logging_config import get_module_logger


class ServiceManager:
    """Manages core service instances for invoice reconciliation."""
    
    def __init__(self):
        """Initialize the service manager."""
        self.logger = get_module_logger('service_manager')
        
        # Service instances
        self.pdf_processor: Optional[PDFProcessor] = None
        self.llm_extractor: Optional[LLMExtractor] = None
        self.validator: Optional[InvoiceValidator] = None
        self.file_manager: Optional[FileManager] = None
        
        self._initialized = False
    
    def initialize(self, output_dir: Path) -> None:
        """
        Initialize all core services.
        
        Args:
            output_dir: Output directory for processed files
            
        Raises:
            RuntimeError: If services are already initialized
        """
        if self._initialized:
            self.logger.warning("Services already initialized")
            return
        
        self.logger.info("Initializing core services...")
        
        try:
            self.pdf_processor = PDFProcessor()
            self.llm_extractor = LLMExtractor()
            self.validator = InvoiceValidator()
            self.file_manager = FileManager(output_dir)
            
            self._initialized = True
            self.logger.info("Core services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            self.cleanup()
            raise
    
    def is_initialized(self) -> bool:
        """Check if services are initialized."""
        return self._initialized and all([
            self.pdf_processor,
            self.llm_extractor,
            self.validator,
            self.file_manager
        ])
    
    def cleanup(self) -> None:
        """Clean up service instances."""
        self.logger.info("Cleaning up services...")
        
        if self.pdf_processor:
            self.pdf_processor.close()
        
        self.pdf_processor = None
        self.llm_extractor = None
        self.validator = None
        self.file_manager = None
        
        self._initialized = False
        self.logger.info("Services cleaned up")
    
    def get_services(self) -> tuple[PDFProcessor, LLMExtractor, InvoiceValidator, FileManager]:
        """
        Get all service instances.
        
        Returns:
            Tuple of (pdf_processor, llm_extractor, validator, file_manager)
            
        Raises:
            RuntimeError: If services are not initialized
        """
        if not self.is_initialized():
            raise RuntimeError("Services not initialized - call initialize() first")
        
        return self.pdf_processor, self.llm_extractor, self.validator, self.file_manager
