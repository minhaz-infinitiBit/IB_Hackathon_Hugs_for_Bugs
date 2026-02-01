"""
LLM Client Module for Document Processing

This module provides LLM-based document analysis capabilities using GraphBit.

Components:
    - DocumentLLMClient: Main client for document analysis
    - DocumentAnalysisResult: Result dataclass
    - analyze_document_content: Convenience function

Usage:
    from app.agent.llm_client import DocumentLLMClient, analyze_document_content
    
    # Using the class
    client = DocumentLLMClient(api_key="your-key")
    result = client.analyze_document(content, "document.pdf")
    
    # Using the convenience function
    result = analyze_document_content(content, "document.pdf")
    
    if result.success:
        print(result.summary)
        print(result.keywords)
        print(result.structured_content)
"""

from .client import (
    DocumentLLMClient,
    DocumentAnalysisResult,
    analyze_document_content,
)
from .config import settings, LLMSettings
from .prompts import DocumentProcessingPrompts

__all__ = [
    "DocumentLLMClient",
    "DocumentAnalysisResult",
    "analyze_document_content",
    "settings",
    "LLMSettings",
    "DocumentProcessingPrompts",
]
