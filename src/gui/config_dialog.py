"""
Configuration dialog for the invoice reconciliation GUI application.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QPushButton, QLineEdit, QLabel, QComboBox, 
    QCheckBox, QSpinBox, QTabWidget, QWidget, QTextEdit,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt

from ..settings import settings
from ..utils import get_project_root
from ..logging_config import get_module_logger


class ConfigDialog(QDialog):
    """Advanced configuration dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_module_logger('gui.config_dialog')
        
        # Store original settings for cancel functionality
        self.original_settings = {}
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Invoice Reconciliator - Settings")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Processing tab
        processing_tab = self.create_processing_tab()
        tab_widget.addTab(processing_tab, "Processing")
        
        # LLM Configuration tab
        llm_tab = self.create_llm_tab()
        tab_widget.addTab(llm_tab, "LLM Configuration")
        
        # File Management tab
        file_tab = self.create_file_management_tab()
        tab_widget.addTab(file_tab, "File Management")
        
        # Button layout
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.setToolTip("Test the API connection to verify your settings work")
        test_btn.clicked.connect(self.test_llm_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save all settings and optionally write to .env file")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Cancel changes and close settings dialog")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setToolTip("Reset all settings to default values")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
    
    def create_processing_tab(self) -> QWidget:
        """Create the processing configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # PDF Processing group
        pdf_group = QGroupBox("PDF Processing")
        pdf_layout = QFormLayout(pdf_group)
        
        # Enable stamping
        self.enable_stamping_cb = QCheckBox("Enable PDF Stamping")
        self.enable_stamping_cb.setToolTip("Add approval stamps to processed PDF files")
        pdf_layout.addRow(self.enable_stamping_cb)
        
        # Always accept
        self.always_accept_cb = QCheckBox("Always Accept (Auto-approve all)")
        self.always_accept_cb.setToolTip("Automatically approve all invoices without validation (use with caution)")
        pdf_layout.addRow(self.always_accept_cb)
        
        # PIC Name
        self.pic_name_edit = QLineEdit()
        self.pic_name_edit.setToolTip("Name of person in charge to include on PDF stamps")
        pdf_layout.addRow("PIC Name:", self.pic_name_edit)
        
        # Stamp position
        self.stamp_position_combo = QComboBox()
        self.stamp_position_combo.setToolTip("Where to place approval stamps on PDF pages")
        self.stamp_position_combo.addItems([
            "top-left", "top-right", "bottom-left", "bottom-right"
        ])
        pdf_layout.addRow("Stamp Position:", self.stamp_position_combo)
        
        # Stamp offset
        self.stamp_offset_edit = QLineEdit()
        self.stamp_offset_edit.setToolTip("Horizontal,Vertical offset in pixels (e.g., '20,20' for 20px right and 20px down)")
        self.stamp_offset_edit.setPlaceholderText("x,y (e.g., 20,20)")
        pdf_layout.addRow("Stamp Offset:", self.stamp_offset_edit)
        
        layout.addWidget(pdf_group)
        
        # General Processing group
        general_group = QGroupBox("General Processing")
        general_layout = QFormLayout(general_group)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.setToolTip("Detail level for application logs (DEBUG shows most detail)")
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        general_layout.addRow("Log Level:", self.log_level_combo)
        
        # Max file size
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setToolTip("Maximum PDF file size to process (larger files may timeout)")
        self.max_file_size_spin.setRange(1, 100)
        self.max_file_size_spin.setSuffix(" MB")
        general_layout.addRow("Max File Size:", self.max_file_size_spin)
        
        # Concurrent processing
        self.concurrent_processing_cb = QCheckBox("Enable Concurrent Processing")
        self.concurrent_processing_cb.setToolTip("Process multiple files simultaneously for faster performance")
        general_layout.addRow(self.concurrent_processing_cb)
        
        layout.addWidget(general_group)
        layout.addStretch()
        
        return tab
    
    def create_llm_tab(self) -> QWidget:
        """Create the LLM configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Warning message
        warning_label = QLabel(
            "⚠️ Warning: Only change settings below if you know what you're doing!\n"
            "Most users only need to set the API Key. Other settings are pre-configured for optimal performance."
        )
        warning_label.setStyleSheet(
            "QLabel { "
            "background-color: #fff3cd; "
            "border: 1px solid #ffeaa7; "
            "border-radius: 4px; "
            "padding: 8px; "
            "color: #856404; "
            "font-weight: bold; "
            "}"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # LLM Configuration group
        llm_group = QGroupBox("LLM Configuration")
        llm_layout = QFormLayout(llm_group)
        
        # Provider selection (for future use)
        self.provider_combo = QComboBox()
        self.provider_combo.setToolTip("AI service provider (currently supports OpenRouter)")
        self.provider_combo.addItems(["OpenRouter", "OpenAI", "Other"])
        llm_layout.addRow("Provider:", self.provider_combo)
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setToolTip("Your OpenRouter API key (required for processing)")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        llm_layout.addRow("API Key:", self.api_key_edit)
        
        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setToolTip("AI model to use (default: google/gemini-2.0-flash-001)")
        llm_layout.addRow("Model:", self.model_edit)
        
        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setToolTip("API endpoint URL (keep default unless using custom service)")
        llm_layout.addRow("Base URL:", self.base_url_edit)
        
        # Max retries
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setToolTip("Number of times to retry failed API requests")
        self.max_retries_spin.setRange(1, 10)
        llm_layout.addRow("Max Retries:", self.max_retries_spin)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setToolTip("How long to wait for API responses before timing out")
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" seconds")
        llm_layout.addRow("Timeout:", self.timeout_spin)
        
        layout.addWidget(llm_group)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status_label = QLabel("Not tested")
        status_layout.addWidget(self.connection_status_label)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return tab
    
    def create_file_management_tab(self) -> QWidget:
        """Create the file management configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File Management group
        file_group = QGroupBox("File Management")
        file_layout = QFormLayout(file_group)
        
        # Save settings to .env
        self.save_to_env_cb = QCheckBox("Save settings to .env file")
        file_layout.addRow(self.save_to_env_cb)
        
        # Create backup
        self.create_backup_cb = QCheckBox("Create backup of processed files")
        file_layout.addRow(self.create_backup_cb)
        
        # Auto-organize by vendor
        self.auto_organize_cb = QCheckBox("Auto-organize by vendor")
        file_layout.addRow(self.auto_organize_cb)
        
        layout.addWidget(file_group)
        
        # Environment File group
        env_group = QGroupBox("Environment File")
        env_layout = QVBoxLayout(env_group)
        
        env_info = QLabel(
            "The .env file contains sensitive configuration like API keys.\n"
            "Enable 'Save settings to .env file' to persist changes."
        )
        env_info.setWordWrap(True)
        env_layout.addWidget(env_info)
        
        # Show current .env path
        env_path = get_project_root() / ".env"
        env_path_label = QLabel(f"Location: {env_path}")
        env_path_label.setStyleSheet("font-family: monospace; font-size: 9pt;")
        env_layout.addWidget(env_path_label)
        
        layout.addWidget(env_group)
        layout.addStretch()
        
        return tab
    
    def load_current_settings(self):
        """Load current settings into the dialog."""
        # Store original settings
        self.original_settings = {
            'input_dir': settings.input_dir,
            'output_dir': settings.output_dir,
            'enable_stamping': settings.enable_stamping,
            'stamp_always_accept': settings.stamp_always_accept,
            'stamp_pic_name': settings.stamp_pic_name,
            'stamp_position': settings.stamp_position,
            'stamp_offset': settings.stamp_offset,
            'log_level': settings.log_level,
            'max_file_size_mb': settings.max_file_size_mb,
            'concurrent_processing': settings.concurrent_processing,
            'llm_api_key': settings.llm_api_key,
            'llm_model': settings.llm_model,
            'llm_base_url': settings.llm_base_url,
            'llm_max_retries': settings.llm_max_retries,
            'llm_timeout_sec': settings.llm_timeout_sec,
        }
        
        # Processing tab
        self.enable_stamping_cb.setChecked(settings.enable_stamping)
        self.always_accept_cb.setChecked(settings.stamp_always_accept)
        self.pic_name_edit.setText(settings.stamp_pic_name)
        self.stamp_position_combo.setCurrentText(settings.stamp_position)
        self.stamp_offset_edit.setText(settings.stamp_offset)
        self.log_level_combo.setCurrentText(settings.log_level)
        self.max_file_size_spin.setValue(settings.max_file_size_mb)
        self.concurrent_processing_cb.setChecked(settings.concurrent_processing)
        
        # LLM tab
        self.api_key_edit.setText(settings.llm_api_key or "")
        self.model_edit.setText(settings.llm_model)
        self.base_url_edit.setText(settings.llm_base_url)
        self.max_retries_spin.setValue(settings.llm_max_retries)
        self.timeout_spin.setValue(settings.llm_timeout_sec)
        
        # File management tab
        self.save_to_env_cb.setChecked(True)  # Default to enabled
        self.create_backup_cb.setChecked(False)  # Feature not implemented yet
        self.auto_organize_cb.setChecked(False)  # Feature not implemented yet
    
    def save_settings(self):
        """Save the current settings."""
        try:
            # Update settings object
            settings.enable_stamping = self.enable_stamping_cb.isChecked()
            settings.stamp_always_accept = self.always_accept_cb.isChecked()
            settings.stamp_pic_name = self.pic_name_edit.text().strip()
            settings.stamp_position = self.stamp_position_combo.currentText()
            settings.stamp_offset = self.stamp_offset_edit.text().strip()
            settings.log_level = self.log_level_combo.currentText()
            settings.max_file_size_mb = self.max_file_size_spin.value()
            settings.concurrent_processing = self.concurrent_processing_cb.isChecked()
            
            # LLM settings
            settings.llm_api_key = self.api_key_edit.text().strip()
            settings.llm_model = self.model_edit.text().strip()
            settings.llm_base_url = self.base_url_edit.text().strip()
            settings.llm_max_retries = self.max_retries_spin.value()
            settings.llm_timeout_sec = self.timeout_spin.value()
            
            # Save to .env file if requested
            if self.save_to_env_cb.isChecked():
                self.save_to_env_file()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            self.logger.error(f"Failed to save settings: {e}")
    
    def save_to_env_file(self):
        """Save settings to .env file."""
        env_path = get_project_root() / ".env"
        
        # Create .env content
        env_content = f"""# LLM Configuration
LLM_API_KEY={settings.llm_api_key}
LLM_MODEL={settings.llm_model}
LLM_BASE_URL={settings.llm_base_url}
LLM_MAX_RETRIES={settings.llm_max_retries}
LLM_TIMEOUT_SECONDS={settings.llm_timeout_sec}

# Application Settings
INPUT_DIR={settings.input_dir}
OUTPUT_DIR={settings.output_dir}
LOG_LEVEL={settings.log_level}
MAX_FILE_SIZE_MB={settings.max_file_size_mb}
CONCURRENT_PROCESSING={settings.concurrent_processing}

# PDF Stamping Settings
ENABLE_STAMPING={settings.enable_stamping}
STAMP_PIC_NAME={settings.stamp_pic_name}
STAMP_ALWAYS_ACCEPT={settings.stamp_always_accept}
STAMP_POSITION={settings.stamp_position}
STAMP_OFFSET={settings.stamp_offset}
"""
        
        try:
            with open(env_path, 'w') as f:
                f.write(env_content)
            self.logger.info(f"Settings saved to {env_path}")
        except Exception as e:
            raise Exception(f"Failed to write .env file: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to defaults
            self.enable_stamping_cb.setChecked(True)
            self.always_accept_cb.setChecked(True)
            self.pic_name_edit.setText("Jane Smith")
            self.stamp_position_combo.setCurrentText("bottom-right")
            self.stamp_offset_edit.setText("20,20")
            self.log_level_combo.setCurrentText("INFO")
            self.max_file_size_spin.setValue(10)
            self.concurrent_processing_cb.setChecked(True)
            
            # LLM defaults
            self.model_edit.setText("google/gemini-2.0-flash-001")
            self.base_url_edit.setText("https://openrouter.ai/api/v1")
            self.max_retries_spin.setValue(3)
            self.timeout_spin.setValue(60)
    
    def test_llm_connection(self):
        """Test the LLM connection."""
        try:
            # Create a temporary settings object with current values
            from openai import OpenAI
            
            api_key = self.api_key_edit.text().strip()
            base_url = self.base_url_edit.text().strip()
            
            if not api_key:
                QMessageBox.warning(self, "Missing API Key", "Please enter an API key to test the connection.")
                return
            
            # Test connection
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # Simple test request
            response = client.chat.completions.create(
                model=self.model_edit.text().strip(),
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            self.connection_status_label.setText("✅ Connection successful")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Connection Test", "LLM connection test successful!")
            
        except Exception as e:
            self.connection_status_label.setText("❌ Connection failed")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "Connection Test Failed", f"Failed to connect to LLM:\n\n{str(e)}")
    
    def reject(self):
        """Handle dialog rejection (cancel)."""
        # Restore original settings
        for key, value in self.original_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        super().reject()
