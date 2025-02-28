import streamlit as st
from PyPDF2 import PdfReader
import requests, json


st.title("Extension Review Chatbot - Upload Your Documents to start asking Questions")
st.markdown(
    "This chatbot displays retrieved documents immediately, then updates with the generated answer."
)


def _show_sidebar() -> None:
    "Display sidebar buttons for document viewing and upload"
    with st.sidebar:
        st.markdown("### Toolbar")
        st.write("*Below you'll find widgets for uploading and viewing documents.*")
        return st.sidebar.file_uploader(
            "Attach PDF documents", type=["pdf"], accept_multiple_files=True
        )


# Extract
def extract_text_from_uploaded_pdfs(pdfs):
    documents = []
    if pdfs:
        for pdf_file in pdfs:
            pages_text = []
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                pages_text.append(page.extract_text())
            documents.append({"filename": pdf_file.name, "content": pages_text})
    return documents


# Get files
uploaded_files = _show_sidebar()

# Get use input
user_question = st.text_input("Your question:")


if st.button("Submit Query") and user_question:
    payload = {
        "question": user_question,
        "documents": extract_text_from_uploaded_pdfs(uploaded_files),
    }
    st.write(payload)
    # # Replace with your API endpoint URL.
    # API_URL = st.secrets.get("API_URL", "http://localhost:8000")
    # response = requests.post(f"{API_URL}/api/query", json=payload, stream=True)

    # client = sseclient.SSEClient(response)

    # docs_displayed = False
    # final_answer = ""

    # for event in client.events():
    #     data = json.loads(event.data)
    #     if data["type"] == "docs" and not docs_displayed:
    #         st.subheader("Retrieved Document Chunks")
    #         for idx, chunk in enumerate(data["content"], start=1):
    #             st.write(f"**Chunk {idx}:** {chunk}")
    #         docs_displayed = True
    #     elif data["type"] == "final":
    #         final_answer = data["content"]
    #         st.subheader("Generated Response")
    #         st.write(final_answer)
