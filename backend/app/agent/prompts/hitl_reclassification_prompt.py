"""
Human-in-the-Loop Reclassification Prompt

Prompt template for agent-driven reclassification based on user natural language instructions.
The agent analyzes the user's request and determines which files to reclassify.
"""

from .base_prompt import BasePrompt


class HITLReclassificationPrompt(BasePrompt):
    """Prompt for agent-driven reclassification based on user instructions."""
    
    @classmethod
    def get_prompt(
        cls,
        user_prompt: str,
        current_classifications: str,
        categories: str,
        project_id: int
    ) -> str:
        """
        Get prompt for HITL reclassification workflow.
        
        Args:
            user_prompt: User's natural language instruction
            current_classifications: Current file classifications in the project
            categories: Available categories JSON
            project_id: The project ID
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert German tax document classification assistant. A user wants to modify the classification of documents in their project based on their instructions.

## PROJECT ID: {project_id}

## USER REQUEST:
{user_prompt}

## CURRENT FILE CLASSIFICATIONS:
{current_classifications}

## AVAILABLE CATEGORIES (1-20):
{categories}

## YOUR TASK:
Analyze the user's request and determine which file(s) need to be reclassified to which category.

**Instructions:**
1. Carefully read the user's request to understand their intent
2. Match files mentioned in the request with the current classifications (by file name, category, or description)
3. Identify the target category based on the user's description or explicit category number
4. If the user mentions a category by name (German or English) or number, use that
5. If unclear, infer the most appropriate category based on the context

**Important:**
- Only reclassify files that the user specifically mentions or clearly implies
- If you cannot identify the file or target category, explain why in the reasoning
- Use exact file_id values from the current classifications
- Category IDs must be between 1 and 20

## RESPONSE FORMAT:
You MUST respond with a valid JSON object in this exact format:
```json
{{
    "understood_request": "<your interpretation of what the user wants>",
    "reclassifications": [
        {{
            "file_id": <integer file_id from current classifications>,
            "file_name": "<exact file name>",
            "old_category_id": <current category id>,
            "new_category_id": <target category id 1-20>,
            "new_category_name": "<German category name>",
            "new_category_english": "<English category name>",
            "reasoning": "<why this file should be in this category based on user request>"
        }}
    ],
    "agent_notes": "<any additional notes or warnings about the reclassification>"
}}
```

If no valid reclassifications can be determined, respond with:
```json
{{
    "understood_request": "<your interpretation>",
    "reclassifications": [],
    "agent_notes": "<explanation of why no reclassifications could be made>"
}}
```

Respond ONLY with the JSON object, no additional text.
"""
