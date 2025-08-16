"""
Test structured output capabilities of the LLM extractor.
Uses centralized logging configuration for tests.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging_config import setup_logging, get_module_logger
from src.settings import settings
from src.llm_extractor import LLMExtractor


def test_structured_output():
    """Test the structured output functionality"""
    # Set up test logging (separate from main app)
    setup_logging(
        log_level="DEBUG",
        console_output=True,
        is_test=True
    )
    
    test_logger = get_module_logger('test_structured_output')
    test_logger.info("=== Testing Structured Output Support ===")
    test_logger.info(f"Using model: {settings.llm_model}")
    test_logger.info(f"Provider URL: {settings.llm_base_url}")
    
    # Initialize extractor
    extractor = LLMExtractor()
    
    # Test structured output support
    test_logger.info("Testing structured output support...")
    supports_structured = extractor.test_structured_output_support()
    test_logger.info(f"Structured output supported: {supports_structured}")
    
    # Test with sample data
    sample_text = """
    INVOICE
    Invoice Number: INV-2024-001
    PO Number: PO-2024-001
    
    Item: Widget A
    SKU: WID-001
    Quantity Ordered: 10
    Quantity Shipped: 8
    Unit Price: $15.99
    
    PURCHASE ORDER
    PO Number: PO-2024-001
    
    Item: Widget A
    SKU: WID-001
    Quantity Ordered: 10
    Unit Price: $15.99
    """
    
    test_logger.info("Testing data extraction with sample text...")
    result = extractor.extract_invoice_data(sample_text)

    if result and any(result):
        test_logger.info("✅ Extraction successful")
        test_logger.info(f"Result type: {type(result)}")
        test_logger.debug(f"Raw result: {result}")
    else:
        test_logger.error("❌ Extraction failed")
    
    test_logger.info("=== Test Completed ===")


if __name__ == "__main__":
    test_structured_output()
