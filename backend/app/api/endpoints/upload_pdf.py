from fastapi import APIRouter, UploadFile, HTTPException, Depends, File as FileUpload, Body
from sqlalchemy.orm import Session
from typing import List
import shutil
import os

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
    