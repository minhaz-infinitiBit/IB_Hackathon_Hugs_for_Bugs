"""
Classifier Prompt

Prompt template for document classification agent that categorizes
tax documents into 20 predefined categories.
"""

from .base_prompt import BasePrompt


class ClassifierPrompt(BasePrompt):
    """Prompt for the document classification agent."""
    
    @classmethod
    def get_prompt(
        cls,
        documents_data: str, 
        categories: str, 
        memory_context: str = ""
    ) -> str:
        """
        Get the prompt for document classification.
        
        Args:
            documents_data: JSON string of document summaries and metadata
            categories: JSON string of available categories
            memory_context: Previous classification context from memory
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert German tax document classifier. Your task is to analyze document summaries and classify each document into one of 20 predefined tax categories.

## CATEGORIES (20 German Tax Document Categories):
{categories}

Each category includes:
- **id**: Unique category identifier (1-20)
- **german**: German category name
- **english**: English translation
- **description**: What the category covers
- **content_info**: Detailed information about typical content
- **keywords**: Keywords to help identify documents
- **typical_documents**: Examples of document types in this category
- **examples**: Concrete examples

## DOCUMENTS TO CLASSIFY:
{documents_data}

## PREVIOUS CLASSIFICATION CONTEXT:
{cls._format_context(memory_context)}

## INSTRUCTIONS:

1. **Analyze Each Document**: Read the summary, keywords, and document_type for each document carefully.

2. **Match to Category**: Based on the content, determine which of the 20 categories best fits each document:
   - Use the **keywords** in each category to match document content
   - Consider **typical_documents** and **content_info** for detailed matching
   - Match document content to category descriptions and examples
   - If a document could fit multiple categories, choose the most specific one
   - Use category 20 ("Nicht Verwendbar" / "Not Applicable") only for truly irrelevant documents

3. **Classification Guidelines**:
   - Tax questionnaires/forms → Category 1 (Fragebogen)
   - Official letters from Finanzamt, tax notices → Category 2 (Wichtige Korrespondenz)
   - Personal info forms (ESt 1A) → Category 3 (Mantelbogen)
   - Special deductible expenses → Category 4 (Sonderausgaben)
   - Medical/disability/funeral costs → Category 5 (Außergewöhnliche Belastung)
   - Health/pension insurance → Category 6 (Vorsorge)
   - Riester/Rürup pension → Category 7 (AV)
   - Child-related documents → Category 8 (Kind)
   - Business/trade income → Category 9 (Gewerbebetrieb)
   - Freelance/self-employed income → Category 10 (Selbständige Arbeit)
   - Salary statements, wage documents → Category 11 (N / N-AUS / WA-ESt)
   - Work-related expenses → Category 12 (Werbungskosten)
   - Dividend statements, bank documents → Category 13 (KAP)
   - Rental income/expenses → Category 14 (V+V)
   - Foreign income → Category 15 (AUS)
   - Foreign info/treaties → Category 16 (Info Ausland)
   - Travel calendars, work logs → Category 17 (Kalender)
   - Previous year tax documents → Category 18 (Vorjahr)
   - Next year tax documents → Category 19 (Nachfolgendes Steuerjahr)
   - Irrelevant documents → Category 20 (Nicht Verwendbar)

4. **Output Format**: Return ONLY a valid JSON array with this exact structure:
```json
[
    {{
        "id": 1,
        "file_name": "exact_filename.extension",
        "category_id": <category_number_1_to_20>,
        "category_name": "<category_german_name>",
        "category_english": "<english_translation>",
        "confidence": <0.0_to_1.0>,
        "reasoning": "<brief explanation for classification>"
    }},
    ...
]
```

5. **Important Rules**:
   - Classify ALL documents provided
   - Use exact file names from the input
   - Assign sequential IDs starting from 1
   - Provide confidence score (0.0 to 1.0) based on how well the document matches the category
   - Give brief but clear reasoning for each classification
   - One document = one category (no multiple classifications)

Now analyze the documents and provide the classification JSON array.
"""
