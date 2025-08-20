"""
Quick test of the reorganized architecture.
"""

from pathlib import Path
from src.core import InvoiceReconciliationEngine
from src.logging_config import setup_logging

def test_reorganized_architecture():
    """Test that the reorganized modules work correctly."""
    # Set up logging
    setup_logging(log_level="INFO", console_output=True, is_test=True)
    
    # Create a test output directory
    output_dir = Path("data/output/test_reorganized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = InvoiceReconciliationEngine(output_dir)
    
    try:
        print("Testing reorganized architecture...")
        engine.initialize()
        print("✓ Engine initialized successfully with reorganized modules")
        
        # Test that we can import core models directly
        from src.core import Invoice, PurchaseOrder, ValidationResult, InvoiceValidator
        print("✓ Core models imported successfully")
        
        # Test that services are accessible 
        from src.core.services import PDFProcessor, LLMExtractor, FileManager
        print("✓ Services imported successfully")
        
        print("✓ Architecture reorganization test completed successfully")
        
    except Exception as e:
        print(f"✗ Architecture test failed: {e}")
        
    finally:
        engine.cleanup()
        print("✓ Engine cleanup completed")

if __name__ == "__main__":
    test_reorganized_architecture()
