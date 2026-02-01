"""
Single Document Classification Prompt

Prompt template for classifying a single document into categories.
"""

from .base_prompt import BasePrompt


class SingleDocumentPrompt(BasePrompt):
    """Prompt for classifying a single document."""
    
    @classmethod
    def get_prompt(
        cls,
        document_data: str,
        categories: str,
        memory_context: str = ""
    ) -> str:
        """
        Get prompt for classifying a single document.
        
        Args:
            document_data: JSON string of single document summary and metadata
            categories: JSON string of available categories
            memory_context: Previous classification context
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert German tax document classifier. Classify this single document into one of 20 tax categories.

Each category includes:
- **id**: Unique category identifier (1-20)
- **german**: German category name
- **english**: English translation
- **description**: What the category covers
- **content_info**: Detailed information about typical content
- **keywords**: Keywords to help identify documents
- **typical_documents**: Examples of document types in this category

## CATEGORIES:
{categories}

## DOCUMENT:
{document_data}

## CONTEXT:
{cls._format_context(memory_context)}

## TASK:
Classify this document using the category keywords and typical_documents to find the best match. Return ONLY a JSON object:
```json
{{
    "file_name": "exact_filename.extension",
    "category_id": <1-20>,
    "category_name": "<german_name>",
    "category_english": "<english_name>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}
```
"""
