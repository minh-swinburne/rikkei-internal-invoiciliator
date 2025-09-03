# Invoice Reconciliator - Complete User Guide

## 📋 What is Invoice Reconciliator?

Invoice Reconciliator is an intelligent business application that automatically validates invoices against purchase orders using artificial intelligence. It helps businesses streamline their accounts payable process by:

- **Automatically matching** invoices with purchase orders
- **Validating** pricing, quantities, and item details
- **Flagging discrepancies** for manual review
- **Organizing results** for easy processing
- **Stamping approved documents** for record keeping

The application uses advanced AI to read and understand PDF documents, making the reconciliation process faster and more accurate than manual verification.

---

## 🚀 Quick Start Guide

### Step 1: Get Your API Key
Before using the application, you need an OpenRouter API key (free to start):

1. **Visit OpenRouter**: Go to https://openrouter.ai/
2. **Sign Up/Login**: Create an account or sign in
3. **Access API Keys**: Click your user menu (top right) → Select "Keys"
4. **Create New Key**: 
   - Click "Create API Key"
   - Enter any name (e.g., "Invoice Reconciliator")
   - Set credit limit to $5 (recommended for new users)
   - Click "Create"
5. **Save Your Key**: Copy the key immediately and save it somewhere safe (it won't show again!)

### Step 2: Configure the Application
1. **Open Settings**: Main menu → Settings → Configuration (or click "Advanced Settings")
2. **Go to LLM Configuration tab**
3. **Paste your API key** in the "API Key" field
4. **Test connection** to verify it works
5. **Save settings**

### Step 3: Start Processing
1. **Place PDF files** in the `data/input/` folder
2. **Click "Start Processing"** in the main window
3. **Monitor progress** in the application
4. **Check results** in the `data/output/` folder

---

## 📁 File Organization

The application automatically creates and manages these folders:

```
📁 Application Folder/
├── 📁 data/
│   ├── 📁 input/          ← Place your PDF files here
│   │   ├── 📁 ingram/     ← Ingram Micro invoices (optional)
│   │   ├── 📁 td_synnex/  ← TD SYNNEX invoices (optional)
│   │   └── 📁 test/       ← Test files (optional)
│   └── 📁 output/         ← Results appear here
│       └── 📁 YYYYMMDD_HHMMSS/  ← Each run creates timestamped folder
│           ├── 📁 approved/     ← ✅ Successfully validated invoices
│           ├── 📁 review/       ← ⚠️ Invoices needing manual review
│           └── 📁 result/       ← 📊 Detailed processing reports
└── 📁 logs/               ← Application logs for troubleshooting
```

### File Types and Organization
- **Input Files**: Merged PDF files containing both invoice and purchase order
- **Approved Files**: Invoices that passed all validation checks
- **Review Files**: Invoices with discrepancies or requiring manual verification
- **Reports**: Detailed analysis of each processed file

---

## ⚙️ Main Interface Guide

### Processing Section
- **Input Directory**: Where to find PDF files (default: `data/input/`)
- **Output Directory**: Where to save results (default: `data/output/`)
- **Start Processing**: Begin analyzing all PDF files in input directory
- **Processing Status**: Real-time progress and file-by-file results

### Log Viewer
- **Real-time logs**: See what the application is doing
- **Filter by level**: Show only errors, warnings, or all messages
- **Copy logs**: Copy all logs to clipboard for support
- **Open log folder**: Access saved log files

### Settings and Configuration
Access via: **Menu → Settings → Configuration** or **Advanced Settings button**

#### Processing Tab
- **PDF Stamping**: Add approval stamps to processed documents
- **PIC Name**: Person in charge name for stamping
- **Auto-approve**: Automatically approve all invoices (use with caution)
- **Log Level**: Control detail level of application logs

#### LLM Configuration Tab
⚠️ **Warning**: Only change these settings if you know what you're doing!

- **API Key**: Your OpenRouter API key (required)
- **Model**: AI model to use (default works well)
- **Base URL**: API endpoint (keep default unless using custom service)
- **Timeout/Retries**: How long to wait and how many times to retry failed requests

#### Network Tab (Corporate Environments)
Use this tab if you encounter SSL certificate or network connection errors:

- **SSL Certificate Verification**: Enable/disable SSL verification (disable for corporate networks)
- **Use Certifi**: Use system certificate bundle for SSL connections
- **Disable SSL Warnings**: Suppress SSL warning messages
- **SSL Certificate File**: Custom certificate bundle from IT department
- **Proxy Settings**: Configure HTTP/HTTPS proxy servers
- **Test Network Connection**: Verify your configuration works

💡 **Quick Fix for Corporate Networks**: If you get SSL errors, simply uncheck "Enable SSL Certificate Verification" and test the connection.

---

## 🔍 Understanding Results

### Approval Status
- **✅ APPROVED**: Invoice matches purchase order perfectly
- **⚠️ REQUIRES REVIEW**: Discrepancies found, manual review needed
- **❌ FAILED**: Significant errors or unreadable documents

### Common Review Reasons
- **Price Mismatch**: Unit prices don't match between invoice and PO
- **Quantity Issues**: Shipped quantity exceeds ordered quantity
- **Missing Information**: SKU, part numbers, or PO numbers not found
- **Item Mismatch**: Products on invoice don't match PO items
- **Credit Memo**: Negative amounts requiring special handling

### Processing Reports
Each processed file generates a detailed report showing:
- Extracted invoice and PO data
- Validation results for each line item
- Reasons for approval or review status
- Confidence scores and recommendations

---

## 🛠️ Troubleshooting

### Common Issues

#### Application Won't Start
- **Check API Key**: Ensure you have a valid OpenRouter API key configured
- **Internet Connection**: Application needs internet access for AI processing
- **Disk Space**: Ensure sufficient space for processing and output files
- **Antivirus**: Some antivirus software may block the application

#### Processing Fails
- **File Quality**: Ensure PDF files contain readable text (not just scanned images)
- **File Format**: Files should contain both invoice and purchase order
- **API Credits**: Check your OpenRouter account has available credits
- **File Size**: Very large files (>10MB) may timeout

#### Poor Results
- **Vendor Support**: Currently supports Ingram Micro, TD SYNNEX, Saison Tech, KDDI America
- **Document Quality**: Use high-quality, text-based PDF files
- **Merged Documents**: Ensure files contain both invoice AND purchase order
- **Layout Issues**: Some complex layouts may require manual review

### Getting Help
1. **Check Logs**: Use the log viewer to see detailed error messages
2. **Copy Logs**: Use "Copy All Logs" to share logs with support
3. **Test Connection**: Use "Test Connection" in settings to verify API access
4. **Contact Support**: Provide log files and sample documents for assistance

---

## 💡 Tips for Best Results

### Document Preparation
- **Use text-based PDFs**: Scanned images don't work as well
- **Merge documents**: Combine invoice and PO into single PDF
- **Good quality**: Clear, readable text produces better results
- **Consistent format**: Stick to supported vendor formats when possible

### Processing Workflow
1. **Start small**: Test with a few files first
2. **Review settings**: Configure stamping and approval preferences
3. **Monitor progress**: Watch the log viewer for any issues
4. **Check results**: Always review the processing reports
5. **Handle reviews**: Manually verify files flagged for review

### Optimization
- **Batch processing**: Process multiple files at once for efficiency
- **Regular monitoring**: Check logs for any recurring issues
- **Keep backups**: Original files are preserved, but backups are recommended
- **Update settings**: Adjust timeout and retry settings if experiencing issues

---

## 🔧 Advanced User Guide

### Technology Stack
The Invoice Reconciliator is built using modern technologies:

- **Python 3.12**: Core application language
- **PySide6**: Cross-platform GUI framework
- **PyMuPDF**: PDF processing and text extraction
- **OpenAI API**: LLM integration via OpenRouter
- **Pydantic**: Data validation and structured parsing

### AI Processing Pipeline
1. **PDF Text Extraction**: Extract text while preserving document structure
2. **Document Classification**: Identify invoice and purchase order sections
3. **Data Extraction**: Use AI to extract structured data (items, prices, quantities)
4. **Validation Engine**: Apply business rules to validate matches
5. **Result Generation**: Create reports and move files to appropriate folders

### Supported Vendors
The application has specialized parsing for:
- **Ingram Micro**: Advanced line item matching and pricing validation
- **TD SYNNEX**: Multi-format invoice and PO recognition
- **Saison Tech**: Japanese vendor format support
- **KDDI America**: Telecommunications equipment invoices
- **Generic Format**: Basic support for other vendors

### Business Rules Engine
The validation engine implements these key rules:
- **PO Number Matching**: Must match exactly between invoice and PO
- **Item Identification**: Match by SKU (6-7 alphanumeric) or VPN
- **Price Validation**: Unit prices must match exactly
- **Quantity Rules**: Shipped quantity ≤ ordered quantity (partial deliveries OK)
- **Additional Fees**: Handling, freight, shipping fees are acceptable
- **Credit Memos**: Negative amounts automatically flagged for review

### Configuration Files
- **Settings**: Stored in application memory and optionally `.env` file
- **Logs**: Saved to `logs/` directory with rotation
- **Cache**: Temporary processing files in `temp/` directory
- **Models**: AI model configurations and prompts

### API Integration
The application uses OpenRouter for AI processing:
- **Model**: Google Gemini 2.0 Flash (fast, cost-effective)
- **Structured Output**: Uses function calling for reliable data extraction
- **Fallback Processing**: Text parsing when structured output fails
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful degradation with manual review fallback

### Performance Optimization
- **Concurrent Processing**: Optional parallel file processing
- **Memory Management**: Efficient PDF handling for large files
- **Caching**: Reduces redundant API calls
- **Progress Tracking**: Real-time status updates
- **Error Recovery**: Continues processing remaining files if one fails

### Security Considerations
- **API Key Storage**: Securely stored in memory and optionally `.env` file
- **Data Privacy**: Documents processed via OpenRouter API (review their privacy policy)
- **Local Processing**: Text extraction and validation done locally
- **File Access**: Only accesses configured input/output directories
- **Logging**: Sensitive data filtered from logs

### Customization Options
Advanced users can modify:
- **Validation Rules**: Edit business logic in `src/validator.py`
- **Vendor Formats**: Add new vendor parsers in `src/pdf_processor.py`
- **AI Prompts**: Customize extraction prompts in `src/llm_extractor.py`
- **Output Formats**: Modify report generation in `src/file_manager.py`
- **GUI Layout**: Customize interface in `src/gui/` modules

### Development and Testing
For developers and advanced users:
- **Test Suite**: Run `python -m pytest tests/` for comprehensive testing
- **Debug Mode**: Set log level to DEBUG for detailed processing information
- **Environment**: Uses UV for Python dependency management
- **Modularity**: Clean separation between PDF processing, AI, validation, and GUI
- **Documentation**: Comprehensive inline documentation and type hints

---

## ⚠️ Troubleshooting Common Issues

### SSL Certificate Errors (Corporate Networks)

**Problem**: You see errors like "SSL Certificate verification failed" or "SSLError" when testing the API connection.

**Cause**: Many corporate networks use SSL interception/inspection, which replaces website certificates with internal ones. This breaks SSL verification for external APIs.

**🎯 Quick Solution**:
1. **Open Settings** → **Configuration** → **Network** tab
2. **Uncheck "Enable SSL Certificate Verification"**
3. **Click "Test Network Connection"** to verify it works
4. **Save settings**

**📋 Detailed Solutions**:

#### Option 1: Disable SSL Verification (Fastest)
```
Settings → Configuration → Network Tab
☐ Enable SSL Certificate Verification  ← Uncheck this
```
⚠️ **Note**: This reduces security but is often necessary in corporate environments.

#### Option 2: Use Company Certificate Bundle
If your IT department provides a certificate bundle:
1. **Get certificate file** from IT department (usually `.pem` or `.crt` file)
2. **Configure in Network tab**:
   ```
   SSL Certificate File: [Browse to your certificate file]
   ☑ Use Certifi for SSL certificates
   ```

#### Option 3: Environment Variables (Advanced)
Add to your `.env` file:
```
SSL_VERIFY=false
USE_CERTIFI=true
DISABLE_SSL_WARNINGS=true
```

### Network Connection Errors

**Problem**: "Network connection failed" or timeout errors.

**Solutions**:

#### Check Proxy Settings
If your company uses a proxy:
1. **Open Settings** → **Configuration** → **Network** tab
2. **Configure proxy settings**:
   ```
   HTTP Proxy: http://proxy.company.com:8080
   HTTPS Proxy: https://proxy.company.com:8080
   ```
3. **Ask IT department** for correct proxy URLs and authentication

#### Firewall Configuration
Ensure these connections are allowed:
- **OpenRouter API**: `https://openrouter.ai/api/v1`
- **Port 443**: HTTPS traffic to external APIs
- **IP Whitelisting**: May be required for `openrouter.ai`

### API Key and Authentication Errors

**Problem**: "Invalid API key" or "Authentication failed" errors.

**Solutions**:
1. **Verify API key**: Copy-paste directly from OpenRouter dashboard
2. **Check key format**: Should start with `sk-or-v1-`
3. **Test on different network**: Try from home/mobile hotspot
4. **Check billing**: Ensure OpenRouter account has available credits

### File Processing Issues

**Problem**: PDFs not processing correctly or "No valid data extracted" errors.

**Solutions**:
1. **Check file format**: Ensure files are actual PDFs, not scanned images
2. **File size**: Large files (>10MB) may timeout - adjust settings
3. **Content quality**: Ensure text is readable and not corrupted
4. **Merged format**: Verify invoice and PO are in the same PDF file

### Performance and Memory Issues

**Problem**: Application runs slowly or crashes during processing.

**Solutions**:
1. **Reduce concurrent processing**: Settings → Processing → Uncheck concurrent processing
2. **Lower file size limit**: Settings → Processing → Reduce max file size
3. **Close other applications**: Free up system memory
4. **Process smaller batches**: Move some files out of input folder temporarily

### Common Error Messages and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `SSLError: certificate verify failed` | Corporate SSL interception | Disable SSL verification in Network settings |
| `ConnectionError: Failed to establish connection` | Network/firewall blocking | Configure proxy settings or contact IT |
| `AuthenticationError: Invalid API key` | Wrong or expired API key | Get new key from OpenRouter dashboard |
| `TimeoutError: Request timed out` | Slow network or large files | Increase timeout in LLM settings |
| `FileNotFoundError: No PDF files found` | Empty input directory | Place PDF files in `data/input/` folder |
| `PermissionError: Access denied` | File permissions or antivirus | Run as administrator or exclude from antivirus |

### Getting Detailed Error Information

1. **Enable Debug Logging**:
   - Settings → Processing → Log Level → DEBUG
   - Restart application

2. **Check Log Files**:
   - Main menu → View → Open Log Folder
   - Look for recent `.log` files
   - Copy relevant error messages

3. **Test Individual Components**:
   - Test network connection in Network settings
   - Test API key in LLM settings
   - Process one file at a time

### When to Contact IT Support

Contact your IT department if you encounter:
- **Persistent SSL certificate errors** after trying solutions
- **Proxy authentication requirements** (username/password)
- **Firewall blocking** external API connections
- **Network policies** preventing application use

Provide them with:
- Application logs showing the errors
- Network settings you've tried
- Confirmation that it works on other networks (if tested)

---

## 📞 Support and Resources

### Documentation
- **This Guide**: Comprehensive user and advanced documentation
- **Code Documentation**: Inline comments and docstrings
- **Build Notes**: Development and deployment information
- **Change Log**: Version history and updates

### Getting Support
1. **Check Logs**: Most issues can be diagnosed from application logs
2. **Test Connection**: Verify API connectivity and configuration
3. **Sample Files**: Prepare sample files that demonstrate the issue
4. **Environment**: Note operating system, Python version, and file types
5. **Contact IT**: Provide logs, configuration, and sample files to support team

### Best Practices
- **Regular Updates**: Keep the application updated for latest features
- **Monitor Usage**: Track API usage to manage costs
- **Quality Control**: Regularly review processing results for accuracy
- **Backup Strategy**: Maintain backups of important documents
- **Training**: Ensure users understand the review and approval process

---

*Invoice Reconciliator - Streamlining accounts payable with artificial intelligence*
