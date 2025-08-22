# GUI Build and Distribution Notes

## ✅ **COMPLETED TASKS**

### 4. ✅ Integrate guide to app
- **Status**: COMPLETE
- **Implementation**: Created `src/gui/help_dialog.py` with dynamic content parsing
- **Features**:
  - F1 keyboard shortcut to open help
  - "?" button in main interface for quick access
  - Help menu item: "User Guide..."
  - Parses USER_GUIDE.txt automatically
  - Fallback content when files missing
  - External file opening support

## 🔄 **IN PROGRESS TASKS**

### 1. 🔄 Exe file icon + App window icon
- **Status**: 70% COMPLETE
- **Progress**: 
  - ✅ Robust icon loading system implemented (`set_application_icon()`)
  - ✅ Multiple search paths for different deployment scenarios
  - ✅ Support for both ICO and PNG formats
  - 🔄 Need proper ICO file conversion (PNG→ICO)
  - 🔄 PyInstaller configuration needs icon specification
- **Next Steps**: 
  - Convert PNG to proper ICO format with multiple sizes
  - Update PyInstaller build script with `--icon=src/assets/icon.ico`
  - Test icon display in compiled executable

## ⏳ **PLANNED TASKS**

### 2. ⏳ Only one instance at a time
- **Status**: PLANNED
- **Approach**: Implement singleton pattern using:
  - Windows: Named mutex or lock file
  - Cross-platform: Socket binding or file locking
  - Show existing window if second instance attempted
- **Benefits**: Prevents confusion, improves resource usage

### 3. ⏳ Add guide for getting API key
- **Status**: PLANNED  
- **Components Needed**:
  - API key acquisition tutorial (OpenRouter signup process)
  - Step-by-step screenshots or instructions
  - Integration into help system
  - Link to OpenRouter website with referral/instructions
- **Location**: Add as section in USER_GUIDE.txt

### 5. ⏳ Remove need to manually edit .env --> Only configure via app settings
- **Status**: PLANNED
- **Implementation Plan**:
  - Enhance ConfigDialog with API key section
  - Automatic .env file generation from GUI settings
  - API key validation and testing within app
  - Migration from existing .env files
  - First-run setup wizard for new users
- **Priority**: HIGH - Major UX improvement

## 🛠 **TECHNICAL REQUIREMENTS**

### Icon System (Task 1)
```python
# PyInstaller build command with icon
pyinstaller --onefile --windowed --icon=src/assets/icon.ico gui_launcher.py

# Icon file requirements
- ICO format with multiple sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
- Transparent background for proper Windows integration
- High-quality source for different DPI displays
```

### Single Instance (Task 2)
```python
# Planned implementation approach
class SingleInstanceManager:
    def __init__(self, app_name: str):
        self.lock_file = Path.home() / f".{app_name}.lock"
        
    def is_already_running(self) -> bool:
        # Check if lock file exists and process is running
        
    def create_lock(self):
        # Create lock file with PID
        
    def show_existing_window(self):
        # Send signal to existing instance to show window
```

### API Configuration (Task 5)
```python
# Enhanced ConfigDialog sections needed
- API Provider selection (OpenRouter, Direct OpenAI, etc.)
- API Key input with masked display
- Base URL configuration
- Model selection with validation
- Connection testing
- Settings persistence to .env
```

## 📋 **DEPLOYMENT CHECKLIST**

### Pre-Release Requirements
- [ ] ICO file conversion completed
- [ ] PyInstaller icon configuration working
- [ ] Single instance management implemented
- [ ] API key configuration dialog functional
- [ ] Comprehensive user guide with API setup
- [ ] .env file auto-generation working
- [ ] Cross-platform testing completed

### Build Script Enhancements Needed
```bash
# Enhanced build command
pyinstaller \
  --onefile \
  --windowed \
  --icon=src/assets/icon.ico \
  --add-data="src/assets;assets" \
  --add-data="dist/USER_GUIDE.txt;." \
  --name="InvoiceReconciliator" \
  gui_launcher.py
```

## 🎯 **PRIORITY ORDER**

1. **HIGH**: Complete icon system (Task 1) - Visual polish and professionalism
2. **HIGH**: API configuration dialog (Task 5) - Major UX improvement 
3. **MEDIUM**: Single instance management (Task 2) - Polish feature
4. **LOW**: Enhanced API key guide (Task 3) - Documentation improvement

## 📝 **NOTES**

- Task 4 (integrate guide) is complete and working well
- Icon system foundation is solid, just needs proper ICO file
- API configuration will be the biggest UX improvement
- Single instance is nice-to-have but not critical for v1.0
- All tasks support the goal of professional, user-friendly application