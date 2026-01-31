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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships 
    files = relationship("File", back_populates="project")
    ordering = relationship("Ordering", back_populates="project", uselist=False)


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filetype = Column(Enum(FileType), nullable=False)
    category_german = Column(String, nullable=True) # Store JSON as text
    category_english = Column(String, nullable=True)
    summary_json = Column(Text, nullable=True)  # Store JSON as text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    project = relationship("Project", back_populates="files")


class Ordering(Base):
    __tablename__ = "ordering"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    ordering_json = Column(Text, nullable=False)  # Store JSON as text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    project = relationship("Project", back_populates="ordering")