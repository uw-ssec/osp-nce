import json
import requests
import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO

# from sseclient import SSEClient


def show_sidebar() -> list:
    """
    Shows a file uploader in the sidebar for PDF documents.

    Returns:
        list: A list of uploaded PDF files (in-memory) from Streamlit.
    """
    with st.sidebar:
        st.markdown("### Toolbar")
        st.markdown("*Below you'll find widgets for uploading and viewing documents.*")

        uploaded = st.file_uploader(
            "Attach PDF documents", type=["pdf"], accept_multiple_files=True
        )

    return uploaded


def extract_text_from_uploaded_pdfs(pdfs) -> list:
    """
    Extract text from each page of the uploaded PDFs.

    Args:
        pdfs (list): A list of uploaded PDF files (from Streamlit).

    Returns:
        list[dict]: Each dict contains {"filename": ..., "content": [...]},
                    where 'content' is a list of page texts.
    """
    documents = []
    for pdf_file in pdfs:
        pdf_reader = PdfReader(pdf_file)
        pages_text = [page.extract_text() or "" for page in pdf_reader.pages]
        documents.append({"filename": pdf_file.name, "content": pages_text})
    return documents


def send_query_with_sse(payload: dict, api_url: str) -> None:
    """
    Sends the query payload to the backend and processes each event
    """
    # Make sure the endpoint includes the SSE route, e.g. "/api/query"
    # response = requests.post(api_url, json=payload, stream=True)
    # client = SSEClient(response)

    # We’ll store partial tokens here (if the backend emits a 'token' event).
    # partial_answer = ""

    # for event in client.events():
    #     if not event.data:
    #         continue

    #     data = json.loads(event.data)
    #     evt_type = data.get("type", "")
    #     content = data.get("content", "")

    #     if evt_type == "docs":
    #         # Display retrieved document chunks
    #         st.subheader("Retrieved Document Chunks")
    #         for idx, chunk in enumerate(content, start=1):
    #             st.write(f"**Chunk {idx}:** {chunk}")

    #     elif evt_type == "token":
    #         # If your backend streams partial tokens, you can accumulate them
    #         partial_answer += content
    #         # Display partial answer in a live chat message or placeholder
    #         with st.chat_message("assistant"):
    #             st.write(partial_answer)

    #     elif evt_type == "final":
    #         # Final message from the backend
    #         st.subheader("Generated Response")
    #         st.write(content)


def run():
    """
    Main entry point of the Streamlit app. Displays a chat-like interface
    for the RAG system.
    """
    st.title("Extension Review Chatbot")
    st.markdown(
        "Upload PDFs on the left and enter a question below. "
        "The system retrieves relevant chunks, then streams the final answer."
    )

    uploaded_files = show_sidebar()
    user_question = st.text_input("Your question:")

    if st.button("Submit Query") and user_question:
        documents_data = extract_text_from_uploaded_pdfs(uploaded_files)
        payload = {"question": user_question, "documents": documents_data}

        # Display what we're sending (for debugging)
        st.write("Payload:", payload)


if __name__ == "__page__":
    run()
