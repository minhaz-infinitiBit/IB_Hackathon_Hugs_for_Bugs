"""
Configuration for LLM Client

Handles environment variables and default settings for GraphBit Azure LLM operations.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class LLMSettings:
    """Settings for GraphBit Azure LLM operations."""
    
    # Azure LLM settings (used with GraphBit's LlmConfig.azure_openai())
    azure_api_key: str = ""
    azure_endpoint: str = ""
    azure_api_version: str = "2024-10-21"  # GraphBit recommended version
    azure_deployment: str = ""
    azure_deployment_embeddings: str = ""
    
    # Default parameters
    max_tokens: int = 2000
    temperature: float = 0.3
    timeout_seconds: int = 120
    
    @classmethod
    def from_env(cls) -> "LLMSettings":
        """Load settings from environment variables."""
        return cls(
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            azure_deployment_embeddings=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDINGS", ""),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
        )
    
    def validate(self) -> bool:
        """Check if settings are valid."""
        if not self.azure_api_key:
            return False
        if not self.azure_endpoint:
            return False
        if not self.azure_deployment:
            return False
        return True


# Global settings instance
settings = LLMSettings.from_env()
