"""
Help dialog for displaying user guide and documentation.
"""
import re
from pathlib import Path
from typing import List, Tuple, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QPushButton, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from ..logging_config import get_module_logger
from ..utils import get_project_root


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
    """Parser for converting text-based user guide to structured help content."""
    
    def __init__(self):
        self.logger = get_module_logger('gui.help_parser')
    
    def parse_file(self, file_path: Path) -> List[HelpSection]:
        """Parse a text file into structured help sections."""
        try:
            if not file_path.exists():
                self.logger.error(f"Help file not found: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content)
            
        except Exception as e:
            self.logger.error(f"Error parsing help file: {e}")
            return []
    
    def parse_content(self, content: str) -> List[HelpSection]:
        """Parse text content into help sections."""
        lines = content.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line in lines:
            # Check for section headers (lines with === or --- underneath)
            if self._is_main_header(lines, lines.index(line) if line in lines else -1):
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # Start new section
                current_section = HelpSection(line.strip(), "", 1)
                current_content = []
                
            elif self._is_sub_header(line):
                # Handle subsections
                if current_section:
                    # Save content so far to current section
                    if current_content:
                        current_section.content = '\n'.join(current_content).strip()
                        current_content = []
                    
                    # Create subsection
                    subsection_title = line.strip().rstrip('-').strip()
                    subsection = HelpSection(subsection_title, "", 2)
                    current_section.add_subsection(subsection)
                    # The subsection content will be collected until next header
                    
            else:
                # Regular content line
                current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        return sections
    
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
    
    def _is_sub_header(self, line: str) -> bool:
        """Check if this line is a subheader (ends with many dashes)."""
        stripped = line.strip()
        # Subheaders typically end with --- or -----
        return (stripped and 
                stripped.endswith('---') and 
                len(stripped) > 10)


class HelpDialog(QDialog):
    """Help dialog that displays user guide and documentation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.help_dialog')
        self.sections: List[HelpSection] = []
        
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
        
        # Title
        title_label = QLabel("Invoice Reconciliator - User Guide")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
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
        self.content_display.setFont(QFont("Consolas", 10))  # Monospace font for better text display
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
                self.sections = parser.parse_file(user_guide_path)
                self.logger.info(f"Loaded help content from: {user_guide_path}")
            else:
                self.logger.warning("No user guide file found, using fallback content")
                self.sections = self.create_fallback_content()
                
        except Exception as e:
            self.logger.error(f"Error loading help content: {e}")
            self.sections = self.create_fallback_content()
    
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
        
        for section in self.sections:
            # Create main section item
            section_item = QTreeWidgetItem(self.toc_tree, [section.title])
            section_item.setData(0, Qt.ItemDataRole.UserRole, section)
            
            # Add subsections if any
            for subsection in section.subsections:
                subsection_item = QTreeWidgetItem(section_item, [subsection.title])
                subsection_item.setData(0, Qt.ItemDataRole.UserRole, subsection)
        
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
        """Display the content of a help section."""
        try:
            content = f"<h2>{section.title}</h2>\n\n"
            
            # Convert plain text to basic HTML formatting
            formatted_content = self.format_text_content(section.content)
            content += formatted_content
            
            # Add subsections if this is a main section with subsections
            if section.subsections:
                for subsection in section.subsections:
                    content += f"\n\n<h3>{subsection.title}</h3>\n"
                    content += self.format_text_content(subsection.content)
            
            self.content_display.setHtml(content)
            
        except Exception as e:
            self.logger.error(f"Error formatting section content: {e}")
            self.content_display.setPlainText(section.content)
    
    def format_text_content(self, text: str) -> str:
        """Convert plain text to basic HTML formatting."""
        if not text:
            return ""
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # Check if it's a list
            if self._is_list_paragraph(paragraph):
                formatted_paragraphs.append(self._format_list(paragraph))
            else:
                # Regular paragraph
                formatted_text = paragraph.replace('\n', '<br>')
                formatted_paragraphs.append(f"<p>{formatted_text}</p>")
        
        return '\n'.join(formatted_paragraphs)
    
    def _is_list_paragraph(self, paragraph: str) -> bool:
        """Check if a paragraph is a list."""
        lines = paragraph.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check if most lines start with numbers or dashes
        list_lines = 0
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '•', '*')) or
                re.match(r'^\d+\.', stripped)):
                list_lines += 1
        
        return list_lines >= len(lines) * 0.6  # At least 60% of lines are list items
    
    def _format_list(self, paragraph: str) -> str:
        """Format a paragraph as an HTML list."""
        lines = paragraph.strip().split('\n')
        list_items = []
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Remove common list prefixes
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '•', '*']:
                    if stripped.startswith(prefix):
                        stripped = stripped[len(prefix):].strip()
                        break
                
                # Also handle numbered lists
                stripped = re.sub(r'^\d+\.\s*', '', stripped)
                
                if stripped:
                    list_items.append(f"<li>{stripped}</li>")
        
        if list_items:
            return f"<ul>{''.join(list_items)}</ul>"
        else:
            return f"<p>{paragraph}</p>"
    
    def open_user_guide_file(self):
        """Open the user guide file in the system's default text editor."""
        try:
            import subprocess
            import platform
            
            # Try to find the user guide file
            project_root = get_project_root()
            possible_paths = [
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
