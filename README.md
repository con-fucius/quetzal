# Quetzal - Smart Research Assistant

A web-based research assistant that helps users process, organize, and chat with their documents using AI.

## Features

- Process URLs and extract content
- Organize documents in folders
- Chat with documents using AI
- Dark/light mode support
- Gradient blue theme
- Document search and retrieval

## Installation

1. Clone the repository

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following content:

```
FLASK_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SQLALCHEMY_DATABASE_URI=sqlite:///database.db
```

4. Run the application:

```bash
python SmartResearchAssistant/app_web.py
```

5. Open your browser and visit `http://localhost:5000`

## Usage

1. Process URLs by clicking on the "Process URL" button in the sidebar
2. Create folders to organize your documents
3. Chat with your documents by selecting them from the sidebar
4. Use the search functionality to find specific information
5. Toggle between dark and light mode using the theme switch in the top right corner

## Technologies Used

- Python (Flask)
- SQLAlchemy for database management
- Weaviate for vector storage and search
- OpenAI, Mistral, and Anthropic for AI processing
- Custom gradient-blue CSS theme
- Font Awesome for icons
- Highlight.js for code highlighting
- Marked.js for Markdown parsing 
