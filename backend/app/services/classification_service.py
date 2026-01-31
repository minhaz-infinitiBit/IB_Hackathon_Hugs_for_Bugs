"""
Document Classification Service

This service handles document classification:
1. Validates the classification workflow
2. Loads preprocessed documents
3. Classifies documents into 20 tax categories
4. Returns structured classification results

Usage:
    from services.classification_service import ClassificationService
    
    service = ClassificationService()
    
    # Validate the workflow first
    if service.validate():
        result = service.classify_documents()
    
    # Or use the convenience method
    result = service.run()
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from app.agent import (
    ClassificationAgent,
    ClassificationResult,
    run_classification,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationServiceResult:
    """Result of classification service execution."""
    success: bool = False
    validated: bool = False
    documents_processed: int = 0
    documents_classified: int = 0
    classifications: List[Dict] = None
    output_file: str = ""
    error_message: str = ""
    
    def __post_init__(self):
        if self.classifications is None:
            self.classifications = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ClassificationService:
    """
    Service for document classification.
    
    This service wraps the ClassificationAgent and provides a clean interface
    for the application layer to classify documents.
    
    Example:
        >>> service = ClassificationService(output_dir="/path/to/preprocessed")
        >>> if service.validate():
        ...     result = service.classify_documents()
        ...     if result.success:
        ...         print(f"Classified {result.documents_classified} documents")
    """
    
    def __init__(
        self,
        output_dir: str = None,
        use_memory: bool = True
    ):
        """
        Initialize the ClassificationService.
        
        Args:
            output_dir: Directory containing preprocessed documents.
                       Defaults to backend/output
            use_memory: Whether to use mem0 for classification history
        """
        if output_dir is None:
            # Default to output directory relative to this file
            base_dir = Path(__file__).parent.parent.parent
            output_dir = base_dir / "output"
        
        self.output_dir = Path(output_dir)
        self.use_memory = use_memory
        
        # Initialize the agent
        self._agent: Optional[ClassificationAgent] = None
        self._validated = False
        
        logger.info(f"ClassificationService initialized. Output dir: {self.output_dir}")
    
    def _get_agent(self) -> ClassificationAgent:
        """Get or create the classification agent."""
        if self._agent is None:
            self._agent = ClassificationAgent(
                output_dir=str(self.output_dir),
                use_memory=self.use_memory
            )
        return self._agent
    
    def validate(self) -> bool:
        """
        Validate the classification workflow.
        
        This method should be called before classification to ensure
        the agent is properly configured (API keys, categories file, etc.)
        
        Returns:
            True if validation passes, False otherwise
        """
        try:
            agent = self._get_agent()
            self._validated = agent.workflow_validate()
            
            if self._validated:
                logger.info("Classification workflow validated successfully")
            else:
                logger.error("Classification workflow validation failed")
            
            return self._validated
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            self._validated = False
            return False
    
    def classify_documents(
        self,
        documents: List[Dict] = None
    ) -> ClassificationServiceResult:
        """
        Classify documents into tax categories.
        
        Args:
            documents: Optional list of document data. If None, loads from output_dir.
            
        Returns:
            ClassificationServiceResult with classification results
        """
        result = ClassificationServiceResult()
        
        try:
            # Validate if not done
            if not self._validated:
                result.validated = self.validate()
                if not result.validated:
                    result.error_message = "Workflow validation failed"
                    return result
            else:
                result.validated = True
            
            # Get agent and execute
            agent = self._get_agent()
            agent_result = agent.execute()
            
            # Map agent result to service result
            result.success = agent_result.success
            result.documents_processed = agent_result.documents_processed
            result.documents_classified = agent_result.documents_classified
            result.classifications = agent_result.classifications
            result.output_file = agent_result.output_file
            result.error_message = agent_result.error
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            result.error_message = str(e)
            return result
    
    def run(self) -> ClassificationServiceResult:
        """
        Run the full classification workflow (validate + classify).
        
        This is a convenience method that combines validation and classification.
        
        Returns:
            ClassificationServiceResult with classification results
        """
        # Validate first
        if not self.validate():
            result = ClassificationServiceResult()
            result.error_message = "Workflow validation failed"
            return result
        
        # Then classify
        return self.classify_documents()
    
    def get_classification_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the last classification results.
        
        Returns:
            Summary dictionary with statistics
        """
        agent = self._get_agent()
        
        from app.agent.tools import get_current_results
        results = get_current_results()
        
        if not results:
            return {"message": "No classification results available"}
        
        # Count by category
        by_category = {}
        for r in results:
            cat_id = r.get("category_id", 20)
            cat_name = r.get("category_name", "Unknown")
            if cat_id not in by_category:
                by_category[cat_id] = {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "count": 0
                }
            by_category[cat_id]["count"] += 1
        
        return {
            "total_documents": len(results),
            "categories_used": len(by_category),
            "by_category": list(by_category.values())
        }


def run_classification_service(output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to run document classification service.
    
    Args:
        output_dir: Directory containing preprocessed documents
        
    Returns:
        Classification results as dictionary
    """
    service = ClassificationService(output_dir=output_dir)
    result = service.run()
    return result.to_dict()


# Allow running as a script
if __name__ == "__main__":
    import sys
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_classification_service(output_dir)
    
    print("\n" + "="*50)
    print("Classification Service Result")
    print("="*50)
    print(f"Success: {result['success']}")
    print(f"Validated: {result['validated']}")
    print(f"Documents Processed: {result['documents_processed']}")
    print(f"Documents Classified: {result['documents_classified']}")
    if result['output_file']:
        print(f"Output File: {result['output_file']}")
    if result['error_message']:
        print(f"Error: {result['error_message']}")
