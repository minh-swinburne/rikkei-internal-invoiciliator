"""
Help dialog for displaying user guide and documentation.
"""
import re
import platform
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QPushButton, QLabel, QFrame, QMessageBox,
    QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from ..logging_config import get_module_logger
from ..utils import (
    get_project_root, 
    convert_markdown_to_html,
    format_markdown_code_block,
    is_markdown_list_paragraph, 
    format_markdown_list_to_html
)


class HelpSection:
    """Represents a section in the help documentation."""
    
    def __init__(self, title: str, content: str, level: int = 1):
        self.title = title
        self.content = content
        self.level = level
        self.subsections: List['HelpSection'] = []
    
    def add_subsection(self, section: 'HelpSection'):
        """Add a subsection to this section."""
        self.subsections.append(section)


class HelpParser:
    """Parser for converting markdown user guide to structured help content."""
    
    def __init__(self):
        self.logger = get_module_logger('gui.help_parser')
        self.document_title: Optional[str] = None
    
    def parse_file(self, file_path: Path) -> Tuple[List[HelpSection], Optional[str]]:
        """
        Parse a markdown file into structured help sections.
        
        Returns:
            Tuple of (sections list, document title from h1 header)
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Help file not found: {file_path}")
                return [], None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections, title = self.parse_content(content)
            return sections, title
            
        except Exception as e:
            self.logger.error(f"Error parsing help file: {e}")
            return [], None
    
    def parse_content(self, content: str) -> Tuple[List[HelpSection], Optional[str]]:
        """
        Parse markdown content into help sections.
        Only h2 headers (##) become main sections, everything else goes into content.
        
        Returns:
            Tuple of (sections list, document title from h1 header)
        """
        lines = content.split('\n')
        sections = []
        current_section = None
        current_content = []
        document_title = None
        
        for i, line in enumerate(lines):
            # Check for h1 header (document title)
            if line.strip().startswith('# ') and not line.strip().startswith('## '):
                if document_title is None:  # Only take the first h1
                    document_title = line.strip()[2:].strip()
                # h1 lines are not included in content
                continue
                
            # Check for h2 headers (main sections)
            elif line.strip().startswith('## '):
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # Start new section
                title = line.strip()[3:].strip()
                current_section = HelpSection(title, "", 2)
                current_content = []
                
            # Check for horizontal rule separators (use as section breaks)
            elif line.strip() == '---':
                # Save current section if we have one
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                    current_section = None
                    current_content = []
                # Don't include the separator line itself
                continue
                
            # Check for text file headers (lines with === or --- underneath) - for compatibility
            elif self._is_main_header(lines, i):
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # Start new section
                current_section = HelpSection(line.strip(), "", 1)
                current_content = []
                
            else:
                # Regular content line (including h3, h4, etc.)
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        return sections, document_title
    
    def _is_main_header(self, lines: List[str], index: int) -> bool:
        """Check if this line is a main header (followed by ===)."""
        if index < 0 or index >= len(lines) - 1:
            return False
        
        current_line = lines[index].strip()
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        
        # Main headers are followed by === or ===== etc.
        return (current_line and 
                next_line and 
                len(set(next_line)) == 1 and 
                next_line[0] == '=')


class HelpDialog(QDialog):
    """Help dialog that displays user guide and documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.help_dialog')
        self.sections: List[HelpSection] = []
        self.document_title: Optional[str] = None
        
        self.setup_ui()
        self.load_help_content()
        self.populate_tree()
    
    def setup_ui(self):
        """Set up the help dialog UI."""
        self.setWindowTitle("Invoice Reconciliator - User Guide")
        self.setModal(True)
        self.resize(900, 700)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title - will be updated after content is loaded
        self.title_label = QLabel("Invoice Reconciliator - User Guide")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(splitter)
        
        # Left side: Table of contents
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabel("Contents")
        self.toc_tree.setMaximumWidth(250)
        self.toc_tree.setMinimumWidth(200)
        self.toc_tree.itemClicked.connect(self.on_section_selected)
        splitter.addWidget(self.toc_tree)
        
        # Right side: Content display
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        
        # Use a more readable font for general content
        content_font = QFont()
        content_font.setFamily("Segoe UI")  # Modern, readable font on Windows
        content_font.setPointSize(10)
        self.content_display.setFont(content_font)
        
        splitter.addWidget(self.content_display)
        
        # Set splitter proportions
        splitter.setSizes([250, 650])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Open user guide file button
        open_file_btn = QPushButton("Open User Guide File")
        open_file_btn.clicked.connect(self.open_user_guide_file)
        button_layout.addWidget(open_file_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_help_content(self):
        """Load help content from the user guide file."""
        try:
            # Try to find the user guide file
            project_root = get_project_root()
            possible_paths = [
                project_root / "src" / "assets" / "USER_GUIDE.md",  # New comprehensive guide
                project_root / "dist" / "USER_GUIDE.txt",
                project_root / "USER_GUIDE.txt",
                project_root / "docs" / "USER_GUIDE.txt",
                project_root / "README.md"
            ]
            
            user_guide_path = None
            for path in possible_paths:
                if path.exists():
                    user_guide_path = path
                    break
            
            if user_guide_path:
                parser = HelpParser()
                self.sections, self.document_title = parser.parse_file(user_guide_path)
                self.logger.info(f"Loaded help content from: {user_guide_path}")
                if self.document_title:
                    self.logger.info(f"Document title: {self.document_title}")
            else:
                self.logger.warning("No user guide file found, using fallback content")
                self.sections = self.create_fallback_content()
                self.document_title = None
                
        except Exception as e:
            self.logger.error(f"Error loading help content: {e}")
            self.sections = self.create_fallback_content()
            self.document_title = None
    
    def create_fallback_content(self) -> List[HelpSection]:
        """Create fallback help content if user guide file is not found."""
        sections = []
        
        # Quick Start
        quick_start = HelpSection("Quick Start", """
1. Make sure you have your OpenRouter API key configured
2. Place PDF files in the data/input folder
3. Use the GUI to configure settings
4. Click 'Start Processing' to begin
5. Check results in the data/output folder

The application processes merged PDF files containing both invoices and purchase orders.
        """.strip())
        sections.append(quick_start)
        
        # Configuration
        config_section = HelpSection("Configuration", """
Before using the application:

1. API Key Setup:
   - Get an OpenRouter API key from https://openrouter.ai
   - Configure it in Settings > Configuration
   - Test the connection to ensure it works

2. Folder Setup:
   - Input folder: Place your PDF files here
   - Output folder: Processed results will appear here
   - The application creates these folders automatically

3. Processing Settings:
   - PIC Name: Person in charge name for stamping
   - Enable/disable PDF stamping
   - Adjust other processing options as needed
        """.strip())
        sections.append(config_section)
        
        # Troubleshooting
        troubleshooting = HelpSection("Troubleshooting", """
Common Issues:

1. Application won't start:
   - Check API key configuration
   - Ensure internet connection
   - Verify sufficient disk space

2. Processing fails:
   - Verify PDF files are readable (not just scanned images)
   - Check API key is valid and has credits
   - Ensure files contain both invoice and purchase order

3. Poor results:
   - Use high-quality PDF files
   - Ensure text is clearly readable
   - Check that vendor format is supported

For additional help, contact your IT support team.
        """.strip())
        sections.append(troubleshooting)
        
        return sections
    
    def populate_tree(self):
        """Populate the table of contents tree."""
        self.toc_tree.clear()
        
        # Update title label and window title if we have a document title
        if self.document_title:
            self.title_label.setText(self.document_title)
            self.setWindowTitle(self.document_title)
        
        for section in self.sections:
            # Create main section item (only h2 sections)
            section_item = QTreeWidgetItem(self.toc_tree, [section.title])
            section_item.setData(0, Qt.ItemDataRole.UserRole, section)
        
        # Expand all items
        self.toc_tree.expandAll()
        
        # Select first item if available
        if self.toc_tree.topLevelItemCount() > 0:
            first_item = self.toc_tree.topLevelItem(0)
            self.toc_tree.setCurrentItem(first_item)
            self.on_section_selected(first_item, 0)
    
    def on_section_selected(self, item: QTreeWidgetItem, column: int):
        """Handle section selection in the tree."""
        try:
            section = item.data(0, Qt.ItemDataRole.UserRole)
            if section:
                self.display_section_content(section)
        except Exception as e:
            self.logger.error(f"Error displaying section: {e}")
    
    def display_section_content(self, section: HelpSection):
        """Display the content of a help section using native markdown rendering."""
        try:
            # Add header title
            content = f"<h2>{section.title}</h2>\n\n"
            content += section.content.strip()

            # Use native markdown rendering - much simpler and better!
            self.content_display.setMarkdown(content)

        except Exception as e:
            self.logger.error(f"Error displaying section content: {e}")
            # Fallback to plain text if markdown fails
            self.content_display.setPlainText(section.content)
    
    def open_user_guide_file(self):
        """Open the user guide file in the system's default text editor."""
        try:
            import subprocess
            import platform
            
            # Try to find the user guide file
            project_root = get_project_root()
            possible_paths = [
                project_root / "src" / "assets" / "USER_GUIDE.md",  # New comprehensive guide
                project_root / "dist" / "USER_GUIDE.txt",
                project_root / "USER_GUIDE.txt",
                project_root / "docs" / "USER_GUIDE.txt"
            ]
            
            user_guide_path = None
            for path in possible_paths:
                if path.exists():
                    user_guide_path = path
                    break
            
            if user_guide_path:
                # Open with system default application
                if platform.system() == 'Windows':
                    import os
                    os.startfile(str(user_guide_path))
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', str(user_guide_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(user_guide_path)])
                
                self.logger.info(f"Opened user guide file: {user_guide_path}")
            else:
                QMessageBox.information(
                    self,
                    "File Not Found",
                    "User guide file not found.\n\n"
                    "The user guide should be located at:\n"
                    "• dist/USER_GUIDE.txt\n"
                    "• USER_GUIDE.txt\n"
                    "• docs/USER_GUIDE.txt"
                )
                
        except Exception as e:
            self.logger.error(f"Error opening user guide file: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not open user guide file:\n{str(e)}"
            )
