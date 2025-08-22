# Invoice Reconciliator v1.0

## Overview
A professional Python-based application for automated invoice and purchase order (PO) reconciliation. This tool extracts data from merged PDF files, processes them using AI (via OpenRouter API), validates against business rules, and provides comprehensive approval workflows with both GUI and CLI interfaces.

## ✨ Key Features
- **🤖 AI-Powered Processing**: Uses advanced language models (Google Gemini 2.0 Flash) for intelligent data extraction
- **📋 Smart Validation**: Comprehensive business rule validation for PO/invoice matching
- **🖥️ Professional GUI**: Modern PySide6 interface with real-time processing and advanced configuration
- **⚡ CLI Support**: Full command-line interface for automation and batch processing
- **📄 PDF Stamping**: Professional approval stamps with configurable positioning
- **🔧 Enterprise Ready**: Robust error handling, audit trails, and compliance features
- **📦 Easy Distribution**: Complete build system with professional installer

## Features
- **🔍 Advanced PDF Processing**: 
  - Extracts structured text from merged PDF files (invoice + purchase order)
  - Supports multiple vendor formats (Ingram, TD SYNNEX, Saison Tech, KDDI America)
  - Responsive PDF stamping with customizable positioning and professional styling
  - Automatic file organization into approved/review directories

- **🤖 AI-Powered Intelligence**: 
  - Uses OpenRouter API with configurable AI models (default: Google Gemini 2.0 Flash)
  - Structured data parsing from unstructured PDF content with intelligent fallbacks
  - Retry mechanisms and comprehensive error handling for API reliability
  - Advanced prompt engineering for accurate vendor-specific data extraction

- **✅ Comprehensive Validation**:
  - **PO Number Matching**: Validates PO numbers between invoice and purchase order
  - **Item Matching**: Uses SKU (6-7 char alphanumeric) or VPN for item identification
  - **Price Validation**: Ensures unit prices match between documents
  - **Quantity Handling**: Supports partial deliveries (shipped ≤ ordered quantity)
  - **Edge Case Detection**: Identifies credit memos, missing SKUs, alternative identifiers
  - **Fee Handling**: Accounts for extra fees (handling, freight, shipping)

- **🖥️ Professional GUI Interface**:
  - Modern PySide6-based interface with comprehensive tooltips
  - Real-time processing with background threading and progress tracking
  - Advanced settings dialog with tabbed configuration
  - Integrated help system with F1 shortcut and dynamic content parsing
  - Professional theme management with dark/light mode support
  - Persistent settings and user preferences
  - Single instance management to prevent multiple app launches

- **⚡ Command Line Interface**:
  - Comprehensive CLI with flexible options for automation
  - Single file or batch directory processing capabilities
  - Configurable logging levels and output directories
  - Flexible stamping options and processing overrides

- **📋 Professional Approval Workflow**:
  - Responsive PDF stamping with gradient backgrounds and proper typography
  - Configurable stamp positioning (all four corners with custom offsets)
  - Stamps include PIC name, timestamp, and status with appropriate icons
  - Moves files to appropriate folders (approved/review required)
  - Maintains detailed audit trail of processing results with JSON output

- **🏗️ Enterprise Architecture**:
  - Global service instances for optimal performance in batch processing
  - Type-safe Path object usage throughout the application
  - Decoupled stamping and file copying operations
  - Comprehensive error handling and structured logging
  - Robust build system with PyInstaller and professional installer

## Requirements
- Python 3.10+
- **Core Dependencies**:
  - PyMuPDF: PDF text extraction and stamping
  - OpenAI library: LLM API integration via OpenRouter
  - Pydantic: Data validation and structured models
  - python-dotenv: Environment configuration management
- **Optional Dependencies**:
  - PySide6: For GUI interface (if using GUI mode)

## Quick Start

### 🚀 Ready-to-Use Release
1. **Download** the installer from the releases page
2. **Run** `Invoice_Reconciliator_Setup.exe` to install
3. **Launch** the application from Start Menu or desktop shortcut
4. **Configure** your OpenRouter API key in Settings
5. **Start Processing** PDFs immediately!

### 🛠️ Development Setup
1. **Clone** the repository:
   ```bash
   git clone https://github.com/minh-swinburne/rikkei-internal-invoiciliator.git
   cd rikkei-internal-invoiciliator
   ```
2. **Create** virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
3. **Install** dependencies:
   ```bash
   # Using uv (recommended - faster)
   uv pip install -r requirements.txt
   # Or using pip
   pip install -r requirements.txt
   ```
4. **Configure** environment:
   ```bash
   copy .env.example .env
   # Edit .env with your OpenRouter API key
   ```
5. **Run** the application:
   ```bash
   # GUI Mode
   python gui_launcher.py
   # CLI Mode
   python main.py --help
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

### 🖥️ GUI Mode (Recommended)
Launch the graphical interface for easy configuration and monitoring:
```bash
python gui_launcher.py
```

**GUI Features:**
- **📁 Drag & Drop**: Easy folder selection for input and output
- **⚙️ Settings Dialog**: Advanced configuration with API testing
- **📊 Real-time Progress**: Live processing updates and file status
- **📋 Results Table**: Sortable results with detailed viewing options
- **❓ Integrated Help**: F1 help system with comprehensive guides
- **🎨 Theme Support**: Professional themes with dark/light modes
- **📄 PDF Viewer**: Built-in PDF viewing for processed documents

### 💻 Command Line Interface
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
1. **API Key Configuration**:
   - Use GUI: Settings → LLM Configuration → API Key
   - Or edit `.env` file manually:
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=google/gemini-2.0-flash-001
   ```

2. **Processing Settings**:
   - **Enable Stamping**: Add approval stamps to PDFs
   - **PIC Name**: Person in charge name for stamps
   - **Stamp Position**: Configurable positioning with custom offsets
   - **Always Accept**: Auto-approve mode for trusted workflows

### Output Structure
The tool automatically creates organized output directories:
```
data/output/YYYYMMDD_HHMMSS/
├── approved/         # ✅ Successfully validated invoices
├── review/           # ⚠️ Invoices requiring manual review
└── result/           # 📊 Processing results and validation details
```

## Building and Distribution

### 🏗️ Create Executable
For deployment and distribution:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Full build process (creates installer)
.\build

# Or step-by-step:
python build.py check    # ✅ Verify dependencies
python build.py build    # 🔨 Create executable  
python build.py install  # 📦 Create installer
```

**Build Output:**
- `dist/Invoice_Reconciliator.exe` - Standalone executable
- `dist/Invoice_Reconciliator_Setup.exe` - Professional installer

### 📋 System Requirements
- **OS**: Windows 10/11 (primary), macOS/Linux (development)
- **Python**: 3.10+ (for development)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 100MB for application, 1GB+ for processing data
- **Network**: Internet connection required for AI processing

## Support and Documentation

### 📚 Help Resources
- **Integrated Help**: Press F1 in the application for comprehensive guides
- **User Guide**: Available in the application and `docs/` folder
- **API Documentation**: Detailed code documentation in source files
- **Build Guides**: Complete build and deployment instructions

### 🐛 Troubleshooting
- **API Issues**: Verify OpenRouter API key and model availability
- **PDF Processing**: Ensure PDFs contain readable text (not just images)
- **Memory Usage**: Monitor memory for large batches; files are processed sequentially
- **Build Problems**: Check Python version and dependency installation
- **Performance**: Use `--log-level DEBUG` for detailed processing information

## Development
- **Testing**: Run `python tests/test_pdf_stamp.py` for PDF stamping functionality
- **Code Style**: Follow PEP 8 guidelines with comprehensive type hints
- **Architecture**: Services are globally initialized for optimal batch performance
- **Extensibility**: New vendor formats easily added via LLM prompt engineering
- **Logging**: Comprehensive structured logging for debugging and audit trails

## Important Notes
- **📄 Input Format**: PDF files must contain both invoice and purchase order (merged document)
- **🏢 Supported Vendors**: Ingram, TD SYNNEX, Saison Tech (invoices), KDDI America (purchase orders)
- **⚠️ Manual Review Cases**: 
  - Credit memos requiring manual verification
  - Items with missing or alternative SKU formats
  - Batch pricing discrepancies
  - VPN inconsistencies between description and column data
- **📁 File Organization**: Automatic sorting into approved/review folders with timestamped directories
- **⚡ Performance**: Global service instances ensure efficient batch processing
- **🏷️ Professional Stamping**: Responsive sizing, gradient backgrounds, configurable positioning

## Version History
- **v1.0.0** - Initial release with full GUI and CLI interfaces
  - Complete AI-powered invoice reconciliation
  - Professional GUI with advanced settings
  - Comprehensive build and distribution system
  - Enterprise-ready features and documentation

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

**🎉 Ready for Production Use** - Version 1.0 includes all enterprise features for professional invoice reconciliation workflows.

