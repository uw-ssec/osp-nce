import os
import textwrap

import requests
import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader

LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L12-v2"
GENERATION_MODEL = "allenai/OLMo-2-1124-7B-Instruct"
EXISTING_COLLECTION = None
EXISTING_QDRANT_PATH = None
RETRIEVAL_K = 2  # Number of relevant documents to retrieve


# TODO: Update for grants
def expand_query(query: str) -> str:
    """
    Modify the query for better retrieval.
    """
    if "Rubin" in query:
        query += " LSST Large Synoptic Survey Telescope"
    return query


# TODO: Update for our use case
def format_prompt(context: str, question: str) -> str:
    """
    Format the retrieval context into the final prompt.
    """
    prompt = textwrap.dedent(f"""
        You are an astrophysics expert with a focus on the Rubin telescope project 
        (formerly known as Large Synoptic Survey Telescope - LSST). Please answer the 
        question on astrophysics based on the following context:

        {context}

        Question: {question}
    """)
    return prompt.strip()


def process_uploaded_files(uploaded_files: list) -> list[dict]:
    """
    Reads uploaded PDF files and extracts text + metadata.
    """
    documents = []
    if not uploaded_files:
        return documents

    for uploaded_file in uploaded_files:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load PDF content using PyMuPDF
        loader = PyMuPDFLoader(uploaded_file.name)
        pages = loader.load()
        for page in pages:
            documents.append(
                {
                    "page_content": page.page_content,
                    "metadata": page.metadata,
                }
            )
    return documents


def retrieve_documents(documents: list[dict], query: str) -> list[dict]:
    """
    Call the retrieval API and return retrieved documents based on the query.
    """
    payload = {
        "documents": documents,
        "query": expand_query(query),
        "existing_collection": EXISTING_COLLECTION,
        "existing_qdrant_path": EXISTING_QDRANT_PATH,
        "embedding_model": EMBEDDING_MODEL,
    }
    try:
        response = requests.post(f"{LLM_API_BASE_URL}/retrieve/", json=payload)
        if response.status_code == 200:
            return response.json().get("docs", [])
        else:
            st.error("Retrieval API returned a non-200 status.")
    except Exception as e:
        st.error(f"❌ Retrieval API failed: {e}")
    return []


def generate_response(prompt: str) -> str:
    """
    Call the generation API with the given prompt and return the generated answer.
    """
    payload = {
        "prompt": prompt,
        "generation_model": GENERATION_MODEL,
    }
    try:
        response = requests.post(f"{LLM_API_BASE_URL}/generate/", json=payload)
        if response.status_code == 200:
            return response.json().get("answer", "")
        else:
            st.error("Generation API returned a non-200 status.")
    except Exception as e:
        st.error(f"❌ Generation API failed: {e}")
    return "⚠️ Failed to generate response."


def get_uploaded_documents() -> list:
    """
    Retrieve user uploads from a file uploader with some help text in the sidebar.
    """
    with st.sidebar:
        st.markdown("### Toolbar")
        uploaded_files = st.file_uploader(
            "Attach documents (PDFs)", type=["pdf"], accept_multiple_files=True
        )
        return uploaded_files


def display_chat_history() -> None:
    """
    Show the LLM response history (in state) alongside retrieved document chunks.
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("chunks"):
                st.markdown("### Retrieved Document Chunks:")
                for chunk in message["chunks"]:
                    st.markdown(f"- {chunk}")


def run_chat_loop(documents: list[dict]) -> None:
    """
    Process new user queries in a loop and generate responses using retrieved documents.
    """
    query = st.chat_input("Your question:")
    if not query:
        return

    # Append user's query to session history
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner("Retrieving relevant documents..."):
        retrieved_docs = retrieve_documents(documents, query)

    # Prepare text from retrieved documents
    retrieved_text = "\n\n".join(doc["page_content"][:500] for doc in retrieved_docs)
    if retrieved_docs:
        with st.chat_message("assistant"):
            st.markdown("### Retrieved Document Chunks:")
            for doc in retrieved_docs:
                st.markdown(f"- {doc['page_content'][:500]}")

    # Format the generation queryand await a response
    with st.spinner("Generating response..."):
        prompt = format_prompt(retrieved_text, query)
        generated_answer = generate_response(prompt)

    # Store and display the generated response
    assistant_message = {
        "role": "assistant",
        "content": generated_answer,
        "chunks": [doc["page_content"][:500] for doc in retrieved_docs],
    }
    st.session_state.messages.append(assistant_message)
    with st.chat_message("assistant"):
        st.markdown(generated_answer)


def run() -> None:
    """
    Instantiate the chatbot page.
    """
    st.title("Interactive PDF Chat - Upload and Ask")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Retrieve and process uploaded files
    uploaded_files = get_uploaded_documents()
    documents = process_uploaded_files(uploaded_files)

    # Display chat history and handle user queries
    display_chat_history()
    run_chat_loop(documents)


if __name__ == "__page__":
    run()
