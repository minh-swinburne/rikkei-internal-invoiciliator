# Workflow Refactoring Summary

## Changes Made

### 1. Global Service Instances
**Before:** Services were recreated for each PDF processing call:
```python
def process_single_pdf(pdf_path: str, output_dir: Path) -> bool:
    pdf_processor = PDFProcessor()      # New instance each time
    llm_extractor = LLMExtractor()      # New instance each time
    validator = InvoiceValidator()      # New instance each time
    file_manager = FileManager(output_dir)  # New instance each time
```

**After:** Services are initialized once and reused:
```python
# Global instances
pdf_processor: Optional[PDFProcessor] = None
llm_extractor: Optional[LLMExtractor] = None
validator: Optional[InvoiceValidator] = None
file_manager: Optional[FileManager] = None

def initialize_services(output_dir: Path) -> None:
    """Initialize global service instances once."""
    global pdf_processor, llm_extractor, validator, file_manager
    pdf_processor = PDFProcessor()
    llm_extractor = LLMExtractor()
    validator = InvoiceValidator()
    file_manager = FileManager(output_dir)
```

**Benefits:**
- Better performance (no object recreation overhead)
- Consistent service state across multiple PDF processing
- Cleaner separation of initialization from processing logic

### 2. Path Object Usage
**Before:** Mixed usage of strings and Path objects:
```python
def process_single_pdf(pdf_path: str, output_dir: Path) -> bool:
    pdf_name = Path(pdf_path).name  # Converting str to Path
    text = pdf_processor.extract_text(pdf_path)  # str parameter
```

**After:** Consistent Path object usage:
```python
def process_single_pdf(pdf_path: Path) -> bool:
    text = pdf_processor.extract_text(pdf_path)  # Path parameter

class PDFProcessor:
    def extract_text(self, pdf_path: str | Path = None) -> str:
        pdf_path = Path(pdf_path)  # Always convert to Path
```

**Benefits:**
- Type safety and consistency
- Better IDE support and autocomplete
- Cleaner path manipulation
- PyMuPDF accepts both str and Path objects

### 3. Decoupled PDF Processing
**Before:** Stamping was tightly coupled with file saving:
```python
def stamp_pdf(self, pdf_path: str, status: str) -> Path:
    if not settings.enable_stamping:
        return self._copy_without_stamping(pdf_path, status)
    # Stamping logic mixed with file operations
```

**After:** Clear separation of concerns:
```python
def process_pdf(self, pdf_path: str | Path, status: str) -> Path:
    """Main entry point - decides between stamping or copying."""
    if settings.enable_stamping:
        return self._stamp_and_save_pdf(pdf_path, status)
    else:
        return self._copy_pdf_to_directory(pdf_path, status)

def _stamp_and_save_pdf(self, pdf_path: Path, status: str) -> Path:
    """Dedicated stamping method."""
    
def _copy_pdf_to_directory(self, pdf_path: Path, status: str) -> Path:
    """Dedicated copying method."""
```

**Benefits:**
- Single responsibility principle
- Easier testing of individual operations
- Clearer code flow
- Better error handling for specific operations

## Architecture Improvements

### Service Lifecycle
1. **Initialization:** Services are created once at application startup
2. **Processing:** Multiple PDFs can be processed using the same service instances
3. **Cleanup:** Services can be properly cleaned up at application shutdown

### Error Handling
- Better fallback mechanisms (stamping failure → copy operation)
- More specific error messages for different failure modes
- Proper exception propagation with context

### Configuration
- Settings are applied consistently across all service instances
- No need to pass configuration to each service method
- Centralized configuration management

## Usage Examples

### Single PDF Processing
```python
# Initialize services once
initialize_services(Path("data/output"))

# Process multiple PDFs
for pdf_file in pdf_files:
    success = process_single_pdf(pdf_file)
    if not success:
        logger.error(f"Failed to process {pdf_file}")
```

### Directory Processing
```python
# Services are initialized once for the entire batch
initialize_services(output_dir)
process_directory(input_dir)
```

## Testing
The refactored architecture is tested with:
- `tests/test_refactored_workflow.py` - End-to-end workflow testing
- Individual service tests can now be more focused
- Better mocking capabilities for unit tests

## Migration Notes
- Existing CLI interface remains unchanged
- All configuration options work as before
- Performance should be improved for batch processing
- Memory usage is more predictable
