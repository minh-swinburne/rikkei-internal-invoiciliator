#!/usr/bin/env python3
"""
Test script to check if the current OpenRouter model supports structured outputs.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logging_config import setup_logging
from src.llm_extractor import LLMExtractor

def test_model_capabilities():
    """Test the current model's capabilities"""
    load_dotenv(override=True)
    
    # Setup logging
    logger = setup_logging("test_structured_output", logging.DEBUG)
    
    # Get configuration
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    print("="*60)
    print("OPENROUTER MODEL CAPABILITY TEST")
    print("="*60)
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print(f"API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print()
    
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        logger.error("OPENROUTER_API_KEY not found in .env file")
        return False
    
    # Initialize extractor
    try:
        extractor = LLMExtractor()
        print("✓ LLM Extractor initialized successfully")
        logger.info("LLM Extractor initialized successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize LLM Extractor: {e}")
        logger.error(f"Failed to initialize LLM Extractor: {e}")
        return False
    
    # Test structured output support
    print("\n" + "-"*40)
    print("TESTING STRUCTURED OUTPUT SUPPORT")
    print("-"*40)
    
    try:
        logger.info("Starting structured output support test")
        supports_structured = extractor.test_structured_output_support()
        
        if supports_structured:
            print("✅ SUCCESS: Model supports structured output (response_format)")
            print("   → Will use structured JSON schema for extraction")
            logger.info("Model supports structured output")
        else:
            print("⚠️  WARNING: Model does not support structured output")
            print("   → Will fallback to plain text mode with JSON parsing")
            logger.warning("Model does not support structured output")
            
        return supports_structured
        
    except Exception as e:
        print(f"❌ ERROR: Failed to test structured output: {e}")
        logger.error(f"Failed to test structured output: {e}")
        return False

def test_basic_extraction():
    """Test basic extraction capability with sample invoice text"""
    logger = logging.getLogger()
    
    print("\n" + "-"*40)
    print("TESTING BASIC EXTRACTION")
    print("-"*40)
    
    sample_text = """
    INVOICE #INV-2024-001
    Purchase Order: PO-12345
    
    Item Details:
    SKU: ABC123
    Description: Sample Product
    Quantity Ordered: 10
    Quantity Shipped: 8
    Unit Price: $25.00
    Total: $200.00
    
    Invoice Total: $200.00
    
    PURCHASE ORDER #PO-12345
    Item Details:
    SKU: ABC123
    Description: Sample Product  
    Quantity Ordered: 10
    Unit Price: $25.00
    Total: $250.00
    """
    
    try:
        extractor = LLMExtractor()
        logger.info("Starting basic extraction test")
        logger.debug(f"Sample text length: {len(sample_text)} characters")
        
        result = extractor.extract_invoice_data(sample_text)
        
        if result:
            print("✅ SUCCESS: Basic extraction completed")
            
            # Extract data safely
            invoice_data = result.get('invoice', {})
            po_data = result.get('purchase_order', {})
            
            invoice_number = invoice_data.get('invoice_number', 'N/A')
            po_number = invoice_data.get('po_number', 'N/A')
            invoice_items = len(invoice_data.get('items', []))
            po_items = len(po_data.get('items', []))
            
            print(f"   → Invoice Number: {invoice_number}")
            print(f"   → PO Number: {po_number}")
            print(f"   → Invoice Items Found: {invoice_items}")
            print(f"   → PO Items Found: {po_items}")
            
            logger.info(f"Extraction successful - Invoice: {invoice_number}, PO: {po_number}")
            logger.debug(f"Full result: {result}")
            
            return True
        else:
            print("❌ ERROR: Extraction returned None")
            logger.error("Extraction returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Basic extraction failed: {e}")
        logger.error(f"Basic extraction failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting OpenRouter model capability tests...\n")
    
    # Test 1: Model capabilities
    structured_support = test_model_capabilities()
    
    # Test 2: Basic extraction
    extraction_works = test_basic_extraction()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Structured Output Support: {'✅ YES' if structured_support else '⚠️  NO (fallback mode)'}")
    print(f"Basic Extraction Working: {'✅ YES' if extraction_works else '❌ NO'}")
    
    if structured_support and extraction_works:
        print("\n🎉 All tests passed! Your model is ready for invoice reconciliation.")
    elif extraction_works:
        print("\n⚠️  Model works but will use fallback mode (slower, less reliable).")
    else:
        print("\n❌ Model is not working. Please check your API key and model configuration.")
        
    print("\nModel recommendations:")
    print("✅ Best: google/gemini-2.0-flash-exp:free (supports structured output)")
    print("✅ Good: anthropic/claude-3-haiku (reliable, fast)")
    print("⚠️  OK: openai/gpt-3.5-turbo (fallback mode)")
    
    # Get logger for final message
    logger = logging.getLogger()
    logger.info("Test completed")

if __name__ == "__main__":
    main()

def test_model_capabilities():
    """Test the current model's capabilities"""
    load_dotenv(override=True)
    
    # Get configuration
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    print("="*60)
    print("OPENROUTER MODEL CAPABILITY TEST")
    print("="*60)
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print(f"API Key: {'✓ Set' if api_key else '✗ Missing'}")
    print()
    
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        return False
    
    # Initialize extractor
    try:
        extractor = LLMExtractor()
        print("✓ LLM Extractor initialized successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize LLM Extractor: {e}")
        return False
    
    # Test structured output support
    print("\n" + "-"*40)
    print("TESTING STRUCTURED OUTPUT SUPPORT")
    print("-"*40)
    
    try:
        supports_structured = extractor.test_structured_output_support()
        
        if supports_structured:
            print("✅ SUCCESS: Model supports structured output (response_format)")
            print("   → Will use structured JSON schema for extraction")
        else:
            print("⚠️  WARNING: Model does not support structured output")
            print("   → Will fallback to plain text mode with JSON parsing")
            
        return supports_structured
        
    except Exception as e:
        print(f"❌ ERROR: Failed to test structured output: {e}")
        return False

def test_basic_extraction():
    """Test basic extraction capability with sample invoice text"""
    print("\n" + "-"*40)
    print("TESTING BASIC EXTRACTION")
    print("-"*40)
    
    sample_text = """
    INVOICE #INV-2024-001
    Purchase Order: PO-12345
    
    Item Details:
    SKU: ABC123
    Description: Sample Product
    Quantity Ordered: 10
    Quantity Shipped: 8
    Unit Price: $25.00
    Total: $200.00
    
    Invoice Total: $200.00
    """
    
    try:
        extractor = LLMExtractor()
        result = extractor.extract_invoice_data(sample_text)
        
        if result:
            print("✅ SUCCESS: Basic extraction completed")
            print(f"   → Invoice Number: {result.get('invoice', {}).get('invoice_number', 'N/A')}")
            print(f"   → PO Number: {result.get('invoice', {}).get('po_number', 'N/A')}")
            print(f"   → Items Found: {len(result.get('invoice', {}).get('items', []))}")
            return True
        else:
            print("❌ ERROR: Extraction returned None")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Basic extraction failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting OpenRouter model capability tests...\n")
    
    # Test 1: Model capabilities
    structured_support = test_model_capabilities()
    
    # Test 2: Basic extraction
    extraction_works = test_basic_extraction()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Structured Output Support: {'✅ YES' if structured_support else '⚠️  NO (fallback mode)'}")
    print(f"Basic Extraction Working: {'✅ YES' if extraction_works else '❌ NO'}")
    
    if structured_support and extraction_works:
        print("\n🎉 All tests passed! Your model is ready for invoice reconciliation.")
    elif extraction_works:
        print("\n⚠️  Model works but will use fallback mode (slower, less reliable).")
    else:
        print("\n❌ Model is not working. Please check your API key and model configuration.")
        
    print("\nModel recommendations:")
    print("✅ Best: google/gemini-2.0-flash-exp:free (supports structured output)")
    print("✅ Good: anthropic/claude-3-haiku (reliable, fast)")
    print("⚠️  OK: openai/gpt-3.5-turbo (fallback mode)")

if __name__ == "__main__":
    main()
