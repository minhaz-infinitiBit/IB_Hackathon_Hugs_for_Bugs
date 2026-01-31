from fastapi import APIRouter, UploadFile, HTTPException, Depends, File as FileUpload
from sqlalchemy.orm import Session
from typing import List
import shutil
import os

from app.core.database import get_db
from app.schemas.pdf_upload import PDFUploadResponse, RunResponse
from app.models.files import Run, File, FileType,RunStatus

router = APIRouter()

@router.post("/upload-pdf/{run_id}", response_model=List[PDFUploadResponse])
async def upload_pdf(
    run_id: int,
    files: List[UploadFile] = FileUpload(...),
    db: Session = Depends(get_db)
):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    UPLOAD_DIR = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}/data/uploads/{run_id}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    responses = []
    saved_file_paths = []
    db_files = []

    try:
        for file in files:
            if file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a PDF")
            
            file_location = f"{UPLOAD_DIR}/{file.filename}"
            
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            saved_file_paths.append(file_location)

            db_file = File(
                file_path=file_location,
                run_id=run_id,
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
                    run_id=run_id
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


@router.post("/runs/", response_model=RunResponse)
async def create_run(db: Session = Depends(get_db)):
    try:
        run = Run(status=RunStatus.pending)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")


@router.get("/runs/{run_id}/files", response_model=List[PDFUploadResponse])
async def list_run_files(
    run_id: int,
    db: Session = Depends(get_db)
):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    files = db.query(File).filter(File.run_id == run_id).all()
    
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
                run_id=run_id
            )
        )
    
    db.commit()
    
    return responses