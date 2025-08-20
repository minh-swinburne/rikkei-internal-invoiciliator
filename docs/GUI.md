I'll help you plan a comprehensive GUI implementation for your invoice reconciliation tool. Let me first examine the current structure and understand how the CLI works to make the best architectural decisions. Now let me check if there's an existing .env file to understand the current configuration: Perfect! Now I have a comprehensive understanding of your current application. Let me provide you with a detailed plan for implementing the GUI version.

## GUI Implementation Plan

### **Architecture Decision: Hybrid Approach**

I recommend a **hybrid approach** that reuses the existing core business logic while creating a dedicated GUI layer. This approach offers the best of both worlds:

**Benefits:**
- ✅ Reuse all existing, tested business logic
- ✅ Maintain CLI for power users and automation
- ✅ Cleaner separation of concerns
- ✅ Easier maintenance and testing
- ✅ Better for compilation to executable

**Structure:**
```
src/
├── core/                    # Business logic (shared)
│   ├── __init__.py
│   ├── engine.py           # Core processing engine
│   └── workflow.py         # Processing workflow orchestration
├── gui/                    # GUI application
│   ├── __init__.py
│   ├── main_window.py      # Main application window
│   ├── config_dialog.py    # Settings configuration
│   ├── log_viewer.py       # Log display widget
│   ├── result_viewer.py    # Results browser
│   ├── pdf_viewer.py       # PDF preview widget
│   └── app.py             # GUI entry point
├── cli/                    # CLI application (refactored)
│   ├── __init__.py
│   └── main.py            # CLI entry point
└── [existing modules...]   # Unchanged
```

### **Configuration Management**

For .env file handling, I recommend:

1. **Read-only in GUI by default** - Load settings from .env on startup
2. **Optional write capability** - Save settings back to .env with user confirmation
3. **Runtime override** - Allow temporary setting changes during session
4. **Validation** - Ensure all required settings are present before processing

### **Detailed GUI Components Plan**

#### **1. Main Window Layout**
```
┌─────────────────────────────────────────────────────────────┐
│ File  Settings  View  Help                              [X] │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Configuration ──────┐ ┌─ Processing Status ──────────┐   │
│ │ Input Dir:  [Browse] │ │ Status: Ready                │   │
│ │ Output Dir: [Browse] │ │ Progress: [██████░░░░] 60%   │   │
│ │ PIC Name: [TextEdit] │ │ Current: invoice_123.pdf     │   │
│ │ [Settings...]        │ │ [Start] [Stop] [Clear Logs]  │   │
│ └──────────────────────┘ └──────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Processing Logs ────────────────────────────────────────┐│
│ │ 2025-08-20 10:30:15 - INFO - Processing started...       ││
│ │ 2025-08-20 10:30:16 - INFO - Found 5 PDFs to process     ││
│ │ 2025-08-20 10:30:17 - WARNING - Issue with invoice_1     ││
│ │ [Auto-scroll] [Clear] [Export Logs]                      ││
│ └──────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ ┌─ Results ────────────────────────────────────────────────┐│
│ │ ┌File Name─────┬Status─────┬Issues─┬Actions────────────┐ ││
│ │ │invoice_1.pdf │ APPROVED  │ 0     │ [View] [PDF]      │ ││
│ │ │invoice_2.pdf │ REVIEW    │ 2     │ [View] [PDF]      │ ││
│ │ │invoice_3.pdf │ ERROR     │ 1     │ [View] [Retry]    │ ││
│ │ └──────────────┴───────────┴───────┴───────────────────┘ ││
│ │ [Refresh] [Export Results] [Open Output Folder]          ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### **2. Settings Dialog**
```
┌─ Application Settings ──────────────────────────────┐
│ ┌─ Processing ────────────────────────────────────┐ │
│ │ ☑ Enable PDF Stamping                           │ │
│ │ ☑ Always Accept (Auto-approve all)              │ │
│ │ PIC Name: [Jane Smith            ]              │ │
│ │ Stamp Position: [Bottom-Right ▼]                │ │
│ │ Log Level: [INFO ▼]                             │ │
│ │ Max File Size: [10] MB                          │ │
│ │ ☑ Concurrent Processing                         │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─ LLM Configuration ─────────────────────────────┐ │
│ │ Provider: [OpenRouter ▼]                        │ │
│ │ API Key: [••••••••••••••••••••••••••••••••••]   │ │
│ │ Model: [anthropic/claude-3.5-sonnet:beta ▼]     │ │
│ │ Base URL: [https://openrouter.ai/api/v1]        │ │
│ │ Max Retries: [3]  Timeout: [60] seconds         │ │
│ │ [Test Connection]                               │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─ File Management ───────────────────────────────┐ │
│ │ ☑ Save settings to .env file                    │ │
│ │ ☑ Create backup of processed files              │ │
│ │ ☑ Auto-organize by vendor                       │ │
│ └─────────────────────────────────────────────────┘ │
│              [Save] [Cancel] [Reset to Defaults]    │
└─────────────────────────────────────────────────────┘
```

#### **3. Result Detail Viewer**
```
┌─ Invoice Details: invoice_123.pdf ──────────────────┐
│ ┌─ PDF Preview ─────┐ ┌─ Extracted Data ──────────┐ │
│ │                   │ │ Invoice: INV-2025-001     │ │
│ │   [PDF VIEWER]    │ │ PO: PO-2025-001           │ │
│ │                   │ │ Vendor: ABC Corp          │ │
│ │                   │ │ ┌─ Items ──────────────┐  │ │
│ │                   │ │ │ W001 | Widget A | 2  │  │ │
│ │                   │ │ │ W002 | Widget B | 1  │  │ │
│ │                   │ │ │ W003 | Widget C | 5  │  │ │
│ │                   │ │ └──────────────────────┘  │ │
│ │                   │ └───────────────────────────┘ │
│ └───────────────────┘                             │ │
│ ┌─ Validation Results ────────────────────────────┐ │
│ │ Status: ⚠ REQUIRES REVIEW                       │ │
│ │ Issues:                                         │ │
│ │ • Item W003: Under-shipment (5 vs 10 ordered)   │ │
│ │ • Extra fee detected: Freight ($25.00)          │ │
│ │ Notes:                                          │ │
│ │ • Partial delivery acceptable                   │ │
│ │ Actions: [Approve Override] [Export] [Reprocess]│ │
│ └─────────────────────────────────────────────────┘ │
│                                    [Close]          │
└─────────────────────────────────────────────────────┘
```

### **Implementation Phases**

#### **Phase 1: Core Refactoring**
1. Extract business logic into `src/core/engine.py`
2. Create processing workflow orchestrator
3. Update CLI to use new core modules
4. Ensure backward compatibility

#### **Phase 2: Basic GUI Structure**
1. Create main window with basic layout
2. Implement settings dialog with .env integration
3. Add folder selection and basic configuration
4. Create log viewer with real-time updates

#### **Phase 3: Processing Integration**
1. Integrate core processing engine with GUI
2. Add progress tracking and status updates
3. Implement background processing with threading
4. Handle errors and user cancellation

#### **Phase 4: Results and Viewing**
1. Create results table with sorting/filtering
2. Implement PDF viewer widget
3. Build detailed result viewer dialog
4. Add export and reporting features

#### **Phase 5: Polish and Distribution**
1. Add application icons and styling
2. Implement auto-updater capability
3. Create installer/executable with PyInstaller
4. Add help documentation and tooltips

### **Technology Stack for GUI**

- **PySide6**: Main GUI framework (already in requirements)
- **QThread**: Background processing without blocking UI
- **QSettings**: Application settings persistence
- **QWebEngineView**: PDF viewing (or use PyMuPDF for simpler rendering)
- **QSyntaxHighlighter**: JSON/log syntax highlighting
- **PyInstaller**: For creating executable

### **Entry Points**

```python
# gui_main.py - New GUI entry point
if __name__ == "__main__":
    from src.gui.app import run_gui_app
    run_gui_app()

# main.py - Keep existing CLI
if __name__ == "__main__":
    # Existing CLI code

# launcher.py - Universal launcher
import sys
if len(sys.argv) > 1 and sys.argv[1] == "--gui":
    from src.gui.app import run_gui_app
    run_gui_app()
else:
    # Run CLI
```

Would you like me to start implementing this plan? I recommend beginning with **Phase 1** - refactoring the core business logic into reusable modules that both CLI and GUI can share. This will ensure we maintain the robustness of your existing solution while building the user-friendly interface.

Which component would you like me to implement first?

Similar code found with 2 license types