"""
Core processing workflow models and status tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Invoice, PurchaseOrder, ValidationResult


class ProcessingStatus(Enum):
    """Status of PDF processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingResult:
    """Result of processing a single PDF file."""
    
    # File information
    pdf_path: Path
    status: ProcessingStatus
    
    # Processing timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Extracted data
    extracted_text: Optional[str] = None
    invoice: Optional[Invoice] = None
    purchase_order: Optional[PurchaseOrder] = None
    validation_result: Optional[ValidationResult] = None
    
    # Output paths
    processed_pdf_path: Optional[Path] = None
    result_json_path: Optional[Path] = None
    
    # Error information
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    
    # Processing metadata
    processing_time_seconds: Optional[float] = None
    approval_status: Optional[str] = None  # "APPROVED" or "REQUIRES REVIEW"
    
    def mark_completed(self, success: bool = True) -> None:
        """Mark the processing as completed."""
        self.completed_at = datetime.now()
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        if success and self.status != ProcessingStatus.FAILED:
            self.status = ProcessingStatus.COMPLETED
    
    def mark_failed(self, error_message: str, error_details: Optional[str] = None) -> None:
        """Mark the processing as failed."""
        self.status = ProcessingStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.mark_completed(success=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'pdf_path': str(self.pdf_path),
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time_seconds': self.processing_time_seconds,
            'approval_status': self.approval_status,
            'processed_pdf_path': str(self.processed_pdf_path) if self.processed_pdf_path else None,
            'result_json_path': str(self.result_json_path) if self.result_json_path else None,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'has_invoice': self.invoice is not None,
            'has_purchase_order': self.purchase_order is not None,
            'has_validation_result': self.validation_result is not None,
            'invoice_number': self.invoice.invoice_number if self.invoice else None,
            'po_number': self.purchase_order.po_number if self.purchase_order else None,
            'vendor': self.invoice.vendor if self.invoice else None,
            'validation_issues_count': len(self.validation_result.issues) if self.validation_result else 0,
            'is_approved': self.validation_result.is_approved if self.validation_result else False
        }


@dataclass 
class ProcessingWorkflow:
    """Manages the workflow of processing multiple PDF files."""
    
    input_dir: Path
    output_dir: Path
    results: List[ProcessingResult] = field(default_factory=list)
    current_result: Optional[ProcessingResult] = None
    
    # Progress tracking
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    cancelled: bool = False
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def start(self, pdf_files: List[Path]) -> None:
        """Start the workflow with a list of PDF files."""
        self.started_at = datetime.now()
        self.total_files = len(pdf_files)
        self.cancelled = False
        
        # Initialize results for all files
        self.results = [
            ProcessingResult(pdf_path=pdf_path, status=ProcessingStatus.PENDING)
            for pdf_path in pdf_files
        ]
    
    def get_next_pending(self) -> Optional[ProcessingResult]:
        """Get the next pending file to process."""
        if self.cancelled:
            return None
            
        for result in self.results:
            if result.status == ProcessingStatus.PENDING:
                result.status = ProcessingStatus.PROCESSING
                self.current_result = result
                return result
        return None
    
    def complete_current(self, success: bool = True) -> None:
        """Mark the current file as completed."""
        if self.current_result:
            self.current_result.mark_completed(success)
            if success:
                self.completed_files += 1
            else:
                self.failed_files += 1
            self.current_result = None
    
    def fail_current(self, error_message: str, error_details: Optional[str] = None) -> None:
        """Mark the current file as failed."""
        if self.current_result:
            self.current_result.mark_failed(error_message, error_details)
            self.failed_files += 1
            self.current_result = None
    
    def cancel(self) -> None:
        """Cancel the workflow."""
        self.cancelled = True
        if self.current_result and self.current_result.status == ProcessingStatus.PROCESSING:
            self.current_result.status = ProcessingStatus.CANCELLED
        
        # Mark all pending files as cancelled
        for result in self.results:
            if result.status == ProcessingStatus.PENDING:
                result.status = ProcessingStatus.CANCELLED
    
    def is_complete(self) -> bool:
        """Check if the workflow is complete."""
        return (self.completed_files + self.failed_files) >= self.total_files or self.cancelled
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        processed = self.completed_files + self.failed_files
        progress_percent = (processed / self.total_files * 100) if self.total_files > 0 else 0
        
        return {
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'processed_files': processed,
            'remaining_files': self.total_files - processed,
            'progress_percent': progress_percent,
            'is_complete': self.is_complete(),
            'is_cancelled': self.cancelled,
            'current_file': str(self.current_result.pdf_path) if self.current_result else None,
            'current_status': self.current_result.status.value if self.current_result else None
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary."""
        processing_time = None
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            processing_time = (end_time - self.started_at).total_seconds()
        
        return {
            'input_dir': str(self.input_dir),
            'output_dir': str(self.output_dir),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time_seconds': processing_time,
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'success_rate': (self.completed_files / self.total_files * 100) if self.total_files > 0 else 0,
            'was_cancelled': self.cancelled
        }
