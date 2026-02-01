import redis
import json
import os
from pathlib import Path
from .celery_worker import celery_app
from app.core.database import get_db
from app.models.files import Project, RunStatus, File
from app.services.preprocess_document import DocumentPreprocessService
from app.services.classification_service import ClassificationService
from app.services.pdf_merger_service import PDFMergerService

document_processing_service = DocumentPreprocessService()
classification_service = ClassificationService()
pdf_merger_service = PDFMergerService()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def publish_status(project_id: int, status: str, message: str = "", progress: int = 0, extra_data: dict = None):
    payload = {
        "project_id": project_id,
        "status": status,
        "message": message,
        "progress": progress
    }
    if extra_data:
        payload.update(extra_data)
    redis_client.publish(f"project:{project_id}:status", json.dumps(payload))


def _update_file_with_preprocessing(db, file: File, result) -> dict:
    """
    Update file record with preprocessing results and return document data for classification.
    
    Args:
        db: Database session
        file: File model instance
        result: PreprocessResult from document preprocessing
        
    Returns:
        Dictionary with document data for classification
    """
    # Update file record with preprocessing data
    file.extracted_content = result.content[:50000] if result.content else None  # Limit size
    file.structured_content = result.structured_content[:50000] if result.structured_content else None
    file.summary = result.summary
    file.keywords = json.dumps(result.keywords) if result.keywords else None
    file.document_type = result.document_type
    file.key_entities = json.dumps(result.key_entities) if result.key_entities else None
    file.llm_output_file = result.llm_output_file
    file.output_folder = result.output_file
    
    db.commit()
    db.refresh(file)
    
    # Build document data for classification
    return {
        "file_id": file.id,
        "file_name": Path(file.file_path).name,
        "summary": result.summary or "",
        "keywords": result.keywords or [],
        "document_type": result.document_type or "",
        "key_entities": result.key_entities or {},
        "structured_content": result.structured_content or ""
    }


def _update_file_with_classification(db, file: File, classification: dict):
    """
    Update file record with classification results.
    
    Args:
        db: Database session
        file: File model instance
        classification: Classification result dictionary
    """
    file.category_id = classification.get("category_id")
    file.category_german = classification.get("category_name")
    file.category_english = classification.get("category_english")
    file.classification_confidence = str(classification.get("confidence", 0.5))
    file.classification_reasoning = classification.get("reasoning", "")
    
    db.commit()


@celery_app.task
def document_processing(project_id: int):
    """
    Main document processing task.
    
    Flow:
    1. Load project and files from database
    2. Preprocess each document (extract content, generate summary via LLM)
    3. Update file records in database with preprocessing results
    4. Keep document summaries in memory for classification
    5. Send documents to classification agent
    6. Save classification results to files and Ordering table
    """
    db = next(get_db())
    project = None
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            publish_status(project_id, "error", "Project not found")
            return

        project.status = RunStatus.processing
        db.commit()
        publish_status(project_id, "processing", "Starting document preprocessing...")

        # Get all files for this project
        files = db.query(File).filter(File.project_id == project_id).all()
        total = len(files)
        
        if total == 0:
            project.status = RunStatus.failed_processing
            db.commit()
            publish_status(project_id, "error", "No files found in project")
            return
        
        # Phase 1: Preprocess all documents and store in memory
        summary_list = []
        for idx, file in enumerate(files, 1):
            publish_status(
                project_id, 
                "processing", 
                f"Preprocessing file {idx}/{total}: {os.path.basename(file.file_path)}", 
                int((idx - 1) / total * 40)  # First 40% for preprocessing
            )

            # Process document
            result = document_processing_service.process_document(file.file_path)

            if not result.success:
                project.status = RunStatus.failed_processing
                db.commit()
                publish_status(
                    project_id, 
                    "error", 
                    f"Failed preprocessing: {file.file_path} - {result.error_message}"
                )
                return

            # Update database and build summary for classification
            doc_data = _update_file_with_preprocessing(db, file, result)
            summary_list.append(doc_data)
            
            publish_status(
                project_id, 
                "processing", 
                f"Completed preprocessing {idx}/{total}", 
                int(idx / total * 40)
            )
        
        # Phase 2: Run classification agent
        publish_status(
            project_id, 
            "processing", 
            "Starting document classification...", 
            45
        )
        
        project.status = RunStatus.in_agent_execution
        db.commit()
        
        # Pass documents to classification service
        classification_result = classification_service.classify_documents(summary_list)
        
        if not classification_result.success:
            project.status = RunStatus.failed_processing
            db.commit()
            publish_status(
                project_id, 
                "error", 
                f"Classification failed: {classification_result.error_message}"
            )
            return
        
        publish_status(
            project_id, 
            "processing", 
            f"Classified {classification_result.documents_classified} documents", 
            70
        )
        
        # Phase 3: Save classification results to database
        publish_status(project_id, "processing", "Saving classification results...", 75)
        
        # Update each file with its classification
        classifications = classification_result.classifications
        
        # Create a mapping of file_name to classification for easier lookup
        classification_map = {cls.get("file_name"): cls for cls in classifications}
        
        for doc_data in summary_list:
            file_name = doc_data["file_name"]
            file_id = doc_data["file_id"]
            
            if file_name in classification_map:
                cls = classification_map[file_name]
                # Add file_id to classification for ordering
                cls["file_id"] = file_id
                
                # Get file and update with classification
                file = db.query(File).filter(File.id == file_id).first()
                if file:
                    _update_file_with_classification(db, file, cls)

        # Phase 4: Merge PDFs by category
        publish_status(project_id, "processing", "Merging PDFs by category...", 80)
        
        # Get all classified files for merging
        classified_files = db.query(File).filter(
            File.project_id == project_id,
            File.category_id.isnot(None)
        ).all()
        
        merged_pdf_info = None
        if classified_files:
            merge_result = pdf_merger_service.merge_pdfs_by_category(
                project_id=project_id,
                files=classified_files,
                project_name=project.project_name
            )
            
            if merge_result.success:
                # Save merged PDF path to project
                project.merged_pdf_path = merge_result.merged_pdf_path
                db.commit()
                
                merged_pdf_info = {
                    "merged_pdf_path": merge_result.merged_pdf_path,
                    "merged_pdf_filename": os.path.basename(merge_result.merged_pdf_path),
                    "total_pages": merge_result.total_pages,
                    "documents_merged": merge_result.documents_merged,
                    "download_url": f"/api/projects/{project_id}/merged-pdf"
                }
                
                publish_status(
                    project_id,
                    "processing",
                    f"Merged {merge_result.documents_merged} documents into {merge_result.total_pages} pages",
                    90
                )
            else:
                publish_status(
                    project_id,
                    "processing",
                    f"PDF merge warning: {merge_result.error_message}",
                    90
                )

        # Mark project as completed
        project.status = RunStatus.finished_processing
        db.commit()
        
        # Build completion message with merged PDF info
        completion_extra = {}
        if merged_pdf_info:
            completion_extra["merged_pdf"] = merged_pdf_info
        
        publish_status(
            project_id, 
            "completed", 
            f"Processing complete. Processed {total} files, classified {classification_result.documents_classified} documents.", 
            100,
            extra_data=completion_extra
        )

    except Exception as e:
        if project:
            project.status = RunStatus.failed_processing
            db.commit()
        publish_status(project_id, "error", str(e))
    finally:
        db.close()