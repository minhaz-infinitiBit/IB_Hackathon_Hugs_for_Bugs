from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter()

@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    import shutil
    import os

    UPLOAD_DIR = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}/data/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    return {"filename": file.filename, "content_type": file.content_type, "message": "File uploaded successfully", "location": file_location}

