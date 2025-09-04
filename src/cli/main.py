"""
CLI main module using the core engine.

This is a refactored version of the original main.py that uses
the new core business logic modules.
"""

import argparse
import sys
from pathlib import Path

from ..utils import get_timestamp
from ..logging_config import setup_logging, get_module_logger
from ..settings import settings
from ..core import InvoiceReconciliationEngine


def main():
    """Main CLI entry point using the core engine."""
    parser = argparse.ArgumentParser(
        description="Invoice Reconciliator - Process invoices and purchase orders"
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/input/test",
        help="Input directory containing vendor subdirectories (default: data/input)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/output",
        help="Output directory for processed files (default: data/output)"
    )
    
    parser.add_argument(
        "--pdf-file",
        type=str,
        help="Process a single PDF file instead of directories"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--stamp",
        action="store_true",
        help="Enable PDF stamping"
    )

    parser.add_argument(
        "--stamp-pic-name",
        type=str,
        default="Jane Smith",
        help="Name of the person to include in the stamp (default: Jane Smith)"
    )

    parser.add_argument(
        "--stamp-always-accept",
        action="store_true",
        help="Always stamp invoices as accepted"
    )

    parser.add_argument(
        "--stamp-only-approved",
        action="store_true",
        help="Only stamp approved invoices, leave problematic ones unstamped"
    )

    parser.add_argument(
        "--stamp-position",
        type=str,
        default="bottom-right",
        choices=["top-left", "top-right", "bottom-left", "bottom-right"],
        help="Position of the stamp on the PDF (default: bottom-right)"
    )

    args = parser.parse_args()

    # Update settings based on CLI arguments
    settings.enable_stamping = args.stamp
    settings.stamp_pic_name = args.stamp_pic_name
    settings.stamp_always_accept = args.stamp_always_accept
    settings.stamp_only_approved = args.stamp_only_approved
    settings.stamp_position = args.stamp_position

    # Set up logging
    logger = setup_logging(
        log_level=args.log_level,
        console_output=True,
        is_test=False
    )
    
    logger.info("=== Invoice Reconciliator Started ===")
    logger.info(f"Using LLM Model: {settings.llm_model}")
    logger.info(f"LLM Provider URL: {settings.llm_base_url}")
    logger.info(f"PDF Stamping: {'Enabled' if settings.enable_stamping else 'Disabled'}")
    
    # Create engine
    try:
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir) / get_timestamp()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize engine
        engine = InvoiceReconciliationEngine(output_dir)
        engine.initialize()

        try:
            if args.pdf_file:
                # Process single file
                pdf_file = Path(args.pdf_file)
                logger.info(f"Processing single PDF file: {pdf_file}")
                
                result = engine.process_single_file(pdf_file)
                
                if result.status.value == "completed":
                    logger.info("PDF processing completed successfully")
                    logger.info(f"Result: {result.approval_status}")
                    if result.validation_result and result.validation_result.issues:
                        logger.info("Issues found:")
                        for issue in result.validation_result.issues:
                            logger.info(f"  - {issue}")
                else:
                    logger.error(f"PDF processing failed: {result.error_message}")
                    sys.exit(1)
                    
            else:
                # Process directory of PDF files
                logger.info(f"Processing directory: {input_dir}")
                
                # Start workflow
                workflow = engine.start_workflow(input_dir)
                logger.info(f"Started workflow with {workflow.total_files} files")
                
                # Process all files
                engine.process_workflow()
                
                # Show results
                summary = workflow.get_summary()
                logger.info("=== Processing Summary ===")
                logger.info(f"Total files: {summary['total_files']}")
                logger.info(f"Completed: {summary['completed_files']}")
                logger.info(f"Failed: {summary['failed_files']}")
                logger.info(f"Success rate: {summary['success_rate']:.1f}%")
                
                if summary['processing_time_seconds']:
                    logger.info(f"Processing time: {summary['processing_time_seconds']:.1f} seconds")
                
                # Show individual results
                results = engine.get_workflow_results()
                for result in results:
                    if result.status.value == "completed":
                        logger.info(f"✓ {result.pdf_path.name} - {result.approval_status}")
                    else:
                        logger.error(f"✗ {result.pdf_path.name} - {result.error_message}")

        finally:
            engine.cleanup()
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        if 'engine' in locals():
            engine.cancel_workflow()
            engine.cleanup()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        if 'engine' in locals():
            engine.cleanup()
        sys.exit(1)
    
    logger.info("=== Invoice Reconciliator Completed ===")


if __name__ == "__main__":
    main()
