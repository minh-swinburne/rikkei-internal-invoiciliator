"""
Result viewer dialog for detailed invoice reconciliation results.
"""

import json
import os
from pathlib import Path
from typing import Optional, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTextEdit, 
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QSplitter, QTabWidget, QWidget, QScrollArea, QMessageBox,
    QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon

from src.utils import load_json, get_project_root

from ..logging_config import get_module_logger
from .pdf_viewer import PDFViewer
from .native_pdf_viewer import NativePDFViewer


class ResultDetailViewer(QDialog):
    """Dialog for viewing detailed reconciliation results."""
    
    def __init__(self, result_file: Path, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.result_viewer')
        self.result_file = result_file
        self.result_data: Optional[dict[str, Any]] = None
        self.pdf_viewer = None  # Initialize to prevent crashes
        
        self.setWindowTitle(f"Invoice Details: {result_file.stem}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Set window flags to ensure proper cleanup
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Dialog)
        
        try:
            self.setup_ui()
            self.load_result_data()
        except Exception as e:
            self.logger.error(f"Failed to initialize result viewer: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load result viewer:\n{str(e)}")
    
    def closeEvent(self, event):
        """Handle window close event with proper cleanup."""
        try:
            # Clean up PDF viewer resources
            if hasattr(self, 'pdf_viewer') and self.pdf_viewer:
                if hasattr(self.pdf_viewer, 'pdf_document') and self.pdf_viewer.pdf_document:
                    self.pdf_viewer.pdf_document.close()
                
            self.logger.debug("Result viewer window closed")
            event.accept()
        except Exception as e:
            self.logger.error(f"Error during result viewer cleanup: {e}")
            event.accept()  # Accept the event anyway to prevent hanging
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Main splitter (left: PDF, right: details)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: PDF viewer
        try:
            # Try to use native PySide6 PDF viewer first
            self.pdf_viewer = NativePDFViewer()
            self.logger.info("Using native PySide6 PDF viewer")
        except Exception as e:
            # Fallback to PyMuPDF viewer
            self.logger.warning(f"Native PDF viewer not available, using PyMuPDF fallback: {e}")
            try:
                self.pdf_viewer = PDFViewer()
            except Exception as fallback_error:
                self.logger.error(f"Failed to create fallback PDF viewer: {fallback_error}")
                # Create placeholder widget
                self.pdf_viewer = QWidget()
                layout = QVBoxLayout(self.pdf_viewer)
                error_label = QLabel("PDF viewer not available")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                error_label.setStyleSheet("color: red; font-weight: bold;")
                layout.addWidget(error_label)
        
        main_splitter.addWidget(self.pdf_viewer)
        
        # Right side: Details tabs
        self.details_widget = QTabWidget()
        self.setup_details_tabs()
        main_splitter.addWidget(self.details_widget)
        
        # Set initial splitter sizes (PDF: 60%, Details: 40%)
        main_splitter.setSizes([720, 480])
        layout.addWidget(main_splitter)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        self.reprocess_btn = QPushButton("Reprocess File")
        self.reprocess_btn.clicked.connect(self.reprocess_file)
        button_layout.addWidget(self.reprocess_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_details_tabs(self):
        """Set up the details tab widget."""
        # Tab 1: Summary
        self.summary_tab = self.create_summary_tab()
        self.details_widget.addTab(self.summary_tab, "Summary")
        
        # Tab 2: Invoice Data
        self.invoice_tab = self.create_invoice_tab()
        self.details_widget.addTab(self.invoice_tab, "Invoice")
        
        # Tab 3: Purchase Order Data
        self.po_tab = self.create_po_tab()
        self.details_widget.addTab(self.po_tab, "Purchase Order")
        
        # Tab 4: Items Comparison
        self.items_tab = self.create_items_tab()
        self.details_widget.addTab(self.items_tab, "Items")
        
        # Tab 5: Validation Results
        self.validation_tab = self.create_validation_tab()
        self.details_widget.addTab(self.validation_tab, "Validation")
        
        # Tab 6: Raw Data
        self.raw_tab = self.create_raw_tab()
        self.details_widget.addTab(self.raw_tab, "Raw Data")
    
    def create_summary_tab(self) -> QWidget:
        """Create the summary tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Overall status
        self.status_group = QGroupBox("Processing Status")
        status_layout = QVBoxLayout(self.status_group)
        
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.issues_label = QLabel("Issues: Loading...")
        status_layout.addWidget(self.issues_label)
        
        layout.addWidget(self.status_group)
        
        # File information
        self.file_info_group = QGroupBox("File Information")
        file_layout = QVBoxLayout(self.file_info_group)
        
        self.file_path_label = QLabel(f"File: {self.result_file.name}")
        file_layout.addWidget(self.file_path_label)
        
        self.processed_time_label = QLabel("Processed: Loading...")
        file_layout.addWidget(self.processed_time_label)
        
        layout.addWidget(self.file_info_group)
        
        # Quick actions
        self.actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(self.actions_group)
        
        self.approve_btn = QPushButton("✓ Approve Override")
        self.approve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.approve_btn.clicked.connect(self.approve_override)
        actions_layout.addWidget(self.approve_btn)
        
        self.reject_btn = QPushButton("✗ Reject for Review")
        self.reject_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.reject_btn.clicked.connect(self.reject_for_review)
        actions_layout.addWidget(self.reject_btn)
        
        layout.addWidget(self.actions_group)
        
        layout.addStretch()
        return widget
    
    def create_invoice_tab(self) -> QWidget:
        """Create the invoice data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Invoice header info
        self.invoice_header_group = QGroupBox("Invoice Information")
        header_layout = QGridLayout(self.invoice_header_group)
        
        # Create labels for header info
        self.invoice_number_label = QLabel("Loading...")
        self.invoice_vendor_label = QLabel("Loading...")
        self.invoice_po_ref_label = QLabel("Loading...")
        self.invoice_credit_memo_label = QLabel("Loading...")
        
        header_layout.addWidget(QLabel("Invoice Number:"), 0, 0)
        header_layout.addWidget(self.invoice_number_label, 0, 1)
        header_layout.addWidget(QLabel("Vendor:"), 1, 0)
        header_layout.addWidget(self.invoice_vendor_label, 1, 1)
        header_layout.addWidget(QLabel("PO Reference:"), 2, 0)
        header_layout.addWidget(self.invoice_po_ref_label, 2, 1)
        header_layout.addWidget(QLabel("Credit Memo:"), 3, 0)
        header_layout.addWidget(self.invoice_credit_memo_label, 3, 1)
        
        layout.addWidget(self.invoice_header_group)
        
        # Invoice items table
        self.invoice_items_group = QGroupBox("Invoice Items")
        items_layout = QVBoxLayout(self.invoice_items_group)
        
        self.invoice_items_table = QTableWidget()
        self.invoice_items_table.setColumnCount(6)
        self.invoice_items_table.setHorizontalHeaderLabels([
            "SKU/VPN", "Description", "Qty Ordered", "Qty Shipped", "Unit Price", "Total"
        ])
        
        # Set table properties
        self.invoice_items_table.setAlternatingRowColors(True)
        self.invoice_items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoice_items_table.setMaximumHeight(300)  # Limit height to ~10 rows
        
        # Configure column widths
        header = self.invoice_items_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        items_layout.addWidget(self.invoice_items_table)
        layout.addWidget(self.invoice_items_group)
        
        # Extra fees section
        self.invoice_fees_group = QGroupBox("Extra Fees")
        fees_layout = QVBoxLayout(self.invoice_fees_group)
        self.invoice_fees_label = QLabel("No extra fees")
        fees_layout.addWidget(self.invoice_fees_label)
        layout.addWidget(self.invoice_fees_group)
        
        layout.addStretch()
        return widget
    
    def create_po_tab(self) -> QWidget:
        """Create the purchase order data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PO header info
        self.po_header_group = QGroupBox("Purchase Order Information")
        header_layout = QGridLayout(self.po_header_group)
        
        # Create labels for header info
        self.po_number_label = QLabel("Loading...")
        
        header_layout.addWidget(QLabel("PO Number:"), 0, 0)
        header_layout.addWidget(self.po_number_label, 0, 1)
        
        layout.addWidget(self.po_header_group)
        
        # PO items table
        self.po_items_group = QGroupBox("Purchase Order Items")
        items_layout = QVBoxLayout(self.po_items_group)
        
        self.po_items_table = QTableWidget()
        self.po_items_table.setColumnCount(5)
        self.po_items_table.setHorizontalHeaderLabels([
            "SKU/VPN", "Description", "Qty Ordered", "Unit Price", "Total"
        ])
        
        # Set table properties
        self.po_items_table.setAlternatingRowColors(True)
        self.po_items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.po_items_table.setMaximumHeight(300)  # Limit height to ~10 rows
        
        # Configure column widths
        header = self.po_items_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        items_layout.addWidget(self.po_items_table)
        layout.addWidget(self.po_items_group)
        
        # Extra fees section
        self.po_fees_group = QGroupBox("Extra Fees")
        fees_layout = QVBoxLayout(self.po_fees_group)
        self.po_fees_label = QLabel("No extra fees")
        fees_layout.addWidget(self.po_fees_label)
        layout.addWidget(self.po_fees_group)
        
        layout.addStretch()
        return widget
    
    def create_items_tab(self) -> QWidget:
        """Create the items comparison tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "SKU/VPN", "Description", "Invoice Qty", "PO Qty", 
            "Invoice Price", "PO Price", "Status", "Issues"
        ])
        
        # Set column widths
        header = self.items_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        
        layout.addWidget(self.items_table)
        return widget
    
    def create_validation_tab(self) -> QWidget:
        """Create the validation results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Validation Status Section
        self.validation_status_group = QGroupBox("Validation Status")
        status_layout = QGridLayout(self.validation_status_group)
        
        # Status labels
        self.validation_approved_label = QLabel("Loading...")
        self.validation_vendor_label = QLabel("Loading...")
        self.validation_invoice_total_label = QLabel("Loading...")
        self.validation_po_total_label = QLabel("Loading...")
        
        status_layout.addWidget(QLabel("Approved:"), 0, 0)
        status_layout.addWidget(self.validation_approved_label, 0, 1)
        status_layout.addWidget(QLabel("Vendor:"), 1, 0)
        status_layout.addWidget(self.validation_vendor_label, 1, 1)
        status_layout.addWidget(QLabel("Invoice Total:"), 2, 0)
        status_layout.addWidget(self.validation_invoice_total_label, 2, 1)
        status_layout.addWidget(QLabel("PO Total:"), 3, 0)
        status_layout.addWidget(self.validation_po_total_label, 3, 1)
        
        layout.addWidget(self.validation_status_group)
        
        # Issues Section
        self.validation_issues_group = QGroupBox("Issues Found")
        issues_layout = QVBoxLayout(self.validation_issues_group)
        
        self.validation_issues_table = QTableWidget()
        self.validation_issues_table.setColumnCount(2)
        self.validation_issues_table.setHorizontalHeaderLabels(["#", "Issue Description"])
        self.validation_issues_table.setMaximumHeight(200)  # Limit height
        self.validation_issues_table.setAlternatingRowColors(True)
        
        # Configure column widths
        issues_header = self.validation_issues_table.horizontalHeader()
        issues_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        issues_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        issues_layout.addWidget(self.validation_issues_table)
        layout.addWidget(self.validation_issues_group)
        
        # Notes Section
        self.validation_notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout(self.validation_notes_group)
        
        self.validation_notes_table = QTableWidget()
        self.validation_notes_table.setColumnCount(2)
        self.validation_notes_table.setHorizontalHeaderLabels(["#", "Note"])
        self.validation_notes_table.setMaximumHeight(150)  # Limit height
        self.validation_notes_table.setAlternatingRowColors(True)
        
        # Configure column widths
        notes_header = self.validation_notes_table.horizontalHeader()
        notes_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        notes_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        notes_layout.addWidget(self.validation_notes_table)
        layout.addWidget(self.validation_notes_group)
        
        layout.addStretch()
        return widget
    
    def create_raw_tab(self) -> QWidget:
        """Create the raw data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.raw_text)
        
        return widget
    
    def load_result_data(self):
        """Load the result data from file."""
        try:
            if self.result_file.exists():
                self.result_data = load_json(self.result_file, self.logger)

                if self.result_data is not None:
                    self.populate_ui()
                else:
                    # JSON loading failed, show error but still try to load PDF
                    self.logger.warning(f"Failed to load JSON data from {self.result_file}")
                    self.show_json_error()
                        
                # Always try to load PDF regardless of JSON success
                self.load_pdf()
            else:
                QMessageBox.warning(self, "File Not Found", f"Result file not found:\n{self.result_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to load result data: {e}")
            # Still try to load PDF even if JSON fails completely
            self.show_json_error(str(e))
            self.load_pdf()
    
    def show_json_error(self, error_msg: str = ""):
        """Show error in UI when JSON loading fails but still allow PDF viewing."""
        try:
            # Set error status in summary
            if hasattr(self, 'status_label'):
                self.status_label.setText("Status: ERROR - JSON Load Failed")
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
            
            if hasattr(self, 'issues_label'):
                self.issues_label.setText("Issues: Unable to load validation data")
            
            if hasattr(self, 'processed_time_label'):
                self.processed_time_label.setText("Processed: Unknown (JSON load error)")
            
            # Show error message in raw data tab if available
            if hasattr(self, 'raw_text'):
                error_details = f"Error loading JSON data:\n{error_msg}\n\nFile: {self.result_file}"
                self.raw_text.setText(error_details)
            
            self.logger.info("Set error status in UI, PDF viewer should still be available")
            
        except Exception as e:
            self.logger.error(f"Error setting JSON error status: {e}")
    
    def populate_ui(self):
        """Populate the UI with loaded data."""
        if not self.result_data:
            return
        
        try:
            # Update summary
            validation_result = self.result_data.get('validation_result', {})
            is_approved = validation_result.get('is_approved', False)
            issues = validation_result.get('issues', [])
            
            # Determine status text
            if is_approved:
                status = 'APPROVED'
            elif issues:
                status = 'REQUIRES REVIEW'
            else:
                status = 'Unknown'
                
            self.status_label.setText(f"Status: {status}")
            
            # Set status color
            if status == 'APPROVED':
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
            elif status == 'REQUIRES REVIEW':
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
            else:
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
            
            # Update issues
            issues = self.result_data.get('validation_result', {}).get('issues', [])
            self.issues_label.setText(f"Issues: {len(issues)}")
            
            # Update processed time
            completed_at = self.result_data.get('completed_at')
            if completed_at:
                # If it's an ISO string, just show it nicely
                if isinstance(completed_at, str):
                    processed_time = completed_at.replace('T', ' ').split('.')[0]  # Remove microseconds
                else:
                    processed_time = str(completed_at)
            else:
                # Fallback to legacy field name
                processed_time = self.result_data.get('processed_timestamp', 'Unknown')
            
            self.processed_time_label.setText(f"Processed: {processed_time}")
            
            # Populate invoice data
            invoice_data = self.result_data.get('invoice', {})
            self.populate_invoice_tab(invoice_data)
            
            # Populate PO data
            po_data = self.result_data.get('purchase_order', {})
            self.populate_po_tab(po_data)
            
            # Populate items table
            self.populate_items_table()
            
            # Populate validation results
            validation_result = self.result_data.get('validation_result', {})
            self.populate_validation_tab(validation_result)
            
            # Populate raw data
            self.raw_text.setText(json.dumps(self.result_data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Failed to populate UI: {e}")
    
    def format_data_display(self, data: dict[str, Any]) -> str:
        """Format data for display in text widgets."""
        if not data:
            return "No data available"
        
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key.replace('_', ' ').title()}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key.replace('_', ' ').title()}: {sub_value}")
            elif isinstance(value, list):
                lines.append(f"{key.replace('_', ' ').title()}: {len(value)} items")
                for i, item in enumerate(value[:5]):  # Show first 5 items
                    lines.append(f"  {i+1}. {item}")
                if len(value) > 5:
                    lines.append(f"  ... and {len(value) - 5} more items")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(lines)
    
    def format_validation_display(self, validation: dict[str, Any]) -> str:
        """Format validation results for display."""
        if not validation:
            return "No validation data available"
        
        lines = []
        lines.append(f"Approved: {validation.get('is_approved', False)}")
        lines.append(f"Vendor: {validation.get('vendor', 'Unknown')}")
        lines.append("")
        
        # Issues
        issues = validation.get('issues', [])
        if issues:
            lines.append("Issues Found:")
            for i, issue in enumerate(issues, 1):
                lines.append(f"{i}. {issue}")
        else:
            lines.append("No issues found")
        
        lines.append("")
        
        # Notes
        notes = validation.get('notes', [])
        if notes:
            lines.append("Notes:")
            for i, note in enumerate(notes, 1):
                lines.append(f"{i}. {note}")
        
        # Totals
        lines.append("")
        lines.append(f"Total Invoice Amount: ${validation.get('total_invoice_amount', 0.0):.2f}")
        lines.append(f"Total PO Amount: ${validation.get('total_po_amount', 0.0):.2f}")
        
        return "\n".join(lines)
    
    def populate_items_table(self):
        """Populate the items comparison table."""
        try:
            invoice_items = self.result_data.get('invoice', {}).get('items', [])
            po_items = self.result_data.get('purchase_order', {}).get('items', [])
            
            # Create a combined view of items
            all_skus = set()
            for item in invoice_items:
                identifier = item.get('sku') or item.get('vpn') or ''
                if identifier:
                    all_skus.add(identifier)
            for item in po_items:
                identifier = item.get('sku') or item.get('vpn') or ''
                if identifier:
                    all_skus.add(identifier)
            
            self.items_table.setRowCount(len(all_skus))
            
            for row, identifier in enumerate(sorted(all_skus)):
                # Find matching items by SKU or VPN
                inv_item = next((item for item in invoice_items 
                               if item.get('sku') == identifier or item.get('vpn') == identifier), {})
                po_item = next((item for item in po_items 
                              if item.get('sku') == identifier or item.get('vpn') == identifier), {})
                
                # Populate row
                self.items_table.setItem(row, 0, QTableWidgetItem(identifier))
                self.items_table.setItem(row, 1, QTableWidgetItem(
                    inv_item.get('description', po_item.get('description', ''))))
                
                # Use quantity_shipped for invoice, quantity_ordered for PO
                inv_qty = inv_item.get('quantity_shipped') or inv_item.get('quantity_ordered') or 0
                po_qty = po_item.get('quantity_ordered') or 0
                
                self.items_table.setItem(row, 2, QTableWidgetItem(str(inv_qty)))
                self.items_table.setItem(row, 3, QTableWidgetItem(str(po_qty)))
                self.items_table.setItem(row, 4, QTableWidgetItem(f"${inv_item.get('unit_price', 0):.2f}"))
                self.items_table.setItem(row, 5, QTableWidgetItem(f"${po_item.get('unit_price', 0):.2f}"))
                
                # Determine status and issues
                status = "OK"
                issues = []
                
                # Use safe quantity comparisons (handle None values)
                inv_qty = inv_item.get('quantity_shipped') or inv_item.get('quantity_ordered') or 0
                po_qty = po_item.get('quantity_ordered') or 0
                inv_price = inv_item.get('unit_price') or 0
                po_price = po_item.get('unit_price') or 0
                
                if not inv_item and po_item:
                    status = "Missing from Invoice"
                    issues.append("Not shipped")
                elif inv_item and not po_item:
                    status = "Not in PO"
                    issues.append("Extra item")
                elif inv_qty != po_qty:
                    if inv_qty > po_qty:
                        status = "Over-shipped"
                        issues.append(f"Shipped {inv_qty}, ordered {po_qty}")
                    else:
                        status = "Under-shipped"
                        issues.append(f"Shipped {inv_qty}, ordered {po_qty}")
                
                if abs(inv_price - po_price) > 0.01:
                    status = "Price Mismatch"
                    issues.append(f"Price diff: ${abs(inv_price - po_price):.2f}")
                
                self.items_table.setItem(row, 6, QTableWidgetItem(status))
                self.items_table.setItem(row, 7, QTableWidgetItem("; ".join(issues)))
                
                # Color code rows based on status
                if status != "OK":
                    for col in range(8):
                        item = self.items_table.item(row, col)
                        if item:
                            if "Missing" in status or "Not in PO" in status:
                                item.setBackground(QColor(255, 235, 235))  # Light red
                            elif "Mismatch" in status or "Over-shipped" in status:
                                item.setBackground(QColor(255, 245, 235))  # Light orange
                            elif "Under-shipped" in status:
                                item.setBackground(QColor(255, 255, 235))  # Light yellow
                
        except Exception as e:
            self.logger.error(f"Failed to populate items table: {e}")
    
    def load_pdf(self):
        """Load the PDF file if available."""
        try:
            pdf_path = None
            
            # First, try to get PDF path from stored result data (if available)
            if self.result_data:
                pdf_path_str = self.result_data.get('processed_pdf_path') or self.result_data.get('pdf_path')
                if pdf_path_str is not None:
                    pdf_path = Path(pdf_path_str)
                    # If it's relative, make it absolute from workspace root
                    if not pdf_path.is_absolute():
                        workspace_root = Path(__file__).parent.parent.parent
                        pdf_path = workspace_root / pdf_path
            
            # If no PDF path in data (or no data), look for PDF file with same name as result file
            if not pdf_path or not pdf_path.exists():
                # Try common locations for the PDF file
                pdf_candidates = [
                    # Same directory as JSON with same base name
                    self.result_file.parent / f"{self.result_file.stem}.pdf",
                    # Input directory with same name
                    get_project_root() / "data" / "input" / f"{self.result_file.stem}.pdf",
                    # Try to extract original path from result file name pattern
                ]
                
                # If we have result data, try paths from it
                if self.result_data:
                    # Try processed_pdf_path first (this is the stamped PDF)
                    processed_path = self.result_data.get('processed_pdf_path')
                    if processed_path:
                        processed_pdf = Path(processed_path)
                        if not processed_pdf.is_absolute():
                            workspace_root = Path(__file__).parent.parent.parent
                            processed_pdf = workspace_root / processed_path
                        pdf_candidates.insert(0, processed_pdf)
                    
                    # Fall back to original pdf_path if processed doesn't exist
                    original_path = self.result_data.get('pdf_path')
                    if original_path:
                        original_pdf = Path(original_path)
                        if not original_pdf.is_absolute():
                            workspace_root = Path(__file__).parent.parent.parent
                            original_pdf = workspace_root / original_path
                        pdf_candidates.insert(-1, original_pdf)
                
                # Try each candidate path
                for candidate in pdf_candidates:
                    if candidate and candidate.exists():
                        pdf_path = candidate
                        break
            
            # Try to load the PDF
            if pdf_path and pdf_path.exists():
                self.logger.info(f"Loading PDF: {pdf_path}")
                # Only try to load if we have a proper PDF viewer
                if hasattr(self.pdf_viewer, 'load_pdf'):
                    try:
                        self.pdf_viewer.load_pdf(pdf_path)
                    except Exception as load_error:
                        self.logger.error(f"Failed to load PDF file: {load_error}")
                        # Try to show error message if supported
                        if hasattr(self.pdf_viewer, 'show_message'):
                            self.pdf_viewer.show_message(f"Failed to load PDF: {str(load_error)}")
                else:
                    self.logger.warning("PDF viewer does not support loading files")
            else:
                error_msg = f"PDF file not found. Tried: {pdf_path if pdf_path else 'No path available'}"
                self.logger.warning(error_msg)
                # Only show message if viewer supports it
                if hasattr(self.pdf_viewer, 'show_message'):
                    self.pdf_viewer.show_message(error_msg)
                    
        except Exception as e:
            self.logger.error(f"Failed to load PDF: {e}")
            self.pdf_viewer.show_message(f"Error loading PDF: {str(e)}")
    
    def populate_invoice_tab(self, invoice_data: dict[str, Any]) -> None:
        """Populate the invoice tab with structured data."""
        if not invoice_data:
            return
        
        try:
            # Populate header information
            self.invoice_number_label.setText(invoice_data.get('invoice_number', 'N/A'))
            self.invoice_vendor_label.setText(invoice_data.get('vendor', 'N/A'))
            self.invoice_po_ref_label.setText(invoice_data.get('po_number', 'N/A'))
            
            is_credit = invoice_data.get('is_credit_memo', False)
            credit_text = "Yes" if is_credit else "No"
            self.invoice_credit_memo_label.setText(credit_text)
            if is_credit:
                self.invoice_credit_memo_label.setStyleSheet("color: #FF5722; font-weight: bold;")
            
            # Populate items table
            items = invoice_data.get('items', [])
            self.invoice_items_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                # SKU/VPN
                identifier = item.get('sku') or item.get('vpn') or 'N/A'
                self.invoice_items_table.setItem(row, 0, QTableWidgetItem(identifier))
                
                # Description
                desc = item.get('description', 'N/A')
                self.invoice_items_table.setItem(row, 1, QTableWidgetItem(desc))
                
                # Quantities
                qty_ordered = item.get('quantity_ordered', 0)
                qty_shipped = item.get('quantity_shipped', qty_ordered)  # Default to ordered if not specified
                self.invoice_items_table.setItem(row, 2, QTableWidgetItem(str(qty_ordered)))
                self.invoice_items_table.setItem(row, 3, QTableWidgetItem(str(qty_shipped)))
                
                # Prices (handle None values)
                unit_price = item.get('unit_price') or 0.0
                qty_shipped = qty_shipped or 0  # Ensure we don't multiply by None
                total = item.get('total') or (unit_price * qty_shipped)
                self.invoice_items_table.setItem(row, 4, QTableWidgetItem(f"${unit_price:.2f}"))
                self.invoice_items_table.setItem(row, 5, QTableWidgetItem(f"${total:.2f}"))
                
                # Color code fees
                is_fee = item.get('is_fee', False)
                if is_fee:
                    for col in range(6):
                        cell_item = self.invoice_items_table.item(row, col)
                        if cell_item:
                            cell_item.setBackground(QColor(255, 248, 220))  # Light yellow for fees
            
            # Populate extra fees
            extra_fees = invoice_data.get('extra_fees', {})
            if extra_fees:
                fees_text = "\n".join([f"{name}: ${amount:.2f}" for name, amount in extra_fees.items()])
                self.invoice_fees_label.setText(fees_text)
            else:
                self.invoice_fees_label.setText("No extra fees")
                
        except Exception as e:
            self.logger.error(f"Failed to populate invoice tab: {e}")
    
    def populate_po_tab(self, po_data: dict[str, Any]) -> None:
        """Populate the purchase order tab with structured data."""
        if not po_data:
            return
        
        try:
            # Populate header information
            self.po_number_label.setText(po_data.get('po_number', 'N/A'))
            
            # Populate items table
            items = po_data.get('items', [])
            self.po_items_table.setRowCount(len(items))
            
            for row, item in enumerate(items):
                # SKU/VPN
                identifier = item.get('sku') or item.get('vpn') or 'N/A'
                self.po_items_table.setItem(row, 0, QTableWidgetItem(identifier))
                
                # Description
                desc = item.get('description', 'N/A')
                self.po_items_table.setItem(row, 1, QTableWidgetItem(desc))
                
                # Quantity
                qty_ordered = item.get('quantity_ordered') or 0
                self.po_items_table.setItem(row, 2, QTableWidgetItem(str(qty_ordered)))
                
                # Prices (handle None values)
                unit_price = item.get('unit_price') or 0.0
                total = item.get('total') or (unit_price * qty_ordered)
                self.po_items_table.setItem(row, 3, QTableWidgetItem(f"${unit_price:.2f}"))
                self.po_items_table.setItem(row, 4, QTableWidgetItem(f"${total:.2f}"))
                
                # Color code fees
                is_fee = item.get('is_fee', False)
                if is_fee:
                    for col in range(5):
                        cell_item = self.po_items_table.item(row, col)
                        if cell_item:
                            cell_item.setBackground(QColor(255, 248, 220))  # Light yellow for fees
            
            # Populate extra fees
            extra_fees = po_data.get('extra_fees', {})
            if extra_fees:
                fees_text = "\n".join([f"{name}: ${amount:.2f}" for name, amount in extra_fees.items()])
                self.po_fees_label.setText(fees_text)
            else:
                self.po_fees_label.setText("No extra fees")
                
        except Exception as e:
            self.logger.error(f"Failed to populate PO tab: {e}")
    
    def populate_validation_tab(self, validation_data: dict[str, Any]) -> None:
        """Populate the validation tab with structured data."""
        if not validation_data:
            return
        
        try:
            # Populate status information
            is_approved = validation_data.get('is_approved', False)
            approval_text = "✅ APPROVED" if is_approved else "❌ NOT APPROVED"
            approval_color = "#4CAF50" if is_approved else "#F44336"
            
            self.validation_approved_label.setText(approval_text)
            self.validation_approved_label.setStyleSheet(f"color: {approval_color}; font-weight: bold;")
            
            self.validation_vendor_label.setText(validation_data.get('vendor', 'N/A'))
            
            invoice_total = validation_data.get('total_invoice_amount', 0.0)
            po_total = validation_data.get('total_po_amount', 0.0)
            
            self.validation_invoice_total_label.setText(f"${invoice_total:.2f}")
            self.validation_po_total_label.setText(f"${po_total:.2f}")
            
            # Color code totals if they don't match
            if abs(invoice_total - po_total) > 0.01:  # Allow for small rounding differences
                self.validation_invoice_total_label.setStyleSheet("color: #FF9800; font-weight: bold;")
                self.validation_po_total_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                self.validation_invoice_total_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.validation_po_total_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Populate issues table
            issues = validation_data.get('issues', [])
            self.validation_issues_table.setRowCount(len(issues))
            
            for row, issue in enumerate(issues):
                # Issue number
                self.validation_issues_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                
                # Issue description with color coding
                issue_item = QTableWidgetItem(str(issue))
                
                # Color code based on severity (simple heuristic)
                if any(keyword in issue.lower() for keyword in ['error', 'mismatch', 'missing', 'invalid']):
                    issue_item.setBackground(QColor(255, 235, 235))  # Light red for errors
                elif any(keyword in issue.lower() for keyword in ['warning', 'partial', 'difference']):
                    issue_item.setBackground(QColor(255, 248, 220))  # Light yellow for warnings
                
                self.validation_issues_table.setItem(row, 1, issue_item)
            
            # If no issues, show a positive message
            if not issues:
                self.validation_issues_table.setRowCount(1)
                self.validation_issues_table.setItem(0, 0, QTableWidgetItem("✓"))
                success_item = QTableWidgetItem("No validation issues found")
                success_item.setBackground(QColor(235, 255, 235))  # Light green
                self.validation_issues_table.setItem(0, 1, success_item)
            
            # Populate notes table
            notes = validation_data.get('notes', [])
            self.validation_notes_table.setRowCount(len(notes))
            
            for row, note in enumerate(notes):
                # Note number
                self.validation_notes_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                
                # Note description
                self.validation_notes_table.setItem(row, 1, QTableWidgetItem(str(note)))
            
            # If no notes, show a placeholder
            if not notes:
                self.validation_notes_table.setRowCount(1)
                self.validation_notes_table.setItem(0, 0, QTableWidgetItem("-"))
                self.validation_notes_table.setItem(0, 1, QTableWidgetItem("No additional notes"))
                
        except Exception as e:
            self.logger.error(f"Failed to populate validation tab: {e}")
    
    def show_not_implemented_dialog(self, feature_name: str, description: str = ""):
        """Show a dialog for features that are not yet implemented."""
        full_description = f"The '{feature_name}' feature is not implemented yet."
        if description:
            full_description += f"\n\n{description}"
        full_description += "\n\nThis feature may be added in future versions if requested by users."
        
        QMessageBox.information(
            self,
            "Feature Not Implemented",
            full_description
        )
    
    def approve_override(self):
        """Approve the result with override."""
        reply = QMessageBox.question(
            self, 
            "Approve Override",
            "Are you sure you want to approve this invoice with override?\n"
            "This will mark it as approved despite any validation issues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_not_implemented_dialog(
                "Approval Override",
                "This would mark the invoice as approved despite validation issues, move it to the approved folder, and create an audit trail of the manual override decision."
            )
    
    def reject_for_review(self):
        """Reject the result for manual review."""
        reply = QMessageBox.question(
            self, 
            "Reject for Review",
            "Are you sure you want to reject this invoice for manual review?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_not_implemented_dialog(
                "Reject for Review",
                "This would mark the invoice for manual review, move it to the review folder, and create a task for human verification of the validation issues."
            )
    
    def reprocess_file(self):
        """Reprocess the file."""
        reply = QMessageBox.question(
            self, 
            "Reprocess File",
            "Are you sure you want to reprocess this file?\n"
            "This will run the reconciliation again with current settings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_not_implemented_dialog(
                "File Reprocessing",
                "This would reprocess the current invoice file with the latest settings and algorithms, generating a new result while preserving the original for comparison."
            )
    
    def export_results(self):
        """Export the results to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Results",
                f"{self.result_file.stem}_detailed_results.json",
                "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                if filename.endswith('.txt'):
                    # Export as human-readable text
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Invoice Details: {self.result_file.name}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("SUMMARY\n")
                        f.write("-" * 20 + "\n")
                        f.write(f"Status: {self.result_data.get('validation_result', {}).get('overall_status', 'Unknown')}\n")
                        f.write(f"Issues: {len(self.result_data.get('validation_result', {}).get('issues', []))}\n\n")
                        f.write("INVOICE DATA\n")
                        f.write("-" * 20 + "\n")
                        f.write(self.format_data_display(self.result_data.get('invoice_data', {})))
                        f.write("\n\nPURCHASE ORDER DATA\n")
                        f.write("-" * 20 + "\n")
                        f.write(self.format_data_display(self.result_data.get('po_data', {})))
                        f.write("\n\nVALIDATION RESULTS\n")
                        f.write("-" * 20 + "\n")
                        f.write(self.format_validation_display(self.result_data.get('validation_result', {})))
                else:
                    # Export as JSON
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.result_data, f, indent=2)
                
                QMessageBox.information(self, "Export Complete", f"Results exported to:\n{filename}")
                self.logger.info(f"Results exported to: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")
            self.logger.error(f"Failed to export results: {e}")


# Legacy class for backward compatibility
class ResultViewer(ResultDetailViewer):
    """Legacy alias for ResultDetailViewer."""
    pass
