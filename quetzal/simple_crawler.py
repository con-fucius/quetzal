"""
Enhanced web crawler implementation for the Quetzal Research Assistant.
Supports sitemap crawling, multi-level crawling, and respects robots.txt.
"""

import logging
import time
import re
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import deque
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.robotparser import RobotFileParser
from simple_doc_processor import SimpleDocProcessor

class SimpleCrawler:
    """
    Enhanced web crawler with support for sitemaps and multi-level crawling.
    """
    
    def __init__(self, respect_robots_txt: bool = True, 
                 crawl_delay: float = 1.0, 
                 max_pages: int = 100, 
                 max_depth: int = 3):
        """
        Initialize the crawler with configuration settings.
        
        Args:
            respect_robots_txt: Whether to respect robots.txt rules
            crawl_delay: Time to wait between requests (in seconds)
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum crawl depth
        """
        self.visited_urls = set()
        self.processor = SimpleDocProcessor()
        self.respect_robots_txt = respect_robots_txt
        self.crawl_delay = crawl_delay
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.robot_parsers = {}  # Cache for robot parsers
        self.last_request_time = 0
        
        # Configure logging
        self.logger = logging.getLogger("SimpleCrawler")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            self.logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def _respect_rate_limits(self):
        """Wait if necessary to respect rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.crawl_delay:
            time.sleep(self.crawl_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_robot_parser(self, base_url: str) -> RobotFileParser:
        """Get or create a robot parser for the given base URL."""
        if not self.respect_robots_txt:
            return None
            
        netloc = urlparse(base_url).netloc
        if netloc in self.robot_parsers:
            return self.robot_parsers[netloc]
        
        # Create new robot parser
        robot_parser = RobotFileParser()
        robots_url = urljoin(base_url, "/robots.txt")
        
        try:
            self._respect_rate_limits()
            robot_parser.set_url(robots_url)
            robot_parser.read()
            self.robot_parsers[netloc] = robot_parser
            return robot_parser
        except Exception as e:
            self.logger.warning(f"Failed to read robots.txt at {robots_url}: {e}")
            return None
    
    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.respect_robots_txt:
            return True
            
        try:
            robot_parser = self._get_robot_parser(url)
            if robot_parser:
                return robot_parser.can_fetch("*", url)
            return True
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True
    
    def extract_text(self, html_content: str) -> str:
        """Extract text content from HTML."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
                script_or_style.decompose()
            
            # Get text and remove extra whitespace
            text = soup.get_text(separator=" ")
            text = " ".join(text.split())
            
            self.logger.info(f"Extracted {len(text)} characters of text content")
            return text
        except Exception as e:
            self.logger.error(f"Error extracting text from HTML: {e}")
            return ""
    
    def extract_links(self, html_content: str, base_url: str = "", 
                     url_patterns: List[str] = None) -> List[str]:
        """
        Extract links from HTML content.
        
        Args:
            html_content: The HTML content to extract links from
            base_url: The base URL for resolving relative links
            url_patterns: List of regex patterns to match URLs against
            
        Returns:
            List of extracted links
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            links = []
            
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                # If base_url is provided, resolve relative URLs
                if base_url:
                    full_url = urljoin(base_url, href)
                    
                    # Check if the URL matches the patterns (if provided)
                    if url_patterns:
                        if not any(re.search(pattern, full_url) for pattern in url_patterns):
                            continue
                    
                    # Only include links to the same domain by default
                    base_domain = urlparse(base_url).netloc
                    url_domain = urlparse(full_url).netloc
                    
                    # Accept the URL if it's from the same domain or subdomain
                    if url_domain == base_domain or url_domain.endswith(f".{base_domain}"):
                        if self._is_valid_url(full_url) and self._can_fetch(full_url):
                            links.append(full_url)
                elif self._is_valid_url(href) and self._can_fetch(href):
                    # If no base_url, just collect all valid URLs
                    links.append(href)
            
            self.logger.info(f"Extracted {len(links)} links")
            return links
        except Exception as e:
            self.logger.error(f"Error extracting links from HTML: {e}")
            return []
    
    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Parse a sitemap XML file and extract URLs.
        
        Args:
            sitemap_url: URL of the sitemap to parse
            
        Returns:
            List of URLs from the sitemap
        """
        try:
            # SECURITY WARNING: Fetching arbitrary sitemap URLs can lead to SSRF if `sitemap_url`
            # is influenced by user input without validation against private IPs.
            # RECOMMENDATION: Validate `sitemap_url` similar to other external URLs if it can be untrusted.
            self.logger.info(f"Parsing sitemap: {sitemap_url}")
            self._respect_rate_limits()
            # SECURITY NOTE: Consider adding User-Agent header.
            response = requests.get(sitemap_url, timeout=30)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch sitemap {sitemap_url}: HTTP {response.status_code}")
                return []
                
            # Check if it's a sitemap index (contains other sitemaps)
            if "<sitemapindex" in response.text:
                urls = []
                # SECURITY WARNING: Parsing XML from external sources can be vulnerable to XXE and DoS (e.g., Billion Laughs).
                # `xml.etree.ElementTree` is generally safer against XXE by default in modern Python, but ensure external entity loading is disabled.
                # RECOMMENDATION: Consider adding limits to response size before parsing to prevent DoS. Ensure parser is securely configured if using libraries like lxml.
                root = ET.fromstring(response.text)
                
                # Extract sitemap URLs from the index
                for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                    loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc is not None and loc.text:
                        # Recursively parse each sitemap
                        child_urls = self.parse_sitemap(loc.text)
                        urls.extend(child_urls)
                
                return urls
            else:
                # Process regular sitemap
                urls = []
                # SECURITY WARNING: XML parsing risks (XXE, DoS) apply here too. See above.
                root = ET.fromstring(response.text)
                
                # Extract URLs
                for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc is not None and loc.text:
                        urls.append(loc.text)
                
                self.logger.info(f"Found {len(urls)} URLs in sitemap")
                return urls
        except ET.ParseError:
            # Some sitemaps might be in a different format or compressed
            self.logger.warning(f"Failed to parse XML from sitemap {sitemap_url}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []
    
    def crawl(self, file_path_or_url: str) -> Tuple[Optional[str], List[str]]:
        """
        Crawl a document or URL to extract text and links.
        
        Args:
            file_path_or_url: Path to a local file or a URL
            
        Returns:
            Tuple of (extracted text, list of links)
        """
        try:
            # Check if it's a URL or a file
            if file_path_or_url.startswith('http://') or file_path_or_url.startswith('https://'):
                # SECURITY WARNING: Potential SSRF risk if `file_path_or_url` is untrusted.
                # The actual request happens in `self.processor.get_html_from_url` and `self.processor.process_url`.
                # Validation should occur there or before calling this method.
                # Get HTML content from URL
                self._respect_rate_limits()
                html_content = self.processor.get_html_from_url(file_path_or_url)
                if not html_content:
                    return None, []
                    
                # Extract text from the URL
                content = self.processor.process_url(file_path_or_url)
                
                # Extract links using the base URL
                links = self.extract_links(html_content, file_path_or_url)
                
                return content, links
            elif file_path_or_url.endswith('.md'):
                # Get HTML content from markdown
                html_content = self.processor.get_html_from_markdown(file_path_or_url)
                if not html_content:
                    return None, []
                
                # Extract text from markdown
                content = self.processor.process_markdown_file(file_path_or_url)
                
                # Extract links (use an empty base_url for local files)
                links = self.extract_links(html_content)
                
                return content, links
            elif file_path_or_url.endswith('.txt'):
                # For text files, just get the content, no links
                content = self.processor.process_text_file(file_path_or_url)
                return content, []
            elif file_path_or_url.endswith('.pdf'):
                # For PDF files, just get the content, no links
                content = self.processor.process_pdf_file(file_path_or_url)
                return content, []
            else:
                self.logger.warning(f"Unsupported file type or URL: {file_path_or_url}")
                return None, []
        except Exception as e:
            self.logger.error(f"Error crawling {file_path_or_url}: {e}")
            return None, [] 
    
    def crawl_with_depth(self, start_url: str, 
                         max_depth: int = None, 
                         max_pages: int = None,
                         url_patterns: List[str] = None) -> Dict[str, str]:
        """
        Crawl a website starting from a URL with depth limit.
        
        Args:
            start_url: Starting URL for crawling
            max_depth: Maximum crawl depth (overrides instance value if provided)
            max_pages: Maximum number of pages to crawl (overrides instance value if provided)
            url_patterns: List of regex patterns to match URLs against
            
        Returns:
            Dictionary mapping URLs to their extracted content
        """
        if not max_depth:
            max_depth = self.max_depth
            
        if not max_pages:
            max_pages = self.max_pages
        
        # Initialize crawl queue and visited set
        queue = deque([(start_url, 0)])  # (url, depth)
        visited = set()
        results = {}
        
        # Check for sitemap.xml first
        sitemap_url = urljoin(start_url, "/sitemap.xml")
        try:
            # SECURITY WARNING: Potential SSRF risk if `sitemap_url` is derived from untrusted input.
            self._respect_rate_limits()
            # SECURITY NOTE: Consider adding User-Agent header.
            response = requests.head(sitemap_url, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"Found sitemap at {sitemap_url}")
                sitemap_urls = self.parse_sitemap(sitemap_url) # Parsing happens here, XML risks apply.
                
                # Add sitemap URLs to the queue
                for url in sitemap_urls:
                    if url not in visited:
                        queue.append((url, 0))
        except Exception as e:
            self.logger.warning(f"Failed to check sitemap at {sitemap_url}: {e}")
        
        # Start crawling
        page_count = 0
        while queue and page_count < max_pages:
            url, depth = queue.popleft()
            
            # Skip if already visited or too deep
            if url in visited or depth > max_depth:
                continue
                
            visited.add(url)
            
            # Process URL
            self.logger.info(f"Crawling {url} (depth {depth})")
            content, links = self.crawl(url)
            
            if content:
                results[url] = content
                page_count += 1
                
                self.logger.info(f"Processed page {page_count}/{max_pages}")
                
                # Stop if we've reached the maximum pages
                if page_count >= max_pages:
                    self.logger.info(f"Reached maximum page count ({max_pages})")
                    break
                
                # Add links to queue for next depth level
                if depth < max_depth:
                    for link in links:
                        # Apply URL pattern filtering
                        if url_patterns:
                            if not any(re.search(pattern, link) for pattern in url_patterns):
                                continue
                                
                        if link not in visited:
                            queue.append((link, depth + 1))
            
        self.logger.info(f"Crawling completed: {page_count} pages processed")
        return results
    
    def check_sitemap(self, base_url: str) -> bool:
        """
        Check if a website has a sitemap.xml file.
        
        Args:
            base_url: Base URL of the website
            
        Returns:
            True if sitemap.xml exists, False otherwise
        """
        sitemap_url = urljoin(base_url, "/sitemap.xml")
        try:
            # SECURITY WARNING: Potential SSRF risk if `sitemap_url` is derived from untrusted input.
            self._respect_rate_limits()
            # SECURITY NOTE: Consider adding User-Agent header.
            response = requests.head(sitemap_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Error checking sitemap at {sitemap_url}: {e}")
            return False 