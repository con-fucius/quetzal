"""
Test script for the enhanced SimpleDocProcessor and SimpleCrawler implementations.
"""

import os
import sys
from simple_doc_processor import SimpleDocProcessor
from simple_crawler import SimpleCrawler

def test_url_processing():
    """Test processing a URL with the crawler."""
    print("\n=== Testing URL Processing ===")
    
    url = "https://langfuse.com/docs/tracing"
    crawler = SimpleCrawler()
    
    print(f"Crawling URL: {url}")
    content, links = crawler.crawl(url)
    
    if content:
        print(f"Successfully extracted content ({len(content)} characters)")
        print("First 100 characters:")
        print(content[:100])
        print()
        
        print(f"Extracted {len(links)} links")
        for i, link in enumerate(links[:5]):  # Show the first 5 links
            print(f"{i+1}. {link}")
        
        if len(links) > 5:
            print(f"... and {len(links) - 5} more")
        
        return True
    else:
        print(f"Failed to extract content from URL: {url}")
        return False

def test_local_file_processing():
    """Test processing local files with the crawler."""
    print("\n=== Testing Local File Processing ===")
    
    # Find a markdown file in the local_docs folder
    docs_dir = os.path.join("local docs")
    if not os.path.exists(docs_dir):
        print(f"Error: Local docs directory not found at {docs_dir}")
        return False
    
    # Find a markdown file in the local_docs folder
    md_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
    if not md_files:
        print(f"Error: No markdown files found in {docs_dir}")
        return False
    
    # Process a random markdown file
    test_file = os.path.join(docs_dir, md_files[0])
    print(f"Testing with file: {test_file}")
    
    crawler = SimpleCrawler()
    content, links = crawler.crawl(test_file)
    
    if content:
        print(f"Successfully extracted content ({len(content)} characters)")
        print("First 100 characters:")
        print(content[:100])
        print()
        
        print(f"Extracted {len(links)} links")
        for i, link in enumerate(links[:5]):  # Show the first 5 links
            print(f"{i+1}. {link}")
        
        if len(links) > 5:
            print(f"... and {len(links) - 5} more")
        
        return True
    else:
        print(f"Failed to extract content from file: {test_file}")
        return False

def main():
    print("Starting enhanced crawler tests...")
    
    url_test_result = test_url_processing()
    file_test_result = test_local_file_processing()
    
    print("\n=== Test Results ===")
    print(f"URL Processing: {'PASS' if url_test_result else 'FAIL'}")
    print(f"File Processing: {'PASS' if file_test_result else 'FAIL'}")
    
    overall_result = url_test_result and file_test_result
    print(f"\nOverall Test Result: {'SUCCESS' if overall_result else 'FAILURE'}")
    
    return overall_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 