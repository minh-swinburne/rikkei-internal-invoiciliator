"""
Thread classes for background processing operations.

This module contains thread definitions that can be reused across CLI and GUI applications.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal, QTimer

from .engine import InvoiceReconciliationEngine
from .workflow import ProcessingResult, ProcessingWorkflow
from ..logging_config import get_module_logger


class ProcessingThread(QThread):
    """Background thread for processing PDFs."""
    
    progress_updated = Signal(dict)
    file_started = Signal(dict)
    file_completed = Signal(dict)
    workflow_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, engine: InvoiceReconciliationEngine, input_dir: Path):
        super().__init__()
        self.engine = engine
        self.input_dir = input_dir
        self.should_stop = False
        self.is_paused = False
        self.pause_event = QTimer()  # Use QTimer for pause control
        self.logger = get_module_logger('processing_thread')
        
        # Note: Log capture is handled by MainWindow's permanent log handler
        # No need to set up additional log handling here to avoid duplication
    
    def run(self):
        """Run the processing in background thread."""
        try:
            # Set up engine callbacks for GUI updates
            self.engine.on_progress_update = self.emit_progress_update
            self.engine.on_file_started = self.emit_file_started
            self.engine.on_file_completed = self.emit_file_completed
            self.engine.on_workflow_completed = self.emit_workflow_completed
            
            # Start the workflow and process all files
            workflow = self.engine.start_workflow(self.input_dir)
            self.engine.process_workflow()
            
            # Note: Workflow completion is already emitted by engine callback
            # No need to emit again here to avoid duplication
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def emit_progress_update(self, progress: dict):
        """Emit progress update with error handling."""
        try:
            self.progress_updated.emit(progress)
        except Exception as e:
            self.logger.error(f"Error emitting progress update: {e}")

    def emit_file_started(self, result: ProcessingResult):
        """Emit file started signal with error handling."""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            self.file_started.emit(result_dict)
        except Exception as e:
            self.logger.error(f"Error emitting file started: {e}")

    def emit_file_completed(self, result: ProcessingResult):
        """Emit file completed signal with error handling."""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            self.file_completed.emit(result_dict)
        except Exception as e:
            self.logger.error(f"Error emitting file completed: {e}")
    
    def emit_workflow_completed(self, workflow: ProcessingWorkflow):
        """Emit workflow completed signal with error handling."""
        try:
            summary = workflow.get_summary() if hasattr(workflow, 'get_summary') else {}
            self.workflow_completed.emit(summary)
        except Exception as e:
            self.logger.error(f"Error emitting workflow completed: {e}")
    
    def stop(self):
        """Request to stop processing."""
        self.should_stop = True
        self.logger.info("Stop requested by user")
        if self.engine:
            try:
                self.engine.cancel_workflow()
            except Exception as e:
                self.logger.error(f"Error during cancellation: {e}")
    
    def pause(self):
        """Pause the processing."""
        self.is_paused = True
        self.logger.info("Processing thread paused")
    
    def resume(self):
        """Resume the processing."""
        self.is_paused = False
        self.logger.info("Processing thread resumed")
    
    def _check_pause(self):
        """Check if processing should be paused and wait if needed."""
        while self.is_paused and not self.should_stop:
            self.msleep(100)  # Sleep for 100ms and check again


class RetryThread(QThread):
    """Background thread for retrying a single file."""
    
    completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, engine: InvoiceReconciliationEngine, pdf_path: Path):
        super().__init__()
        self.engine = engine
        self.pdf_path = pdf_path
        self.logger = get_module_logger('retry_thread')
    
    def run(self):
        """Run the retry processing in background thread."""
        try:
            # Ensure engine is initialized
            if not self.engine.is_initialized():
                self.engine.initialize()
            
            result = self.engine.process_single_file(self.pdf_path, is_retry=True)
            
            # Convert to dict for signal emission
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            self.completed.emit(result_dict)
            
        except Exception as e:
            self.logger.error(f"Error in retry thread: {e}")
            self.error_occurred.emit(str(e))
