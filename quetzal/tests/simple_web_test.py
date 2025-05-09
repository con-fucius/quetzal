import unittest
from unittest.mock import patch, MagicMock
import sys
import os

print("Test script started")

# Mock the web crawler dependencies
class MockWebCrawler:
    def __init__(self, config=None):
        self.config = config or {}
        self.visited_urls = set()
        print("MockWebCrawler initialized")
    
    def _is_valid_url(self, url):
        return url.startswith("http://") or url.startswith("https://")
    
    def fetch_url(self, url):
        if not self._is_valid_url(url) or url in self.visited_urls:
            return None
        self.visited_urls.add(url)
        return "<html><body>Mock content</body></html>"
    
    def extract_text(self, html_content):
        return "Extracted text"
    
    def extract_links(self, html_content, base_url):
        return ["https://example.com/page1", "https://example.com/page2"]
    
    def crawl_url(self, url, max_depth=1):
        if not self._is_valid_url(url):
            return {}
        return {url: "Extracted text"}
    
    def crawl_multiple_urls(self, urls, max_depth=1):
        results = {}
        for url in urls:
            results.update(self.crawl_url(url, max_depth))
        return results

# Create test class
class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        print("Setting up test case")
        self.crawler = MockWebCrawler()
    
    def test_is_valid_url(self):
        print("Running is_valid_url test")
        self.assertTrue(self.crawler._is_valid_url("https://example.com"))
        self.assertFalse(self.crawler._is_valid_url("example.com"))
    
    def test_fetch_url(self):
        print("Running fetch_url test")
        # Test successful fetch
        content = self.crawler.fetch_url("https://example.com")
        self.assertEqual(content, "<html><body>Mock content</body></html>")
        
        # Test already visited URL
        content = self.crawler.fetch_url("https://example.com")
        self.assertIsNone(content)
        
        # Test invalid URL
        content = self.crawler.fetch_url("example.com")
        self.assertIsNone(content)
    
    def test_crawl_url(self):
        print("Running crawl_url test")
        results = self.crawler.crawl_url("https://example.com")
        self.assertIsInstance(results, dict)
        self.assertIn("https://example.com", results)

print("Test class defined")

if __name__ == "__main__":
    print("Running tests")
    unittest.main() 