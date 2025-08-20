"""
Core invoice reconciliation engine.

This module contains the main business logic for processing PDF files,
extracting data, validating, and managing results. It's designed to be
used by both CLI and GUI applications.
"""

from pathlib import Path
from typing import List, Optional, Callable, Any
import logging

from .service_manager import ServiceManager
from .workflow import ProcessingWorkflow, ProcessingResult, ProcessingStatus
from ..settings import settings
from ..logging_config import get_module_logger


class InvoiceReconciliationEngine:
    """
    Core engine for invoice reconciliation processing.
    
    This class encapsulates all the business logic for processing PDF files,
    making it reusable between CLI and GUI applications.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the reconciliation engine.
        
        Args:
            output_dir: Directory for output files
        """
        self.logger = get_module_logger('engine')
        self.output_dir = output_dir
        self.service_manager = ServiceManager()
        self.current_workflow: Optional[ProcessingWorkflow] = None
        
        # Callback hooks for progress updates (used by GUI)
        self.on_progress_update: Optional[Callable[[dict], None]] = None
        self.on_file_started: Optional[Callable[[ProcessingResult], None]] = None
        self.on_file_completed: Optional[Callable[[ProcessingResult], None]] = None
        self.on_workflow_completed: Optional[Callable[[ProcessingWorkflow], None]] = None
        self.on_log_message: Optional[Callable[[str, str], None]] = None  # (level, message)
    
    def initialize(self) -> None:
        """Initialize the engine and its services."""
        self.logger.info("Initializing Invoice Reconciliation Engine...")
        self.service_manager.initialize(self.output_dir)
        self.logger.info("Engine initialized successfully")
    
    def cleanup(self) -> None:
        """Clean up engine resources."""
        self.logger.info("Cleaning up engine...")
        self.service_manager.cleanup()
        self.current_workflow = None
        self.logger.info("Engine cleanup completed")
    
    def find_pdf_files(self, input_dir: Path) -> List[Path]:
        """
        Find all PDF files in the input directory.
        
        Args:
            input_dir: Directory to search for PDF files
            
        Returns:
            List of PDF file paths
        """
        self.logger.info(f"Searching for PDF files in: {input_dir}")
        
        if not input_dir.exists():
            self.logger.error(f"Input directory does not exist: {input_dir}")
            return []
        
        # First try direct PDF files in the directory
        pdf_files = list(input_dir.glob("*.pdf"))
        
        # If no PDFs found, search recursively in subdirectories
        if not pdf_files:
            self.logger.info("No PDFs in root directory, searching subdirectories...")
            pdf_files = list(input_dir.rglob("*.pdf"))
        
        self.logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def start_workflow(self, input_dir: Path) -> ProcessingWorkflow:
        """
        Start a new processing workflow.
        
        Args:
            input_dir: Directory containing PDF files to process
            
        Returns:
            ProcessingWorkflow instance
            
        Raises:
            RuntimeError: If engine is not initialized or no PDF files found
        """
        if not self.service_manager.is_initialized():
            raise RuntimeError("Engine not initialized - call initialize() first")
        
        pdf_files = self.find_pdf_files(input_dir)
        if not pdf_files:
            raise RuntimeError(f"No PDF files found in {input_dir}")
        
        self.current_workflow = ProcessingWorkflow(
            input_dir=input_dir,
            output_dir=self.output_dir
        )
        
        self.current_workflow.start(pdf_files)
        self.logger.info(f"Started workflow with {len(pdf_files)} files")
        
        return self.current_workflow
    
    def process_single_file(self, pdf_path: Path) -> ProcessingResult:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ProcessingResult with processing outcome
        """
        result = ProcessingResult(pdf_path=pdf_path, status=ProcessingStatus.PROCESSING)
        
        try:
            self.logger.info(f"Processing PDF: {pdf_path.name}")
            self._emit_file_started(result)
            
            # Get services
            pdf_processor, llm_extractor, validator, file_manager = self.service_manager.get_services()
            
            # Step 1: Extract text from PDF
            self._update_status(result, ProcessingStatus.EXTRACTING, "Extracting text from PDF...")
            text = pdf_processor.extract_text(pdf_path)
            
            if not text.strip():
                raise RuntimeError("No text extracted from PDF")
            
            result.extracted_text = text
            self.logger.info(f"Extracted {len(text)} characters of text")
            
            # Step 2: Extract structured data using LLM
            self._update_status(result, ProcessingStatus.EXTRACTING, "Extracting invoice and PO data...")
            invoice, purchase_order = llm_extractor.extract_invoice_data(text)
            
            if not invoice or not purchase_order:
                raise RuntimeError("Failed to extract invoice or purchase order data")
            
            result.invoice = invoice
            result.purchase_order = purchase_order
            self.logger.info(f"Extracted invoice {invoice.invoice_number} and PO {purchase_order.po_number}")
            
            # Step 3: Validate the data
            self._update_status(result, ProcessingStatus.VALIDATING, "Validating invoice against purchase order...")
            validation_result = validator.validate(invoice, purchase_order)
            result.validation_result = validation_result
            
            # Determine processing status
            approval_status = "APPROVED" if validation_result.is_approved else "REQUIRES REVIEW"
            
            # Override status if configured to always accept
            if settings.stamp_always_accept:
                approval_status = "APPROVED"
            
            result.approval_status = approval_status
            self.logger.info(f"Validation result: {approval_status}")
            
            if validation_result.issues:
                self.logger.info("Validation issues found:")
                for issue in validation_result.issues:
                    self.logger.info(f"  - {issue}")
            
            # Step 4: Process and save the PDF
            self._update_status(result, ProcessingStatus.SAVING, "Processing and saving PDF...")
            final_path = file_manager.process_pdf(pdf_path, approval_status)
            result.processed_pdf_path = final_path
            
            # Step 5: Save extraction and validation results
            result_path = file_manager.save_result(invoice, purchase_order, validation_result, final_path)
            result.result_json_path = result_path
            
            result.mark_completed(success=True)
            self.logger.info(f"Successfully processed PDF: {final_path}")
            
        except Exception as e:
            error_msg = f"Error processing PDF {pdf_path.name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            result.mark_failed(error_msg, str(e))
        
        self._emit_file_completed(result)
        return result
    
    def process_workflow(self) -> None:
        """
        Process the current workflow (all pending files).
        
        Raises:
            RuntimeError: If no workflow is active
        """
        if not self.current_workflow:
            raise RuntimeError("No active workflow - call start_workflow() first")
        
        self.logger.info("Starting workflow processing...")
        
        while not self.current_workflow.is_complete():
            # Check for cancellation
            if self.current_workflow.cancelled:
                self.logger.info("Workflow cancelled by user")
                break
            
            # Get next file to process
            result = self.current_workflow.get_next_pending()
            if not result:
                break
            
            # Process the file
            processed_result = self.process_single_file(result.pdf_path)
            
            # Update workflow with result
            result.status = processed_result.status
            result.extracted_text = processed_result.extracted_text
            result.invoice = processed_result.invoice
            result.purchase_order = processed_result.purchase_order
            result.validation_result = processed_result.validation_result
            result.processed_pdf_path = processed_result.processed_pdf_path
            result.result_json_path = processed_result.result_json_path
            result.error_message = processed_result.error_message
            result.error_details = processed_result.error_details
            result.processing_time_seconds = processed_result.processing_time_seconds
            result.approval_status = processed_result.approval_status
            result.completed_at = processed_result.completed_at
            
            # Update workflow counters
            if result.status == ProcessingStatus.COMPLETED:
                self.current_workflow.complete_current(success=True)
            else:
                self.current_workflow.complete_current(success=False)
            
            # Emit progress update
            self._emit_progress_update()
        
        self.current_workflow.completed_at = self.current_workflow.started_at
        self.logger.info("Workflow processing completed")
        self._emit_workflow_completed()
    
    def cancel_workflow(self) -> None:
        """Cancel the current workflow."""
        if self.current_workflow:
            self.current_workflow.cancel()
            self.logger.info("Workflow cancellation requested")
    
    def get_workflow_progress(self) -> dict:
        """Get current workflow progress."""
        if not self.current_workflow:
            return {'total_files': 0, 'processed_files': 0, 'progress_percent': 0}
        return self.current_workflow.get_progress()
    
    def get_workflow_results(self) -> List[ProcessingResult]:
        """Get all processing results from the current workflow."""
        if not self.current_workflow:
            return []
        return self.current_workflow.results
    
    def _update_status(self, result: ProcessingResult, status: ProcessingStatus, message: str) -> None:
        """Update processing status and emit log message."""
        result.status = status
        self.logger.info(message)
        self._emit_log_message("INFO", message)
    
    def _emit_progress_update(self) -> None:
        """Emit progress update callback."""
        if self.on_progress_update and self.current_workflow:
            progress = self.current_workflow.get_progress()
            self.on_progress_update(progress)
    
    def _emit_file_started(self, result: ProcessingResult) -> None:
        """Emit file started callback."""
        if self.on_file_started:
            self.on_file_started(result)
    
    def _emit_file_completed(self, result: ProcessingResult) -> None:
        """Emit file completed callback."""
        if self.on_file_completed:
            self.on_file_completed(result)
    
    def _emit_workflow_completed(self) -> None:
        """Emit workflow completed callback."""
        if self.on_workflow_completed and self.current_workflow:
            self.on_workflow_completed(self.current_workflow)
    
    def _emit_log_message(self, level: str, message: str) -> None:
        """Emit log message callback."""
        if self.on_log_message:
            self.on_log_message(level, message)
