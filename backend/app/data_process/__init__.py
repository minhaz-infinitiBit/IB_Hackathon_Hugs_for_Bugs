"""
Data Processing Module

This module provides document extraction and preprocessing capabilities
for the backend application.

Main Components:
    - DocumentExtractor: Class for extracting content from documents
    - ExtractionResult: Dataclass containing extraction results
    - extract_document: Convenience function for quick extraction

Usage:
    from data_process import DocumentExtractor, extract_document
    
    # Using the class
    extractor = DocumentExtractor(device="cuda:0")
    result = extractor.extract("/path/to/document.pdf")
    
    # Using the convenience function
    result = extract_document("/path/to/document.pdf")
    
    if result.success:
        print(result.content)
        print(result.metadata)
"""

from .document_extractor import (
    DocumentExtractor,
    ExtractionResult,
    DocumentMetadata,
    extract_document,
)

__all__ = [
    "DocumentExtractor",
    "ExtractionResult", 
    "DocumentMetadata",
    "extract_document",
]
