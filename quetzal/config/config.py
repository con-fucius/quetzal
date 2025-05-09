"""
Configuration file for the Smart Research Assistant.
This file contains all configurable parameters for the application.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
VECTORS_DIR = os.path.join(DATA_DIR, "vectors")

# Web crawling settings
WEB_CRAWLER_CONFIG = {
    "user_agent": "SmartResearchAssistant/1.0",
    "timeout": 30,  # seconds
    "max_retries": 3,
    "retry_delay": 5,  # seconds
    "respect_robots_txt": True,
    "max_pages_per_site": 100,
}

# Document processing settings
DOCUMENT_PROCESSOR_CONFIG = {
    "chunk_size": 1000,  # characters
    "chunk_overlap": 200,  # characters
    "supported_file_types": [".txt", ".md", ".pdf"],
}

# LLM Integration settings
LLM_CONFIG = {
    "provider": "mistral",
    "model": "mistral-embed",  # Default embedding model
    "generation_model": "mistral-medium-latest",  # Default generation model
    "temperature": 0.1,  # Lower temperature for more focused responses
    "max_tokens": 4000,
    "context_window": 8000,
}

# Storage settings
STORAGE_CONFIG = {
    "vector_db_type": "faiss",  # Options: "faiss", "chroma"
    "cache_enabled": True,
    "cache_type": "memory",  # Options: "memory", "redis"
    "cache_ttl": 3600,  # seconds
}

# Web server settings
SERVER_CONFIG = {
    "host": "localhost",
    "port": 8000,
    "debug": True,
    "reload": True,
}

# Logging settings
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_to_file": True,
    "log_file": os.path.join(BASE_DIR, "logs", "app.log"),
}

# API keys - should be loaded from environment variables in production
API_KEYS = {
    "mistral": os.environ.get("MISTRAL_API_KEY", ""),
}

# Ensure API keys are set
def validate_api_keys():
    """Validate that required API keys are set."""
    if not API_KEYS["mistral"]:
        raise ValueError(
            "MISTRAL_API_KEY is not set. Please set it as an environment variable."
        )

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(VECTORS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True) 