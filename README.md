# rikkei-internal-invoiciliator

# Invoice Reconciliation Tool

## Overview
This project is a Python-based tool designed to automate the reconciliation of invoices and purchase orders (POs) in PDF format. The tool extracts text from PDFs, processes the data using a Large Language Model (LLM) API (via OpenRouter), and validates the invoices against the purchase orders based on predefined protocols. It also provides a simple GUI for configuration and monitoring.

## Features
- **PDF Processing**: 
  - Extracts structured text from merged PDF files (invoice + purchase order)
  - Supports multiple vendor formats (Ingram, TD SYNNEX, Saison Tech, KDDI America)
  - Stamps approved invoices with approval information
- **LLM Integration**: 
  - Uses OpenRouter API with OpenAI library for intelligent data extraction
  - Configurable model selection (default: Google Gemini 2.0 Flash)
  - Structured data parsing from unstructured PDF content
- **Validation Protocols**:
  - **PO Number Matching**: Validates PO numbers between invoice and purchase order
  - **Item Matching**: Uses SKU (6-7 char alphanumeric) or VPN for item identification
  - **Price Validation**: Ensures unit prices match between documents
  - **Quantity Handling**: Supports partial deliveries (shipped ≤ ordered quantity)
  - **Edge Case Detection**: Identifies credit memos, missing SKUs, alternative identifiers
  - **Fee Handling**: Accounts for extra fees (handling, freight, shipping)
- **Approval Workflow**:
  - Stamps approved invoices with PIC name and date
  - Moves files to appropriate folders (approved/review required)
  - Maintains audit trail of processing results
- **GUI Configuration**:
  - Input/output folder selection
  - PIC name and date configuration
  - Real-time progress monitoring
  - Processing logs and results display

## Requirements
- Python 3.8+
- PySide6: For building the GUI.
- PyMuPDF: For PDF processing.
- OpenAI library: For LLM API integration.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/minh-swinburne/rikkei-internal-invoiciliator.git
   cd rikkei-internal-invoiciliator
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create environment configuration:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` file with your OpenRouter API key and preferred model.

## Configuration
Create a `.env` file in the project root with your OpenRouter configuration:
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```

## Usage
1. Launch the application:
   ```bash
   python main.py
   ```
2. Use the GUI to configure the job and start the reconciliation process.

## Notes
- **Input Format**: PDF files must contain both invoice and purchase order (merged document)
- **Supported Vendors**: Ingram, TD SYNNEX, Saison Tech (invoices), KDDI America (purchase orders)
- **Manual Review Cases**: 
  - Credit memos requiring manual verification
  - Items with missing or alternative SKU formats
  - Batch pricing discrepancies
  - VPN inconsistencies between description and column data
- **File Organization**: Processed files are automatically sorted into approved/review folders

## License
This project is licensed under the MIT License. See the LICENSE file for details.

