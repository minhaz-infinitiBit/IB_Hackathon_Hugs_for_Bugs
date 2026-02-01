#!/usr/bin/env python3
"""
Test Script for Document Preprocessing Module

This script tests the document extraction and preprocessing functionality.
Uses sample files from the files/ folder or pass a file path as argument.

Usage:
    python test_preprocess.py [path/to/document.pdf] [--device cpu] [--enable-llm]
    
Example:
    python test_preprocess.py
    python test_preprocess.py ../files/1.pdf
    python test_preprocess.py ../files/1.pdf --enable-llm
"""

import argparse
import sys
import os

# Add the backend app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.preprocess_document import DocumentPreprocessService, process_document_file

# Sample test files from the files/ folder (relative to backend/)
# Includes: PDF, Image, CSV, XLSB, and MSG files
SAMPLE_FILES = [
    # Already processed:
    # "../files/1.pdf",
    # "../files/Bild1.png",
    # "../files/ActivityDetails-Germany.csv",
    # "../files/Reisekalenderauswertung.xlsb",
    # "../files/Re Flynn Management Ltd - Begley Thomas - 2022 German Income Tax Assessment Notice.msg",
    # "../files/4941181 - BvF mit Termin_ Unterlagen und Lohnnachweis.pdf",
    
    # Remaining PDF files:
    "../files/2.pdf",
    "../files/3.pdf",
    "../files/4.pdf",
    "../files/5.pdf",
    "../files/6.pdf",
    "../files/7.pdf",
    "../files/8.pdf",
    "../files/9.pdf",
    "../files/10.pdf",
    "../files/11.pdf",
    "../files/12.pdf",
    "../files/2024 Germany Tax Questionnaire.pdf",
    "../files/35041_01-2024_DivAuswertungen__002.pdf",
    "../files/35041_02-2024_DivAuswertungen__004.pdf",
    "../files/35041_02-2024_DivAuswertungen__005.pdf",
    "../files/35041_03-2024_DivAuswertungen__606.pdf",
    "../files/35041_04-2024_DivAuswertungen__906.pdf",
    "../files/35041_05-2024_DivAuswertungen__C04.pdf",
    "../files/35041_06-2024_DivAuswertungen__F03.pdf",
    "../files/35041_07-2024_DivAuswertungen__I04.pdf",
    "../files/35041_08-2024_DivAuswertungen__L05.pdf",
    "../files/35041_09-2024_DivAuswertungen__O04.pdf",
    "../files/35041_10-2024_DivAuswertungen__R02.pdf",
    "../files/35041_11-2024_DivAuswertungen__U03.pdf",
    "../files/35041_12-2024_DivAuswertungen__X03.pdf",
    "../files/5070400 - ESt-Bescheid 2023 .pdf",
    "../files/Arbeitstagekalender 2024.pdf",
    "../files/CC 2023 Income Tax Cover Letter.pdf",
    "../files/Coughlan, Cian_2023_German Income Tax Return.pdf",
    "../files/Coughlan, Cian_2024_EStE_German Tax Return.pdf",
    "../files/Coughlan, Cian_WP_2024.pdf",
    "../files/Lohnsteuerbescheinigungen 2024.pdf",
    "../files/Re Flynn Management Ltd  Begley, Thomas  2022 German Income Tax Assessment Notice.pdf",
    
    # Remaining Image files:
    "../files/Bild2.png",
    "../files/Bild3.png",
    "../files/Bild4.png",
    "../files/Bild5.png",
    "../files/Bild6.png",
    "../files/Bild7.png",
    "../files/Bild8.png",
    "../files/Bild9.png",
    "../files/Bild10.png",
    "../files/Bild11.png",
    "../files/Bild12.png",
]


def main():
    parser = argparse.ArgumentParser(description="Test document preprocessing")
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to the document to process"
    )
    parser.add_argument(
        "--device",
        default="cpu",  # Default to CPU for Mac without CUDA
        help="Device to use (cpu, mps for Apple Silicon)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for extracted content"
    )
    parser.add_argument(
        "--no-image-description",
        action="store_true",
        default=True,  # Disabled by default for faster testing on CPU
        help="Disable image description generation (faster)"
    )
    parser.add_argument(
        "--enable-image-description",
        action="store_true",
        help="Enable image description generation"
    )
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        default=True,
        help="Enable LLM processing for document summarization and structuring (default: enabled)"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM processing"
    )
    
    args = parser.parse_args()
    
    # Handle image description flag
    enable_image_desc = args.enable_image_description and not args.no_image_description
    
    # Handle LLM flag - enabled by default unless explicitly disabled
    enable_llm = not args.no_llm
    
    # Collect files to process
    files_to_process = []
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.file_path:
        # Single file specified
        files_to_process.append(args.file_path)
    else:
        # Process all sample files
        for sample in SAMPLE_FILES:
            sample_path = os.path.join(backend_dir, sample)
            if os.path.exists(sample_path):
                files_to_process.append(sample_path)
        
        if not files_to_process:
            print("No sample files found in ../files/")
            print("Usage: python test_preprocess.py <path_to_file>")
            return 1
    
    print("\n" + "=" * 70)
    print("Document Preprocessing Test")
    print("=" * 70)
    print(f"Files to process: {len(files_to_process)}")
    for f in files_to_process:
        print(f"  - {os.path.basename(f)}")
    print(f"Device: {args.device}")
    print(f"Output dir: {args.output_dir or 'default (./output)'}")
    print(f"Image description: {'enabled' if enable_image_desc else 'disabled'}")
    print(f"LLM processing: {'enabled' if enable_llm else 'disabled'}")
    print("=" * 70 + "\n")
    
    # Create service
    service = DocumentPreprocessService(
        output_dir=args.output_dir,
        device=args.device,
        enable_image_description=enable_image_desc,
        enable_llm=enable_llm
    )
    
    # Process each file
    results = []
    for file_path in files_to_process:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n{'='*70}")
        print(f"Processing: {os.path.basename(file_path)}")
        print("="*70)
        
        result = service.process_document(file_path)
        results.append((file_path, result))
        
        if result.success:
            print(f"✅ Success!")
            print(f"   Output: {result.output_file}")
            print(f"   Pages: {result.metadata.get('page_count', 'N/A')}")
            print(f"   Content length: {len(result.content)} chars")
            if result.llm_processed:
                print(f"   🤖 LLM processed: Yes")
                print(f"   LLM output: {result.llm_output_file}")
                if result.summary:
                    print(f"   Summary: {result.summary[:100]}...")
                if result.keywords:
                    print(f"   Keywords: {', '.join(result.keywords[:5])}")
        else:
            print(f"❌ Failed: {result.error_message}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    success_count = sum(1 for _, r in results if r.success)
    llm_count = sum(1 for _, r in results if r.llm_processed)
    print(f"Processed: {len(results)} files")
    print(f"Success: {success_count}")
    print(f"LLM processed: {llm_count}")
    print(f"Failed: {len(results) - success_count}")
    
    for file_path, result in results:
        status = "✅" if result.success else "❌"
        llm_status = "🤖" if result.llm_processed else ""
        print(f"  {status} {llm_status} {os.path.basename(file_path)}")
        if result.success:
            print(f"      Output: {result.output_file}")
            if result.llm_output_file:
                print(f"      LLM output: {result.llm_output_file}")
    
    print("=" * 70 + "\n")
    
    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
