"""
Final simplified test script to verify web crawler functionality.
"""

import os
import sys
from simple_doc_processor import SimpleDocProcessor
from simple_crawler import SimpleCrawler

def main():
    print("Starting simplified document processing and crawling test...")
    
    # Create processors
    doc_processor = SimpleDocProcessor()
    crawler = SimpleCrawler()
    
    # Test document path
    test_doc_path = os.path.join("tests", "test_document.md")
    
    # Verify document exists
    if not os.path.exists(test_doc_path):
        print(f"Error: Test document not found at {test_doc_path}")
        return False
    
    print(f"Processing document: {test_doc_path}")
    
    # Get HTML content from the document for web crawler testing
    html_content = doc_processor.get_html_from_markdown(test_doc_path)
    if not html_content:
        print("Error: Failed to process document")
        return False
    
    # Process the document text
    content = doc_processor.process_markdown_file(test_doc_path)
    if not content:
        print("Error: Failed to extract text from document")
        return False
    
    print(f"Successfully processed document ({len(content)} characters)")
    print("First 100 characters:")
    print(content[:100])
    
    # Test web crawler
    print("\nTesting web crawler with document content...")
    
    # Test extract_text
    extracted_text = crawler.extract_text(html_content)
    if not extracted_text:
        print("Error: Failed to extract text from HTML")
        return False
    
    print(f"Successfully extracted text ({len(extracted_text)} characters)")
    print("First 100 characters of extracted text:")
    print(extracted_text[:100])
    
    # Test extract_links (this should find the URLs in the markdown document)
    base_url = "https://openai.github.io"
    links = crawler.extract_links(html_content, base_url)
    
    print(f"\nExtracted {len(links)} links:")
    for i, link in enumerate(links[:10]):  # Show up to 10 links
        print(f"{i+1}. {link}")
    
    if len(links) > 10:
        print(f"... and {len(links) - 10} more")
    
    return len(links) > 0

if __name__ == "__main__":
    success = main()
    print("\nTest completed.")
    print(f"Result: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1) 