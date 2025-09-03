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
        
        # Network Configuration tab
        network_tab = self.create_network_tab()
        tab_widget.addTab(network_tab, "Network")
        
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
        self.always_accept_cb = QCheckBox("Always Accept (Stamp)")
        self.always_accept_cb.setToolTip("Automatically stamp all invoices as Accepted (use with caution)")
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
        self.stamp_offset_edit.setToolTip("Horizontal,Vertical offset in pixels (e.g., '20,200' for 20px right and 20px down)")
        self.stamp_offset_edit.setPlaceholderText("x,y (e.g., 20,200)")
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
    
    def create_network_tab(self) -> QWidget:
        """Create the network configuration tab for corporate environments."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # SSL Configuration Group
        ssl_group = QGroupBox("SSL Configuration (Corporate Networks)")
        ssl_layout = QFormLayout(ssl_group)
        
        # SSL Verification checkbox
        self.ssl_verify_cb = QCheckBox("Enable SSL Certificate Verification")
        self.ssl_verify_cb.setChecked(True)  # Default to secure
        self.ssl_verify_cb.setToolTip("Uncheck this if you get SSL certificate errors in corporate networks")
        self.ssl_verify_cb.stateChanged.connect(self._on_ssl_verify_changed)
        ssl_layout.addRow("SSL Verification:", self.ssl_verify_cb)
        
        # SSL Warning label
        self.ssl_warning_label = QLabel()
        self.ssl_warning_label.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")
        self.ssl_warning_label.setWordWrap(True)
        self.ssl_warning_label.hide()
        ssl_layout.addRow("", self.ssl_warning_label)
        
        # Use certifi checkbox
        self.use_certifi_cb = QCheckBox("Use certifi certificate bundle")
        self.use_certifi_cb.setChecked(True)  # Default enabled
        self.use_certifi_cb.setToolTip("Use up-to-date CA certificates from certifi package")
        ssl_layout.addRow("Certificate Bundle:", self.use_certifi_cb)
        
        # Disable SSL warnings checkbox
        self.disable_ssl_warnings_cb = QCheckBox("Disable SSL warnings")
        self.disable_ssl_warnings_cb.setEnabled(False)  # Only enabled when SSL is disabled
        self.disable_ssl_warnings_cb.setToolTip("Suppress SSL warning messages in logs")
        ssl_layout.addRow("SSL Warnings:", self.disable_ssl_warnings_cb)
        
        # Custom CA certificate file
        ca_layout = QHBoxLayout()
        self.ssl_cert_file_edit = QLineEdit()
        self.ssl_cert_file_edit.setPlaceholderText("Path to custom SSL certificate file (optional)")
        self.ssl_cert_file_edit.setToolTip("Custom SSL certificate file for corporate environments")
        ca_browse_btn = QPushButton("Browse...")
        ca_browse_btn.clicked.connect(self._browse_ssl_cert_file)
        ca_layout.addWidget(self.ssl_cert_file_edit)
        ca_layout.addWidget(ca_browse_btn)
        ssl_layout.addRow("Custom Certificate:", ca_layout)
        
        layout.addWidget(ssl_group)
        
        # Proxy Configuration Group
        proxy_group = QGroupBox("Proxy Settings (Corporate Networks)")
        proxy_layout = QFormLayout(proxy_group)
        
        # HTTP Proxy
        self.http_proxy_edit = QLineEdit()
        self.http_proxy_edit.setPlaceholderText("http://proxy.company.com:8080")
        self.http_proxy_edit.setToolTip("HTTP proxy server for corporate networks")
        proxy_layout.addRow("HTTP Proxy:", self.http_proxy_edit)
        
        # HTTPS Proxy
        self.https_proxy_edit = QLineEdit()
        self.https_proxy_edit.setPlaceholderText("https://proxy.company.com:8080")
        self.https_proxy_edit.setToolTip("HTTPS proxy server for corporate networks")
        proxy_layout.addRow("HTTPS Proxy:", self.https_proxy_edit)
        
        layout.addWidget(proxy_group)
        
        # Test Connection Button
        test_connection_btn = QPushButton("Test Network Connection")
        test_connection_btn.setToolTip("Test API connection with current network settings")
        test_connection_btn.clicked.connect(self._test_network_connection)
        layout.addWidget(test_connection_btn)
        
        # Help Information
        help_label = QLabel(
            "<b>ℹ️ Corporate Network Help:</b><br>"
            "• <b>SSL Certificate Errors:</b> Uncheck 'Enable SSL Certificate Verification'<br>"
            "• <b>Connection Issues:</b> Configure proxy settings above<br>"
            "• <b>Contact IT:</b> Ask for proper SSL certificates or network access<br>"
            "• <b>Test Connection:</b> Use the button above to verify settings work"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px; margin: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(help_label)
        
        layout.addStretch()
        
        return tab
    
    def _on_ssl_verify_changed(self, state: int) -> None:
        """Handle SSL verification checkbox changes."""
        ssl_enabled = state == Qt.CheckState.Checked.value
        
        if not ssl_enabled:
            self.ssl_warning_label.setText("⚠️ SSL verification is DISABLED - Use only in corporate environments!")
            self.ssl_warning_label.show()
            self.disable_ssl_warnings_cb.setEnabled(True)
            self.disable_ssl_warnings_cb.setChecked(True)
        else:
            self.ssl_warning_label.hide()
            self.disable_ssl_warnings_cb.setEnabled(False)
            self.disable_ssl_warnings_cb.setChecked(False)
    
    def _browse_ssl_cert_file(self) -> None:
        """Browse for SSL certificate file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSL Certificate File",
            "",
            "Certificate files (*.pem *.crt *.cert *.ca-bundle);;All files (*.*)"
        )
        
        if file_path:
            self.ssl_cert_file_edit.setText(file_path)
    
    def _test_network_connection(self) -> None:
        """Test network connection with current settings."""
        # Apply current settings temporarily
        self._apply_network_settings_temporarily()
        
        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("Testing Network Connection")
        progress.setText("Testing API connection with current network settings...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        
        try:
            # Test the LLM connection
            from ..core.services.llm_extractor import LLMExtractor
            
            # This will use the current settings including SSL configuration
            extractor = LLMExtractor()
            
            # Test a simple API call
            success = extractor.test_structured_output_support()
            
            progress.accept()
            
            if success:
                QMessageBox.information(
                    self,
                    "Network Test Successful",
                    "✅ Network connection test passed!\n\n"
                    "The application can successfully connect to the AI service "
                    "with your current network settings."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Network Test Completed with Issues",
                    "⚠️ Network connection was established but with some limitations.\n\n"
                    "The application may work but some features might be limited.\n"
                    "Check the log viewer for more details."
                )
        
        except Exception as e:
            progress.accept()
            
            error_msg = str(e)
            if "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
                QMessageBox.critical(
                    self,
                    "SSL Certificate Error",
                    "🔒 SSL Certificate verification failed!\n\n"
                    "This is common in corporate networks with SSL interception.\n\n"
                    "💡 Solution: Uncheck 'Enable SSL Certificate Verification' "
                    "and test again.\n\n"
                    f"Technical details: {error_msg[:200]}..."
                )
            elif "connection" in error_msg.lower():
                QMessageBox.critical(
                    self,
                    "Network Connection Error",
                    "🌐 Network connection failed!\n\n"
                    "This may be due to firewall or proxy restrictions.\n\n"
                    "💡 Solutions:\n"
                    "• Configure proxy settings if required\n"
                    "• Check firewall allows HTTPS connections\n"
                    "• Try from a different network\n\n"
                    f"Technical details: {error_msg[:200]}..."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Network Test Failed",
                    f"❌ Network connection test failed:\n\n{error_msg[:300]}...\n\n"
                    "Check your network settings and API key, then try again."
                )
    
    def _apply_network_settings_temporarily(self) -> None:
        """Temporarily apply network settings for testing."""
        # Store current settings
        import os
        
        # Apply SSL settings
        os.environ['SSL_VERIFY'] = 'true' if self.ssl_verify_cb.isChecked() else 'false'
        os.environ['USE_CERTIFI'] = 'true' if self.use_certifi_cb.isChecked() else 'false'
        os.environ['DISABLE_SSL_WARNINGS'] = 'true' if self.disable_ssl_warnings_cb.isChecked() else 'false'
        
        if self.ssl_cert_file_edit.text().strip():
            os.environ['SSL_CERT_FILE'] = self.ssl_cert_file_edit.text().strip()
        
        # Apply proxy settings
        if self.http_proxy_edit.text().strip():
            os.environ['HTTP_PROXY'] = self.http_proxy_edit.text().strip()
        
        if self.https_proxy_edit.text().strip():
            os.environ['HTTPS_PROXY'] = self.https_proxy_edit.text().strip()
    
    def load_current_settings(self):
        """Load current settings into the dialog."""
        import os
        
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
        
        # Network tab - Load from settings object first, then environment variables as fallback
        ssl_verify = getattr(settings, 'ssl_verify', True)
        self.ssl_verify_cb.setChecked(ssl_verify)
        
        use_certifi = getattr(settings, 'use_certifi', True)
        self.use_certifi_cb.setChecked(use_certifi)
        
        disable_ssl_warnings = getattr(settings, 'disable_ssl_warnings', False)
        self.disable_ssl_warnings_cb.setChecked(disable_ssl_warnings)
        
        ssl_cert_file = getattr(settings, 'ssl_cert_file', '') or ''
        self.ssl_cert_file_edit.setText(ssl_cert_file)
        
        http_proxy = getattr(settings, 'http_proxy', '') or ''
        self.http_proxy_edit.setText(http_proxy)
        
        https_proxy = getattr(settings, 'https_proxy', '') or ''
        self.https_proxy_edit.setText(https_proxy)
    
    def save_settings(self):
        """Save the current settings."""
        try:
            import os
            
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
            
            # Network settings - Update both settings object and environment
            settings.ssl_verify = self.ssl_verify_cb.isChecked()
            settings.use_certifi = self.use_certifi_cb.isChecked()
            settings.disable_ssl_warnings = self.disable_ssl_warnings_cb.isChecked()
            settings.ssl_cert_file = self.ssl_cert_file_edit.text().strip() or None
            settings.http_proxy = self.http_proxy_edit.text().strip() or None
            settings.https_proxy = self.https_proxy_edit.text().strip() or None
            
            # Also apply to environment for immediate effect
            os.environ['SSL_VERIFY'] = 'true' if self.ssl_verify_cb.isChecked() else 'false'
            os.environ['USE_CERTIFI'] = 'true' if self.use_certifi_cb.isChecked() else 'false'
            os.environ['DISABLE_SSL_WARNINGS'] = 'true' if self.disable_ssl_warnings_cb.isChecked() else 'false'
            
            ssl_cert_file = self.ssl_cert_file_edit.text().strip()
            if ssl_cert_file:
                os.environ['SSL_CERT_FILE'] = ssl_cert_file
            elif 'SSL_CERT_FILE' in os.environ:
                del os.environ['SSL_CERT_FILE']
            
            http_proxy = self.http_proxy_edit.text().strip()
            if http_proxy:
                os.environ['HTTP_PROXY'] = http_proxy
            elif 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            
            https_proxy = self.https_proxy_edit.text().strip()
            if https_proxy:
                os.environ['HTTPS_PROXY'] = https_proxy
            elif 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
            
            # Save to .env file if requested
            if self.save_to_env_cb.isChecked():
                self.save_to_env_file()
            
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
            self.logger.info("Settings saved successfully.")
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
CONCURRENT_PROCESSING={'true' if settings.concurrent_processing else 'false'}

# PDF Stamping Settings
ENABLE_STAMPING={'true' if settings.enable_stamping else 'false'}
STAMP_PIC_NAME={settings.stamp_pic_name}
STAMP_ALWAYS_ACCEPT={'true' if settings.stamp_always_accept else 'false'}
STAMP_POSITION={settings.stamp_position}
STAMP_OFFSET={settings.stamp_offset}

# Network Configuration (Corporate Environments)
SSL_VERIFY={'true' if self.ssl_verify_cb.isChecked() else 'false'}
USE_CERTIFI={'true' if self.use_certifi_cb.isChecked() else 'false'}
DISABLE_SSL_WARNINGS={'true' if self.disable_ssl_warnings_cb.isChecked() else 'false'}
"""

        # Add optional network settings only if they have values
        ssl_cert_file = self.ssl_cert_file_edit.text().strip()
        if ssl_cert_file:
            env_content += f"SSL_CERT_FILE={ssl_cert_file}\n"
        
        http_proxy = self.http_proxy_edit.text().strip()
        if http_proxy:
            env_content += f"HTTP_PROXY={http_proxy}\n"
        
        https_proxy = self.https_proxy_edit.text().strip()
        if https_proxy:
            env_content += f"HTTPS_PROXY={https_proxy}\n"
        
        try:
            with open(env_path, 'w') as f:
                f.write(env_content)
            self.logger.info(f"Settings saved to {env_path}")
        except Exception as e:
            self.logger.error(f"Failed to write .env file: {e}")
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
            self.stamp_offset_edit.setText("20,200")
            self.log_level_combo.setCurrentText("INFO")
            self.max_file_size_spin.setValue(10)
            self.concurrent_processing_cb.setChecked(True)
            
            # LLM defaults
            self.model_edit.setText("google/gemini-2.0-flash-001")
            self.base_url_edit.setText("https://openrouter.ai/api/v1")
            self.max_retries_spin.setValue(3)
            self.timeout_spin.setValue(60)
            
            # Network defaults (secure by default)
            self.ssl_verify_cb.setChecked(True)
            self.use_certifi_cb.setChecked(True)
            self.disable_ssl_warnings_cb.setChecked(False)
            self.ssl_cert_file_edit.clear()
            self.http_proxy_edit.clear()
            self.https_proxy_edit.clear()
    
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
            
            self.logger.info("LLM connection test successful.")
            self.connection_status_label.setText("✅ Connection successful")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Connection Test", "LLM connection test successful!")
            
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {e}")
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
