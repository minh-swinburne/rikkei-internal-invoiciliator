"""
Test script to verify the core engine works correctly.
"""

from pathlib import Path
from src.core import InvoiceReconciliationEngine
from src.logging_config import setup_logging

def test_engine():
    """Test the core engine initialization."""
    # Set up logging
    setup_logging(log_level="INFO", console_output=True, is_test=True)
    
    # Create a test output directory
    output_dir = Path("data/output/test_engine")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = InvoiceReconciliationEngine(output_dir)
    
    try:
        print("Initializing engine...")
        engine.initialize()
        print("✓ Engine initialized successfully")
        
        # Test finding PDF files
        input_dir = Path("data/input/test")
        if input_dir.exists():
            pdf_files = engine.find_pdf_files(input_dir)
            print(f"✓ Found {len(pdf_files)} PDF files in test directory")
        else:
            print("⚠ Test input directory doesn't exist, skipping file search test")
        
        print("✓ Core engine test completed successfully")
        
    except Exception as e:
        print(f"✗ Engine test failed: {e}")
        
    finally:
        engine.cleanup()
        print("✓ Engine cleanup completed")

if __name__ == "__main__":
    test_engine()
