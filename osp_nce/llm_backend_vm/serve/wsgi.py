from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from libs.retriever import Retriever
from libs.generator import Generator
from libs.model_loader import ModelLoader

# generator = Generator() 
# model_loader = ModelLoader()

app = FastAPI() 

# Define request model for retrieval
class RetrieveRequest(BaseModel):
    documents: List[Dict[str, Any]]
    query: str
    embedding_model: str

@app.get("/retrieve/")
async def retrieve(request: RetrieveRequest):
    try:
        retriever = Retriever(model_name = request.embedding_model)
        retriever.create_vector_store(request.documents, collection_name="temp_collection")
        relevant_docs = retriever.retrieve_docs(request.query)
        return {relevant_docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/chat")
# async def chat():
#     params = {prompt_str, model_choice}
#     model = model_loader.load(model_choice)
#     generator.model = model
#     answer = generator.invoke(prompt_str)
#     return answer

# @app.get("/load_model")
# async def add_model():
#     params = {model_name_on_hugging_face}
#     model_loader.download(model_name_on_hugging_face)
#     return {"status": status}


# ## MOCKUP STREAMLIT INTERACTION
# # -> User uploads document

# # pdf.read(document)
# # json serialization code 

# # relevant_docs = requests.get("vm_endpoint/retrieve", {serialized_json, query})

# # Render docs (Please select the most relevant page)

# # Prompt Processing 
# # prompt_str = System Prompt + relevant_docs + query + (Any chat history we want to send)
# # answer = requests.get("vm_endpoint/chat", {prompt_str})
