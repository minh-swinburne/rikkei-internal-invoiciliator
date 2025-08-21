"""
Result viewer dialog for detailed invoice reconciliation results.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QSplitter, QTabWidget, QWidget, QScrollArea, QMessageBox,
    QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon

from ..logging_config import get_module_logger
from .pdf_viewer import PDFViewer
from .native_pdf_viewer import NativePDFViewer


class ResultDetailViewer(QDialog):
    """Dialog for viewing detailed reconciliation results."""
    
    def __init__(self, result_file: Path, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.result_viewer')
        self.result_file = result_file
        self.result_data: Optional[Dict[str, Any]] = None
        
        self.setWindowTitle(f"Invoice Details: {result_file.stem}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.load_result_data()
    
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
            self.pdf_viewer = PDFViewer()
        
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
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.invoice_details = QTextEdit()
        self.invoice_details.setReadOnly(True)
        self.invoice_details.setFont(QFont("Consolas", 10))
        scroll_layout.addWidget(self.invoice_details)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return widget
    
    def create_po_tab(self) -> QWidget:
        """Create the purchase order data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.po_details = QTextEdit()
        self.po_details.setReadOnly(True)
        self.po_details.setFont(QFont("Consolas", 10))
        scroll_layout.addWidget(self.po_details)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.items_table)
        return widget
    
    def create_validation_tab(self) -> QWidget:
        """Create the validation results tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.validation_text)
        
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
                with open(self.result_file, 'r', encoding='utf-8') as f:
                    self.result_data = json.load(f)
                
                self.populate_ui()
                self.load_pdf()
            else:
                QMessageBox.warning(self, "File Not Found", f"Result file not found:\n{self.result_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to load result data: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load result data:\n{str(e)}")
    
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
            processed_time = self.result_data.get('processed_timestamp', 'Unknown')
            self.processed_time_label.setText(f"Processed: {processed_time}")
            
            # Populate invoice data
            invoice_data = self.result_data.get('invoice_data', {})
            self.invoice_details.setText(self.format_data_display(invoice_data))
            
            # Populate PO data
            po_data = self.result_data.get('po_data', {})
            self.po_details.setText(self.format_data_display(po_data))
            
            # Populate items table
            self.populate_items_table()
            
            # Populate validation results
            validation_result = self.result_data.get('validation_result', {})
            self.validation_text.setText(self.format_validation_display(validation_result))
            
            # Populate raw data
            self.raw_text.setText(json.dumps(self.result_data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Failed to populate UI: {e}")
    
    def format_data_display(self, data: Dict[str, Any]) -> str:
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
    
    def format_validation_display(self, validation: Dict[str, Any]) -> str:
        """Format validation results for display."""
        if not validation:
            return "No validation data available"
        
        lines = []
        lines.append(f"Overall Status: {validation.get('overall_status', 'Unknown')}")
        lines.append(f"Processing Success: {validation.get('processing_success', False)}")
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
        
        return "\n".join(lines)
    
    def populate_items_table(self):
        """Populate the items comparison table."""
        try:
            invoice_items = self.result_data.get('invoice_data', {}).get('items', [])
            po_items = self.result_data.get('po_data', {}).get('items', [])
            
            # Create a combined view of items
            all_skus = set()
            for item in invoice_items:
                all_skus.add(item.get('sku') or item.get('vpn', ''))
            for item in po_items:
                all_skus.add(item.get('sku') or item.get('vpn', ''))
            
            self.items_table.setRowCount(len(all_skus))
            
            for row, sku in enumerate(sorted(all_skus)):
                # Find matching items
                inv_item = next((item for item in invoice_items if item.get('sku') == sku or item.get('vpn') == sku), {})
                po_item = next((item for item in po_items if item.get('sku') == sku or item.get('vpn') == sku), {})
                
                # Populate row
                self.items_table.setItem(row, 0, QTableWidgetItem(sku))
                self.items_table.setItem(row, 1, QTableWidgetItem(inv_item.get('description', po_item.get('description', ''))))
                self.items_table.setItem(row, 2, QTableWidgetItem(str(inv_item.get('quantity', 0))))
                self.items_table.setItem(row, 3, QTableWidgetItem(str(po_item.get('quantity', 0))))
                self.items_table.setItem(row, 4, QTableWidgetItem(f"${inv_item.get('unit_price', 0):.2f}"))
                self.items_table.setItem(row, 5, QTableWidgetItem(f"${po_item.get('unit_price', 0):.2f}"))
                
                # Determine status and issues
                status = "OK"
                issues = []
                
                inv_qty = inv_item.get('quantity', 0)
                po_qty = po_item.get('quantity', 0)
                inv_price = inv_item.get('unit_price', 0)
                po_price = po_item.get('unit_price', 0)
                
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
            
            # First, try to get PDF path from stored result data
            if self.result_data and 'pdf_path' in self.result_data:
                pdf_path = Path(self.result_data['pdf_path'])
                # If it's relative, make it absolute from workspace root
                if not pdf_path.is_absolute():
                    workspace_root = Path(__file__).parent.parent.parent
                    pdf_path = workspace_root / pdf_path
            
            # If no PDF path in data, look for PDF file with same name as result file
            if not pdf_path or not pdf_path.exists():
                pdf_path = self.result_file.parent / f"{self.result_file.stem}.pdf"
            
            # If still not found, try input file path
            if not pdf_path.exists() and self.result_data:
                input_path = self.result_data.get('input_file_path')
                if input_path:
                    input_pdf = Path(input_path)
                    if not input_pdf.is_absolute():
                        workspace_root = Path(__file__).parent.parent.parent
                        input_pdf = workspace_root / input_pdf
                    if input_pdf.exists():
                        pdf_path = input_pdf
            
            # Try to load the PDF
            if pdf_path and pdf_path.exists():
                self.logger.info(f"Loading PDF: {pdf_path}")
                self.pdf_viewer.load_pdf(pdf_path)
            else:
                error_msg = f"PDF file not found. Tried: {pdf_path if pdf_path else 'No path available'}"
                self.logger.warning(error_msg)
                self.pdf_viewer.show_message(error_msg)
                    
        except Exception as e:
            self.logger.error(f"Failed to load PDF: {e}")
            self.pdf_viewer.show_message(f"Error loading PDF: {str(e)}")
    
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
            # TODO: Implement approval logic
            QMessageBox.information(self, "Approved", "Invoice approved with override.")
            self.logger.info(f"Invoice approved with override: {self.result_file.name}")
    
    def reject_for_review(self):
        """Reject the result for manual review."""
        reply = QMessageBox.question(
            self, 
            "Reject for Review",
            "Are you sure you want to reject this invoice for manual review?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement rejection logic
            QMessageBox.information(self, "Rejected", "Invoice marked for manual review.")
            self.logger.info(f"Invoice rejected for review: {self.result_file.name}")
    
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
            # TODO: Implement reprocessing logic
            QMessageBox.information(self, "Reprocessing", "File queued for reprocessing.")
            self.logger.info(f"File queued for reprocessing: {self.result_file.name}")
    
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
