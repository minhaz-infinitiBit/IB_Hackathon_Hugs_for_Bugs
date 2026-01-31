"""
Document Preprocessing Service

This service handles document preprocessing:
1. Extracts content from documents using DocumentExtractor
2. Calls LLM to structure, summarize, and add keywords
3. Writes the processed content to output files

Usage:
    from services.preprocess_document import DocumentPreprocessService
    
    service = DocumentPreprocessService()
    result = service.process_document("/path/to/document.pdf")
    
    # Or run directly as a script
    python -m app.services.preprocess_document /path/to/document.pdf
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from app.data_process import DocumentExtractor, ExtractionResult
from app.agent.llm_client import DocumentLLMClient, DocumentAnalysisResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PreprocessResult:
    """Result of document preprocessing."""
    success: bool = False
    file_path: str = ""
    content: str = ""
    structured_content: str = ""  # LLM-structured content
    summary: str = ""  # LLM-generated summary
    keywords: List[str] = None  # LLM-generated keywords
    document_type: str = ""  # LLM-identified document type
    key_entities: dict = None  # LLM-extracted entities
    metadata: dict = None
    output_file: str = ""
    llm_output_file: str = ""  # Path to LLM-processed output
    error_message: str = ""
    llm_processed: bool = False  # Whether LLM processing was done
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.key_entities is None:
            self.key_entities = {}


class DocumentPreprocessService:
    """
    Service for preprocessing documents.
    
    This service extracts content from documents, cleans it,
    and uses LLM to structure, summarize, and extract keywords.
    
    Attributes:
        output_dir (Path): Directory to save output files
        device (str): Device for document extraction (cpu, cuda, mps)
        enable_llm (bool): Whether to use LLM for processing
    """
    
    def __init__(
        self,
        output_dir: str = None,
        device: str = "cpu",  # Default to CPU for Mac compatibility
        enable_image_description: bool = False,  # Disabled by default for CPU
        enable_llm: bool = True,  # Enable LLM processing by default
    ):
        """
        Initialize the DocumentPreprocessService.
        
        Args:
            output_dir: Directory to save output files. Defaults to ./output
            device: Device string for extraction (cpu, cuda:0, mps)
            enable_image_description: Enable image description generation
            enable_llm: Enable LLM processing for summarization (uses Azure OpenAI from env)
        """
        if output_dir is None:
            # Default to output directory relative to this file
            base_dir = Path(__file__).parent.parent.parent
            output_dir = base_dir / "output"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = device
        self.enable_image_description = enable_image_description
        self.enable_llm = enable_llm
        
        # Lazy initialization
        self._extractor: Optional[DocumentExtractor] = None
        self._llm_client: Optional[DocumentLLMClient] = None
        
        logger.info(f"DocumentPreprocessService initialized. Output dir: {self.output_dir}, LLM: {enable_llm}")
    
    @property
    def extractor(self) -> DocumentExtractor:
        """Lazily initialize and return the document extractor."""
        if self._extractor is None:
            self._extractor = DocumentExtractor(
                device=self.device,
                enable_image_description=self.enable_image_description
            )
        return self._extractor
    
    @property
    def llm_client(self) -> Optional[DocumentLLMClient]:
        """Lazily initialize and return the LLM client (uses Azure OpenAI)."""
        if not self.enable_llm:
            return None
        if self._llm_client is None:
            self._llm_client = DocumentLLMClient()
        return self._llm_client
    
    def process_document(self, file_path: str) -> PreprocessResult:
        """
        Process a document: extract, clean, and save output.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            PreprocessResult containing the processed content
        """
        result = PreprocessResult(file_path=file_path)
        
        logger.info(f"Processing document: {file_path}")
        
        # Step 1: Extract content from document
        extraction_result = self.extractor.extract(file_path)
        
        if not extraction_result.success:
            result.error_message = extraction_result.error_message
            logger.error(f"Extraction failed: {result.error_message}")
            return result
        
        # Step 2: Store extracted content
        result.content = extraction_result.content
        result.metadata = extraction_result.metadata
        
        # Step 3: Write raw extraction output to file
        output_file, doc_output_dir = self._write_output(file_path, extraction_result)
        result.output_file = str(output_file)
        
        # Step 4: Call LLM to structure, summarize, and add keywords
        if self.enable_llm and self.llm_client:
            try:
                logger.info("Processing with LLM for structuring and summarization...")
                file_name = Path(file_path).name
                
                llm_result = self.llm_client.analyze_document(
                    content=extraction_result.content,
                    file_name=file_name
                )
                
                if llm_result.success:
                    result.structured_content = llm_result.structured_content
                    result.summary = llm_result.summary
                    result.keywords = llm_result.keywords
                    result.document_type = llm_result.document_type
                    result.key_entities = llm_result.key_entities
                    result.llm_processed = True
                    
                    # Write LLM-processed output to separate file
                    llm_output_file = self._write_llm_output(
                        doc_output_dir, 
                        file_path, 
                        llm_result
                    )
                    result.llm_output_file = str(llm_output_file)
                    
                    logger.info(f"LLM processing complete. Document type: {result.document_type}")
                else:
                    logger.warning(f"LLM processing failed: {llm_result.error_message}")
                    
            except Exception as e:
                logger.warning(f"LLM processing error (continuing without): {e}")
        
        result.success = True
        logger.info(f"Document processed successfully. Output: {output_file}")
        
        return result
    
    def _write_output(self, file_path: str, extraction_result: ExtractionResult) -> tuple:
        """
        Write extraction results to output files.
        
        Args:
            file_path: Original file path
            extraction_result: Result from extraction
            
        Returns:
            Path to the main output file
        """
        # Create output directory for this document
        file_name = Path(file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_output_dir = self.output_dir / f"{file_name}_{timestamp}"
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write full content as markdown
        content_file = doc_output_dir / f"{file_name}_content.md"
        content_file.write_text(extraction_result.content, encoding='utf-8')
        logger.info(f"Wrote content to: {content_file}")
        
        # Write individual pages
        pages_dir = doc_output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        for idx, page_content in enumerate(extraction_result.page_contents, 1):
            page_file = pages_dir / f"page_{idx:03d}.md"
            page_file.write_text(page_content, encoding='utf-8')
        logger.info(f"Wrote {len(extraction_result.page_contents)} page files")
        
        # Write metadata as JSON
        metadata_file = doc_output_dir / f"{file_name}_metadata.json"
        with metadata_file.open('w', encoding='utf-8') as f:
            json.dump(extraction_result.metadata, f, indent=2)
        logger.info(f"Wrote metadata to: {metadata_file}")
        
        # Write a summary file with all info
        summary_file = doc_output_dir / f"{file_name}_summary.json"
        summary_data = {
            "file_path": str(file_path),
            "extraction_success": extraction_result.success,
            "metadata": extraction_result.metadata,
            "content_preview": extraction_result.content[:1000] + "..." if len(extraction_result.content) > 1000 else extraction_result.content,
            "content_length": len(extraction_result.content),
            "page_count": len(extraction_result.page_contents),
            "output_directory": str(doc_output_dir),
            "processed_at": datetime.now().isoformat(),
        }
        with summary_file.open('w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Wrote summary to: {summary_file}")
        
        return content_file, doc_output_dir
    
    def _write_llm_output(
        self, 
        doc_output_dir: Path, 
        file_path: str, 
        llm_result: DocumentAnalysisResult
    ) -> Path:
        """
        Write LLM-processed output to files.
        
        Args:
            doc_output_dir: Output directory for this document
            file_path: Original file path
            llm_result: Result from LLM analysis
            
        Returns:
            Path to the LLM output file
        """
        file_name = Path(file_path).stem
        
        # Write structured content
        structured_file = doc_output_dir / f"{file_name}_structured.md"
        structured_file.write_text(llm_result.structured_content, encoding='utf-8')
        logger.info(f"Wrote structured content to: {structured_file}")
        
        # Write LLM analysis results as JSON
        llm_output_file = doc_output_dir / f"{file_name}_llm_analysis.json"
        llm_data = {
            "document_type": llm_result.document_type,
            "summary": llm_result.summary,
            "keywords": llm_result.keywords,
            "key_entities": llm_result.key_entities,
            "processed_at": datetime.now().isoformat(),
        }
        with llm_output_file.open('w', encoding='utf-8') as f:
            json.dump(llm_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote LLM analysis to: {llm_output_file}")
        
        # Write a human-readable summary file
        summary_txt = doc_output_dir / f"{file_name}_summary.txt"
        summary_content = f"""Document Analysis Summary
{'='*50}

File: {Path(file_path).name}
Document Type: {llm_result.document_type}

SUMMARY:
{llm_result.summary}

KEYWORDS:
{', '.join(llm_result.keywords)}

KEY ENTITIES:
"""
        if llm_result.key_entities:
            for entity_type, entities in llm_result.key_entities.items():
                if entities:
                    summary_content += f"\n  {entity_type.title()}:\n"
                    for entity in entities:
                        summary_content += f"    - {entity}\n"
        
        summary_txt.write_text(summary_content, encoding='utf-8')
        logger.info(f"Wrote summary text to: {summary_txt}")
        
        return llm_output_file


def process_document_file(
    file_path: str, 
    output_dir: str = None, 
    device: str = "cpu",
    enable_llm: bool = True
) -> PreprocessResult:
    """
    Convenience function to process a document file.
    
    Args:
        file_path: Path to the document
        output_dir: Optional output directory
        device: Device to use (cpu, cuda:0, mps)
        enable_llm: Whether to enable LLM processing for summarization
        
    Returns:
        PreprocessResult with processed content
    """
    service = DocumentPreprocessService(
        output_dir=output_dir, 
        device=device,
        enable_llm=enable_llm
    )
    return service.process_document(file_path)


# Allow running as a script for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.services.preprocess_document <file_path> [output_dir] [device] [enable_llm]")
        print("  file_path: Path to the document to process")
        print("  output_dir: Optional output directory (default: ./output)")
        print("  device: Device (default: cpu, use 'cuda:0' for GPU)")
        print("  enable_llm: Enable LLM processing (default: true)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    device = sys.argv[3] if len(sys.argv) > 3 else "cpu"
    enable_llm = sys.argv[4].lower() != 'false' if len(sys.argv) > 4 else True
    
    print(f"\n{'='*60}")
    print(f"Document Preprocessing")
    print(f"{'='*60}")
    print(f"Input file: {file_path}")
    print(f"Output dir: {output_dir or 'default (./output)'}")
    print(f"Device: {device}")
    print(f"LLM enabled: {enable_llm}")
    print(f"{'='*60}\n")
    
    result = process_document_file(file_path, output_dir, device, enable_llm)
    
    print(f"\n{'='*60}")
    print(f"Processing Result")
    print(f"{'='*60}")
    print(f"Success: {result.success}")
    
    if result.success:
        print(f"Output file: {result.output_file}")
        print(f"LLM processed: {result.llm_processed}")
        if result.llm_output_file:
            print(f"LLM output file: {result.llm_output_file}")
        print(f"Metadata: {json.dumps(result.metadata, indent=2)}")
        print(f"Content length: {len(result.content)} characters")
        if result.summary:
            print(f"\nSummary:")
            print("-" * 40)
            print(result.summary)
            print("-" * 40)
        if result.keywords:
            print(f"\nKeywords: {', '.join(result.keywords)}")
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 40)
        print(result.content[:500])
        print("-" * 40)
    else:
        print(f"Error: {result.error_message}")
    
    print(f"{'='*60}\n")