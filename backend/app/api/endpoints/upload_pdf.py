from fastapi import APIRouter, UploadFile, HTTPException, Depends, File as FileUpload, Body
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import json

from app.core.database import get_db
from app.schemas.pdf_upload import (
    PDFUploadResponse, 
    ProjectResponse,
    ReclassificationRequest,
    ReclassificationResponse,
    ProjectMemoryResponse
)
from app.models.files import Project, File, FileType, RunStatus
from app.tasks import document_processing
from app.services.reclassification_service import ReclassificationService

router = APIRouter()
reclassification_service = ReclassificationService()

@router.post("/upload-pdf/{project_id}", response_model=List[PDFUploadResponse])
async def upload_pdf(
    project_id: int,
    files: List[UploadFile] = FileUpload(...),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    UPLOAD_DIR = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}/data/uploads/{project_id}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    responses = []
    saved_file_paths = []
    db_files = []

    try:
        for file in files:
            file_location = f"{UPLOAD_DIR}/{file.filename}"
            
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            saved_file_paths.append(file_location)

            db_file = File(
                file_path=file_location,
                project_id=project_id,
                filetype=FileType.pdf
            )
            db.add(db_file)
            db_files.append(db_file)
            
        db.commit()
        
        for db_file in db_files:
            db.refresh(db_file)
        
        for file, db_file in zip(files, db_files):
            responses.append(
                PDFUploadResponse(
                    filename=file.filename,
                    content_type=file.content_type,
                    message="File uploaded successfully",
                    location=db_file.file_path,
                    preview_url=f"/files/preview?file_path={db_file.file_path}",
                    project_id=project_id
                )
            )
    
    except HTTPException:
        for path in saved_file_paths:
            if os.path.exists(path):
                os.remove(path)
        raise
    except Exception as e:
        db.rollback()
        for path in saved_file_paths:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(status_code=500, detail=str(e))
    
    return responses


@router.post("/projects/", response_model=ProjectResponse)
async def create_project(
    project_name: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    try:
        project = Project(project_name=project_name, status=RunStatus.pending)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/projects/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        projects = db.query(Project).offset(skip).limit(limit).all()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/projects/{project_id}/files", response_model=List[PDFUploadResponse])
async def list_project_files(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = db.query(File).filter(File.project_id == project_id).all()
    
    responses = []
    
    for file in files:
        if not os.path.exists(file.file_path):
            db.delete(file)
            continue
            
        responses.append(
            PDFUploadResponse(
                filename=os.path.basename(file.file_path),
                content_type="application/pdf",
                message="File retrieved successfully",
                location=file.file_path,
                preview_url=f"/files/preview?file_path={file.file_path}",
                project_id=project_id
            )
        )
    
    db.commit()
    
    return responses



@router.post("/process-project/{project_id}")
async def process_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    try:
        task = document_processing.delay(project_id)
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process project: {str(e)}")


@router.get("/projects/{project_id}/ordering")
async def get_project_ordering(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the classification ordering results for a project.
    Returns the documents organized by category after classification is complete.
    Built dynamically from File records.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all classified files for this project
    files = db.query(File).filter(
        File.project_id == project_id,
        File.category_id.isnot(None)
    ).all()
    
    if not files:
        return {
            "project_id": project_id,
            "status": project.status.value,
            "message": "No classification results available yet",
            "ordering": None
        }
    
    # Build ordering data from File records
    by_category = {}
    for file in files:
        cat_id = file.category_id
        if cat_id not in by_category:
            by_category[cat_id] = {
                "category_id": cat_id,
                "category_name": file.category_german or "",
                "category_english": file.category_english or "",
                "files": []
            }
        by_category[cat_id]["files"].append({
            "file_id": file.id,
            "file_name": os.path.basename(file.file_path),
            "preview_url": f"/files/preview?file_path={file.file_path}",
            "confidence": file.classification_confidence,
            "reasoning": file.classification_reasoning
        })
    
    # Sort by category ID
    ordered_files = []
    categories = {}
    for cat_id in sorted(by_category.keys()):
        categories[str(cat_id)] = by_category[cat_id]
        for file_info in by_category[cat_id]["files"]:
            ordered_files.append({
                "file_id": file_info["file_id"],
                "file_name": file_info["file_name"],
                "preview_url": file_info["preview_url"],
                "category_id": cat_id,
                "category_name": by_category[cat_id]["category_name"],
                "category_english": by_category[cat_id]["category_english"]
            })
    
    ordering_data = {
        "project_id": project_id,
        "total_documents": len(files),
        "categories": categories,
        "ordered_files": ordered_files
    }
    
    return {
        "project_id": project_id,
        "status": project.status.value,
        "ordering": ordering_data
    }


@router.get("/projects/{project_id}/classifications")
async def get_project_classifications(
    project_id: int,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get classification results for files in a project.
    Optionally filter by category_id.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(File).filter(File.project_id == project_id)
    
    if category_id is not None:
        query = query.filter(File.category_id == category_id)
    
    files = query.all()
    
    results = []
    for file in files:
        results.append({
            "file_id": file.id,
            "file_name": os.path.basename(file.file_path),
            "file_path": file.file_path,
            "preview_url": f"/files/preview?file_path={file.file_path}",
            "category_id": file.category_id,
            "category_german": file.category_german,
            "category_english": file.category_english,
            "classification_confidence": file.classification_confidence,
            "classification_reasoning": file.classification_reasoning,
            "summary": file.summary,
            "document_type": file.document_type,
            "keywords": json.loads(file.keywords) if file.keywords else []
        })
    
    return {
        "project_id": project_id,
        "status": project.status.value,
        "total_files": len(results),
        "files": results
    }


@router.get("/projects/{project_id}/merged-pdf")
async def get_merged_pdf(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the merged PDF info for a project.
    Returns metadata about the merged PDF including download URL.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.merged_pdf_path:
        return {
            "project_id": project_id,
            "status": project.status.value,
            "merged_pdf_available": False,
            "merged_pdf_path": None,
            "message": "Merged PDF not available. Processing may not be complete."
        }
    
    file_exists = os.path.exists(project.merged_pdf_path)
    file_size = os.path.getsize(project.merged_pdf_path) if file_exists else 0
    
    return {
        "project_id": project_id,
        "status": project.status.value,
        "merged_pdf_available": file_exists,
        "merged_pdf_path": project.merged_pdf_path,
        "merged_pdf_filename": os.path.basename(project.merged_pdf_path),
        "preview_url": f"/files/preview?file_path={project.merged_pdf_path}",
        "file_size_bytes": file_size,
        "download_url": f"/api/projects/{project_id}/merged-pdf/download"
    }


@router.get("/projects/{project_id}/merged-pdf/download")
async def download_merged_pdf(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Download the merged PDF file for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.merged_pdf_path:
        raise HTTPException(
            status_code=404, 
            detail="Merged PDF not available. Processing may not be complete."
        )
    
    if not os.path.exists(project.merged_pdf_path):
        raise HTTPException(status_code=404, detail="Merged PDF file not found on disk")
    
    filename = os.path.basename(project.merged_pdf_path)
    
    return FileResponse(
        path=project.merged_pdf_path,
        filename=filename,
        media_type="application/pdf"
    )


# ==================== HUMAN-IN-THE-LOOP ENDPOINTS ====================

@router.get("/projects/{project_id}/memory", response_model=ProjectMemoryResponse)
async def get_project_memory(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the project's classification results from agent memory.
    
    This endpoint retrieves the stored classification results for a project,
    which can be used to display current classifications before reclassification.
    """
    # First check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get from agent memory
    memory_results = reclassification_service.get_project_memory(project_id)
    
    if not memory_results:
        # Try to build from database
        files = db.query(File).filter(
            File.project_id == project_id,
            File.category_id.isnot(None)
        ).all()
        
        if files:
            classifications = [
                {
                    "file_id": f.id,
                    "file_name": os.path.basename(f.file_path),
                    "file_path": f.file_path,
                    "preview_url": f"/files/preview?file_path={f.file_path}",
                    "category_id": f.category_id,
                    "category_name": f.category_german,
                    "category_english": f.category_english,
                    "confidence": f.classification_confidence,
                    "reasoning": f.classification_reasoning
                }
                for f in files
            ]
            return ProjectMemoryResponse(
                project_id=project_id,
                found=True,
                total_documents=len(classifications),
                classifications=classifications,
                merged_pdf_path=project.merged_pdf_path,
                timestamp=None
            )
        
        return ProjectMemoryResponse(
            project_id=project_id,
            found=False,
            total_documents=0,
            classifications=[],
            merged_pdf_path=None,
            timestamp=None
        )
    
    return ProjectMemoryResponse(
        project_id=project_id,
        found=True,
        total_documents=memory_results.get("total_documents", 0),
        classifications=memory_results.get("classifications", []),
        merged_pdf_path=memory_results.get("merged_pdf_path"),
        merged_pdf_preview_url=f"/files/preview?file_path={memory_results.get('merged_pdf_path')}" if memory_results.get('merged_pdf_path') else None,
        timestamp=memory_results.get("timestamp")
    )


@router.post("/projects/{project_id}/reclassify", response_model=ReclassificationResponse)
async def reclassify_files(
    project_id: int,
    request: ReclassificationRequest,
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop endpoint to reclassify files in a project using natural language.
    
    This endpoint accepts a natural language prompt and uses an AI agent to:
    
    1. Analyze the user's intent from the prompt
    2. Identify which files need to be reclassified
    3. Determine the target categories
    4. Update database records (File model)
    5. Optionally regenerate the merged PDF (default: True)
    6. Update agent memory with new results
    
    Example request body:
    ```json
    {
        "prompt": "Move the bank statement PDF to category 3",
        "regenerate_pdf": true
    }
    ```
    
    Or more complex:
    ```json
    {
        "prompt": "The document 'contract.pdf' should be in the employment category, and move all bank documents to Bankbescheinigungen",
        "regenerate_pdf": true
    }
    ```
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Execute agent-based reclassification
    result = reclassification_service.reclassify_with_prompt(
        project_id=project_id,
        db=db,
        user_prompt=request.prompt,
        regenerate_pdf=request.regenerate_pdf
    )
    
    # Convert result to response
    return ReclassificationResponse(
        project_id=result.project_id,
        success=result.success,
        message=result.message,
        prompt=result.prompt,
        agent_reasoning=result.agent_reasoning,
        total_updates=result.total_updates,
        successful_updates=result.successful_updates,
        failed_updates=result.failed_updates,
        results=[
            {
                "file_id": r.file_id,
                "old_category_id": r.old_category_id,
                "new_category_id": r.new_category_id,
                "success": r.success,
                "message": r.message
            }
            for r in result.results
        ],
        merged_pdf_regenerated=result.merged_pdf_regenerated,
        merged_pdf_path=result.merged_pdf_path,
        download_url=result.download_url
    )


@router.put("/projects/{project_id}/files/{file_id}/category")
async def update_file_category(
    project_id: int,
    file_id: int,
    new_category_id: int = Body(..., ge=1, le=20, embed=True),
    reasoning: str = Body(None, embed=True),
    regenerate_pdf: bool = Body(True, embed=True),
    db: Session = Depends(get_db)
):
    """
    Update a single file's category.
    
    This is a simpler endpoint for updating just one file at a time.
    For bulk updates, use the /projects/{project_id}/reclassify endpoint.
    
    Request body:
    ```json
    {
        "new_category_id": 5,
        "reasoning": "Document is an employment contract",
        "regenerate_pdf": true
    }
    ```
    """
    # Validate project and file
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file = db.query(File).filter(
        File.id == file_id,
        File.project_id == project_id
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found in project")
    
    # Execute reclassification
    result = reclassification_service.reclassify(
        project_id=project_id,
        db=db,
        updates=[{
            "file_id": file_id,
            "new_category_id": new_category_id,
            "reasoning": reasoning
        }],
        regenerate_pdf=regenerate_pdf
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    # Get the single result
    item_result = result.results[0] if result.results else None
    
    return {
        "project_id": project_id,
        "file_id": file_id,
        "old_category_id": item_result.old_category_id if item_result else None,
        "new_category_id": new_category_id,
        "success": True,
        "message": item_result.message if item_result else "Updated",
        "merged_pdf_regenerated": result.merged_pdf_regenerated,
        "merged_pdf_path": result.merged_pdf_path,
        "download_url": result.download_url
    }


@router.get("/projects/{project_id}/categories")
async def get_available_categories(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get available categories with current file counts for a project.
    
    Returns all 20 categories with the count of files in each category,
    useful for displaying options when reclassifying files.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Load categories
    categories = reclassification_service.categories
    
    # Count files per category
    from sqlalchemy import func
    category_counts = db.query(
        File.category_id,
        func.count(File.id).label('count')
    ).filter(
        File.project_id == project_id,
        File.category_id.isnot(None)
    ).group_by(File.category_id).all()
    
    counts_dict = {cat_id: count for cat_id, count in category_counts}
    
    # Build response
    result = []
    for cat in categories:
        cat_id = cat.get("id")
        result.append({
            "category_id": cat_id,
            "category_name": cat.get("name", ""),
            "category_english": cat.get("english_name", ""),
            "description": cat.get("description", ""),
            "file_count": counts_dict.get(cat_id, 0)
        })
    
    total_files = sum(counts_dict.values())
    
    return {
        "project_id": project_id,
        "total_categories": len(categories),
        "total_files": total_files,
        "categories": result
    }


@router.get("/projects/{project_id}/grouped-by-category")
async def get_project_grouped_by_category(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all files for a specific project, grouped by their German category.
    Enforces that the project must be in 'finished_processing' status.
    """
    try:
        # Check if project exists and is finished
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status != RunStatus.finished_processing:
            raise HTTPException(
                status_code=400, 
                detail=f"Project is not finished processing. Current status: {project.status.value}"
            )

        # Query files for this project
        files = db.query(File).filter(File.project_id == project_id).all()
        
        if not files:
            return {
                "project_id": project_id,
                "project_name": project.project_name,
                "message": "No files found for this project",
                "grouped_files": {}
            }
        
        # Group files by category_german
        grouped_dict = {}
        for file in files:
            category = file.category_german or "Uncategorized"
            if category not in grouped_dict:
                grouped_dict[category] = []
            
            grouped_dict[category].append({
                "file_id": file.id,
                "file_name": os.path.basename(file.file_path),
                "file_path": file.file_path,
                "preview_url": f"/files/preview?file_path={file.file_path}",
                "confidence": file.classification_confidence,
                "reasoning": file.classification_reasoning
            })
        
        # Convert to list of category objects
        grouped_list = []
        for category, category_files in grouped_dict.items():
            grouped_list.append({
                "category": category,
                "files": category_files
            })
        
        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "total_files": len(files),
            "total_categories": len(grouped_list),
            "grouped_files": grouped_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve grouped files: {str(e)}")


@router.get("/preview")
async def preview_file(file_path: str):
    """
    Get file content for previewing by redirecting to static files.
    """
    try:
        # Security: Normalize path and check if it's within the allowed base directory
        # Use realpath to resolve any symlinks and ensure consistent path representation
        abs_file_path = os.path.realpath(file_path)
        
        # Determine the base directories
        current_file = os.path.realpath(__file__)
        # backend/app/api/endpoints/upload_pdf.py -> 4 levels up is backend
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
        
        # uploads are in backend/app/data/uploads
        uploads_dir = os.path.realpath(os.path.join(backend_dir, "app", "data", "uploads"))
        # output is in backend/output
        output_dir = os.path.realpath(os.path.join(backend_dir, "output"))

        # More robust check using commonpath
        def is_subpath(child, parent):
            try:
                return os.path.commonpath([child, parent]) == parent
            except ValueError:
                return False

        if is_subpath(abs_file_path, uploads_dir):
            rel_path = os.path.relpath(abs_file_path, uploads_dir)
            return RedirectResponse(url=f"/static/uploads/{rel_path}")
        elif is_subpath(abs_file_path, output_dir):
            rel_path = os.path.relpath(abs_file_path, output_dir)
            return RedirectResponse(url=f"/static/output/{rel_path}")
        else:
            # For debugging, we include the paths in the error message
            error_detail = (
                f"Access restricted. Path: {abs_file_path} is not in "
                f"uploads: {uploads_dir} or output: {output_dir}"
            )
            print(f"DEBUG PREVIEW: {error_detail}")
            raise HTTPException(status_code=403, detail=error_detail)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to redirect to file: {str(e)}")