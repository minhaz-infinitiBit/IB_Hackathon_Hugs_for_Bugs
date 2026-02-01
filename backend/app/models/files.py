from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RunStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    in_agent_execution = "in_agent_execution"
    finished_processing = "finished_processing"
    failed_processing = "failed_processing"


class FileType(enum.Enum):
    pdf = '.pdf'
    doc = '.doc'
    docx = '.docx'
    docm = '.docm'
    dot = '.dot'
    dotx = '.dotx'
    xls = '.xls'
    xlsx = '.xlsx'
    xlsm = '.xlsm'
    xlt = '.xlt'
    xltx = '.xltx'
    ppt = '.ppt'
    pptx = '.pptx'
    pptm = '.pptm'
    pot = '.pot'
    potx = '.potx'
    rtf = '.rtf'
    odt = '.odt'
    ods = '.ods'
    odp = '.odp'
    csv = '.csv'
    txt = '.txt'
    md = '.md'
    msg = '.msg'
    eml = '.eml'
    htm = '.htm'
    html = '.html'
    png = '.png'
    jpg = '.jpg'
    jpeg = '.jpeg'
    gif = '.gif'
    bmp = '.bmp'
    tif = '.tif'
    tiff = '.tiff'
    svg = '.svg'
    webp = '.webp'
    wmf = '.wmf'
    emf = '.emf'
    eps = '.eps'


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.processing)
    project_name = Column(String, nullable=False)
    merged_pdf_path = Column(String, nullable=True)  # Path to the merged PDF after classification
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships 
    files = relationship("File", back_populates="project")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filetype = Column(Enum(FileType), nullable=False)
    
    # Preprocessing fields
    extracted_content = Column(Text, nullable=True)  # Raw extracted content
    structured_content = Column(Text, nullable=True)  # LLM-structured content
    summary = Column(Text, nullable=True)  # LLM-generated summary
    keywords = Column(Text, nullable=True)  # JSON array of keywords
    document_type = Column(String, nullable=True)  # LLM-identified document type
    key_entities = Column(Text, nullable=True)  # JSON object of key entities
    llm_output_file = Column(String, nullable=True)  # Path to LLM-processed output
    output_folder = Column(String, nullable=True)  # Path to output folder for this file
    
    # Classification fields
    category_id = Column(Integer, nullable=True)  # Category ID (1-20)
    category_german = Column(String, nullable=True)  # German category name
    category_english = Column(String, nullable=True)  # English category name
    classification_confidence = Column(String, nullable=True)  # Confidence score
    classification_reasoning = Column(Text, nullable=True)  # Reasoning for classification
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    project = relationship("Project", back_populates="files")