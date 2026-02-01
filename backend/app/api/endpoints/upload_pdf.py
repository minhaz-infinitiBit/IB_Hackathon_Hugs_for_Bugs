from fastapi import APIRouter, UploadFile, HTTPException, Depends, File as FileUpload, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import json

from app.core.database import get_db
from app.schemas.pdf_upload import PDFUploadResponse, ProjectResponse
from app.models.files import Project, File, FileType, RunStatus
from app.tasks import document_processing

router = APIRouter()

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
    