"""
Document Classification Agent

GraphBit-based agent workflow for classifying tax documents into 20 categories.
Uses GraphBit's Workflow, Node, Executor with Azure LLM and mem0 with Qdrant for memory.

This module provides the main ClassificationAgent class that will be called from
the services layer through the workflow_validate method.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from graphbit import Workflow, Node, LlmConfig, Executor
from dotenv import load_dotenv

from .prompts import ClassifierPrompt, SingleDocumentPrompt, ReclassificationPrompt
from .tools import (
    CLASSIFIER_TOOLS,
    get_current_results,
    clear_results,
    load_categories_from_file,
    get_categories_for_prompt,
    CATEGORIES_FILE,
)
from .memory import MemoryManager, get_memory_manager

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of document classification."""
    success: bool = False
    documents_processed: int = 0
    documents_classified: int = 0
    classifications: List[Dict] = field(default_factory=list)
    output_file: str = ""
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "documents_processed": self.documents_processed,
            "documents_classified": self.documents_classified,
            "classifications": self.classifications,
            "output_file": self.output_file,
            "error": self.error
        }


class ClassificationAgent:
    """
    Document classification agent using GraphBit workflow.
    
    This agent:
    1. Loads document summaries and metadata from preprocessed output
    2. Uses GraphBit Workflow/Node/Executor to classify each document into one of 20 categories
    3. Stores classification history in mem0 with Qdrant
    4. Outputs structured classification results
    
    Usage:
        agent = ClassificationAgent(output_dir="/path/to/output")
        
        # Validate workflow setup
        is_valid = agent.workflow_validate()
        
        # Execute classification
        result = agent.execute()
    """
    
    def __init__(
        self,
        output_dir: str = None,
        use_memory: bool = True
    ):
        """
        Initialize the classifier agent.
        
        Args:
            output_dir: Directory containing preprocessed document outputs
            use_memory: Whether to use mem0 for classification history
        """
        if output_dir is None:
            # Default to backend/output
            output_dir = Path(__file__).parent.parent.parent / "output"
        
        self.output_dir = Path(output_dir)
        self.use_memory = use_memory
        
        # Azure LLM configuration
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        
        # GraphBit components
        self.llm_config: Optional[LlmConfig] = None
        self.executor: Optional[Executor] = None
        
        # Memory manager
        self.memory = get_memory_manager() if use_memory else None
        
        # Categories
        self.categories = load_categories_from_file()
        
        # Workflow state
        self._workflow_validated = False
        
        logger.info(f"ClassificationAgent initialized. Output dir: {self.output_dir}")
    
    def _initialize_llm(self) -> None:
        """Initialize GraphBit LLM configuration and executor."""
        if self.llm_config is not None:
            return
            
        # Create GraphBit LLM config using azure_openai
        self.llm_config = LlmConfig.azure_openai(
            api_key=self.api_key,
            deployment_name=self.deployment,
            endpoint=self.endpoint,
            api_version=self.api_version
        )
        
        # Create GraphBit Executor
        self.executor = Executor(
            config=self.llm_config,
            timeout_seconds=120,
            lightweight_mode=True
        )
        
        logger.info("GraphBit LLM and Executor initialized")
    
    def workflow_validate(self) -> bool:
        """
        Validate the workflow setup and configuration.
        
        This method should be called from the services layer to ensure
        the agent is properly configured before execution.
        
        Returns:
            True if workflow is valid, False otherwise
        """
        try:
            # Check API key
            if not self.api_key:
                logger.error("AZURE_OPENAI_API_KEY not set")
                return False
            
            # Check endpoint
            if not self.endpoint:
                logger.error("AZURE_OPENAI_ENDPOINT not set")
                return False
            
            # Check output directory
            if not self.output_dir.exists():
                logger.warning(f"Output directory does not exist: {self.output_dir}")
                # Create it
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Check categories file
            if not CATEGORIES_FILE.exists():
                logger.error(f"Categories file not found: {CATEGORIES_FILE}")
                return False
            
            # Check categories loaded
            if not self.categories:
                logger.error("No categories loaded")
                return False
            
            # Initialize LLM
            self._initialize_llm()
            
            # Test workflow creation
            test_workflow = Workflow("Validation Test Workflow")
            test_node = Node.agent(
                name="Test Classifier",
                prompt="Test prompt",
                agent_id="test_classifier",
                tools=[],
                temperature=0.3,
                max_tokens=100
            )
            test_workflow.add_node(test_node)
            test_workflow.validate()
            
            self._workflow_validated = True
            logger.info("Workflow validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False
    
    def load_document_summaries(self) -> List[Dict]:
        """
        Load all document summaries from the output directory.
        
        Returns:
            List of document data dictionaries
        """
        documents = []
        
        if not self.output_dir.exists():
            logger.error(f"Output directory not found: {self.output_dir}")
            return documents
        
        # Iterate through each document folder
        for folder in self.output_dir.iterdir():
            if not folder.is_dir():
                continue
            
            doc_data = {
                "folder_name": folder.name,
                "file_name": "",
                "summary": "",
                "keywords": [],
                "document_type": "",
                "key_entities": {},
                "metadata": {}
            }
            
            # Look for LLM analysis file
            llm_files = list(folder.glob("*_llm_analysis.json"))
            if llm_files:
                try:
                    with open(llm_files[0], 'r', encoding='utf-8') as f:
                        llm_data = json.load(f)
                    doc_data["summary"] = llm_data.get("summary", "")
                    doc_data["keywords"] = llm_data.get("keywords", [])
                    doc_data["document_type"] = llm_data.get("document_type", "")
                    doc_data["key_entities"] = llm_data.get("key_entities", {})
                except Exception as e:
                    logger.warning(f"Error loading LLM analysis for {folder.name}: {e}")
            
            # Look for metadata file
            metadata_files = list(folder.glob("*_metadata.json"))
            if metadata_files:
                try:
                    with open(metadata_files[0], 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    doc_data["metadata"] = metadata
                    doc_data["file_name"] = metadata.get("file_name", folder.name)
                except Exception as e:
                    logger.warning(f"Error loading metadata for {folder.name}: {e}")
            
            # Only add if we have meaningful data
            if doc_data["summary"] or doc_data["file_name"]:
                if not doc_data["file_name"]:
                    # Extract file name from folder name (remove timestamp)
                    parts = folder.name.rsplit("_", 2)
                    if len(parts) >= 2:
                        doc_data["file_name"] = parts[0]
                    else:
                        doc_data["file_name"] = folder.name
                documents.append(doc_data)
        
        logger.info(f"Loaded {len(documents)} document summaries")
        return documents
    
    def classify_documents(self, documents: List[Dict] = None) -> List[Dict]:
        """
        Classify all documents into categories.
        
        Args:
            documents: Optional list of document data. If None, loads from output_dir.
            
        Returns:
            List of classification results
        """
        if documents is None:
            documents = self.load_document_summaries()
        
        if not documents:
            logger.warning("No documents to classify")
            return []
        
        # Initialize LLM if not done
        self._initialize_llm()
        
        # Clear previous results
        clear_results()
        
        # Get memory context
        memory_context = ""
        if self.memory:
            memory_context = self.memory.get_classification_context()
        
        # Prepare documents data for prompt
        docs_for_prompt = []
        for doc in documents:
            docs_for_prompt.append({
                "file_name": doc["file_name"],
                "summary": doc["summary"],
                "keywords": doc["keywords"],
                "document_type": doc["document_type"],
                "key_entities": doc["key_entities"]
            })
        
        documents_json = json.dumps(docs_for_prompt, indent=2, ensure_ascii=False)
        categories_json = get_categories_for_prompt()
        
        # Build classification prompt
        classification_prompt = ClassifierPrompt.get_prompt(
            documents_data=documents_json,
            categories=categories_json,
            memory_context=memory_context
        )
        
        logger.info(f"Classifying {len(documents)} documents using GraphBit Workflow...")
        
        try:
            # Build GraphBit Workflow
            workflow = Workflow("Document Classification Workflow")
            
            # Create classifier agent node
            classifier_agent = Node.agent(
                name="Document Classifier",
                prompt=classification_prompt,
                agent_id="document_classifier",
                tools=CLASSIFIER_TOOLS,
                temperature=0.3,
                max_tokens=4000
            )
            
            # Add node to workflow
            workflow.add_node(classifier_agent)
            
            # Validate workflow
            workflow.validate()
            
            # Execute workflow using GraphBit Executor
            result = self.executor.execute(workflow)
            
            # Get the agent output
            response_text = result.get_node_output("Document Classifier")
            
            logger.info(f"Raw workflow result type: {type(result)}")
            logger.info(f"Node output type: {type(response_text)}")
            logger.info(f"Node output value: {response_text[:500] if response_text else 'None'}...")
            
            if not response_text:
                # Try alternative methods
                logger.warning("get_node_output returned None, trying alternative methods...")
                
                if hasattr(result, 'output'):
                    response_text = str(result.output)
                elif hasattr(result, 'result'):
                    response_text = str(result.result)
                elif hasattr(result, 'final_output'):
                    response_text = str(result.final_output)
                else:
                    logger.error(f"Could not extract output from result. Available attrs: {dir(result)}")
                    response_text = ""
            
            if not response_text:
                logger.error("No response text from workflow execution")
                return []
            
            # Parse response
            classifications = self._parse_classification_response(response_text)
            
            # Store in memory
            if self.memory and classifications:
                for cls in classifications:
                    self.memory.add_classification_result(
                        file_name=cls.get("file_name", ""),
                        category_id=cls.get("category_id", 20),
                        category_name=cls.get("category_name", ""),
                        confidence=cls.get("confidence", 0.5),
                        reasoning=cls.get("reasoning", "")
                    )
            
            logger.info(f"Successfully classified {len(classifications)} documents")
            return classifications
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            raise
    
    def _parse_classification_response(self, response: str) -> List[Dict]:
        """Parse LLM response to extract classification results."""
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        try:
            # Look for JSON array
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Try markdown code block
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        logger.error(f"Failed to parse classification response: {response[:500]}")
        return []
    
    def save_results(self, classifications: List[Dict], output_file: str = None) -> str:
        """
        Save classification results to a file.
        
        Args:
            classifications: List of classification results
            output_file: Optional output file path
            
        Returns:
            Path to the saved file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"classification_results_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        # Organize by category
        by_category = {}
        for cls in classifications:
            cat_id = cls.get("category_id", 20)
            if cat_id not in by_category:
                by_category[cat_id] = {
                    "category_id": cat_id,
                    "category_name": cls.get("category_name", ""),
                    "category_english": cls.get("category_english", ""),
                    "documents": []
                }
            by_category[cat_id]["documents"].append({
                "id": cls.get("id", 0),
                "file_name": cls.get("file_name", ""),
                "confidence": cls.get("confidence", 0.5),
                "reasoning": cls.get("reasoning", "")
            })
        
        # Sort categories by ID
        sorted_categories = sorted(by_category.values(), key=lambda x: x["category_id"])
        
        # Create output
        output_data = {
            "classification_summary": {
                "total_documents": len(classifications),
                "categories_used": len(by_category),
                "generated_at": datetime.now().isoformat()
            },
            "results_by_category": sorted_categories,
            "results_ordered": classifications
        }
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved classification results to: {output_file}")
        return str(output_file)
    
    def execute(self) -> ClassificationResult:
        """
        Execute the full classification workflow.
        
        Returns:
            ClassificationResult with execution results
        """
        logger.info("Starting document classification workflow...")
        result = ClassificationResult()
        
        try:
            # Step 1: Validate workflow if not done
            if not self._workflow_validated:
                if not self.workflow_validate():
                    result.error = "Workflow validation failed"
                    return result
            
            # Step 2: Load documents
            documents = self.load_document_summaries()
            result.documents_processed = len(documents)
            
            if not documents:
                result.error = "No documents found to classify"
                return result
            
            # Step 3: Classify documents
            classifications = self.classify_documents(documents)
            result.documents_classified = len(classifications)
            result.classifications = classifications
            
            if not classifications:
                result.error = "Classification failed - no results"
                return result
            
            # Step 4: Save results
            output_file = self.save_results(classifications)
            result.output_file = output_file
            result.success = True
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            result.error = str(e)
            return result


def run_classification(output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to run document classification.
    
    Args:
        output_dir: Directory containing preprocessed documents
        
    Returns:
        Classification results as dictionary
    """
    agent = ClassificationAgent(output_dir=output_dir)
    result = agent.execute()
    return result.to_dict()
