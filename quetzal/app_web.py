import os
import json
import uuid
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from research_assistant import ResearchAssistant, ResearchAssistantError
from models import db, Folder, Document, Chat, Message

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# SECURITY WARNING: Hardcoded default secret key is insecure.
# In production, SECRET_KEY MUST be set as a strong, random environment variable.
# Consider raising an error if SECRET_KEY is not set in production environments.
# Example secure approach:
# app.secret_key = os.environ.get("SECRET_KEY")
# if not app.secret_key:
#     raise ValueError("SECRET_KEY environment variable not set. Cannot run without it.")
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_for_testing") # Placeholder: Original insecure code left for now
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quetzal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Research Assistant with API keys
assistant = None
initialization_error = None

try:
    assistant = ResearchAssistant(
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        weaviate_api_key=os.environ.get("WEAVIATE_API_KEY"),
        weaviate_url=os.environ.get("WEAVIATE_URL")
    )
    print("Research Assistant initialized successfully.")
except ResearchAssistantError as e:
    initialization_error = str(e)
    print(f"Error initializing Research Assistant: {initialization_error}")
except Exception as e:
    initialization_error = str(e)
    print(f"Unexpected error initializing Research Assistant: {initialization_error}")

# Create database tables
with app.app_context():
    db.create_all()
    # Create default folder if it doesn't exist
    if not Folder.query.filter_by(name="Default").first():
        default_folder = Folder(name="Default", description="Default folder for documents and chats")
        db.session.add(default_folder)
        db.session.commit()

@app.route("/")
def index():
    """Render the main interface."""
    return render_template("index.html")

@app.route("/status")
def status():
    """Return the status of the Research Assistant initialization."""
    return jsonify({
        "assistant_initialized": assistant is not None,
        "error": initialization_error
    })

@app.route("/process-url", methods=["POST"])
def process_url():
    """Process a URL and store in the vector database."""
    data = request.json
    url = data.get("url")
    folder_id = data.get("folder_id")
    
    if not url:
        return jsonify({"success": False, "error": "No URL provided"})
    
    if assistant is None:
        return jsonify({
            "success": False, 
            "error": f"Research Assistant not initialized. Error: {initialization_error}"
        })
    
    try:
        # Process the URL and store document
        result = assistant.process_and_store_document(url, folder_id=folder_id)
        
        if result["success"]:
            # Save document in database
            doc = Document(
                title=result["title"],
                source=url,
                vector_id=result["document_ids"][0] if result["document_ids"] else None,
                folder_id=folder_id,
                document_type="url"
            )
            db.session.add(doc)
            db.session.commit()
            
            # Update result with database ID
            result["document_id"] = doc.id
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/upload-document", methods=["POST"])
def upload_document():
    """Upload and process a document."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"})
    
    if assistant is None:
        return jsonify({
            "success": False, 
            "error": f"Research Assistant not initialized. Error: {initialization_error}"
        })
    
    file = request.files["file"]
    folder_id = request.form.get("folder_id")
    
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"})
    
    # Check file type (pdf, txt, md)
    allowed_extensions = {"pdf", "txt", "md"}
    file_ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_extensions:
        return jsonify({
            "success": False, 
            "error": f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        })
    
    try:
        # SECURITY WARNING: Saving uploads with user-provided filenames without sanitization is risky (Path Traversal).
        # Also, using a predictable temp directory can be insecure.
        # RECOMMENDATION:
        # 1. Sanitize the filename using `werkzeug.utils.secure_filename`.
        # 2. Use the `tempfile` module for secure temporary file creation and management.
        # Example (conceptual):
        # import tempfile
        # from werkzeug.utils import secure_filename
        # original_filename = secure_filename(file.filename)
        # if not original_filename: raise ValueError("Invalid filename")
        # file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        # with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}", dir="<secure_temp_dir>") as tmp_file:
        #     file.save(tmp_file.name)
        #     temp_path = tmp_file.name
        #     # ... process temp_path ...
        #     # Ensure cleanup in a finally block: if temp_path and os.path.exists(temp_path): os.remove(temp_path)

        # Placeholder: Original insecure code left for now
        # Save the file to disk temporarily
        temp_path = f"temp_{uuid.uuid4()}.{file_ext}"
        file.save(temp_path)
        
        # Process the file
        result = assistant.process_and_store_document(temp_path, folder_id=folder_id)
        
        # Clean up the temporary file
        os.remove(temp_path)
        
        if result["success"]:
            # Save document in database
            doc = Document(
                title=result["title"],
                source=file.filename,
                vector_id=result["document_ids"][0] if result["document_ids"] else None,
                folder_id=folder_id,
                document_type="file"
            )
            db.session.add(doc)
            db.session.commit()
            
            # Update result with database ID
            result["document_id"] = doc.id
        
        return jsonify(result)
    except Exception as e:
        # Clean up if there was an error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)})

@app.route("/query", methods=["POST"])
def query():
    """Query the research assistant."""
    data = request.json
    query_text = data.get("query")
    chat_id = data.get("chat_id")
    folder_id = data.get("folder_id")
    search_type = data.get("search_type", "hybrid")
    
    if not query_text:
        return jsonify({"success": False, "error": "No query provided"})
    
    if assistant is None:
        return jsonify({
            "success": False, 
            "error": f"Research Assistant not initialized. Error: {initialization_error}"
        })
        
    try:
        # Get chat or create a new one
        if not chat_id:
            chat = Chat(
                title=query_text[:30] + "..." if len(query_text) > 30 else query_text,
                folder_id=folder_id
            )
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        else:
            chat = Chat.query.get(chat_id)
            if not chat:
                return jsonify({"success": False, "error": "Invalid chat ID"})
        
        # Save user message
        user_message = Message(
            chat_id=chat_id,
            role="user",
            content=query_text
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get answer from the research assistant
        result = assistant.answer_query(query_text, search_type=search_type, folder_id=folder_id)
        
        # Save assistant message
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources")
        )
        db.session.add(assistant_message)
        
        # Update chat title if it's the first message
        message_count = Message.query.filter_by(chat_id=chat_id).count()
        if message_count <= 2:  # User message + assistant response we just added
            chat.title = query_text[:30] + "..." if len(query_text) > 30 else query_text
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "chat_id": chat_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/new-chat", methods=["GET"])
def new_chat():
    """Create a new chat."""
    folder_id = request.args.get("folder_id")
    
    try:
        chat = Chat(title="New Chat", folder_id=folder_id)
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "chat_id": chat.id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get-chats", methods=["GET"])
def get_chats():
    """Get list of all chats, optionally filtered by folder."""
    folder_id = request.args.get("folder_id")
    
    try:
        query = Chat.query.order_by(Chat.updated_at.desc())
        
        if folder_id:
            query = query.filter_by(folder_id=folder_id)
            
        chats = query.all()
        
        return jsonify({
            "success": True,
            "chats": [chat.to_dict() for chat in chats]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get-chat-history", methods=["POST"])
def get_chat_history():
    """Get chat history for a specific chat."""
    data = request.json
    chat_id = data.get("chat_id")
    
    if not chat_id:
        return jsonify({"success": False, "error": "No chat ID provided"})
    
    try:
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
        
        return jsonify({
            "success": True,
            "history": [message.to_dict() for message in messages]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rename-chat", methods=["POST"])
def rename_chat():
    """Rename a chat."""
    data = request.json
    chat_id = data.get("chat_id")
    title = data.get("title")
    
    if not chat_id or not title:
        return jsonify({"success": False, "error": "Chat ID and title are required"})
    
    try:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat not found"})
        
        chat.title = title
        chat.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/delete-chat", methods=["POST"])
def delete_chat():
    """Delete a chat."""
    data = request.json
    chat_id = data.get("chat_id")
    
    if not chat_id:
        return jsonify({"success": False, "error": "No chat ID provided"})
    
    try:
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat not found"})
        
        db.session.delete(chat)  # This will cascade delete all messages
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get-folders", methods=["GET"])
def get_folders():
    """Get list of all folders."""
    try:
        # Only get top-level folders
        folders = Folder.query.filter_by(parent_id=None).all()
        
        return jsonify({
            "success": True,
            "folders": [folder.to_dict() for folder in folders]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/create-folder", methods=["POST"])
def create_folder():
    """Create a new folder."""
    data = request.json
    name = data.get("name")
    description = data.get("description")
    parent_id = data.get("parent_id")
    
    if not name:
        return jsonify({"success": False, "error": "Folder name is required"})
    
    try:
        folder = Folder(
            name=name,
            description=description,
            parent_id=parent_id
        )
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "folder": folder.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/update-folder", methods=["POST"])
def update_folder():
    """Update a folder's name or description."""
    data = request.json
    folder_id = data.get("folder_id")
    name = data.get("name")
    description = data.get("description")
    
    if not folder_id or not name:
        return jsonify({"success": False, "error": "Folder ID and name are required"})
    
    try:
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"success": False, "error": "Folder not found"})
        
        folder.name = name
        folder.description = description
        folder.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "folder": folder.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/delete-folder", methods=["POST"])
def delete_folder():
    """Delete a folder."""
    data = request.json
    folder_id = data.get("folder_id")
    
    if not folder_id:
        return jsonify({"success": False, "error": "Folder ID is required"})
    
    try:
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"success": False, "error": "Folder not found"})
        
        # Prevent deletion of default folder
        if folder.name == "Default":
            return jsonify({"success": False, "error": "Cannot delete the default folder"})
        
        # Move contents to default folder or handle as needed
        default_folder = Folder.query.filter_by(name="Default").first()
        
        # Move chats to default folder
        Chat.query.filter_by(folder_id=folder_id).update({"folder_id": default_folder.id})
        
        # Move documents to default folder
        Document.query.filter_by(folder_id=folder_id).update({"folder_id": default_folder.id})
        
        # Delete folder and commit changes
        db.session.delete(folder)
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/get-documents", methods=["GET"])
def get_documents():
    """Get list of documents, optionally filtered by folder."""
    folder_id = request.args.get("folder_id")
    
    try:
        query = Document.query.order_by(Document.updated_at.desc())
        
        if folder_id:
            query = query.filter_by(folder_id=folder_id)
            
        documents = query.all()
        
        return jsonify({
            "success": True,
            "documents": [doc.to_dict() for doc in documents]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/move-to-folder", methods=["POST"])
def move_to_folder():
    """Move a document or chat to a different folder."""
    data = request.json
    item_type = data.get("type")  # "document" or "chat"
    item_id = data.get("id")
    folder_id = data.get("folder_id")
    
    if not item_type or not item_id or not folder_id:
        return jsonify({
            "success": False, 
            "error": "Item type, ID, and target folder ID are required"
        })
    
    try:
        # Verify folder exists
        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"success": False, "error": "Target folder not found"})
        
        # Move item to folder
        if item_type == "document":
            doc = Document.query.get(item_id)
            if not doc:
                return jsonify({"success": False, "error": "Document not found"})
            doc.folder_id = folder_id
        elif item_type == "chat":
            chat = Chat.query.get(item_id)
            if not chat:
                return jsonify({"success": False, "error": "Chat not found"})
            chat.folder_id = folder_id
        else:
            return jsonify({"success": False, "error": "Invalid item type"})
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/theme", methods=["POST"])
def set_theme():
    """Set the user's theme preference."""
    data = request.json
    theme = data.get("theme")
    
    if theme not in ["light", "dark"]:
        return jsonify({"success": False, "error": "Invalid theme"})
    
    session["theme"] = theme
    
    return jsonify({"success": True})

@app.route("/theme", methods=["GET"])
def get_theme():
    """Get the user's theme preference."""
    theme = session.get("theme", "light")
    
    return jsonify({
        "success": True,
        "theme": theme
    })

if __name__ == "__main__":
    # SECURITY WARNING: The Flask development server (`app.run`) is NOT suitable for production.
    # Running with `debug=True` exposes an interactive debugger and potential RCE.
    # Running with `host="0.0.0.0"` makes the server accessible externally.
    # RECOMMENDATION: Use a production-grade WSGI server (e.g., Gunicorn, uWSGI) for deployment.
    # For development, consider loading debug/host settings from environment variables.
    # Example:
    # is_debug = os.environ.get("FLASK_DEBUG", "True").lower() in ['true', '1', 't']
    # host_setting = os.environ.get("FLASK_HOST", "127.0.0.1") # Default to localhost for safety
    # app.run(host=host_setting, port=port, debug=is_debug)

    # Placeholder: Original insecure code left for now
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Quetzal Research Assistant on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)