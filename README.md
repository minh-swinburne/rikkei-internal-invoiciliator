# rikkei-internal-invoiciliator

# Invoice Reconciliator

## Overview
This project is a Python-based tool designed to automate the reconciliation of invoices and purchase orders (POs) in PDF format. The tool extracts text from PDFs, processes the data using a Large Language Model (LLM) API (via OpenRouter), and validates the invoices against the purchase orders based on predefined protocols. It also provides a simple GUI for configuration and monitoring.

## Features
- **PDF Processing**: 
  - Extracts structured text from merged PDF files (invoice + purchase order)
  - Supports multiple vendor formats (Ingram, TD SYNNEX, Saison Tech, KDDI America)
  - Responsive PDF stamping with customizable positioning and styling
  - Automatic file organization into approved/review directories
- **LLM Integration**: 
  - Uses OpenRouter API with OpenAI library for intelligent data extraction
  - Configurable model selection (default: Google Gemini 2.0 Flash)
  - Structured data parsing from unstructured PDF content with fallback to text parsing
  - Retry mechanisms and error handling for API reliability
- **Validation Protocols**:
  - **PO Number Matching**: Validates PO numbers between invoice and purchase order
  - **Item Matching**: Uses SKU (6-7 char alphanumeric) or VPN for item identification
  - **Price Validation**: Ensures unit prices match between documents
  - **Quantity Handling**: Supports partial deliveries (shipped ≤ ordered quantity)
  - **Edge Case Detection**: Identifies credit memos, missing SKUs, alternative identifiers
  - **Fee Handling**: Accounts for extra fees (handling, freight, shipping)
- **Approval Workflow**:
  - Responsive PDF stamping with gradient backgrounds and proper typography
  - Customizable stamp positioning (top-left, top-right, bottom-left, bottom-right)
  - Stamps include PIC name, timestamp, and status with appropriate icons
  - Moves files to appropriate folders (approved/review required)
  - Maintains audit trail of processing results with JSON output
- **CLI Interface**:
  - Comprehensive command-line interface with multiple options
  - Single file or batch directory processing
  - Configurable logging levels and output directories
  - Flexible stamping options and overrides
- **Architecture**:
  - Global service instances for better performance in batch processing
  - Path object usage throughout for type safety
  - Decoupled stamping and file copying operations
  - Comprehensive error handling and logging

## Requirements
- Python 3.10+
- **Core Dependencies**:
  - PyMuPDF: PDF text extraction and stamping
  - OpenAI library: LLM API integration via OpenRouter
  - Pydantic: Data validation and structured models
  - python-dotenv: Environment configuration management
- **Optional Dependencies**:
  - PySide6: For GUI interface (if using GUI mode)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/minh-swinburne/rikkei-internal-invoiciliator.git
   cd rikkei-internal-invoiciliator
   ```
2. Create and activate virtual environment (recommended):
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv (faster alternative)
   uv pip install -r requirements.txt
   ```

## Configuration
Create a `.env` file in the project root with your OpenRouter configuration:
```env
# Required: OpenRouter API Configuration
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.0-flash-001

# Optional: LLM Settings
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SEC=30

# Optional: PDF Processing Settings
ENABLE_STAMPING=true
STAMP_POSITION=bottom-right
STAMP_PIC_NAME="Default User"
STAMP_ALWAYS_ACCEPT=false
```

### Supported Models
The tool supports various models available through OpenRouter:
- `google/gemini-2.0-flash-001` (default, recommended)
- `anthropic/claude-3-5-sonnet-20241022`
- `openai/gpt-4o-mini`
- `meta-llama/llama-3.1-405b-instruct`

### Environment Variables
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `OPENROUTER_BASE_URL`: OpenRouter API endpoint (default: https://openrouter.ai/api/v1)
- `OPENROUTER_MODEL`: Model to use for processing (default: google/gemini-2.0-flash-001)
- `LLM_MAX_RETRIES`: Maximum retry attempts for API calls (default: 3)
- `LLM_TIMEOUT_SEC`: Timeout for API requests in seconds (default: 30)
- `ENABLE_STAMPING`: Enable/disable PDF stamping (default: true)
- `STAMP_POSITION`: Default stamp position (default: bottom-right)
- `STAMP_PIC_NAME`: Default person name for stamps (default: "Default User")
- `STAMP_ALWAYS_ACCEPT`: Always approve invoices (default: false)

## Usage

### Command Line Interface
The application provides a comprehensive CLI with the following options:

#### Basic Usage
```bash
# Process all PDFs in the default input directory
python main.py

# Process a single PDF file
python main.py --pdf-file path/to/invoice.pdf

# Process PDFs from a specific directory
python main.py --input-dir data/input/vendor_folder
```

#### CLI Arguments
- `--input-dir`: Input directory containing PDF files (default: `data/input`)
- `--output-dir`: Output directory for processed files (default: `data/output`)
- `--pdf-file`: Process a single PDF file instead of directories
- `--log-level`: Logging verbosity level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `--stamp`: Enable PDF stamping with approval information
- `--stamp-pic-name`: Name of the person to include in stamps (default: `Jane Smith`)
- `--stamp-always-accept`: Always stamp invoices as approved regardless of validation
- `--stamp-position`: Position of stamp on PDF (`top-left`, `top-right`, `bottom-left`, `bottom-right`)

#### Example Commands
```bash
# Basic processing with stamping enabled
python main.py --stamp --stamp-pic-name "Jane Smith"

# Debug mode with custom input directory and always approve
python main.py --input-dir data/input/test --log-level DEBUG --stamp --stamp-pic-name "Jane Smith" --stamp-always-accept

# Process specific vendor folder with custom output and stamp position
python main.py --input-dir data/input/ingram --output-dir results/batch_001 --stamp --stamp-position top-right --stamp-pic-name "John Doe"

# Single file processing with detailed logging
python main.py --pdf-file invoices/INV-001.pdf --log-level DEBUG --stamp --stamp-pic-name "Alice Johnson"

# Batch processing without stamping (copy only)
python main.py --input-dir data/input/td_synnex --output-dir results/review_only

# Production processing with specific PIC
python main.py --input-dir data/input --stamp --stamp-pic-name "Yuko Yamada"
```

### Configuration Setup
1. Create environment configuration:
   ```bash
   copy .env.example .env
   ```
2. Edit `.env` file with your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=google/gemini-2.0-flash-001
   ```

### Output Structure
The tool automatically creates timestamped output directories with the following structure:
```
data/output/YYYYMMDD_HHMMSS/
├── approved/         # Successfully validated invoices
├── review/           # Invoices requiring manual review
└── result/           # Processing results and validation details
```

## Notes
- **Input Format**: PDF files must contain both invoice and purchase order (merged document)
- **Supported Vendors**: Ingram, TD SYNNEX, Saison Tech (invoices), KDDI America (purchase orders)
- **Manual Review Cases**: 
  - Credit memos requiring manual verification
  - Items with missing or alternative SKU formats
  - Batch pricing discrepancies
  - VPN inconsistencies between description and column data
- **File Organization**: Processed files are automatically sorted into approved/review folders with timestamped directories
- **Performance**: Global service instances ensure efficient batch processing without service recreation overhead
- **Stamping Features**:
  - Responsive sizing based on content length
  - Gradient backgrounds and professional styling
  - Customizable positioning and person information
  - Fallback to copying if stamping fails

## Troubleshooting
- **API Issues**: Check your OpenRouter API key and model availability
- **PDF Processing**: Ensure PDFs contain readable text (not just images)
- **Memory Usage**: For large batches, monitor memory usage; services are reused but PDFs are processed sequentially
- **Logging**: Use `--log-level DEBUG` for detailed processing information
- **File Permissions**: Ensure write permissions for output directories

## Development
- **Testing**: Run `python tests/test_pdf_stamp.py` to test PDF stamping functionality
- **Code Style**: Follow PEP 8 guidelines and use type hints
- **Architecture**: Services are globally initialized for better performance in batch operations
- **Extensibility**: New vendor formats can be added by extending the LLM extraction prompts

## License
This project is licensed under the MIT License. See the LICENSE file for details.

