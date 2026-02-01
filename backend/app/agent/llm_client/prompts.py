"""
Prompts for Document Processing with LLM

Contains prompt templates for:
- Document content structuring
- Summary generation
- Keyword extraction
"""


class DocumentProcessingPrompts:
    """Prompts for document processing tasks."""
    
    @staticmethod
    def get_structure_and_summarize_prompt(content: str, file_name: str) -> str:
        """
        Get prompt for structuring document content and generating summary + keywords.
        
        Args:
            content: Raw extracted document content
            file_name: Name of the source file
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert document analyst. Your task is to analyze the extracted content from a document and provide:
1. A well-structured, cleaned version of the content
2. A concise summary
3. Relevant keywords that describe the document

**IMPORTANT: If the document content is in any language other than English (e.g., German, French, Spanish, etc.), you MUST translate ALL content to English. The entire output must be in English.**

**Source File:** {file_name}

**Extracted Content:**
```
{content[:15000]}  
```
{"... [Content truncated for processing]" if len(content) > 15000 else ""}

**Instructions:**

Please analyze this document and provide your response in the following JSON format:

{{
    "structured_content": "The cleaned and well-formatted content with proper sections, headers, and organization. Fix any OCR errors, organize tables properly, and improve readability while preserving all important information. TRANSLATE TO ENGLISH if the original is in another language.",
    "summary": "A concise 2-4 sentence summary describing what this document is about, its purpose, and key information it contains. MUST be in English.",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "document_type": "The type of document. Identify what type of document this is.",
    "original_language": "The detected language of the original document (e.g., 'English', 'German', 'French')",
    "key_entities": {{
        "people": ["Names of people mentioned"],
        "organizations": ["Organizations/companies mentioned"],
        "dates": ["Important dates found"],
        "amounts": ["Financial amounts or figures"]
    }}
}}

**Guidelines:**
1. For structured_content:
   - **TRANSLATE to English if the document is in another language**
   - Fix obvious OCR errors and typos
   - Organize tables in a readable format (use markdown tables if possible)
   - Add clear section headers where appropriate
   - Preserve all numerical data accurately
   - Remove redundant whitespace and formatting artifacts

2. For summary:
   - **MUST be written in English**
   - Focus on the main purpose and key information
   - Be concise but comprehensive
   - Include the document type in the summary

3. For keywords:
   - **MUST be in English**
   - Include 5-10 relevant keywords
   - Focus on terms that would help identify/search this document
   - Include document type, main subjects, and key topics

4. For key_entities:
   - Extract all relevant named entities
   - Include dates in a consistent format
   - Include currency with amounts
   - Keep proper nouns (names, company names) in original form but translate titles/descriptions

Respond ONLY with valid JSON. Do not include any text before or after the JSON."""
    
    @staticmethod
    def get_simple_summary_prompt(content: str) -> str:
        """
        Get a simpler prompt for just summary and keywords.
        
        Args:
            content: Document content
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this document content and provide a JSON response with:
1. A brief summary (2-3 sentences) - MUST be in English
2. 5-10 relevant keywords - MUST be in English
3. The document type
4. The original language of the document

**IMPORTANT: If the document is in any language other than English, translate the summary and keywords to English.**

Content:
```
{content[:10000]}
```

Respond in this JSON format only:
{{
    "summary": "Brief summary of the document IN ENGLISH",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "document_type": "Type of document",
    "original_language": "Detected language of the original document"
}}"""
