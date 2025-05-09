"""
Simple document processor for testing the Smart Research Assistant.
"""

import os
import markdown2
import requests
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup

class SimpleDocProcessor:
    """
    A simple document processor that extracts text from markdown files, text files, PDF files, and URLs.
    """
    
    def process_text_file(self, file_path):
        """Process a .txt file and return its content."""
        # SECURITY WARNING: This method takes a file path. If `file_path` originates from untrusted user input
        # without prior validation and confinement, this could lead to Local File Inclusion (LFI).
        # RECOMMENDATION: Ensure calling code validates `file_path` against a safe base directory.
        # Example check (conceptual, place in calling code or early here):
        # SAFE_BASE = "/path/to/allowed/directory"
        # abs_path = os.path.abspath(file_path)
        # if not abs_path.startswith(os.path.abspath(SAFE_BASE)):
        #     raise ValueError("Attempt to access file outside allowed directory.")
        
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            print(f"Successfully processed text file: {file_path}")
            return content
        except Exception as e:
            print(f"Error processing text file {file_path}: {e}")
            return None
    
    def process_markdown_file(self, file_path):
        """Process a markdown file and return its content."""
        # SECURITY WARNING: Potential LFI risk if `file_path` is untrusted (see process_text_file).
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                markdown_content = file.read()
            
            # Convert markdown to HTML and then extract text
            html_content = markdown2.markdown(markdown_content)
            
            # SECURITY WARNING: Rudimentary HTML tag stripping using replace() is insecure and easily bypassed.
            # If the output text is ever used in an HTML context, this could lead to XSS.
            # RECOMMENDATION: Use a robust HTML parsing/stripping library like BeautifulSoup.
            # Example:
            # from bs4 import BeautifulSoup
            # soup = BeautifulSoup(html_content, "html.parser")
            # text_content = soup.get_text(separator="\n", strip=True)

            # Placeholder: Original insecure code left for now
            # Simple cleaning of HTML tags
            text_content = html_content.replace("<br>", "\n").replace("<p>", "\n").replace("</p>", "\n")
            for tag in ["<h1>", "</h1>", "<h2>", "</h2>", "<h3>", "</h3>", "<h4>", "</h4>",
                        "<h5>", "</h5>", "<h6>", "</h6>", "<ul>", "</ul>", "<li>", "</li>",
                        "<ol>", "</ol>", "<code>", "</code>", "<pre>", "</pre>"]:
                text_content = text_content.replace(tag, "\n")
            
            # Clean up extra whitespace
            text_content = " ".join(text_content.split())
            
            print(f"Successfully processed markdown file: {file_path}")
            return text_content
        except Exception as e:
            print(f"Error processing markdown file {file_path}: {e}")
            return None
    
    def process_pdf_file(self, file_path):
        """Process a .pdf file and return its content."""
        # SECURITY WARNING: Potential LFI risk if `file_path` is untrusted (see process_text_file).
        # Also, PDF parsing libraries can be vulnerable to DoS with malformed files.
        # RECOMMENDATION: Keep PyPDF2 updated. Consider resource limits/timeouts if processing untrusted PDFs.
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                
                # Clean up extra whitespace
                text = " ".join(text.split())
                
                print(f"Successfully processed PDF file: {file_path}")
                return text
        except Exception as e:
            print(f"Error processing PDF file {file_path}: {e}")
            return None
    
    def process_url(self, url):
        """Fetch and process content from a URL."""
        # SECURITY WARNING: This method fetches content from an arbitrary URL. If `url` originates
        # from untrusted user input without prior validation, this could lead to Server-Side Request Forgery (SSRF).
        # RECOMMENDATION: Ensure calling code validates `url` against private IP ranges and allowed schemes (HTTP/HTTPS).
        # Example check (conceptual, place in calling code or early here):
        # import socket
        # from urllib.parse import urlparse
        # parsed = urlparse(url)
        # if parsed.scheme not in ['http', 'https']: raise ValueError("Invalid scheme")
        # try:
        #     ip = socket.gethostbyname(parsed.netloc)
        #     if ip_is_private(ip): # Function to check against private ranges
        #         raise ValueError("Access to private IP range denied.")
        # except socket.gaierror: raise ValueError("Could not resolve hostname")
        
        try:
            # SECURITY NOTE: Consider adding a User-Agent header for politeness.
            # headers = {'User-Agent': 'QuetzalBot/1.0'}
            # response = requests.get(url, headers=headers, timeout=30) # Add timeout
            response = requests.get(url) # Placeholder: Original code left
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
                    script_or_style.decompose()
                
                # Get text and remove extra whitespace
                text = soup.get_text(separator=" ")
                text = " ".join(text.split())
                
                print(f"Successfully processed URL: {url}")
                return text
            else:
                print(f"Failed to fetch URL: {url} with status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return None
    
    def get_html_from_markdown(self, file_path):
        """Get HTML content from a markdown file for link extraction."""
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                markdown_content = file.read()
            
            # Convert markdown to HTML
            html_content = markdown2.markdown(markdown_content)
            return f"<html><body>{html_content}</body></html>"
        except Exception as e:
            print(f"Error processing markdown file {file_path}: {e}")
            return None
    
    def get_html_from_url(self, url):
        """Get HTML content from a URL for link extraction."""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch URL: {url} with status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None
    
    def process_document(self, file_path_or_url):
        """Process a document based on its type (file or URL)."""
        if file_path_or_url.startswith('http://') or file_path_or_url.startswith('https://'):
            return self.process_url(file_path_or_url)
        elif file_path_or_url.endswith('.pdf'):
            return self.process_pdf_file(file_path_or_url)
        elif file_path_or_url.endswith('.md'):
            return self.process_markdown_file(file_path_or_url)
        elif file_path_or_url.endswith('.txt'):
            return self.process_text_file(file_path_or_url)
        else:
            print(f"Unsupported file type or URL: {file_path_or_url}")
            return None 