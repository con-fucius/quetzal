import uuid
import os
import time
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.collections.classes.config import Configure, DataType

class WeaviateError(Exception):
    """Custom exception for Weaviate errors."""
    pass

class VectorStore:
    """Integration with Weaviate vector database."""
    
    def __init__(self, api_key: Optional[str] = None, cloud_url: Optional[str] = None):
        """
        Initialize the Weaviate client.
        
        Args:
            api_key: Weaviate API key
            cloud_url: Weaviate Cloud URL
            
        Raises:
            WeaviateError: If client initialization fails
        """
        try:
            # Initialize the sentence transformer model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize Weaviate client with retry mechanism
            self.client = None
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries and self.client is None:
                try:
                    if cloud_url:
                        # Cloud connection
                        print(f"Attempting to connect to Weaviate cloud at {cloud_url} (attempt {retry_count + 1}/{max_retries})")
                        self.client = weaviate.connect_to_weaviate_cloud(
                            cluster_url=cloud_url,
                            auth_credentials=Auth.api_key(api_key),
                            additional_config=AdditionalConfig(
                                timeout=Timeout(init=60, query=60, insert=120)
                            ),
                            skip_init_checks=True  # Skip gRPC health checks to avoid connection issues
                        )
                        print(f"Connected to Weaviate Cloud at {cloud_url}")
                    else:
                        # Local connection (fallback)
                        print("No cloud URL provided, connecting to local Weaviate instance")
                        self.client = weaviate.connect_to_local(
                            skip_init_checks=True
                        )
                        print("Connected to local Weaviate instance")
                except Exception as e:
                    retry_count += 1
                    print(f"Connection attempt {retry_count} failed: {str(e)}")
                    
                    if cloud_url and retry_count == max_retries:
                        # If cloud connection failed after max retries, try local as fallback
                        print("Cloud connection failed, attempting local fallback connection")
                        try:
                            self.client = weaviate.connect_to_local(
                                skip_init_checks=True
                            )
                            print("Connected to local Weaviate instance as fallback")
                        except Exception as local_e:
                            print(f"Local fallback connection also failed: {str(local_e)}")
                            raise WeaviateError(f"Failed to connect to both cloud and local Weaviate instances")
                    
                    # Wait before retrying
                    if retry_count < max_retries and self.client is None:
                        time.sleep(2)  # 2 second delay between retries
            
            if self.client is None:
                raise WeaviateError("Failed to initialize Weaviate client after retries")
                
            # Create schema if it doesn't exist
            self._create_schema()
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            # RECOMMENDATION: Log full error `e` server-side. Raise generic error or sanitize `str(e)`.
            raise WeaviateError(f"Failed to initialize Weaviate client: {str(e)}") # Placeholder: Original code left
    
    def _create_schema(self):
        """Create the document schema if it doesn't exist."""
        try:
            # Check if collection exists
            try:
                # Try to get the collection by name
                collection = self.client.collections.get("Document")
                print("Document collection exists in schema.")
                return
            except Exception as e:
                print(f"Document collection doesn't exist. Creating it: {str(e)}")
                
                # Create the collection using Weaviate's builder pattern
                collection = self.client.collections.create(
                    name="Document",
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        {
                            "name": "content",
                            "data_type": [DataType.TEXT],
                            "description": "The document content"
                        },
                        {
                            "name": "source",
                            "data_type": [DataType.TEXT],
                            "description": "Source of the document (file path or URL)"
                        },
                        {
                            "name": "title",
                            "data_type": [DataType.TEXT],
                            "description": "Title of the document"
                        },
                        {
                            "name": "document_id",
                            "data_type": [DataType.TEXT],
                            "description": "Reference to external document ID"
                        },
                        {
                            "name": "folder_id",
                            "data_type": [DataType.TEXT],
                            "description": "Reference to folder ID"
                        }
                    ]
                )
                print("Document collection created successfully.")
                
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to create schema: {str(e)}") # Placeholder: Original code left
    
    def add_document(self, content: str, source: str, title: str, document_id: Optional[str] = None, folder_id: Optional[str] = None) -> List[str]:
        """
        Add a document to the vector store.
        
        Args:
            content: Document content
            source: Source of the document
            title: Title of the document
            document_id: Optional reference to external document ID
            folder_id: Optional reference to folder ID
            
        Returns:
            List of document IDs
            
        Raises:
            WeaviateError: If document addition fails
        """
        try:
            # Generate document ID
            vec_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self.model.encode(content).tolist()
            
            # Prepare document data
            # SECURITY NOTE: Sensitive data (potentially in `content`, `source`, `title`) is stored in Weaviate.
            # Ensure appropriate access controls are configured on the Weaviate instance itself
            # and that application-level authorization prevents unauthorized data access/modification.
            doc_data = {
                "content": content,
                "source": source,
                "title": title
            }
            
            # Add optional document ID reference if provided
            if document_id:
                doc_data["document_id"] = document_id
                
            # Add optional folder ID reference if provided
            if folder_id:
                doc_data["folder_id"] = folder_id
            
            # Add document to Weaviate
            collection = self.client.collections.get("Document")
            collection.data.insert(
                properties=doc_data,
                vector=embedding,
                uuid=vec_id
            )
            
            return [vec_id]
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to add document: {str(e)}") # Placeholder: Original code left
    
    def search(self, query: str, search_type: str = "hybrid", limit: int = 5, document_id: Optional[str] = None, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using various search strategies.
        
        Args:
            query: Search query
            search_type: Type of search to perform: "vector", "keyword", or "hybrid"
            limit: Maximum number of results to return
            document_id: Optional filter to search only within a specific document
            folder_id: Optional filter to search only within a specific folder
            
        Returns:
            List of relevant documents
            
        Raises:
            WeaviateError: If search fails
        """
        try:
            # Make sure Document collection exists
            try:
                collection = self.client.collections.get("Document")
            except Exception as e:
                print(f"Error accessing Document collection: {str(e)}")
                self._create_schema()
                collection = self.client.collections.get("Document")
            
            # Generate query embedding
            query_embedding = self.model.encode(query).tolist()
            
            # Set up optional document filtering
            where_filter = None
            if document_id:
                where_filter = {
                    "path": ["document_id"],
                    "operator": "Equal",
                    "valueText": document_id # SECURITY NOTE: Ensure `document_id` is validated if user-controlled to prevent filter injection.
                }
            elif folder_id:
                where_filter = {
                    "path": ["folder_id"],
                    "operator": "Equal",
                    "valueText": folder_id # SECURITY NOTE: Ensure `folder_id` is validated if user-controlled to prevent filter injection.
                }
                
            results = None
            documents = []
            
            # Execute appropriate search type
            if search_type == "vector":
                # Vector search for semantic similarity
                results = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=limit,
                    filters=where_filter
                )
            
            elif search_type == "keyword":
                # Keyword search for text matching
                results = collection.query.bm25(
                    query=query,
                    limit=limit,
                    filters=where_filter
                )
                
            elif search_type == "hybrid":
                # Hybrid search for combined semantic and keyword match
                # SECURITY NOTE: Ensure `query` is appropriately handled by the Weaviate client/server
                # to prevent potential query injection vulnerabilities in the keyword part of the search.
                results = collection.query.hybrid(
                    query=query,
                    vector=query_embedding,
                    alpha=0.5,  # Balance between vector (alpha) and keyword (1-alpha)
                    limit=limit,
                    filters=where_filter
                )
            
            else:
                raise WeaviateError(f"Invalid search type: {search_type}")
            
            # Format results
            if hasattr(results, 'objects'):
                for obj in results.objects:
                    doc = {
                        "content": obj.properties.get("content", ""),
                        "source": obj.properties.get("source", ""),
                        "title": obj.properties.get("title", ""),
                        "document_id": obj.properties.get("document_id", ""),
                        "folder_id": obj.properties.get("folder_id", "")
                    }
                    documents.append(doc)
            
            return documents
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to search documents: {str(e)}") # Placeholder: Original code left
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            doc_id: ID of the document to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            WeaviateError: If deletion fails
        """
        # SECURITY NOTE: Ensure calling code performs authorization checks before allowing deletion.
        try:
            collection = self.client.collections.get("Document")
            collection.data.delete(uuid=doc_id)
            return True
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to delete document: {str(e)}") # Placeholder: Original code left
    
    def delete_documents_by_document_id(self, document_id: str) -> bool:
        """
        Delete all vector entries associated with a specific document ID.
        
        Args:
            document_id: External document ID to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            WeaviateError: If deletion fails
        """
        # SECURITY NOTE: Ensure calling code performs authorization checks before allowing deletion.
        # Also ensure `document_id` is validated if user-controlled.
        try:
            collection = self.client.collections.get("Document")
            where_filter = {
                "path": ["document_id"],
                "operator": "Equal",
                "valueText": document_id
            }
            result = collection.data.delete_many(where=where_filter)
            return True
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to delete documents by document ID: {str(e)}") # Placeholder: Original code left
    
    def delete_all_documents(self) -> bool:
        """
        Delete all documents from the vector store.
        
        Returns:
            True if deletion was successful
            
        Raises:
            WeaviateError: If deletion fails
        """
        # SECURITY NOTE: Ensure calling code performs authorization checks before allowing deletion.
        # This is a destructive operation.
        try:
            collection = self.client.collections.get("Document")
            collection.data.delete_many()
            return True
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            raise WeaviateError(f"Failed to delete all documents: {str(e)}") # Placeholder: Original code left