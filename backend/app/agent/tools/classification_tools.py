"""
Classification Tools for Document Classification Agent

Provides tools that the agent can use during classification workflow:
- Get categories from JSON
- Classify documents
- Save classification results
- Access classification history from memory
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from graphbit import tool

logger = logging.getLogger(__name__)

# Path to categories file
CATEGORIES_FILE = Path(__file__).parent.parent.parent / "data" / "categories.json"

# Global storage for classification results
_classification_results: List[Dict] = []


@tool(_description="Get all tax document categories with their descriptions, examples, keywords, and typical documents. Use this to understand what categories are available for classification.")
def get_categories() -> str:
    """
    Get all available document categories with enriched information.

    Returns:
        JSON string with all categories including keywords, content_info, and typical_documents
    """
    try:
        if CATEGORIES_FILE.exists():
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                categories = json.load(f)

            # Return enriched category info for the agent
            enriched = []
            for cat in categories:
                enriched.append({
                    "id": cat["id"],
                    "german": cat["category_german"],
                    "english": cat["english_translation"],
                    "description": cat["description"],
                    "content_info": cat.get("content_info", ""),
                    "keywords": cat.get("keywords", []),
                    "typical_documents": cat.get("typical_documents", []),
                    "examples": cat["examples"]
                })

            return json.dumps({
                "success": True,
                "total_categories": len(enriched),
                "categories": enriched
            }, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": f"Categories file not found at {CATEGORIES_FILE}"
            })
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool(_description="Classify a document into one of the 20 tax categories. Provide file_name, category_id (1-20), confidence (0-1), and reasoning.")
def classify_document(
    file_name: str,
    category_id: int,
    confidence: float,
    reasoning: str
) -> str:
    """
    Classify a document into a category and store in memory.

    Args:
        file_name: Name of the document file
        category_id: Category ID (1-20)
        confidence: Classification confidence (0.0 to 1.0)
        reasoning: Brief explanation for the classification

    Returns:
        JSON string with classification result
    """
    global _classification_results

    # Import here to avoid circular imports
    from ..memory import get_memory_manager

    try:
        # Validate category ID (fixed 20 categories)
        if not 1 <= category_id <= 20:
            return json.dumps({
                "success": False,
                "error": f"Invalid category_id {category_id}. Must be between 1 and 20."
            })

        # Load categories to get names
        category_name = ""
        category_english = ""

        if CATEGORIES_FILE.exists():
            with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                categories = json.load(f)
            for cat in categories:
                if cat["id"] == category_id:
                    category_name = cat["category_german"]
                    category_english = cat["english_translation"]
                    break

        # Create classification result
        result = {
            "id": len(_classification_results) + 1,
            "file_name": file_name,
            "category_id": category_id,
            "category_name": category_name,
            "category_english": category_english,
            "confidence": confidence,
            "reasoning": reasoning,
            "classified_at": datetime.now().isoformat()
        }

        # Store in results
        _classification_results.append(result)

        # Store in memory (uses update to handle re-classifications)
        memory = get_memory_manager()
        memory.update_classification(
            file_name=file_name,
            category_id=category_id,
            category_name=category_name,
            confidence=confidence,
            reasoning=reasoning
        )

        logger.info(f"Classified '{file_name}' as category {category_id} ({category_name})")

        return json.dumps({
            "success": True,
            "classification": result
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool(_description="Save all classification results to a JSON file. Call this after all documents have been classified.")
def save_classification_results(output_path: str = None) -> str:
    """
    Save all classification results to a file.

    Args:
        output_path: Optional path for output file

    Returns:
        JSON string with save status
    """
    global _classification_results

    try:
        if not _classification_results:
            return json.dumps({
                "success": False,
                "error": "No classification results to save"
            })

        # Default output path
        if not output_path:
            output_dir = Path(__file__).parent.parent.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"classification_results_{timestamp}.json"
        else:
            output_path = Path(output_path)

        # Organize results by category
        by_category = {}
        for result in _classification_results:
            cat_id = result["category_id"]
            if cat_id not in by_category:
                by_category[cat_id] = {
                    "category_id": cat_id,
                    "category_name": result["category_name"],
                    "category_english": result["category_english"],
                    "documents": []
                }
            by_category[cat_id]["documents"].append({
                "id": result["id"],
                "file_name": result["file_name"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"]
            })

        # Create output structure
        output_data = {
            "classification_summary": {
                "total_documents": len(_classification_results),
                "categories_used": len(by_category),
                "generated_at": datetime.now().isoformat()
            },
            "results_by_category": list(by_category.values()),
            "results_ordered": _classification_results
        }

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved classification results to: {output_path}")

        return json.dumps({
            "success": True,
            "output_file": str(output_path),
            "total_documents": len(_classification_results),
            "categories_used": len(by_category)
        }, indent=2)

    except Exception as e:
        logger.error(f"Error saving classification results: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool(_description="Get classification history from memory to understand previous classifications and maintain context.")
def get_classification_history(limit: int = 10) -> str:
    """
    Get recent classification history from memory.

    Args:
        limit: Maximum number of history entries to retrieve

    Returns:
        JSON string with classification history
    """
    # Import here to avoid circular imports
    from ..memory import get_memory_manager

    try:
        memory = get_memory_manager()
        history = memory.get_recent_memories(limit=limit, memory_type="classification")

        return json.dumps({
            "success": True,
            "history_count": len(history),
            "history": history
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error getting classification history: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def get_current_results() -> List[Dict]:
    """Get current classification results (non-tool function)."""
    global _classification_results
    return _classification_results.copy()


def clear_results() -> None:
    """Clear classification results (non-tool function)."""
    global _classification_results
    _classification_results = []


def load_categories_from_file() -> List[Dict]:
    """Load categories from JSON file (non-tool function)."""
    if CATEGORIES_FILE.exists():
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_categories_for_prompt() -> str:
    """Format categories for prompt with enriched information (non-tool function)."""
    categories = load_categories_from_file()
    enriched = []
    for cat in categories:
        enriched.append({
            "id": cat["id"],
            "german": cat["category_german"],
            "english": cat["english_translation"],
            "description": cat["description"],
            "content_info": cat.get("content_info", ""),
            "keywords": cat.get("keywords", []),
            "typical_documents": cat.get("typical_documents", []),
            "examples": cat["examples"]
        })
    return json.dumps(enriched, indent=2, ensure_ascii=False)


# Export tools list for agent
CLASSIFIER_TOOLS = [
    get_categories,
    classify_document,
    save_classification_results,
    get_classification_history
]
 