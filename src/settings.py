"""
Application settings using Pydantic Settings for provider-agnostic configuration.
"""

from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env file from current directory (will be updated in Settings __init__)
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings with provider-agnostic LLM configuration."""
    
    # LLM Provider Configuration (provider-agnostic)
    llm_api_key: Optional[str] = Field(default=None, description="API key for LLM provider")
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for LLM API"
    )
    llm_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="Model identifier for LLM provider"
    )
    llm_max_retries: int = Field(default=3, description="Maximum retry attempts for API calls")
    llm_timeout_sec: int = Field(default=60, description="API timeout in seconds")
    
    # Application Configuration
    input_dir: str = Field(default="data/input", description="Default input directory for PDF files")
    output_dir: str = Field(default="data/output", description="Default output directory for results")
    log_level: str = Field(default="INFO", description="Logging level")
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    concurrent_processing: bool = Field(default=True, description="Enable concurrent processing")

    # PDF Processing
    enable_stamping: bool = Field(default=True, description="Enable PDF approval stamping")
    stamp_pic_name: str = Field(default="Jane Smith", description="Name of PIC for PDF stamp")
    stamp_only_approved: bool = Field(default=False, description="Only stamp approved invoices, leave problematic ones unstamped")
    stamp_always_accept: bool = Field(default=False, description="Always stamp invoices as accepted")
    stamp_position: str = Field(default="bottom-right", description="Position for PDF stamps")
    stamp_offset: str = Field(default="20,200", description="Horizontal,Vertical offset for stamp position")
    
    # SSL/Network Configuration for Corporate Environments
    ssl_verify: bool = Field(default=True, description="Enable SSL certificate verification")
    ssl_cert_file: Optional[str] = Field(default=None, description="Path to custom SSL certificate file")
    disable_ssl_warnings: bool = Field(default=False, description="Disable SSL warnings")
    use_certifi: bool = Field(default=True, description="Use certifi package for SSL certificates")
    http_proxy: Optional[str] = Field(default=None, description="HTTP proxy URL")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS proxy URL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env
    }
    
    def __init__(self, **kwargs):
        # Load .env file from project root (avoiding circular import)
        try:
            import sys
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller bundle
                exe_dir = Path(sys.executable).parent
                env_file_path = exe_dir / ".env"
            else:
                # Development mode - find project root
                current = Path(__file__).parent.parent
                markers = ['main.py', '.git', 'requirements.txt', 'gui_launcher.py']
                for marker in markers:
                    if (current / marker).exists():
                        env_file_path = current / ".env"
                        break
                else:
                    env_file_path = current / ".env"
            
            if env_file_path.exists():
                load_dotenv(env_file_path, override=True)
        except Exception:
            # Fallback to current directory
            load_dotenv(".env", override=True)
        
        # Load from multiple environment variable names for LLM settings only
        if 'llm_api_key' not in kwargs:
            kwargs['llm_api_key'] = (
                os.getenv('LLM_API_KEY') or 
                os.getenv('OPENROUTER_API_KEY') or 
                os.getenv('OPENAI_API_KEY')
            )
        
        if 'llm_base_url' not in kwargs:
            kwargs['llm_base_url'] = (
                os.getenv('LLM_BASE_URL') or 
                os.getenv('OPENROUTER_BASE_URL') or 
                "https://openrouter.ai/api/v1"
            )
        
        if 'llm_model' not in kwargs:
            kwargs['llm_model'] = (
                os.getenv('LLM_MODEL') or 
                os.getenv('OPENROUTER_MODEL') or 
                "google/gemini-2.0-flash-001"
            )
        
        # Let Pydantic handle all other environment variables automatically
        super().__init__(**kwargs)
        
        # Note: API key validation is handled by the GUI - don't fail during initialization
        # This allows the GUI to start and prompt the user to configure the API key
    
    def validate_api_key(self) -> bool:
        """Check if API key is configured. Returns True if valid, False otherwise."""
        return bool(self.llm_api_key and self.llm_api_key.strip())
    
    def get_api_key_error(self) -> str:
        """Get a user-friendly error message for missing API key."""
        return (
            "LLM API key is required for processing invoices.\n"
            "Please configure your API key in Advanced Settings.\n"
            "You can get a free API key from OpenRouter.ai"
        )
    
    @property
    def stamp_offset_xy(self) -> tuple[int, int]:
        """Parse stamp offset string into (x, y) tuple."""
        try:
            x_str, y_str = self.stamp_offset.split(",")
            return int(x_str.strip()), int(y_str.strip())
        except (ValueError, AttributeError):
            # Return default offset if parsing fails
            return 20, 20


# Global settings instance
settings = Settings()
