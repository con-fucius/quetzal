import requests
import json
import time
import os
import sys

BASE_URL = "http://127.0.0.1:5000"
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

def test_application_running():
    """Test if the application is running and properly initialized."""
    print("Testing if application is running...")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("assistant_initialized", False):
                    print("✅ Application is running and Research Assistant is properly initialized")
                    return True
                else:
                    print(f"❌ Application is running but Research Assistant failed to initialize: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"Attempt {attempt+1}/{MAX_RETRIES}: Application responded with status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1}/{MAX_RETRIES}: Connection error: {e}")
        
        # Wait before retrying
        if attempt < MAX_RETRIES - 1:
            print(f"Waiting {RETRY_DELAY} seconds before retry...")
            time.sleep(RETRY_DELAY)
    
    print("❌ Application is not running or not responding")
    return False

def process_url(url, folder_id=None):
    """Process a URL through the application."""
    print(f"Processing URL: {url}")
    
    data = {"url": url}
    if folder_id:
        data["folder_id"] = folder_id
        
    response = requests.post(f"{BASE_URL}/process-url", json=data, timeout=60)
    return response.json()

def upload_document(file_path, folder_id=None):
    """Upload a document to the application."""
    print(f"Uploading document: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return {"success": False, "error": "File not found"}
    
    files = {"file": open(file_path, "rb")}
    data = {}
    if folder_id:
        data["folder_id"] = folder_id
        
    response = requests.post(f"{BASE_URL}/upload-document", files=files, data=data, timeout=60)
    return response.json()

def ask_question(query, folder_id=None, chat_id=None):
    """Ask a question to the research assistant."""
    print(f"Asking question: {query[:50]}...")
    
    data = {"query": query}
    if folder_id:
        data["folder_id"] = folder_id
    if chat_id:
        data["chat_id"] = chat_id
        
    response = requests.post(f"{BASE_URL}/query", json=data, timeout=60)
    return response.json()

def get_folders():
    """Get all folders from the application."""
    response = requests.get(f"{BASE_URL}/get-folders")
    return response.json()

def run_test_plan():
    """Run the complete test plan according to the testing strategy."""
    print("\n" + "="*50)
    print("TESTING QUETZAL RESEARCH ASSISTANT")
    print("="*50)
    
    # Test 1: Application Startup
    print("\n1. TESTING APPLICATION STARTUP")
    print("-"*30)
    if not test_application_running():
        print("❌ Cannot continue with testing - application is not properly initialized")
        return False
    
    # Get folder ID for subsequent tests
    folders = get_folders()
    if folders.get("success", False):
        default_folder_id = folders["folders"][0]["id"]
        print(f"Using default folder ID: {default_folder_id}")
    else:
        print("❌ Failed to get folders")
        print(f"Error: {folders.get('error', 'Unknown error')}")
        default_folder_id = None
    
    # Test 2: Process URL
    print("\n2. TESTING URL PROCESSING")
    print("-"*30)
    scrapy_url = "https://docs.scrapy.org/en/latest/#"
    result = process_url(scrapy_url, default_folder_id)
    print("\nURL Processing Result:")
    print(json.dumps(result, indent=2))
    
    if result.get("success", False):
        print(f"✅ Successfully processed URL: {scrapy_url}")
    else:
        print(f"❌ Failed to process URL: {result.get('error', 'Unknown error')}")
        if not result.get("success") and "assistant not initialized" in result.get("error", ""):
            print("Cannot continue with testing - Research Assistant is not initialized")
            return False
    
    # Wait a moment for processing to complete
    print("Waiting 10 seconds for processing to complete...")
    time.sleep(10)
    
    # Test 3: Upload document
    print("\n3. TESTING DOCUMENT UPLOAD")
    print("-"*30)
    doc_path = "SmartResearchAssistant/local docs/OpenAI Agents SDK Documentation on Agents.md"
    upload_result = upload_document(doc_path, default_folder_id)
    print("\nDocument Upload Result:")
    print(json.dumps(upload_result, indent=2))
    
    if upload_result.get("success", False):
        print(f"✅ Successfully uploaded document: {doc_path}")
    else:
        print(f"❌ Failed to upload document: {upload_result.get('error', 'Unknown error')}")
    
    # Wait a moment for processing to complete
    print("Waiting 10 seconds for processing to complete...")
    time.sleep(10)
    
    # Test 4: Ask a question
    print("\n4. TESTING QUESTION ANSWERING")
    print("-"*30)
    query = "Tell me about raising a StopDownload exception from a handler for the bytes_received or headers_received signals using the Scrapy application framework for crawling web sites and how it stops the download of a given response? Generate a code example and the expected output"
    answer_result = ask_question(query, default_folder_id)
    
    if answer_result.get("success", False):
        print("✅ Successfully got an answer")
        print("\nAnswer:")
        print("="*80)
        print(answer_result.get("answer", "No answer provided"))
        print("="*80)
        
        print("\nSources:")
        for source in answer_result.get("sources", []):
            print(f"- {source.get('title')}: {source.get('source')}")
    else:
        print(f"❌ Failed to get an answer: {answer_result.get('error', 'Unknown error')}")
    
    print("\n" + "="*50)
    print("TESTING COMPLETE")
    print("="*50)
    return True

if __name__ == "__main__":
    success = run_test_plan()
    if not success:
        sys.exit(1) 