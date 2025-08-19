"""
Application settings using Pydantic Settings for provider-agnostic configuration.
"""

from typing import Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load .env file
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
        default="anthropic/claude-3.5-sonnet:beta",
        description="Model identifier for LLM provider"
    )
    llm_max_retries: int = Field(default=3, description="Maximum retry attempts for API calls")
    llm_timeout_sec: int = Field(default=60, description="API timeout in seconds")
    
    # Application Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    concurrent_processing: bool = Field(default=True, description="Enable concurrent processing")

    # PDF Processing
    enable_stamping: bool = Field(default=True, description="Enable PDF approval stamping")
    stamp_pic_name: str = Field(default="Jane Smith", description="Name of PIC for PDF stamp")
    stamp_always_accept: bool = Field(default=True, description="Always stamp invoices as accepted")
    stamp_position: str = Field(default="bottom-right", description="Position for PDF stamps")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env
    }
    
    def __init__(self, **kwargs):
        # Load from multiple environment variable names
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
                "anthropic/claude-3.5-sonnet:beta"
            )
        
        super().__init__(**kwargs)
        
        # Validate required fields
        if not self.llm_api_key:
            raise ValueError(
                f"LLM API key is required. Set LLM_API_KEY or OPENROUTER_API_KEY environment variable.\n"
                f"Available env vars: {list(os.environ.keys())[:10]}..."
            )


# Global settings instance
settings = Settings()
