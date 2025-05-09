import os
import glob
from typing import Dict, Any, List, Optional
from simple_doc_processor import SimpleDocProcessor
from simple_crawler import SimpleCrawler
from google_llm import GoogleLLM, GoogleAPIError
from vector_store import VectorStore, WeaviateError
from urllib.parse import urlparse

class ResearchAssistantError(Exception):
    """Custom exception for Research Assistant errors."""
    pass

class ResearchAssistant:
    """Smart Research Assistant with RAG capabilities."""
    
    def __init__(self, google_api_key: Optional[str] = None, 
                 weaviate_api_key: Optional[str] = None, 
                 weaviate_url: Optional[str] = None):
        """
        Initialize the Research Assistant.
        
        Args:
            google_api_key: Google AI Studio API key
            weaviate_api_key: Weaviate API key
            weaviate_url: Weaviate Cloud URL
            
        Raises:
            ResearchAssistantError: If initialization fails
        """
        try:
            self.doc_processor = SimpleDocProcessor()
            self.crawler = SimpleCrawler(
                respect_robots_txt=True,
                crawl_delay=1.0,
                max_pages=100,
                max_depth=3
            )
            
            # Initialize Google LLM
            self.llm = GoogleLLM(api_key=google_api_key or os.environ.get("GOOGLE_API_KEY"))
            
            # Initialize Vector Store
            self.vector_store = VectorStore(
                api_key=weaviate_api_key or os.environ.get("WEAVIATE_API_KEY"),
                cloud_url=weaviate_url or os.environ.get("WEAVIATE_URL")
            )
        except GoogleAPIError as e:
            raise ResearchAssistantError(f"Failed to initialize Google LLM: {str(e)}")
        except WeaviateError as e:
            raise ResearchAssistantError(f"Failed to initialize Vector Store: {str(e)}")
        except Exception as e:
            raise ResearchAssistantError(f"Failed to initialize Research Assistant: {str(e)}")
    
    def process_document(self, file_path_or_url: str) -> Optional[str]:
        """
        Process a single document from file or URL.
        
        Args:
            file_path_or_url: Path to file or URL to process
            
        Returns:
            Processed content or None if processing fails
            
        Raises:
            ResearchAssistantError: If document processing fails
        """
        try:
            # SECURITY WARNING: `file_path_or_url` is passed directly to `self.doc_processor` methods.
            # If this input originates from an untrusted source (e.g., user web request), it MUST be
            # validated *before* calling this method to prevent LFI (for file paths) and SSRF (for URLs).
            # The validation should happen in the calling code (e.g., app_web.py).
            print(f"Processing: {file_path_or_url}")
            
            # Extract content based on source type
            if file_path_or_url.startswith(('http://', 'https://')):
                # SECURITY NOTE: Relies on `SimpleDocProcessor.process_url` for fetching and processing.
                # Ensure `SimpleDocProcessor.process_url` implements SSRF protection.
                content = self.doc_processor.process_url(file_path_or_url)
            else:
                # SECURITY NOTE: Relies on `SimpleDocProcessor` file methods for processing.
                # Ensure `SimpleDocProcessor` methods implement LFI protection (or path confinement).
                if file_path_or_url.endswith('.pdf'):
                    content = self.doc_processor.process_pdf_file(file_path_or_url)
                elif file_path_or_url.endswith('.md'):
                    content = self.doc_processor.process_markdown_file(file_path_or_url)
                elif file_path_or_url.endswith('.txt'):
                    content = self.doc_processor.process_text_file(file_path_or_url)
                else:
                    raise ResearchAssistantError(f"Unsupported file type: {file_path_or_url}")
            
            if not content:
                raise ResearchAssistantError(f"Failed to extract content from: {file_path_or_url}")
            
            return content
        except Exception as e:
            raise ResearchAssistantError(f"Error processing document: {str(e)}")
    
    def process_and_store_document(self, file_path_or_url: str, document_id: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a document and store it in the vector database.
        
        Args:
            file_path_or_url: Path to file or URL to process
            document_id: Optional external document ID for reference
            folder_id: Optional folder ID for organization
            
        Returns:
            Dictionary containing processing results
            
        Raises:
            ResearchAssistantError: If processing or storage fails
        """
        try:
            # Process the document
            content = self.process_document(file_path_or_url)
            if not content:
                return {"success": False, "error": "Failed to extract content"}
            
            # Extract title
            if file_path_or_url.startswith(('http://', 'https://')):
                parts = file_path_or_url.split('/')
                title = parts[-1] if parts[-1] else parts[-2]
            else:
                filename = os.path.basename(file_path_or_url)
                title = os.path.splitext(filename)[0]
            
            # Store in vector database
            doc_ids = self.vector_store.add_document(
                content=content,
                source=file_path_or_url,
                title=title,
                document_id=document_id,
                folder_id=folder_id
            )
            
            return {
                "success": True,
                "document_ids": doc_ids,
                "title": title,
                "characters_processed": len(content),
                "document_id": document_id,
                "folder_id": folder_id
            }
        except WeaviateError as e:
            return {
                "success": False,
                "error": f"Failed to store document: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_multiple_documents(self, file_paths_or_urls: List[str], document_ids: Optional[List[str]] = None, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple documents and store them in the vector database.
        
        Args:
            file_paths_or_urls: List of file paths or URLs to process
            document_ids: Optional list of document IDs
            folder_id: Optional folder ID for organization
            
        Returns:
            List of processing results for each document
        """
        results = []
        for i, path_or_url in enumerate(file_paths_or_urls):
            doc_id = document_ids[i] if document_ids and i < len(document_ids) else None
            result = self.process_and_store_document(path_or_url, doc_id, folder_id)
            results.append({"source": path_or_url, **result})
        return results
    
    def answer_query(self, query: str, search_type: str = "hybrid", context_limit: int = 5, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a query using RAG with enhanced retrieval.
        
        Args:
            query: User's question
            search_type: Type of search to use (vector, keyword, hybrid)
            context_limit: Maximum number of relevant documents to use
            folder_id: Optional folder ID to constrain the search
            
        Returns:
            Dictionary containing answer and sources
            
        Raises:
            ResearchAssistantError: If query processing fails
        """
        try:
            # Generate improved search query with query expansion
            expanded_query = self._expand_query(query)
            
            # Search for relevant documents
            print(f"Searching for documents relevant to query using {search_type} search")
            relevant_docs = self.vector_store.search(expanded_query, search_type=search_type, limit=context_limit)
            
            if not relevant_docs:
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "sources": []
                }
            
            # Combine contents from relevant documents to create context
            print(f"Found {len(relevant_docs)} relevant document chunks")
            
            # Create organized context with sources
            formatted_context = ""
            sources = []
            
            for i, doc in enumerate(relevant_docs):
                # Add formatted context
                formatted_context += f"\n[Document {i+1}]: {doc['content']}\n"
                
                # Track sources without duplicates
                source_info = {
                    "title": doc.get("title", "Untitled"), 
                    "source": doc["source"]
                }
                if source_info not in sources:
                    sources.append(source_info)
            
            # Query the LLM with the context
            print("Generating answer with enhanced context...")
            # SECURITY WARNING: The `query` (user question) and `formatted_context` (retrieved content)
            # are combined into the prompt sent to the LLM. This is susceptible to Prompt Injection if
            # the user query or the indexed document content contains malicious instructions.
            # RECOMMENDATION: Implement robust prompt engineering. Clearly delimit user input vs. instructions.
            # Consider input/output filtering or using more structured LLM API calls if available.
            system_prompt = """You are a research assistant that provides accurate,
            factual answers based solely on the provided documents.
            Always attribute information to the specific document numbers [Document X] in your answer.
            If the provided documents don't contain relevant information to answer the question,
            say 'I don't have enough information to answer this question completely.'
            Your response should be comprehensive, well-organized, and directly address the query."""
            
            user_prompt = f"""Question: {query}
            
            Context from documents:
            {formatted_context}
            
            Answer the question using only information from these documents.
            Cite document numbers using [Document X] format."""
            
            try:
                # SECURITY NOTE: Relies on `GoogleLLM.process_content` for actual API call.
                # Ensure that method handles API keys securely and potentially sanitizes error messages.
                answer = self.llm.process_content(
                    content="",
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
            except GoogleAPIError as e:
                return {
                    "answer": f"Error generating answer: {str(e)}",
                    "sources": sources
                }
            
            # Verify answer relevance
            if self._is_answer_lacking_info(answer):
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "sources": sources
                }
            
            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            raise ResearchAssistantError(f"Error processing query: {str(e)}")
    
    def _expand_query(self, query: str) -> str:
        """
        Expand the query to improve retrieval using LLM.
        
        Args:
            query: Original user query
            
        Returns:
            Expanded query for better search
        """
        try:
            # Simple keywords-based expansion for now
            # To keep latency low, we'll use a simple approach instead of calling LLM
            # This can be enhanced with actual LLM calls in the future
            
            # Remove question words and common filler words
            expansion_stopwords = ["what", "when", "where", "who", "how", "why", "is", "are", "the", "a", "an", 
                                  "of", "in", "on", "and", "or", "to", "from", "with"]
            
            query_words = query.lower().split()
            keywords = [word for word in query_words if word not in expansion_stopwords and len(word) > 2]
            
            # Combine original query with extracted keywords
            expanded_query = f"{query} {' '.join(keywords)}"
            
            return expanded_query
        except Exception:
            # Fall back to original query if expansion fails
            return query
    
    def _is_answer_lacking_info(self, answer: str) -> bool:
        """
        Check if the generated answer indicates lack of information.
        
        Args:
            answer: Generated answer text
            
        Returns:
            True if the answer indicates insufficient information
        """
        # Look for phrases indicating lack of information
        lack_info_phrases = [
            "don't have enough information", 
            "insufficient information",
            "not enough context",
            "cannot answer",
            "unable to answer", 
            "not provided in the documents",
            "isn't mentioned in the documents"
        ]
        
        lower_answer = answer.lower()
        for phrase in lack_info_phrases:
            if phrase in lower_answer:
                return True
                
        return False
    
    def store_document_content(self, content: str, source: str, title: str = None, document_id: Optional[str] = None, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process and store document content directly in the vector store.
        
        Args:
            content: The text content to store
            source: Source information (URL or file path)
            title: Optional title for the document
            document_id: Optional document ID for reference
            folder_id: Optional folder ID for organization
            
        Returns:
            Dictionary with processing result
        """
        try:
            if not content:
                return {"success": False, "error": "No content provided"}
            
            # Use source as title if not provided
            if not title:
                if source.startswith(('http://', 'https://')):
                    parsed_url = urlparse(source)
                    title = f"Content from {parsed_url.netloc}"
                else:
                    title = os.path.basename(source)
            
            # Store in vector database
            doc_ids = self.vector_store.add_document(
                content=content, 
                source=source, 
                title=title,
                document_id=document_id,
                folder_id=folder_id
            )
            
            return {
                "success": True,
                "document_ids": doc_ids,
                "title": title,
                "characters_processed": len(content),
                "document_id": document_id,
                "folder_id": folder_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)} 