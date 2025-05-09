import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Print diagnostic info
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Working directory:", os.getcwd())

# Define a simple test case
class WebCrawlerTest(unittest.TestCase):
    def setUp(self):
        print("Setting up test case")
    
    def test_simple(self):
        print("Running simple test")
        self.assertEqual(1, 1)
        
    @patch('requests.get')
    def test_mock_request(self, mock_get):
        print("Running mock request test")
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        # Just testing the mock, not actual code
        import requests
        response = requests.get("https://example.com")
        self.assertEqual(response.text, "<html><body>Test content</body></html>")

if __name__ == "__main__":
    print("Starting tests...")
    unittest.main() 