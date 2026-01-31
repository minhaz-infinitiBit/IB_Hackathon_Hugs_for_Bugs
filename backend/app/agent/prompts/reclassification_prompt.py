"""
Reclassification Prompt

Prompt template for reclassifying a document based on user feedback.
"""

from .base_prompt import BasePrompt


class ReclassificationPrompt(BasePrompt):
    """Prompt for reclassifying a document based on feedback."""
    
    @classmethod
    def get_prompt(
        cls,
        document_data: str,
        current_category: str,
        categories: str,
        feedback: str
    ) -> str:
        """
        Get prompt for reclassifying a document based on feedback.
        
        Args:
            document_data: Document summary and metadata
            current_category: Current classification
            categories: Available categories
            feedback: User feedback on why reclassification is needed
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert German tax document classifier. A document was previously classified but needs reclassification based on feedback.

## DOCUMENT:
{document_data}

## CURRENT CLASSIFICATION:
{current_category}

## USER FEEDBACK:
{feedback}

## ALL CATEGORIES:
{categories}

## TASK:
Based on the feedback, reclassify this document. Return ONLY a JSON object:
```json
{{
    "file_name": "exact_filename.extension",
    "category_id": <1-20>,
    "category_name": "<german_name>",
    "category_english": "<english_name>",
    "confidence": <0.0-1.0>,
    "reasoning": "<explanation considering feedback>"
}}
```
"""
