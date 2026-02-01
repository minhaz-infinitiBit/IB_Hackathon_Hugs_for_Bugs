"""
Prompts Module for Classification Agent

Contains all prompt templates used by the document classification agent.
"""

from .base_prompt import BasePrompt
from .classifier_prompt import ClassifierPrompt
from .single_document_prompt import SingleDocumentPrompt
from .reclassification_prompt import ReclassificationPrompt
from .hitl_reclassification_prompt import HITLReclassificationPrompt

__all__ = [
    "BasePrompt",
    "ClassifierPrompt",
    "SingleDocumentPrompt",
    "ReclassificationPrompt",
    "HITLReclassificationPrompt",
]
