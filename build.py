#!/usr/bin/env python3
"""
Build Script for Invoice Reconciliator
Handles the complete build process including dependency checks, compilation, and installer creation.
"""

import sys
import subprocess
import shutil
from pathlib import Path
import platform


class BuildManager:
    """Manages the complete build process for Invoice Reconciliator."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.system = platform.system().lower()
        
        # Ensure output directory exists
        self.dist_dir.mkdir(exist_ok=True)
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            "PyInstaller",
            "PySide6", 
            "openai",
            "pydantic",
            "dotenv",
            "pymupdf"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package}")
        
        if missing_packages:
            print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
            print("Install them with: uv pip install " + " ".join(missing_packages))
            return False
            
        print("✅ All dependencies found!")
        return True
    
    def clean_build_directories(self):
        """Clean up previous build artifacts."""
        print("🧹 Cleaning build directories...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  🗑️  Removed {dir_path}")
        
        print("✅ Build directories cleaned!")
    
    def verify_assets(self) -> bool:
        """Verify that required assets exist."""
        print("🔍 Verifying assets...")
        
        required_assets = [
            self.project_root / "src" / "assets" / "icon.ico",
            self.project_root / "src" / "assets" / "USER_GUIDE.md",
            self.project_root / ".env.template"
        ]
        
        missing_assets = []
        
        for asset in required_assets:
            if asset.exists():
                print(f"  ✅ {asset.name}")
            else:
                missing_assets.append(asset)
                print(f"  ❌ {asset}")
        
        if missing_assets:
            print(f"\n❌ Missing assets: {[str(a) for a in missing_assets]}")
            return False
            
        print("✅ All assets found!")
        return True
    
    def build_executable(self) -> bool:
        """Build the executable using PyInstaller."""
        print("🔨 Building executable...")
        
        spec_file = self.project_root / "build.spec"
        
        if not spec_file.exists():
            print("❌ build.spec not found!")
            return False
        
        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",  # Clean cache and remove temporary files
            str(spec_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("✅ Executable built successfully!")
            print("Build output:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print("Error output:", e.stderr)
            return False
    
    def create_installer(self) -> bool:
        """Create an installer package."""
        print("📦 Creating installer...")
        
        exe_path = self.dist_dir / "InvoiceReconciliator.exe"
        
        if not exe_path.exists():
            print("❌ Executable not found! Build may have failed.")
            return False
        
        # For now, we'll create a simple zip package
        # Later this can be enhanced with proper installer tools
        
        version = self.get_version()
        installer_name = f"InvoiceReconciliator-v{version}-{self.system}.zip"
        installer_path = self.dist_dir / installer_name

        print(f"Creating package: {installer_name}")
        
        try:
            import zipfile
            
            with zipfile.ZipFile(installer_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add the executable
                zf.write(exe_path, "InvoiceReconciliator.exe")
                
                # Add documentation
                readme_content = self.create_readme()
                zf.writestr("README.txt", readme_content)
                
                # Add template files
                env_template = self.project_root / ".env.template"
                if env_template.exists():
                    zf.write(env_template, ".env.template")
                
                # Add user guide
                user_guide = self.project_root / "src" / "assets" / "USER_GUIDE.md"
                if user_guide.exists():
                    zf.write(user_guide, "USER_GUIDE.md")
            
            print(f"✅ Installer created: {installer_path}")
            print(f"📁 Size: {installer_path.stat().st_size / 1024 / 1024:.1f} MB")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create installer: {e}")
            return False
    
    def create_advanced_installer(self) -> bool:
        """Create a proper Windows installer using NSIS or Inno Setup."""
        print("🏗️  Creating advanced installer...")
        
        # This would require NSIS or Inno Setup to be installed
        # For now, we'll create the configuration but not execute
        
        nsis_script = self.create_nsis_script()
        nsis_path = self.project_root / "installer.nsi"
        
        with open(nsis_path, 'w') as f:
            f.write(nsis_script)
        
        print(f"✅ NSIS script created: {nsis_path}")
        print("To create installer, install NSIS and run:")
        print(f"  makensis {nsis_path}")
        
        return True
    
    def create_nsis_script(self) -> str:
        """Create NSIS installer script."""
        version = self.get_version()
        
        return f'''
; Invoice Reconciliator NSIS Installer Script
; Generated automatically by build script

!define APP_NAME "Invoice Reconciliator"
!define APP_VERSION "{version}"
!define APP_PUBLISHER "KDDI"
!define APP_DESCRIPTION "Automated Invoice/PO Reconciliation Tool"
!define APP_WEBSITE "https://github.com/minh-swinburne/rikkei-internal-invoiciliator"

; Main application file
!define MAIN_APP_EXE "InvoiceReconciliator.exe"

; Use Modern UI
!include "MUI2.nsh"

; General configuration
Name "${{APP_NAME}}"
OutFile "InvoiceReconciliator-v{version}-Setup.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"
InstallDirRegKey HKCU "Software\\${{APP_NAME}}" ""
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "src\\assets\\icon.ico"
!define MUI_UNICON "src\\assets\\icon.ico"

; Pages
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version information
VIProductVersion "{version}.0.0.0"
VIAddVersionKey "ProductName" "${{APP_NAME}}"
VIAddVersionKey "CompanyName" "${{APP_PUBLISHER}}"
VIAddVersionKey "FileDescription" "${{APP_DESCRIPTION}}"
VIAddVersionKey "FileVersion" "{version}"

; Installation section
Section "Main Application" SecMain
    SetOutPath "$INSTDIR"
    
    ; Add files
    File "dist\\InvoiceReconciliator.exe"
    File ".env.template"
    File "src\\assets\\USER_GUIDE.md"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{MAIN_APP_EXE}}"
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{MAIN_APP_EXE}}"
    
    ; Registry entries
    WriteRegStr HKCU "Software\\${{APP_NAME}}" "" $INSTDIR
    
    ; Uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" "$INSTDIR\\Uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\\InvoiceReconciliator.exe"
    Delete "$INSTDIR\\.env.template"
    Delete "$INSTDIR\\USER_GUIDE.md"
    Delete "$INSTDIR\\Uninstall.exe"
    
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk"
    RMDir "$SMPROGRAMS\\${{APP_NAME}}"
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
    DeleteRegKey HKCU "Software\\${{APP_NAME}}"
SectionEnd
'''
    
    def get_version(self) -> str:
        """Get application version."""
        # Try to read from a version file or git tag
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().lstrip('v')
        except:
            return "1.0.0"  # Default version
    
    def create_readme(self) -> str:
        """Create README for the installer package."""
        version = self.get_version()
        
        return f'''
Invoice Reconciliator v{version}
===============================

Thank you for downloading Invoice Reconciliator!

QUICK START:
1. Run InvoiceReconciliator.exe
2. Click "Advanced Settings" to configure your API key
3. Set input/output directories
4. Click "Start Processing"

FIRST TIME SETUP:
- You'll need an OpenRouter API key (free tier available)
- See USER_GUIDE.md for detailed setup instructions
- Copy .env.template to .env and add your API key (optional)

SYSTEM REQUIREMENTS:
- Windows 10 or later
- Internet connection for AI processing
- ~100MB disk space

SUPPORT:
- User Guide: USER_GUIDE.md
- GitHub: https://github.com/minh-swinburne/rikkei-internal-invoiciliator
- Issues: Create an issue on GitHub

WHAT'S INCLUDED:
- InvoiceReconciliator.exe - Main application
- USER_GUIDE.md - Complete documentation
- .env.template - Configuration template

The application stores settings in your user profile and doesn't require
administrator rights to run (only for installation).

Enjoy automated invoice reconciliation!
'''
    
    def build_all(self) -> bool:
        """Run the complete build process."""
        print("🚀 Starting complete build process...")
        print(f"Platform: {platform.system()} {platform.machine()}")
        print(f"Python: {sys.version}")
        print()
        
        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Verify Assets", self.verify_assets),
            ("Clean Build Dirs", lambda: (self.clean_build_directories(), True)[1]),
            ("Build Executable", self.build_executable),
            ("Create Installer", self.create_installer),
            ("Create NSIS Script", self.create_advanced_installer),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*50}")
            print(f"STEP: {step_name}")
            print('='*50)
            
            if not step_func():
                print(f"\n❌ BUILD FAILED at step: {step_name}")
                return False
        
        print(f"\n{'='*50}")
        print("🎉 BUILD COMPLETED SUCCESSFULLY!")
        print('='*50)
        print(f"📁 Output directory: {self.dist_dir}")
        print("Files created:")

        for file in self.dist_dir.glob("*"):
            print(f"  📄 {file.name} ({file.stat().st_size / 1024 / 1024:.1f} MB)")
        
        return True


def main():
    """Main build script entry point."""
    builder = BuildManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            builder.clean_build_directories()
        elif command == "check":
            builder.check_dependencies()
            builder.verify_assets()
        elif command == "build":
            builder.build_executable()
        elif command == "installer":
            builder.create_installer()
        elif command == "all":
            builder.build_all()
        else:
            print("Unknown command. Use: clean, check, build, installer, or all")
    else:
        # Default: build all
        builder.build_all()


if __name__ == "__main__":
    main()
