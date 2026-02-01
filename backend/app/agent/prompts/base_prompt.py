"""
Base Prompt Class

Abstract base class for all prompt templates in the classification agent.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BasePrompt(ABC):
    """
    Abstract base class for prompt templates.
    
    All prompt classes should inherit from this class and implement
    the get_prompt method.
    """
    
    @classmethod
    @abstractmethod
    def get_prompt(cls, **kwargs) -> str:
        """
        Generate the prompt string.
        
        Args:
            **kwargs: Prompt-specific arguments
            
        Returns:
            Formatted prompt string
        """
        pass
    
    @classmethod
    def _format_context(cls, context: Optional[str]) -> str:
        """
        Format memory context for prompt inclusion.
        
        Args:
            context: Memory context string
            
        Returns:
            Formatted context or default message
        """
        return context if context else "No previous context available."
