#!/usr/bin/env python3
"""
Invoice Reconciliation Tool
Main entry point for the application.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pdf_processor import PDFProcessor
from src.llm_extractor import LLMExtractor
from src.validator import validate_invoice_po
from src.file_manager import FileManager
from src.models import Invoice, PurchaseOrder, Item
from src.logging_config import setup_logging

def process_pdf_file(pdf_path: str, vendor: str, approved_dir: str, review_dir: str, 
                     stamp_all: bool = True, temp_dir: str = "./temp") -> dict[str, any]:
    """Process a single PDF file through the reconciliation pipeline."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        pdf_processor = PDFProcessor()
        llm_extractor = LLMExtractor()
        file_manager = FileManager(approved_dir, review_dir)
        
        # Create a temporary copy for processing
        temp_pdf_path = file_manager.copy_file_for_processing(pdf_path, temp_dir, vendor)
        
        # Extract text from PDF
        logger.info(f"Processing PDF: {pdf_path} (Vendor: {vendor})")
        pdf_processor.load(temp_pdf_path)
        text = pdf_processor.extract_text()
        pdf_processor.close()
        
        if not text:
            logger.error(f"Failed to extract text from {pdf_path}")
            result = {"filename": os.path.basename(pdf_path), "vendor": vendor, 
                     "approved": False, "reason": "Text extraction failed"}
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, "MANUAL REVIEW - TEXT EXTRACTION FAILED")
            file_manager.move_file(temp_pdf_path, False, vendor)
            return result
        
        # Extract structured data using LLM
        extracted_data = llm_extractor.extract_invoice_data(text)
        if not extracted_data:
            logger.error(f"Failed to extract structured data from {pdf_path}")
            result = {"filename": os.path.basename(pdf_path), "vendor": vendor,
                     "approved": False, "reason": "LLM extraction failed"}
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, "MANUAL REVIEW - LLM EXTRACTION FAILED")
            file_manager.move_file(temp_pdf_path, False, vendor)
            return result
        
        # Convert to Pydantic models
        try:
            invoice_data = extracted_data.get("invoice", {})
            po_data = extracted_data.get("purchase_order", {})
            
            # Create Invoice object using Pydantic
            invoice = Invoice(
                invoice_number=invoice_data.get("invoice_number", ""),
                po_number=invoice_data.get("po_number", ""),
                items=[
                    Item(**item) for item in invoice_data.get("items", [])
                ],
                extra_fees=invoice_data.get("extra_fees", {}),
                is_credit_memo=invoice_data.get("is_credit_memo", False)
            )
            
            # Create PurchaseOrder object using Pydantic
            purchase_order = PurchaseOrder(
                po_number=po_data.get("po_number", ""),
                items=[
                    Item(**item) for item in po_data.get("items", [])
                ],
                extra_fees=po_data.get("extra_fees", {})
            )
            
            logger.info(f"Successfully created models - Invoice: {invoice.invoice_number}, PO: {purchase_order.po_number}")
            
        except Exception as e:
            logger.error(f"Failed to create Pydantic models from extracted data: {e}")
            result = {"filename": os.path.basename(pdf_path), "vendor": vendor,
                     "approved": False, "reason": f"Model validation failed: {str(e)}"}
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, "MANUAL REVIEW - MODEL VALIDATION FAILED")
            file_manager.move_file(temp_pdf_path, False, vendor)
            return result
        
        # Validate invoice against purchase order
        validation_result = validate_invoice_po(invoice, purchase_order)
        
        # Process based on validation result
        if validation_result.approved:
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, "AUTO-APPROVED")
            final_path = file_manager.move_file(temp_pdf_path, True, vendor)
            logger.info(f"Invoice approved and moved to: {final_path}")
        else:
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, f"MANUAL REVIEW - {validation_result.reason}")
            final_path = file_manager.move_file(temp_pdf_path, False, vendor)
            logger.info(f"Invoice requires manual review: {final_path}")
        
        return {
            "filename": os.path.basename(pdf_path),
            "vendor": vendor,
            "approved": validation_result.approved,
            "reason": validation_result.reason,
            "manual_review": validation_result.manual_review,
            "details": getattr(validation_result, 'details', None)
        }
        
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        result = {"filename": os.path.basename(pdf_path), "vendor": vendor,
                 "approved": False, "reason": f"Processing error: {str(e)}"}
        
        # Try to stamp and move the file even if processing failed
        try:
            temp_pdf_path = file_manager.copy_file_for_processing(pdf_path, temp_dir, vendor)
            if stamp_all:
                file_manager.stamp_pdf(temp_pdf_path, f"MANUAL REVIEW - PROCESSING ERROR")
            file_manager.move_file(temp_pdf_path, False, vendor)
        except Exception as move_error:
            logger.error(f"Failed to handle error file {pdf_path}: {move_error}")
            
        return result

def discover_vendor_files(input_base_dir: str) -> dict[str, list[str]]:
    """Discover PDF files organized by vendor subdirectories"""
    vendor_files = {}
    input_path = Path(input_base_dir)
    
    if not input_path.exists():
        return vendor_files
        
    # Look for vendor subdirectories
    for vendor_dir in input_path.iterdir():
        if vendor_dir.is_dir():
            vendor_name = vendor_dir.name
            pdf_files = list(vendor_dir.glob("*.pdf"))
            if pdf_files:
                vendor_files[vendor_name] = [str(f) for f in pdf_files]
                
    # Also check for PDFs directly in the input directory (no vendor specified)
    direct_pdfs = list(input_path.glob("*.pdf"))
    if direct_pdfs:
        vendor_files["unknown"] = [str(f) for f in direct_pdfs]
        
    return vendor_files

def process_vendor_files(vendor_files: dict[str, list[str]], approved_dir: str, 
                        review_dir: str, stamp_all: bool = True) -> list[dict]:
    """Process all vendor files"""
    logger = logging.getLogger(__name__)
    all_results = []
    
    for vendor, files in vendor_files.items():
        logger.info(f"\n{'='*20} Processing {vendor.upper()} files {'='*20}")
        logger.info(f"Found {len(files)} files for vendor: {vendor}")
        
        for pdf_file in files:
            result = process_pdf_file(pdf_file, vendor, approved_dir, review_dir, stamp_all)
            all_results.append(result)
            
    return all_results

def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Invoice Reconciliation Tool - Process invoices and purchase orders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Process data/input/ to data/output/
  python main.py --input ./invoices --output ./processed
  python main.py --no-stamp                        # Don't stamp PDFs
  python main.py --vendor ingram                   # Process only Ingram files
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        default="./data/input",
        help="Input directory containing vendor subdirectories with PDF files (default: ./data/input)"
    )
    
    parser.add_argument(
        "--output", "-o", 
        default="./data/output",
        help="Output base directory (default: ./data/output)"
    )
    
    parser.add_argument(
        "--vendor", "-v",
        help="Process only files from specific vendor (e.g., 'ingram', 'td_synnex')"
    )
    
    parser.add_argument(
        "--no-stamp",
        action="store_true",
        help="Skip PDF stamping (useful for testing)"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true", 
        help="Launch GUI mode (not yet implemented)"
    )
    
    parser.add_argument(
        "--verbose", "-vv",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser

def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(override=True)

    # Setup proper logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(name="invoice_reconciliation", level=log_level)
    
    logger.info("Invoice Reconciliation Tool starting...")
    logger.info(f"Arguments: {vars(args)}")
    
    # Handle GUI mode (placeholder for future implementation)
    if args.gui:
        logger.info("GUI mode requested but not yet implemented")
        print("GUI mode is not yet implemented. Use CLI mode for now.")
        return
    
    # Setup directories
    input_dir = args.input
    output_base = args.output
    approved_dir = os.path.join(output_base, "approved")
    review_dir = os.path.join(output_base, "review")
    temp_dir = os.path.join(output_base, "temp")
    
    # Create output directories
    os.makedirs(approved_dir, exist_ok=True)
    os.makedirs(review_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_base}")
    logger.info(f"Stamping enabled: {not args.no_stamp}")
    
    # Discover vendor files
    vendor_files = discover_vendor_files(input_dir)
    
    if not vendor_files:
        logger.warning(f"No PDF files found in {input_dir}")
        print(f"No PDF files found in {input_dir}")
        print("Make sure your PDFs are in vendor subdirectories like:")
        print("  data/input/ingram/invoice1.pdf")
        print("  data/input/td_synnex/invoice2.pdf")
        return
    
    # Filter by vendor if specified
    if args.vendor:
        if args.vendor in vendor_files:
            vendor_files = {args.vendor: vendor_files[args.vendor]}
            logger.info(f"Processing only vendor: {args.vendor}")
        else:
            logger.error(f"Vendor '{args.vendor}' not found. Available vendors: {list(vendor_files.keys())}")
            return
    
    # Display discovered files
    total_files = sum(len(files) for files in vendor_files.values())
    logger.info(f"Discovered {total_files} PDF files from {len(vendor_files)} vendors:")
    for vendor, files in vendor_files.items():
        logger.info(f"  {vendor}: {len(files)} files")
    
    # Process all files
    stamp_all = not args.no_stamp
    results = process_vendor_files(vendor_files, approved_dir, review_dir, stamp_all)
    
    # Generate summary report
    approved_count = sum(1 for r in results if r["approved"])
    manual_count = len(results) - approved_count
    
    print("\n" + "="*60)
    print("RECONCILIATION SUMMARY")
    print("="*60)
    print(f"Total processed: {len(results)}")
    print(f"Auto-approved: {approved_count}")
    print(f"Manual review required: {manual_count}")
    print("\nResults by vendor:")
    
    # Group results by vendor
    vendor_summary = {}
    for result in results:
        vendor = result["vendor"]
        if vendor not in vendor_summary:
            vendor_summary[vendor] = {"approved": 0, "manual": 0, "files": []}
        if result["approved"]:
            vendor_summary[vendor]["approved"] += 1
        else:
            vendor_summary[vendor]["manual"] += 1
        vendor_summary[vendor]["files"].append(result)
    
    for vendor, summary in vendor_summary.items():
        print(f"\n{vendor.upper()}:")
        print(f"  Approved: {summary['approved']}")
        print(f"  Manual Review: {summary['manual']}")
        for result in summary["files"]:
            status = "✓ APPROVED" if result["approved"] else "⚠ MANUAL REVIEW"
            print(f"    {result['filename']}: {status} - {result['reason']}")
    
    # Cleanup temporary directory
    try:
        import shutil
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary files")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp directory: {e}")
    
    logger.info("Processing complete!")

if __name__ == "__main__":
    main()
