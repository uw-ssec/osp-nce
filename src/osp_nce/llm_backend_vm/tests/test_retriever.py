from pathlib import Path
from libs.retriever.retriever import Retriever  # Adjust path based on your module structure
from langchain.document_loaders import PyMuPDFLoader

# Function to load and convert documents
def load_documents(pdf_folder: Path):
    """Loads PDFs from a given folder and extracts text."""
    documents = []
    for file in pdf_folder.glob("*.pdf"):
        loader = PyMuPDFLoader(str(file))
        documents.extend(loader.load())
    return documents

# Test function
def test_retriever():
    # Path to test PDFs
    pdf_folder = Path("data/raw/test/")

    # Load documents
    documents = load_documents(pdf_folder)
    
    if not documents:
        print("No documents found in the test directory.")
        return

    # Print datatype of documents
    print(f"Datatype of documents: {type(documents)}")
    # Initialize Retriever
    model_name = "sentence-transformers/all-MiniLM-L12-v2"  # Change this to the actual model
    retriever = Retriever(model_name=model_name)

    # Create vector store
    retriever.create_vector_store(documents, collection_name="test_collection")

    # Sample query
    query = "When do you need to make an extension?"
    retrieved_docs = retriever.retrieve_docs(query)

    print("\n🔍 Retrieved Documents:")
    for i, doc in enumerate(retrieved_docs):
        print(f"\n--- Document {i+1} ---")
        print(f"File: {doc.metadata.get('file_path', 'Unknown File')}")
        print(f"Page: {doc.metadata.get('page', 'N/A')+1}/{doc.metadata.get('total_pages', 'Unknown')}")
        print(f"Created On: {doc.metadata.get('creationDate', 'Unknown')}")
        print(f"Doc ID: {doc.metadata.get('_id', 'Unknown ID')}")
        print(f"\n🔍 Content Preview:\n{doc.page_content[:500]}...\n")  

# Run the test
if __name__ == "__main__":
    test_retriever()
