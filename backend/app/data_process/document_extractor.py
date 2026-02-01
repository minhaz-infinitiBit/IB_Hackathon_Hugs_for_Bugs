"""
Document Extractor Module

A class-based module for extracting and cleaning content from documents
using Docling. Supports PDF, Images (PNG, JPG, JPEG), Office files
(DOCX, XLSX, PPTX via LibreOffice conversion), CSV, XLSB (via pandas),
and MSG (Outlook email) files.

Usage:
    from data_process.document_extractor import DocumentExtractor
    
    extractor = DocumentExtractor()
    result = extractor.extract(file_path="/path/to/document.pdf")
    
    if result.success:
        print(result.content)  # Cleaned markdown content
        print(result.metadata)  # Document metadata
"""

import logging
import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Docling imports
from docling_core.types.doc.base import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    smolvlm_picture_description,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc.document import PictureDescriptionData

# Pandas for CSV/Excel files
import pandas as pd


logger = logging.getLogger(__name__)


def get_best_device() -> str:
    """
    Detect and return the best available device for processing.
    
    Returns:
        'cuda' if CUDA is available, otherwise 'cpu'
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


# Supported file extensions
PDF_EXTENSIONS = {'.pdf'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
# Office files that need LibreOffice conversion
OFFICE_EXTENSIONS = {
    '.doc', '.docx', '.docm', '.dot', '.dotx', '.rtf',  # Word
    '.xls', '.xlsx', '.xlsm', '.xlt', '.xltx',  # Excel (not CSV/XLSB)
    '.ppt', '.pptx', '.pot', '.potx',  # PowerPoint
    '.odt',  # OpenDocument
}
# Files handled directly by pandas (no LibreOffice needed)
PANDAS_EXTENSIONS = {'.csv', '.xlsb'}
# Email files
EMAIL_EXTENSIONS = {'.msg', '.eml'}


@dataclass
class ExtractionResult:
    """Result of document extraction operation."""
    success: bool = False
    content: str = ""
    page_contents: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    error_message: str = ""
    file_path: str = ""
    

@dataclass
class DocumentMetadata:
    """Metadata extracted from document."""
    file_name: str = ""
    file_path: str = ""
    file_type: str = ""
    page_count: int = 0
    image_count: int = 0
    table_count: int = 0
    extracted_at: str = ""


class OfficeToPdfError(RuntimeError):
    """Error during Office to PDF conversion."""
    pass


class DocumentExtractor:
    """
    A class for extracting content from documents using Docling.
    
    Supports:
        - PDF files (direct processing)
        - Image files (PNG, JPG, JPEG) via OCR
        - Office files (DOCX, XLSX, PPTX, etc.) via LibreOffice conversion
    
    Attributes:
        device (str): Device to use for processing (default: "cpu")
        enable_image_description (bool): Whether to generate image descriptions
    
    Example:
        >>> extractor = DocumentExtractor(device="cpu")
        >>> result = extractor.extract("/path/to/document.pdf")
        >>> if result.success:
        ...     print(result.content)
    """
    
    def __init__(
        self, 
        device: Optional[str] = None,
        enable_image_description: bool = False,
        enable_formula_enrichment: bool = True,
        enable_code_enrichment: bool = True,
        enable_table_structure: bool = True,
        max_pages: int = 4,
    ):
        """
        Initialize the DocumentExtractor.
        
        Args:
            device: Device string (e.g., "cpu", "cuda", "cuda:0", "mps" for Apple Silicon).
                    If None, auto-detects best available device (CUDA if available, else CPU).
            enable_image_description: Enable SmolVLM image description generation
            enable_formula_enrichment: Enable formula/math enrichment
            enable_code_enrichment: Enable code block enrichment
            enable_table_structure: Enable table structure recognition for better tables
            max_pages: Maximum number of pages to extract (default: 4). Set to 0 or None for no limit.
        """
        # Auto-detect device if not specified
        self.device = device if device is not None else get_best_device()
        self.enable_image_description = enable_image_description
        self._converter: Optional[DocumentConverter] = None
        self._initialized = False
        
        # Configuration options
        self._enable_formula_enrichment = enable_formula_enrichment
        self._enable_code_enrichment = enable_code_enrichment
        self._enable_table_structure = enable_table_structure
        self._max_pages = max_pages if max_pages and max_pages > 0 else None
        
        # LibreOffice executable cache
        self._libreoffice_exe: Optional[str] = None
        
        logger.info(f"DocumentExtractor configured to use device: {self.device}")
        
    def _initialize_converter(self) -> None:
        """Lazily initialize the Docling document converter."""
        if self._initialized:
            return
            
        logger.info(f"Initializing DocumentExtractor with device: {self.device}")
        
        pipeline_options = PdfPipelineOptions()
        
        # Enable enrichments
        pipeline_options.do_code_enrichment = self._enable_code_enrichment
        pipeline_options.do_formula_enrichment = self._enable_formula_enrichment
        pipeline_options.do_picture_description = self.enable_image_description
        
        # Enable table structure recognition for better table extraction
        if self._enable_table_structure:
            pipeline_options.do_table_structure = True
            try:
                pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            except Exception:
                # Fallback if TableFormerMode not available
                pass
        
        if self.enable_image_description:
            pipeline_options.picture_description_options = smolvlm_picture_description
            pipeline_options.picture_description_options.prompt = (
                "Describe the image in three sentences. Be concise and accurate."
            )
        
        # Set accelerator options
        pipeline_options.accelerator_options = AcceleratorOptions(device=self.device)
        
        # Image processing settings - enable for better quality
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        
        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        
        self._initialized = True
        logger.info("DocumentExtractor initialized successfully")
    
    def extract(self, file_path: str) -> ExtractionResult:
        """
        Extract content from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractionResult containing the extracted content and metadata
        """
        result = ExtractionResult(file_path=file_path)
        
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            result.error_message = f"File not found: {file_path}"
            logger.error(result.error_message)
            return result
        
        ext = path.suffix.lower()
        
        try:
            # Initialize converter if needed
            self._initialize_converter()
            
            # Route to appropriate processor based on file type
            if ext in PDF_EXTENSIONS:
                return self._extract_pdf(path)
            elif ext in IMAGE_EXTENSIONS:
                return self._extract_image(path)
            elif ext in PANDAS_EXTENSIONS:
                return self._extract_pandas(path)
            elif ext in EMAIL_EXTENSIONS:
                return self._extract_email(path)
            elif ext in OFFICE_EXTENSIONS:
                return self._extract_office(path)
            else:
                result.error_message = f"Unsupported file type: {ext}"
                logger.error(result.error_message)
                return result
            
        except Exception as e:
            result.error_message = f"Error extracting document: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _extract_pdf(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from a PDF file using Docling.
        
        Args:
            file_path: Path object to the PDF file
            
        Returns:
            ExtractionResult with extracted content
        """
        result = ExtractionResult(file_path=str(file_path))
        
        try:
            # Convert the document
            conversion_result = self._converter.convert(file_path)
            doc = conversion_result.document
            
            # Extract page contents (limited to max_pages if set)
            page_contents = []
            page_numbers = []
            total_pages = len(doc.pages)
            pages_to_process = list(doc.pages.values())
            
            # Limit to max_pages if configured
            if self._max_pages and len(pages_to_process) > self._max_pages:
                pages_to_process = pages_to_process[:self._max_pages]
                logger.info(f"Limiting extraction to {self._max_pages} pages (document has {total_pages} pages)")
            
            for page in pages_to_process:
                page_no = page.page_no
                page_numbers.append(page_no)
                
                page_content = doc.export_to_markdown(
                    page_no=page_no,
                    image_mode=ImageRefMode.PLACEHOLDER,
                )
                page_contents.append(page_content)
            
            # Extract image captions and annotations
            captions = []
            annotations = []
            
            for picture in doc.pictures:
                caption = picture.caption_text(doc=doc) or ''
                captions.append(caption)
                
                annot = ''
                for ann in picture.annotations:
                    if isinstance(ann, PictureDescriptionData):
                        annot += ann.text + "\n"
                annotations.append(annot.strip())
            
            # Build full content with image metadata embedded
            full_content = self._build_full_content(
                page_numbers, page_contents, captions, annotations
            )
            
            # Clean the content
            cleaned_content = self._clean_content(full_content)
            cleaned_page_contents = [self._clean_content(pc) for pc in page_contents]
            
            # Build metadata
            pages_extracted = len(page_contents)
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
                "page_count": total_pages,
                "pages_extracted": pages_extracted,
                "image_count": len(doc.pictures),
                "table_count": len(doc.tables),
                "extracted_at": datetime.now().isoformat(),
            }
            
            result.success = True
            result.content = cleaned_content
            result.page_contents = cleaned_page_contents
            result.metadata = metadata
            
            logger.info(
                f"Successfully extracted '{file_path.name}': "
                f"{pages_extracted}/{total_pages} pages, "
                f"{metadata['image_count']} images, "
                f"{metadata['table_count']} tables"
            )
            
            return result
            
        except Exception as e:
            result.error_message = f"PDF extraction failed: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _extract_image(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from an image file using OCR.
        
        Args:
            file_path: Path object to the image file
            
        Returns:
            ExtractionResult with extracted content
        """
        result = ExtractionResult(file_path=str(file_path))
        
        try:
            # Docling can process images directly
            conversion_result = self._converter.convert(file_path)
            doc = conversion_result.document
            
            # Export to markdown
            content = doc.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
            cleaned_content = self._clean_content(content)
            
            # Build metadata
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
                "page_count": 1,
                "image_count": len(doc.pictures) if hasattr(doc, 'pictures') else 0,
                "table_count": len(doc.tables) if hasattr(doc, 'tables') else 0,
                "extracted_at": datetime.now().isoformat(),
            }
            
            result.success = True
            result.content = cleaned_content
            result.page_contents = [cleaned_content]
            result.metadata = metadata
            
            logger.info(f"Successfully extracted image '{file_path.name}'")
            
            return result
            
        except Exception as e:
            result.error_message = f"Image extraction failed: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _extract_office(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from an Office file by converting to PDF first.
        
        Args:
            file_path: Path object to the Office file
            
        Returns:
            ExtractionResult with extracted content
        """
        result = ExtractionResult(file_path=str(file_path))
        
        try:
            # Convert Office file to PDF using LibreOffice
            with tempfile.TemporaryDirectory(prefix="office_convert_") as temp_dir:
                temp_path = Path(temp_dir)
                pdf_path = self._convert_office_to_pdf(file_path, temp_path)
                
                if not pdf_path.exists():
                    result.error_message = f"Failed to convert {file_path.name} to PDF"
                    return result
                
                # Extract from the converted PDF
                pdf_result = self._extract_pdf(pdf_path)
                
                # Update metadata to reflect original file
                if pdf_result.success:
                    pdf_result.metadata["file_name"] = file_path.name
                    pdf_result.metadata["file_path"] = str(file_path)
                    pdf_result.metadata["file_type"] = file_path.suffix
                    pdf_result.metadata["converted_from"] = file_path.suffix
                    pdf_result.file_path = str(file_path)
                
                return pdf_result
                
        except OfficeToPdfError as e:
            result.error_message = f"Office conversion failed: {str(e)}"
            logger.error(result.error_message)
            return result
        except Exception as e:
            result.error_message = f"Office extraction failed: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _extract_pandas(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from CSV or XLSB files using pandas.
        
        Args:
            file_path: Path object to the CSV/XLSB file
            
        Returns:
            ExtractionResult with extracted content
        """
        result = ExtractionResult(file_path=str(file_path))
        
        try:
            ext = file_path.suffix.lower()
            content_parts = []
            sheet_count = 0
            row_count = 0
            
            if ext == '.csv':
                # Read CSV file
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
                sheet_count = 1
                row_count = len(df)
                
                content_parts.append(f"# {file_path.name}\n")
                content_parts.append(f"**File Type:** CSV\n")
                content_parts.append(f"**Rows:** {len(df)}\n")
                content_parts.append(f"**Columns:** {len(df.columns)}\n\n")
                content_parts.append("## Data\n\n")
                content_parts.append(df.to_markdown(index=False))
                
            elif ext == '.xlsb':
                # Read XLSB file (Excel Binary) - requires pyxlsb
                try:
                    # Try to read all sheets
                    xl = pd.ExcelFile(file_path, engine='pyxlsb')
                    sheet_names = xl.sheet_names
                    sheet_count = len(sheet_names)
                    
                    content_parts.append(f"# {file_path.name}\n")
                    content_parts.append(f"**File Type:** Excel Binary (XLSB)\n")
                    content_parts.append(f"**Sheets:** {len(sheet_names)}\n\n")
                    
                    for sheet_name in sheet_names:
                        df = pd.read_excel(xl, sheet_name=sheet_name)
                        row_count += len(df)
                        
                        content_parts.append(f"## Sheet: {sheet_name}\n")
                        content_parts.append(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}\n\n")
                        
                        if len(df) > 0:
                            content_parts.append(df.to_markdown(index=False))
                        else:
                            content_parts.append("*(Empty sheet)*")
                        content_parts.append("\n\n")
                        
                except ImportError:
                    result.error_message = "pyxlsb not installed. Install with: pip install pyxlsb"
                    logger.error(result.error_message)
                    return result
            
            full_content = "\n".join(content_parts)
            cleaned_content = self._clean_content(full_content)
            
            # Build metadata
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
                "page_count": sheet_count,
                "row_count": row_count,
                "image_count": 0,
                "table_count": sheet_count,
                "extracted_at": datetime.now().isoformat(),
            }
            
            result.success = True
            result.content = cleaned_content
            result.page_contents = [cleaned_content]
            result.metadata = metadata
            
            logger.info(f"Successfully extracted '{file_path.name}': {sheet_count} sheets, {row_count} rows")
            
            return result
            
        except Exception as e:
            result.error_message = f"Pandas extraction failed: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _extract_email(self, file_path: Path) -> ExtractionResult:
        """
        Extract content from email files (.msg, .eml).
        
        Args:
            file_path: Path object to the email file
            
        Returns:
            ExtractionResult with extracted content
        """
        result = ExtractionResult(file_path=str(file_path))
        
        try:
            ext = file_path.suffix.lower()
            content_parts = []
            attachments = []
            
            if ext == '.msg':
                # Extract from Outlook MSG file
                try:
                    import extract_msg
                    
                    msg = extract_msg.Message(str(file_path))
                    
                    content_parts.append(f"# Email: {msg.subject or 'No Subject'}\n")
                    content_parts.append(f"**From:** {msg.sender or 'Unknown'}\n")
                    content_parts.append(f"**To:** {msg.to or 'Unknown'}\n")
                    if msg.cc:
                        content_parts.append(f"**CC:** {msg.cc}\n")
                    content_parts.append(f"**Date:** {msg.date or 'Unknown'}\n\n")
                    
                    content_parts.append("## Body\n\n")
                    body = msg.body or ""
                    if not body and msg.htmlBody:
                        # Try to extract text from HTML body
                        import re
                        body = re.sub(r'<[^>]+>', ' ', msg.htmlBody)
                        body = re.sub(r'\s+', ' ', body).strip()
                    content_parts.append(body)
                    content_parts.append("\n\n")
                    
                    # List attachments
                    if msg.attachments:
                        content_parts.append("## Attachments\n\n")
                        for att in msg.attachments:
                            att_name = getattr(att, 'longFilename', None) or getattr(att, 'shortFilename', 'Unknown')
                            attachments.append(att_name)
                            content_parts.append(f"- {att_name}\n")
                    
                    msg.close()
                    
                except ImportError:
                    result.error_message = "extract-msg not installed. Install with: pip install extract-msg"
                    logger.error(result.error_message)
                    return result
                    
            elif ext == '.eml':
                # Extract from EML file
                import email
                from email import policy
                
                with open(file_path, 'rb') as f:
                    msg = email.message_from_binary_file(f, policy=policy.default)
                
                content_parts.append(f"# Email: {msg.get('Subject', 'No Subject')}\n")
                content_parts.append(f"**From:** {msg.get('From', 'Unknown')}\n")
                content_parts.append(f"**To:** {msg.get('To', 'Unknown')}\n")
                if msg.get('Cc'):
                    content_parts.append(f"**CC:** {msg.get('Cc')}\n")
                content_parts.append(f"**Date:** {msg.get('Date', 'Unknown')}\n\n")
                
                content_parts.append("## Body\n\n")
                
                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == 'text/plain':
                            body = part.get_content()
                            break
                        elif content_type == 'text/html' and not body:
                            html = part.get_content()
                            body = re.sub(r'<[^>]+>', ' ', html)
                            body = re.sub(r'\s+', ' ', body).strip()
                else:
                    body = msg.get_content()
                
                content_parts.append(body or "(No body content)")
                content_parts.append("\n\n")
                
                # List attachments
                if msg.is_multipart():
                    att_list = []
                    for part in msg.walk():
                        filename = part.get_filename()
                        if filename:
                            att_list.append(filename)
                            attachments.append(filename)
                    
                    if att_list:
                        content_parts.append("## Attachments\n\n")
                        for att_name in att_list:
                            content_parts.append(f"- {att_name}\n")
            
            full_content = "\n".join(content_parts)
            cleaned_content = self._clean_content(full_content)
            
            # Build metadata
            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix,
                "page_count": 1,
                "image_count": 0,
                "table_count": 0,
                "attachment_count": len(attachments),
                "attachments": attachments,
                "extracted_at": datetime.now().isoformat(),
            }
            
            result.success = True
            result.content = cleaned_content
            result.page_contents = [cleaned_content]
            result.metadata = metadata
            
            logger.info(f"Successfully extracted email '{file_path.name}': {len(attachments)} attachments")
            
            return result
            
        except Exception as e:
            result.error_message = f"Email extraction failed: {str(e)}"
            logger.exception(result.error_message)
            return result
    
    def _convert_office_to_pdf(self, input_path: Path, out_dir: Path, timeout_sec: int = 300) -> Path:
        """
        Convert Office file to PDF using LibreOffice headless.
        
        Args:
            input_path: Path to the Office file
            out_dir: Output directory for the PDF
            timeout_sec: Timeout in seconds
            
        Returns:
            Path to the converted PDF
        """
        input_path = input_path.resolve()
        if not input_path.is_file():
            raise OfficeToPdfError(f"Input file not found: {input_path}")
        
        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        
        lo_exe = self._get_libreoffice_executable()
        
        with tempfile.TemporaryDirectory(prefix="lo_user_") as temp_user_dir:
            user_installation_url = Path(temp_user_dir).as_uri()
            
            cmd = [
                lo_exe,
                f"-env:UserInstallation={user_installation_url}",
                "--headless",
                "--nofirststartwizard",
                "--nologo",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(input_path),
            ]
            
            logger.info(f"Converting {input_path.name} to PDF using LibreOffice...")
            
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_sec,
                )
            except subprocess.TimeoutExpired as e:
                raise OfficeToPdfError(
                    f"LibreOffice timed out converting '{input_path.name}' after {timeout_sec}s."
                ) from e
            except subprocess.CalledProcessError as e:
                raise OfficeToPdfError(
                    f"LibreOffice failed to convert '{input_path.name}' "
                    f"(exit code {e.returncode}). stderr:\n{e.stderr.decode(errors='ignore')}"
                ) from e
            except FileNotFoundError as e:
                raise OfficeToPdfError(f"LibreOffice executable not found at '{lo_exe}'.") from e
        
        pdf_path = out_dir / f"{input_path.stem}.pdf"
        if not pdf_path.exists():
            raise OfficeToPdfError(
                f"Expected PDF '{pdf_path.name}' not found after LibreOffice conversion."
            )
        
        logger.info(f"Successfully converted {input_path.name} to PDF")
        return pdf_path
    
    def _get_libreoffice_executable(self) -> str:
        """Find and cache LibreOffice executable."""
        if self._libreoffice_exe is not None:
            return self._libreoffice_exe
        
        # Check environment variables first
        env_override = os.getenv("LIBREOFFICE_PATH") or os.getenv("SOFFICE_PATH")
        if env_override and Path(env_override).exists():
            self._libreoffice_exe = env_override
            return self._libreoffice_exe
        
        # Platform-specific search
        if platform.system() == "Windows":
            candidates = [
                shutil.which("soffice"),
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        elif platform.system() == "Darwin":  # macOS
            candidates = [
                shutil.which("libreoffice"),
                shutil.which("soffice"),
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            ]
        else:  # Linux
            candidates = [
                shutil.which("libreoffice"),
                shutil.which("soffice"),
            ]
        
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                self._libreoffice_exe = candidate
                logger.info(f"Found LibreOffice at: {candidate}")
                return self._libreoffice_exe
        
        raise OfficeToPdfError(
            "LibreOffice not found. Install it or set LIBREOFFICE_PATH env var.\n"
            "On macOS: brew install --cask libreoffice"
        )
    
    def _build_full_content(
        self, 
        page_numbers: List[int], 
        page_contents: List[str],
        captions: List[str],
        annotations: List[str]
    ) -> str:
        """
        Build the full document content with image metadata.
        
        Args:
            page_numbers: List of page numbers
            page_contents: List of page content strings
            captions: List of image captions
            annotations: List of image annotations/descriptions
            
        Returns:
            Combined markdown content
        """
        # Create image replacer function
        image_pattern = re.compile(r"<!--\s*image\s*-->")
        replacer = self._make_image_replacer(captions, annotations)
        
        full_content = ''
        for idx, page_no in enumerate(page_numbers):
            page_content = page_contents[idx]
            # Replace image placeholders with actual captions/annotations
            page_content = image_pattern.sub(replacer, page_content)
            full_content += f"\n<!-- page {page_no} -->\n{page_content}"
        
        return full_content
    
    def _make_image_replacer(self, captions: List[str], annotations: List[str]):
        """
        Create a replacer function for image placeholders.
        
        Args:
            captions: List of image captions
            annotations: List of image annotations
            
        Returns:
            Replacer function for re.sub
        """
        i = [0]  # Use list to allow mutation in closure
        
        def _repl(_):
            idx = i[0]
            cap = (captions[idx] or "").strip() if idx < len(captions) else ""
            ann = (annotations[idx] or "").strip() if idx < len(annotations) else ""
            i[0] += 1
            
            if cap or ann:
                lines = [f"\n```\n-- image {idx + 1} --"]
                if cap:
                    lines.append(f"caption: {cap}")
                if ann:
                    lines.append(f"description: {ann}")
                return "\n".join(lines) + "\n```\n"
            else:
                return f"<!-- image {idx + 1} -->"
        
        return _repl
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and normalize the extracted content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Cleaned content string
        """
        if not content:
            return ""
        
        # Remove excessive whitespace while preserving structure
        # Remove multiple consecutive blank lines (keep max 2)
        content = re.sub(r'\n{4,}', '\n\n\n', content)
        
        # Remove trailing whitespace from each line
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        content = '\n'.join(lines)
        
        # Remove leading/trailing whitespace from the entire document
        content = content.strip()
        
        return content


# Convenience function for simple usage
def extract_document(file_path: str, device: Optional[str] = None, max_pages: int = 4) -> ExtractionResult:
    """
    Convenience function to extract content from a document.
    
    Args:
        file_path: Path to the document file
        device: Device to use (cpu, cuda, cuda:0, mps). If None, auto-detects best available device.
        max_pages: Maximum number of pages to extract (default: 4). Set to 0 or None for no limit.
        
    Returns:
        ExtractionResult with extracted content
    """
    extractor = DocumentExtractor(device=device, max_pages=max_pages)
    return extractor.extract(file_path)
