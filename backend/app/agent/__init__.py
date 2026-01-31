"""
Document Classification Agent Module

This module provides an AI agent for classifying tax documents into 20 categories
using GraphBit workflow with mem0 memory layer for context tracking.

Structure:
- classification_agent.py: Main agent class with workflow_validate method
- prompts/: Prompt templates (ClassifierPrompt, SingleDocumentPrompt, ReclassificationPrompt)
- tools/: Agent tools (get_categories, classify_document, save_classification_results, etc.)
- memory.py: Memory management using mem0 with Qdrant
"""

from .classification_agent import (
    ClassificationAgent,
    ClassificationResult,
    run_classification,
)
from .prompts import (
    BasePrompt,
    ClassifierPrompt,
    SingleDocumentPrompt,
    ReclassificationPrompt,
)
from .tools import (
    get_categories,
    classify_document,
    save_classification_results,
    get_classification_history,
    CLASSIFIER_TOOLS,
)
from .memory import (
    MemoryManager,
    get_memory_manager,
    reset_memory_manager,
)

__all__ = [
    # Main agent
    "ClassificationAgent",
    "ClassificationResult",
    "run_classification",
    # Prompts
    "BasePrompt",
    "ClassifierPrompt",
    "SingleDocumentPrompt",
    "ReclassificationPrompt",
    # Tools
    "get_categories",
    "classify_document",
    "save_classification_results",
    "get_classification_history",
    "CLASSIFIER_TOOLS",
    # Memory
    "MemoryManager",
    "get_memory_manager",
    "reset_memory_manager",
]
