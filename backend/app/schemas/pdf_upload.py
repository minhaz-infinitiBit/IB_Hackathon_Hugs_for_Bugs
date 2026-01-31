from pydantic import BaseModel

class PDFUploadResponse(BaseModel):
    filename: str
    content_type: str
    message: str
    location: str
    run_id: int

class RunResponse(BaseModel):
    id: int
    status: str

    class Config:
        from_attributes = True

