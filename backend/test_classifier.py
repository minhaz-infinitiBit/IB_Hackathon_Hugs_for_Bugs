#!/usr/bin/env python3
"""
Test Script for Document Classification Agent

This script tests the document classification workflow that:
1. Loads preprocessed document summaries from backend/output
2. Uses Azure OpenAI to classify documents into 20 tax categories
3. Saves results to a JSON file

Usage:
    python test_classifier.py [--output-dir PATH] [--no-memory]
"""

import argparse
import sys
import os
import json

# Add the backend app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent import ClassificationAgent, run_classification


def main():
    parser = argparse.ArgumentParser(description="Test document classification agent")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory containing preprocessed document outputs (default: ./output)"
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable mem0 memory layer"
    )
    parser.add_argument(
        "--save-path",
        default=None,
        help="Custom path for saving classification results"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("Document Classification Agent Test")
    print("=" * 70)
    
    # Initialize agent
    agent = ClassificationAgent(
        output_dir=args.output_dir,
        use_memory=not args.no_memory
    )
    
    print(f"Output directory: {agent.output_dir}")
    print(f"Memory enabled: {not args.no_memory}")
    print(f"Categories loaded: {len(agent.categories)}")
    
    # Validate workflow
    print("\n🔍 Validating workflow...")
    if not agent.workflow_validate():
        print("❌ Workflow validation failed!")
        return 1
    print("✅ Workflow validation passed!")
    print("=" * 70 + "\n")
    
    # Load and display documents to classify
    print("📄 Loading document summaries...")
    documents = agent.load_document_summaries()
    
    print(f"\nFound {len(documents)} documents to classify:")
    for i, doc in enumerate(documents[:10], 1):  # Show first 10
        print(f"  {i}. {doc['file_name']}")
        if doc['summary']:
            print(f"      Summary: {doc['summary'][:80]}...")
    if len(documents) > 10:
        print(f"  ... and {len(documents) - 10} more documents")
    
    print("\n" + "=" * 70)
    print("🤖 Running classification...")
    print("=" * 70 + "\n")
    
    # Execute classification
    result = agent.execute()
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if result.success:
        print(f"✅ Classification completed successfully!")
        print(f"   Documents processed: {result.documents_processed}")
        print(f"   Documents classified: {result.documents_classified}")
        print(f"   Output file: {result.output_file}")
        
        # Show classification summary
        print("\n📊 Classification Summary by Category:")
        print("-" * 50)
        
        # Group by category
        by_category = {}
        for cls in result.classifications:
            cat_id = cls.get('category_id', 20)
            if cat_id not in by_category:
                by_category[cat_id] = {
                    'name': cls.get('category_name', ''),
                    'english': cls.get('category_english', ''),
                    'docs': []
                }
            by_category[cat_id]['docs'].append(cls.get('file_name', ''))
        
        for cat_id in sorted(by_category.keys()):
            cat_info = by_category[cat_id]
            print(f"\n  Category {cat_id}: {cat_info['name']} ({cat_info['english']})")
            for doc in cat_info['docs']:
                print(f"    - {doc}")
        
        print("\n" + "-" * 50)
        print(f"\nFull results saved to: {result.output_file}")
    else:
        print(f"❌ Classification failed!")
        print(f"   Error: {result.error}")
    
    print("=" * 70 + "\n")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
