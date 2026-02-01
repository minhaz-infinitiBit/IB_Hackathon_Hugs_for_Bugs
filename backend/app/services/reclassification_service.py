"""
Reclassification Service (Human-in-the-Loop)

This service handles the reclassification of documents after initial classification.
It provides the "human in the loop" functionality:
1. Accept user prompt for reclassification
2. Use agent to analyze prompt and determine reclassifications
3. Retrieve project results from agent memory
4. Update classifications based on agent decision
5. Update database records
6. Regenerate merged PDF
7. Update agent memory with new results

Usage:
    from services.reclassification_service import ReclassificationService
    
    service = ReclassificationService()
    result = service.reclassify_with_prompt(
        project_id=1,
        db=db_session,
        user_prompt="Move the bank statement to category 3",
        regenerate_pdf=True
    )
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from sqlalchemy.orm import Session
from graphbit import Workflow, Node, LlmConfig, Executor
from dotenv import load_dotenv

from app.agent.memory import get_memory_manager, MemoryManager
from app.agent.tools import load_categories_from_file, get_categories_for_prompt
from app.agent.prompts import HITLReclassificationPrompt
from app.models.files import Project, File, RunStatus
from app.services.pdf_merger_service import PDFMergerService

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ReclassificationResultItem:
    """Result for a single file reclassification."""
    file_id: int
    old_category_id: Optional[int] = None
    new_category_id: int = 0
    success: bool = False
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReclassificationResult:
    """Result of reclassification operation."""
    project_id: int = 0
    success: bool = False
    message: str = ""
    prompt: str = ""
    agent_reasoning: str = ""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    results: List[ReclassificationResultItem] = field(default_factory=list)
    merged_pdf_regenerated: bool = False
    merged_pdf_path: str = ""
    download_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["results"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.results]
        return result


class ReclassificationService:
    """
    Service for handling human-in-the-loop document reclassification.
    
    This service manages the complete reclassification flow:
    1. Accepts user prompt for reclassification
    2. Uses agent to analyze prompt and determine reclassifications
    3. Retrieves current classifications from agent memory/database
    4. Updates classifications based on agent decision
    5. Updates database records (File model)
    6. Optionally regenerates the merged PDF
    7. Updates agent memory with new results
    
    Example:
        >>> service = ReclassificationService()
        >>> result = service.reclassify_with_prompt(
        ...     project_id=1,
        ...     db=db_session,
        ...     user_prompt="Move bank statement to category 3",
        ...     regenerate_pdf=True
        ... )
        >>> if result.success:
        ...     print(f"Updated {result.successful_updates} files")
    """
    
    def __init__(self):
        """Initialize the ReclassificationService."""
        self.memory_manager: MemoryManager = get_memory_manager()
        self.pdf_merger_service = PDFMergerService()
        self.categories = load_categories_from_file()
        
        # Azure LLM configuration for agent
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        
        # GraphBit components (lazy initialization)
        self.llm_config: Optional[LlmConfig] = None
        self.executor: Optional[Executor] = None
        
        logger.info("ReclassificationService initialized")
    
    def _initialize_llm(self) -> bool:
        """Initialize GraphBit LLM configuration and executor."""
        if self.llm_config is not None:
            return True
        
        if not self.api_key or not self.endpoint:
            logger.error("Azure OpenAI credentials not configured")
            return False
        
        try:
            self.llm_config = LlmConfig.azure_openai(
                api_key=self.api_key,
                deployment_name=self.deployment,
                endpoint=self.endpoint,
                api_version=self.api_version
            )
            
            self.executor = Executor(
                config=self.llm_config,
                timeout_seconds=120,
                lightweight_mode=True
            )
            
            logger.info("GraphBit LLM and Executor initialized for reclassification")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return False
    
    def get_category_info(self, category_id: int) -> Dict[str, str]:
        """
        Get category name and English name by ID.
        
        Args:
            category_id: The category ID (1-20)
            
        Returns:
            Dictionary with category_name (German) and category_english
        """
        for cat in self.categories:
            if cat.get("id") == category_id:
                return {
                    "category_name": cat.get("name", ""),
                    "category_english": cat.get("english_name", "")
                }
        return {"category_name": "", "category_english": ""}
    
    def get_project_memory(self, project_id: int) -> Optional[Dict]:
        """
        Retrieve project results from agent memory.
        
        Args:
            project_id: The project ID
            
        Returns:
            Dictionary with project classifications or None if not found
        """
        return self.memory_manager.get_project_results(project_id)
    
    def _get_current_classifications_json(self, db: Session, project_id: int) -> str:
        """
        Get current classifications as JSON string for the agent prompt.
        
        Args:
            db: Database session
            project_id: The project ID
            
        Returns:
            JSON string of current classifications
        """
        files = db.query(File).filter(
            File.project_id == project_id,
            File.category_id.isnot(None)
        ).all()
        
        classifications = []
        for f in files:
            classifications.append({
                "file_id": f.id,
                "file_name": os.path.basename(f.file_path),
                "category_id": f.category_id,
                "category_name": f.category_german or "",
                "category_english": f.category_english or "",
                "summary": (f.summary or "")[:200],  # Truncate for prompt
                "document_type": f.document_type or ""
            })
        
        return json.dumps(classifications, indent=2, ensure_ascii=False)
    
    def _parse_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Parse agent response to extract reclassification instructions.
        
        Args:
            response: Raw agent response string
            
        Returns:
            Parsed dictionary with reclassifications
        """
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        try:
            # Look for JSON object
            start = response.find("{")
            end = response.rfind("}") + 1
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
        
        logger.error(f"Failed to parse agent response: {response[:500]}")
        return {"reclassifications": [], "agent_notes": "Failed to parse response"}
    
    def reclassify_with_prompt(
        self,
        project_id: int,
        db: Session,
        user_prompt: str,
        regenerate_pdf: bool = True
    ) -> ReclassificationResult:
        """
        Reclassify files using agent analysis of user's natural language prompt.
        
        This is the main entry point for prompt-based human-in-the-loop reclassification.
        
        Args:
            project_id: The project ID
            db: Database session
            user_prompt: Natural language instruction for reclassification
            regenerate_pdf: Whether to regenerate the merged PDF
            
        Returns:
            ReclassificationResult with operation results
        """
        result = ReclassificationResult(project_id=project_id)
        result.prompt = user_prompt
        
        try:
            # Step 1: Validate project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                result.message = f"Project {project_id} not found"
                return result
            
            # Step 2: Initialize LLM
            if not self._initialize_llm():
                result.message = "Failed to initialize LLM for reclassification"
                return result
            
            # Step 3: Get current classifications
            current_classifications = self._get_current_classifications_json(db, project_id)
            if current_classifications == "[]":
                result.message = "No classified files found in project"
                return result
            
            # Step 4: Get categories for prompt
            categories_json = get_categories_for_prompt()
            
            # Step 5: Build and execute agent workflow
            prompt = HITLReclassificationPrompt.get_prompt(
                user_prompt=user_prompt,
                current_classifications=current_classifications,
                categories=categories_json,
                project_id=project_id
            )
            
            logger.info(f"Executing HITL reclassification agent for project {project_id}")
            
            # Build GraphBit Workflow
            workflow = Workflow("HITL Reclassification Workflow")
            
            agent_node = Node.agent(
                name="Reclassification Agent",
                prompt=prompt,
                agent_id="hitl_reclassifier",
                tools=[],
                temperature=0.3,
                max_tokens=2000
            )
            
            workflow.add_node(agent_node)
            workflow.validate()
            
            # Execute workflow
            workflow_result = self.executor.execute(workflow)
            response_text = workflow_result.get_node_output("Reclassification Agent")
            
            if not response_text:
                result.message = "Agent returned empty response"
                return result
            
            logger.info(f"Agent response: {response_text[:500]}...")
            
            # Step 6: Parse agent response
            parsed = self._parse_agent_response(response_text)
            
            result.agent_reasoning = parsed.get("understood_request", "")
            agent_notes = parsed.get("agent_notes", "")
            reclassifications = parsed.get("reclassifications", [])
            
            if not reclassifications:
                result.message = f"No reclassifications determined. {agent_notes}"
                result.success = True  # Not an error, just nothing to do
                return result
            
            # Step 7: Convert agent output to updates format and execute
            updates = []
            for reclass in reclassifications:
                updates.append({
                    "file_id": reclass.get("file_id"),
                    "new_category_id": reclass.get("new_category_id"),
                    "new_category_name": reclass.get("new_category_name"),
                    "new_category_english": reclass.get("new_category_english"),
                    "reasoning": reclass.get("reasoning", user_prompt)
                })
            
            # Execute the actual reclassification
            return self.reclassify(
                project_id=project_id,
                db=db,
                updates=updates,
                regenerate_pdf=regenerate_pdf,
                prompt=user_prompt,
                agent_reasoning=result.agent_reasoning
            )
            
        except Exception as e:
            logger.error(f"HITL reclassification error: {e}")
            result.message = f"Error during reclassification: {str(e)}"
            return result
    
    def reclassify(
        self,
        project_id: int,
        db: Session,
        updates: List[Dict],
        regenerate_pdf: bool = True,
        prompt: str = "",
        agent_reasoning: str = ""
    ) -> ReclassificationResult:
        """
        Reclassify files in a project.
        
        This method performs the actual reclassification based on explicit updates.
        
        Args:
            project_id: The project ID
            db: Database session
            updates: List of update dictionaries containing:
                - file_id: The file ID to update
                - new_category_id: The new category ID (1-20)
                - new_category_name: Optional German category name
                - new_category_english: Optional English category name
                - reasoning: Optional reasoning for the change
            regenerate_pdf: Whether to regenerate the merged PDF
            prompt: Original user prompt (for response)
            agent_reasoning: Agent's interpretation of the prompt
            
        Returns:
            ReclassificationResult with operation results
        """
        result = ReclassificationResult(project_id=project_id)
        result.total_updates = len(updates)
        result.prompt = prompt
        result.agent_reasoning = agent_reasoning
        
        try:
            # Step 1: Validate project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                result.message = f"Project {project_id} not found"
                return result
            
            # Step 2: Get project results from memory
            project_memory = self.get_project_memory(project_id)
            if not project_memory:
                logger.warning(f"No memory results for project {project_id}, will use database only")
            
            # Step 3: Process each update
            results_list = []
            successful = 0
            failed = 0
            
            for update in updates:
                item_result = self._process_single_update(
                    db=db,
                    project_id=project_id,
                    update=update,
                    project_memory=project_memory
                )
                results_list.append(item_result)
                
                if item_result.success:
                    successful += 1
                else:
                    failed += 1
            
            result.results = results_list
            result.successful_updates = successful
            result.failed_updates = failed
            
            if successful == 0:
                result.message = "No updates were successful"
                return result
            
            # Step 4: Update agent memory with new classifications
            if project_memory:
                # Refresh classifications from database
                updated_classifications = self._build_classifications_from_db(db, project_id)
                
                self.memory_manager.save_project_results(
                    project_id=project_id,
                    classifications=updated_classifications,
                    documents=project_memory.get("documents"),
                    merged_pdf_path=project_memory.get("merged_pdf_path")
                )
                logger.info(f"Updated agent memory for project {project_id}")
            
            # Step 5: Regenerate PDF if requested
            if regenerate_pdf:
                merge_result = self._regenerate_merged_pdf(db, project_id, project.project_name)
                
                if merge_result:
                    result.merged_pdf_regenerated = True
                    result.merged_pdf_path = merge_result.get("merged_pdf_path", "")
                    result.download_url = f"/api/projects/{project_id}/merged-pdf/download"
                    
                    # Update project with new merged PDF path
                    project.merged_pdf_path = result.merged_pdf_path
                    db.commit()
                    
                    # Also update memory with new PDF path
                    if project_memory:
                        self.memory_manager.save_project_results(
                            project_id=project_id,
                            classifications=self._build_classifications_from_db(db, project_id),
                            documents=project_memory.get("documents"),
                            merged_pdf_path=result.merged_pdf_path
                        )
            
            result.success = True
            result.message = f"Successfully updated {successful} of {result.total_updates} files"
            
            return result
            
        except Exception as e:
            logger.error(f"Reclassification error: {e}")
            result.message = f"Error during reclassification: {str(e)}"
            return result
    
    def _process_single_update(
        self,
        db: Session,
        project_id: int,
        update: Dict,
        project_memory: Optional[Dict]
    ) -> ReclassificationResultItem:
        """
        Process a single file reclassification update.
        
        Args:
            db: Database session
            project_id: The project ID
            update: Update dictionary
            project_memory: Project memory data (optional)
            
        Returns:
            ReclassificationResultItem with the result
        """
        file_id = update.get("file_id")
        new_category_id = update.get("new_category_id")
        
        item_result = ReclassificationResultItem(
            file_id=file_id,
            new_category_id=new_category_id
        )
        
        try:
            # Get the file from database
            file = db.query(File).filter(
                File.id == file_id,
                File.project_id == project_id
            ).first()
            
            if not file:
                item_result.message = f"File {file_id} not found in project {project_id}"
                return item_result
            
            # Store old category for reference
            item_result.old_category_id = file.category_id
            
            # Get category info if not provided
            new_category_name = update.get("new_category_name")
            new_category_english = update.get("new_category_english")
            
            if not new_category_name or not new_category_english:
                cat_info = self.get_category_info(new_category_id)
                new_category_name = new_category_name or cat_info.get("category_name", "")
                new_category_english = new_category_english or cat_info.get("category_english", "")
            
            # Update database record
            file.category_id = new_category_id
            file.category_german = new_category_name
            file.category_english = new_category_english
            
            reasoning = update.get("reasoning", "")
            if reasoning:
                # Append to existing reasoning
                existing_reasoning = file.classification_reasoning or ""
                file.classification_reasoning = f"{existing_reasoning}\n[Reclassified]: {reasoning}".strip()
            
            db.commit()
            db.refresh(file)
            
            # Update memory if available
            if project_memory:
                self.memory_manager.update_project_classification(
                    project_id=project_id,
                    file_id=file_id,
                    new_category_id=new_category_id,
                    new_category_name=new_category_name,
                    new_category_english=new_category_english,
                    reasoning=reasoning
                )
            
            item_result.success = True
            item_result.message = f"Updated category from {item_result.old_category_id} to {new_category_id}"
            
            logger.info(f"Reclassified file {file_id}: {item_result.old_category_id} -> {new_category_id}")
            
            return item_result
            
        except Exception as e:
            logger.error(f"Error updating file {file_id}: {e}")
            item_result.message = f"Error: {str(e)}"
            return item_result
    
    def _build_classifications_from_db(
        self,
        db: Session,
        project_id: int
    ) -> List[Dict]:
        """
        Build classifications list from database records.
        
        Args:
            db: Database session
            project_id: The project ID
            
        Returns:
            List of classification dictionaries
        """
        files = db.query(File).filter(
            File.project_id == project_id,
            File.category_id.isnot(None)
        ).all()
        
        classifications = []
        for file in files:
            classifications.append({
                "file_id": file.id,
                "file_name": os.path.basename(file.file_path),
                "file_path": file.file_path,
                "category_id": file.category_id,
                "category_name": file.category_german,
                "category_english": file.category_english,
                "confidence": file.classification_confidence,
                "reasoning": file.classification_reasoning
            })
        
        return classifications
    
    def _regenerate_merged_pdf(
        self,
        db: Session,
        project_id: int,
        project_name: str = None
    ) -> Optional[Dict]:
        """
        Regenerate the merged PDF for a project.
        
        Args:
            db: Database session
            project_id: The project ID
            project_name: Optional project name for filename
            
        Returns:
            Dictionary with merge result or None if failed
        """
        try:
            # Get all classified files
            classified_files = db.query(File).filter(
                File.project_id == project_id,
                File.category_id.isnot(None)
            ).all()
            
            if not classified_files:
                logger.warning(f"No classified files found for project {project_id}")
                return None
            
            # Merge PDFs
            merge_result = self.pdf_merger_service.merge_pdfs_by_category(
                project_id=project_id,
                files=classified_files,
                project_name=project_name
            )
            
            if merge_result.success:
                logger.info(f"Regenerated merged PDF for project {project_id}: {merge_result.merged_pdf_path}")
                return {
                    "success": True,
                    "merged_pdf_path": merge_result.merged_pdf_path,
                    "total_pages": merge_result.total_pages,
                    "documents_merged": merge_result.documents_merged
                }
            else:
                logger.error(f"Failed to regenerate PDF: {merge_result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error regenerating PDF: {e}")
            return None


def reclassify_project(
    project_id: int,
    db: Session,
    updates: List[Dict],
    regenerate_pdf: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to reclassify files in a project.
    
    Args:
        project_id: The project ID
        db: Database session
        updates: List of update dictionaries
        regenerate_pdf: Whether to regenerate the merged PDF
        
    Returns:
        Reclassification result as dictionary
    """
    service = ReclassificationService()
    result = service.reclassify(
        project_id=project_id,
        db=db,
        updates=updates,
        regenerate_pdf=regenerate_pdf
    )
    return result.to_dict()
