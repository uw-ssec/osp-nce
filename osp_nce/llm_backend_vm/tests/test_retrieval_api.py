from pathlib import Path
import requests
import json
from langchain.document_loaders import PyMuPDFLoader

def load_documents(pdf_folder: Path):
    """Loads PDFs from a given folder and extracts text."""
    documents = []
    for file in pdf_folder.glob("*.pdf"):
        loader = PyMuPDFLoader(str(file))
        docs = loader.load()
        for doc in docs:
            documents.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata  # Keep metadata intact
            })
    return documents

# Define API URL (update if running on a different port or host)
API_URL = "http://localhost:8000/retrieve/"

pdf_folder = Path("data/raw/test")

# Load documents
documents = load_documents(pdf_folder)

if not documents:
    print("❌ No documents found in the folder.")
    exit()

# Define test query
test_query = "When do you need to make an extension?"

# Define embedding model
embedding_model = "sentence-transformers/all-MiniLM-L12-v2"

# Construct request payload (ensuring documents are correctly formatted)
payload = {
    "documents": documents,  # List of document JSONs
    "query": test_query,
    "embedding_model": embedding_model
}

# Send POST request
try:
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()  # Raises error if response status is not 2xx

    # Parse response
    response_data = response.json()
    retrieved_docs = response_data.get("docs", [])
    status_code = response_data.get("status_code", 500)

    if status_code == 200:
        print("\n✅ Successfully retrieved documents:")
        for i, doc in enumerate(retrieved_docs):
            print(f"\n--- Document {i+1} ---")
            print(f"📄 Metadata: {doc.get('metadata', {})}")
            print(f"\n🔍 Content Preview:\n{doc.get('page_content', '')[:500]}...\n")
    else:
        print(f"❌ Retrieval failed with error: {response_data.get('error', 'Unknown error')}")

except requests.exceptions.RequestException as e:
    print(f"❌ API request failed: {e}")
