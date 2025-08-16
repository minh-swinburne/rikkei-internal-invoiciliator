"""
Main CLI application for invoice reconciliation.
Uses provider-agnostic configuration and centralized logging.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.logging_config import setup_logging, get_module_logger
from src.settings import settings
from src.pdf_processor import PDFProcessor
from src.llm_extractor import LLMExtractor
from src.validator import InvoiceValidator
from src.file_manager import FileManager
from src.models import Invoice, PurchaseOrder


def process_single_pdf(
    pdf_path: str,
    vendor: Optional[str] = None,
    output_dir: str = "data/output"
) -> bool:
    """
    Process a single PDF file for invoice reconciliation.
    
    Args:
        pdf_path: Path to the PDF file to process
        vendor: Optional vendor identifier
        output_dir: Output directory for processed files
        
    Returns:
        True if processing succeeded, False otherwise
    """
    logger = get_module_logger('main')
    logger.info(f"Processing PDF: {pdf_path}")
    
    try:
        # Initialize processors
        pdf_processor = PDFProcessor()
        llm_extractor = LLMExtractor()
        validator = InvoiceValidator()
        file_manager = FileManager(output_dir)
        
        # Extract text from PDF
        logger.info("Extracting text from PDF")
        text = pdf_processor.extract_text(pdf_path)
        
        if not text.strip():
            logger.error("No text extracted from PDF")
            return False
        
        logger.info(f"Extracted {len(text)} characters of text")
        
        # Extract structured data using LLM
        logger.info("Extracting invoice and PO data using LLM")
        invoice, purchase_order = llm_extractor.extract_invoice_data(text)
        
        if not invoice or not purchase_order:
            logger.error("Failed to extract invoice or purchase order data")
            return False
        
        logger.info(f"Successfully extracted invoice {invoice.invoice_number} and PO {purchase_order.po_number}")
        
        # Validate the data
        logger.info("Validating invoice against purchase order")
        validation_result = validator.validate(invoice, purchase_order)
        
        # Determine processing status
        status = "APPROVED" if validation_result.is_approved else "REQUIRES REVIEW"
        logger.info(f"Validation result: {status}")
        
        if validation_result.issues:
            logger.info(f"Validation issues found:")
            for issue in validation_result.issues:
                logger.info(f"  - {issue}")
        
        # Stamp and file the PDF
        logger.info(f"Processing PDF with status: {status}")
        final_path = file_manager.stamp_pdf(pdf_path, status)
        
        logger.info(f"Successfully processed PDF: {final_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
        return False


def process_vendor_directory(
    vendor: str,
    input_dir: str = "data/input",
    output_dir: str = "data/output"
) -> None:
    """
    Process all PDF files in a vendor-specific directory.
    
    Args:
        vendor: Vendor identifier (subdirectory name)
        input_dir: Base input directory
        output_dir: Output directory for processed files
    """
    logger = get_module_logger('main')
    vendor_dir = Path(input_dir) / vendor
    
    if not vendor_dir.exists():
        logger.error(f"Vendor directory does not exist: {vendor_dir}")
        return
    
    pdf_files = list(vendor_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {vendor_dir}")
        return
    
    logger.info(f"Processing {len(pdf_files)} PDF files for vendor: {vendor}")
    
    success_count = 0
    for pdf_file in pdf_files:
        logger.info(f"Processing file {pdf_file.name}")
        if process_single_pdf(str(pdf_file), vendor, output_dir):
            success_count += 1
        else:
            logger.error(f"Failed to process {pdf_file.name}")
    
    logger.info(f"Processed {success_count}/{len(pdf_files)} files successfully for vendor {vendor}")


def process_all_vendors(
    input_dir: str = "data/input",
    output_dir: str = "data/output"
) -> None:
    """
    Process PDF files for all vendors.
    
    Args:
        input_dir: Base input directory
        output_dir: Output directory for processed files
    """
    logger = get_module_logger('main')
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    # Find all vendor subdirectories
    vendor_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    if not vendor_dirs:
        logger.warning(f"No vendor directories found in {input_dir}")
        return
    
    logger.info(f"Found {len(vendor_dirs)} vendor directories")
    
    for vendor_dir in vendor_dirs:
        vendor_name = vendor_dir.name
        logger.info(f"Processing vendor directory: {vendor_name}")
        process_vendor_directory(vendor_name, input_dir, output_dir)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Invoice Reconciliation Tool - Process invoices and purchase orders"
    )
    
    parser.add_argument(
        "--vendor",
        type=str,
        help="Specific vendor to process (e.g., 'ingram', 'td-synnex')"
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/input",
        help="Input directory containing vendor subdirectories (default: data/input)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/output",
        help="Output directory for processed files (default: data/output)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--pdf-file",
        type=str,
        help="Process a single PDF file instead of directories"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(
        log_level=args.log_level,
        console_output=True,
        is_test=False
    )
    
    logger.info("=== Invoice Reconciliation Tool Started ===")
    logger.info(f"Using LLM Model: {settings.llm_model}")
    logger.info(f"LLM Provider URL: {settings.llm_base_url}")
    logger.info(f"PDF Stamping: {'Enabled' if settings.enable_pdf_stamping else 'Disabled'}")
    
    try:
        if args.pdf_file:
            # Process single file
            logger.info(f"Processing single PDF file: {args.pdf_file}")
            success = process_single_pdf(args.pdf_file, args.vendor, args.output_dir)
            if success:
                logger.info("PDF processing completed successfully")
            else:
                logger.error("PDF processing failed")
                sys.exit(1)
                
        elif args.vendor:
            # Process specific vendor
            logger.info(f"Processing vendor: {args.vendor}")
            process_vendor_directory(args.vendor, args.input_dir, args.output_dir)
            
        else:
            # Process all vendors
            logger.info("Processing all vendors")
            process_all_vendors(args.input_dir, args.output_dir)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)
    
    logger.info("=== Invoice Reconciliation Tool Completed ===")


if __name__ == "__main__":
    main()
