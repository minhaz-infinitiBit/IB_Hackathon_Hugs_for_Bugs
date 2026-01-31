from pydantic import BaseModel
from datetime import datetime

class PDFUploadResponse(BaseModel):
    filename: str
    content_type: str
    message: str
    location: str
    project_id: int

class ProjectResponse(BaseModel):
    id: int
    project_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

