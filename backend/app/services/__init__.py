"""
Services Module

This module provides various services for the backend application.

Main Components:
    - DocumentPreprocessService: Service for document preprocessing
    - PreprocessResult: Result dataclass for preprocessing
    - process_document_file: Convenience function
    - ClassificationService: Service for document classification
    - ClassificationServiceResult: Result dataclass for classification
    - run_classification_service: Convenience function
"""

from .preprocess_document import (
    DocumentPreprocessService,
    PreprocessResult,
    process_document_file,
)
from .classification_service import (
    ClassificationService,
    ClassificationServiceResult,
    run_classification_service,
)

__all__ = [
    # Preprocessing
    "DocumentPreprocessService",
    "PreprocessResult",
    "process_document_file",
    # Classification
    "ClassificationService",
    "ClassificationServiceResult",
    "run_classification_service",
]
