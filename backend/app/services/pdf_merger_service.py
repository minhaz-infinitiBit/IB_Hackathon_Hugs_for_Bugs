"""
PDF Merger Service

This service handles merging classified PDFs into a single document organized by category.
For each category (1-20), it adds the category header page followed by any PDFs classified
in that category.

Usage:
    from services.pdf_merger_service import PDFMergerService
    
    service = PDFMergerService()
    result = service.merge_pdfs_by_category(project_id, classifications, db)
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from pypdf import PdfReader, PdfWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Category header pages folder
CATEGORY_PAGES_DIR = Path(__file__).parent.parent / "data" / "Mustermann_Max_2024_WP_pages"

# Total number of categories
TOTAL_CATEGORIES = 20


@dataclass
class PDFMergeResult:
    """Result of PDF merge operation."""
    success: bool = False
    merged_pdf_path: str = ""
    total_pages: int = 0
    categories_included: int = 0
    documents_merged: int = 0
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# Base directory for merged PDFs: backend/app/data/merged/{project_id}/
MERGED_BASE_DIR = Path(__file__).parent.parent / "data" / "merged"


class PDFMergerService:
    """
    Service for merging classified PDFs by category.
    
    This service creates a single merged PDF with:
    - Category header pages (page_001.pdf through page_020.pdf)
    - PDFs classified under each category placed after their header
    
    Example:
        >>> service = PDFMergerService()
        >>> result = service.merge_pdfs_by_category(project_id, files_by_category)
        >>> if result.success:
        ...     print(f"Merged PDF: {result.merged_pdf_path}")
    """
    
    def __init__(
        self,
        base_output_dir: str = None,
        category_pages_dir: str = None
    ):
        """
        Initialize the PDFMergerService.
        
        Args:
            base_output_dir: Base directory for saving merged PDF outputs.
                            Defaults to backend/app/data/merged
                            Actual output will be in {base_output_dir}/{project_id}/
            category_pages_dir: Directory containing category header pages.
                               Defaults to backend/app/data/Mustermann_Max_2024_WP_pages
        """
        if base_output_dir is None:
            self.base_output_dir = MERGED_BASE_DIR
        else:
            self.base_output_dir = Path(base_output_dir)
        
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        if category_pages_dir is None:
            category_pages_dir = CATEGORY_PAGES_DIR
        
        self.category_pages_dir = Path(category_pages_dir)
        
        logger.info(f"PDFMergerService initialized. Base output dir: {self.base_output_dir}")
        logger.info(f"Category pages dir: {self.category_pages_dir}")
    
    def _get_category_header_path(self, category_id: int) -> Path:
        """
        Get the path to the category header page PDF.
        
        Args:
            category_id: Category ID (1-20)
            
        Returns:
            Path to the category header PDF
        """
        # Format: page_001.pdf, page_002.pdf, etc.
        filename = f"page_{category_id:03d}.pdf"
        return self.category_pages_dir / filename
    
    def _validate_category_pages(self) -> bool:
        """
        Validate that all category header pages exist.
        
        Returns:
            True if all pages exist, False otherwise
        """
        for cat_id in range(1, TOTAL_CATEGORIES + 1):
            path = self._get_category_header_path(cat_id)
            if not path.exists():
                logger.error(f"Category header page not found: {path}")
                return False
        return True
    
    def _organize_files_by_category(
        self,
        files: List[Any]
    ) -> Dict[int, List[str]]:
        """
        Organize files by their category ID.
        
        Args:
            files: List of File model objects with category_id and file_path
            
        Returns:
            Dictionary mapping category_id to list of file paths
        """
        by_category = {cat_id: [] for cat_id in range(1, TOTAL_CATEGORIES + 1)}
        
        for file in files:
            cat_id = file.category_id
            if cat_id is not None and 1 <= cat_id <= TOTAL_CATEGORIES:
                if os.path.exists(file.file_path):
                    by_category[cat_id].append(file.file_path)
                else:
                    logger.warning(f"File not found, skipping: {file.file_path}")
        
        return by_category
    
    def merge_pdfs_by_category(
        self,
        project_id: int,
        files: List[Any],
        project_name: str = None
    ) -> PDFMergeResult:
        """
        Merge PDFs by category into a single document.
        
        For each category (1-20):
        1. Add the category header page (page_001.pdf, etc.)
        2. Add any PDFs classified in that category
        
        Args:
            project_id: The project ID
            files: List of File model objects with category_id and file_path
            project_name: Optional project name for the output filename
            
        Returns:
            PDFMergeResult with the merged PDF path and statistics
        """
        result = PDFMergeResult()
        
        # Validate category pages exist
        if not self._validate_category_pages():
            result.error_message = "Category header pages not found"
            return result
        
        try:
            # Create project-specific output directory: app/data/merged/{project_id}/
            project_output_dir = self.base_output_dir / str(project_id)
            project_output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Merged PDF output directory: {project_output_dir}")
            
            # Organize files by category
            files_by_category = self._organize_files_by_category(files)
            
            # Create PDF writer
            pdf_writer = PdfWriter()
            
            total_pages = 0
            categories_with_docs = 0
            documents_merged = 0
            
            # Process each category in order (1-20)
            for cat_id in range(1, TOTAL_CATEGORIES + 1):
                # Add category header page
                header_path = self._get_category_header_path(cat_id)
                
                try:
                    header_reader = PdfReader(str(header_path))
                    for page in header_reader.pages:
                        pdf_writer.add_page(page)
                        total_pages += 1
                    
                    logger.debug(f"Added category {cat_id} header page")
                    
                except Exception as e:
                    logger.error(f"Error reading category header {header_path}: {e}")
                    result.error_message = f"Failed to read category header: {e}"
                    return result
                
                # Add PDFs for this category (if any)
                category_files = files_by_category.get(cat_id, [])
                
                if category_files:
                    categories_with_docs += 1
                    
                    for file_path in category_files:
                        try:
                            file_reader = PdfReader(file_path)
                            for page in file_reader.pages:
                                pdf_writer.add_page(page)
                                total_pages += 1
                            
                            documents_merged += 1
                            logger.debug(f"Added document: {file_path} to category {cat_id}")
                            
                        except Exception as e:
                            logger.warning(f"Error reading PDF {file_path}: {e}")
                            # Continue with other files instead of failing
                            continue
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if project_name:
                safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
                output_filename = f"{safe_name}_merged_{timestamp}.pdf"
            else:
                output_filename = f"project_{project_id}_merged_{timestamp}.pdf"
            
            # Save to project-specific directory
            output_path = project_output_dir / output_filename
            
            # Write merged PDF
            with open(output_path, "wb") as output_file:
                pdf_writer.write(output_file)
            
            logger.info(f"Merged PDF created: {output_path}")
            logger.info(f"Total pages: {total_pages}, Documents merged: {documents_merged}")
            
            result.success = True
            result.merged_pdf_path = str(output_path)
            result.total_pages = total_pages
            result.categories_included = TOTAL_CATEGORIES  # All 20 categories are always included
            result.documents_merged = documents_merged
            
            return result
            
        except Exception as e:
            logger.error(f"PDF merge error: {e}")
            result.error_message = str(e)
            return result


def merge_project_pdfs(
    project_id: int,
    files: List[Any],
    project_name: str = None,
    base_output_dir: str = None
) -> Dict[str, Any]:
    """
    Convenience function to merge project PDFs by category.
    
    Args:
        project_id: The project ID
        files: List of File model objects
        project_name: Optional project name
        base_output_dir: Optional base output directory (merged PDF will be in {base_output_dir}/{project_id}/)
        
    Returns:
        Merge result as dictionary
    """
    service = PDFMergerService(base_output_dir=base_output_dir)
    result = service.merge_pdfs_by_category(project_id, files, project_name)
    return result.to_dict()


# Allow testing as a script
if __name__ == "__main__":
    print("PDFMergerService - Run via tasks.py after classification")
    print("Example usage:")
    print("  from app.services.pdf_merger_service import PDFMergerService")
    print("  service = PDFMergerService()")
    print("  result = service.merge_pdfs_by_category(project_id, files)")
