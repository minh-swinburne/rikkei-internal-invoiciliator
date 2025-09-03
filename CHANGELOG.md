# Changelog

All notable changes to the Invoice Reconciliator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-09-03

### 🌐 Corporate Network Support
- **Network Configuration Tab**: Added comprehensive GUI settings for corporate environments with SSL and proxy configuration
- **SSL Certificate Management**: Support for corporate SSL interception with disable verification option and custom certificate bundles
- **Proxy Configuration**: HTTP/HTTPS proxy support for corporate firewalls with GUI configuration interface
- **Network Connection Testing**: Built-in test functionality to verify API connectivity with current network settings
- **Enhanced Error Handling**: Consolidated SSL and network error reporting with specific guidance for corporate users

### 🔧 Configuration Improvements  
- **Boolean Format Consistency**: Standardized all boolean values in .env files to lowercase format (true/false) for better compatibility
- **Settings System Enhancement**: Added SSL/network fields to Pydantic settings with automatic environment variable loading
- **Backup Configuration**: QSettings integration for network settings persistence as backup to .env file
- **Template Updates**: Updated .env.template with comprehensive network configuration options

### 📚 Documentation & User Experience
- **Corporate Network Guide**: Added detailed SSL troubleshooting section to USER_GUIDE.md with step-by-step solutions
- **SSL Quick Fix Documentation**: Created OPENAI_SSL.md with technical SSL resolution examples
- **Enhanced Help Content**: Updated user guide with network tab instructions and corporate environment guidance
- **Error Message Improvements**: More descriptive SSL/network error messages with solution suggestions

### 🏗️ Technical Enhancements
- **HTTP Client Configuration**: Enhanced LLM extractor with proper SSL and proxy support using httpx client
- **Environment Variable Management**: Automatic SSL environment configuration (SSL_CERT_FILE, REQUESTS_CA_BUNDLE, etc.)
- **Certificate Bundle Support**: Integration with certifi package for up-to-date CA certificates
- **SSL Warning Management**: Option to disable SSL warnings in corporate environments

### 🐛 Bug Fixes
- **Configuration File Consistency**: Fixed mixed boolean case issues in configuration templates
- **Settings Persistence**: Improved settings synchronization between GUI, environment variables, and config files
- **SSL Context Issues**: Resolved SSL verification problems in corporate networks with proper fallback handling

## [1.1.0] - 2025-08-27

### 🆕 New Features
- **Single File Retry System**: Added ability to retry individual failed files with same settings, automatically saving results to separate files with `_retry_N` suffix
- **Enhanced Item Data Structure**: Added `name` field to Item model for clean product names while preserving full description text for better matching stability
- **Improved Result Display**: Enhanced issues count display in results table to accurately show validation problems

### 🔧 Improvements
- **Always-Accept Logic Refinement**: Fixed stamp-only behavior when always-accept mode is enabled - files now show correct validation status and go to proper directories while displaying "APPROVED" stamps
- **Optimized LLM Schema**: Enhanced JSON schema with detailed property descriptions to guide AI extraction for more accurate invoice and PO data parsing
- **Better Error Handling**: Improved error processing to save complete JSON results with exception details and display proper ERROR status in GUI
- **Cleaner UI Design**: Removed redundant "#" columns from Validation tab tables since Qt provides built-in row numbering

### 🐛 Bug Fixes
- **Duplicate Log Elimination**: Resolved duplicate log entries in GUI log viewer by optimizing logger hierarchy and removing redundant signal emissions
- **Thread Communication**: Fixed duplicate workflow completion messages and retry result handling in background processing threads
- **Status Display Accuracy**: Corrected issues count calculation to properly reflect validation problems from `validation_result.issues`

### 📚 Documentation
- **Screenshot Integration**: Added comprehensive screenshots to README showcasing main interface, settings, result viewer, and help system
- **Visual Documentation**: Enhanced user guide with visual examples of processing results, error handling, and configuration options

### 🏗️ Technical Changes
- **Model Schema Updates**: Updated LLM extraction schema to include both `name` and `description` fields with clear usage guidelines
- **File Manager Enhancements**: Improved PDF processing to separate stamp text from file directory placement logic
- **Logger Optimization**: Streamlined logging system using root logger propagation to eliminate handler duplication

## [1.0.0] - 2025-08-22

### 🎉 Initial Release
- **AI-Powered Processing**: Complete invoice and PO reconciliation using OpenRouter API with Google Gemini 2.0 Flash
- **Modular Architecture**: Robust PDF processing supporting Ingram, TD SYNNEX, Saison Tech, and KDDI America formats
- **Comprehensive Validation**: Business rule validation for PO matching, SKU/VPN identification, price verification, and quantity handling
- **Professional GUI**: Modern PySide6 interface with real-time progress tracking, advanced configuration, and theme support
- **CLI Interface**: Full command-line support for automation and batch processing workflows
- **PDF Stamping System**: Responsive approval stamps with configurable positioning and professional styling
- **Error Handling**: Robust error management with audit trails and compliance features
- **File Organization**: Automatic sorting into approved/review directories with timestamped outputs
- **Help System**: Integrated F1 help with comprehensive user documentation
- **Build System**: Complete distribution system with professional Windows installer

### 📋 Business Rules
- PO number matching between invoice and purchase order
- Item identification via SKU (6-7 char alphanumeric) or VPN
- Unit price validation with quantity discrepancy handling
- Partial delivery support (shipped ≤ ordered quantities)
- Edge case detection for credit memos and missing identifiers
- Extra fee handling for shipping, handling, and freight charges

### 🏢 Supported Formats
- **Invoice Vendors**: Ingram Micro, TD SYNNEX, Saison Technology
- **Purchase Orders**: KDDI America format
- **File Type**: Merged PDF documents (invoice + PO)

### ⚠️ Known Limitations
- Input PDFs must contain both invoice and purchase order in single merged document
- Manual review required for credit memos, missing SKUs, and batch pricing discrepancies
- Internet connection required for AI processing via OpenRouter API

---

## Release Notes Format

### Types of Changes
- 🆕 **Added** for new features
- 🔧 **Changed** for changes in existing functionality  
- 🗑️ **Deprecated** for soon-to-be removed features
- 🐛 **Fixed** for any bug fixes
- 🔒 **Security** for vulnerability fixes
- 📚 **Documentation** for documentation changes
- 🏗️ **Technical** for internal/developer changes
