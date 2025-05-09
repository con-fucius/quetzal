import os
import google.generativeai as genai
from typing import Optional, Dict, Any

class GoogleAPIError(Exception):
    """Custom exception for Google AI Studio API errors."""
    pass

class GoogleLLM:
    """Integration with Google AI Studio's Gemini model for processing text content."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Google AI Studio client."""
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise GoogleAPIError(
                "Google AI Studio API key is required. Set it in the .env file or pass as a parameter.\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def process_content(self, content: str = "", prompt: Optional[str] = None,
                       system_prompt: Optional[str] = None, max_tokens: int = 2000) -> str:
        """Process content with the Gemini model."""
        try:
            # SECURITY WARNING: `prompt` and `content` (often containing user input or retrieved data)
            # are directly concatenated into `full_prompt`. This is vulnerable to Prompt Injection.
            # RECOMMENDATION: Use structured API calls if available (e.g., roles for system/user messages).
            # Clearly delimit user input within the prompt. Consider input/output filtering.
            # Prepare the prompt
            if prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            elif content:
                full_prompt = f"{system_prompt}\n\nPlease analyze and summarize the following content: {content}" if system_prompt else f"Please analyze and summarize the following content: {content}"
            else:
                raise ValueError("Either prompt or content must be provided")
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            # SECURITY WARNING: Propagating raw exception messages (`str(e)`) can leak sensitive details.
            # RECOMMENDATION: Log the full error `e` server-side. Raise a more generic error or sanitize `str(e)`
            # if this `GoogleAPIError` might be shown to users or less trusted logs.
            raise GoogleAPIError(f"Failed to process content: {str(e)}") # Placeholder: Original code left
            
    def query(self, query: str, context: str) -> str:
        """Query the Gemini model with context."""
        prompt = f"Based on the following information:\n\n{context}\n\nPlease answer: {query}"
        system_prompt = """You are a research assistant that provides accurate, factual answers based solely on the provided context.
        If the provided context doesn't contain relevant information to answer the question,
        say 'I don't have enough information to answer this question.'"""
        
        return self.process_content(content="", prompt=prompt, system_prompt=system_prompt) 