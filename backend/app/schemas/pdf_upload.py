from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

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
    merged_pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== RECLASSIFICATION SCHEMAS ====================

class ReclassificationRequest(BaseModel):
    """
    Request to reclassify files in a project.
    
    This is the human-in-the-loop endpoint that allows changing
    file categories after initial classification using natural language.
    """
    prompt: str = Field(
        ...,
        min_length=5,
        description="Natural language instruction for reclassification. "
                    "E.g., 'Move the bank statement PDF to category 3' or "
                    "'The document contract.pdf should be in employment category'"
    )
    regenerate_pdf: bool = Field(
        True, 
        description="Whether to regenerate the merged PDF after reclassification"
    )


class ReclassificationResultItem(BaseModel):
    """Result for a single file reclassification."""
    file_id: int
    old_category_id: Optional[int] = None
    new_category_id: int
    success: bool
    message: str


class ReclassificationResponse(BaseModel):
    """Response for reclassification request."""
    project_id: int
    success: bool
    message: str
    prompt: Optional[str] = None
    agent_reasoning: Optional[str] = None
    total_updates: int
    successful_updates: int
    failed_updates: int
    results: List[ReclassificationResultItem]
    merged_pdf_regenerated: bool = False
    merged_pdf_path: Optional[str] = None
    download_url: Optional[str] = None


class ProjectMemoryResponse(BaseModel):
    """Response for getting project memory/results."""
    project_id: int
    found: bool
    total_documents: int = 0
    classifications: List[dict] = []
    merged_pdf_path: Optional[str] = None
    timestamp: Optional[str] = None
