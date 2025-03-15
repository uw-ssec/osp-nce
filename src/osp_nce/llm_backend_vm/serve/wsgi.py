""" 
This module defines the FastAPI application for the RAG service. 


We implement separate endpoints for retrieval and generation.
The retrieval endpoint accepts a query and a list of documents, and returns the most relevant documents based on the query.
The generation endpoint accepts a prompt and returns the generated text.

Implementing separate endpoints allows us to scale the retrieval and generation components independently.
"""


import traceback
from libs.models.language_model import LanguageModel
from langchain.schema import Document
from libs.retriever.retriever import Retriever
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException


app = FastAPI(title="RAG Application")

# Global model instance (lazy-loaded)
MODEL_INSTANCES = {}


class RetrieveRequest(BaseModel):
    """
    Defines request schema for the retrieval endpoint.
    """
    documents: Optional[List[Dict[str, Any]]] = []
    query: str
    existing_collection: Optional[str] = None
    existing_qdrant_path: Optional[str] = None
    embedding_model: str


class GenerationRequest(BaseModel):
    """
    Defines request schema for the generation endpoint.
    """
    prompt: str
    generation_model: str


def json_to_document(json_data):
    """
    Convert JSON dict to LangChain Document object.
    """
    return Document(
        page_content=json_data["page_content"],
        metadata=json_data["metadata"]
    )


@app.post("/retrieve/")
async def retrieve(request: RetrieveRequest):
    """
    Retrieve documents based on the query.

    Args:
        request: RetrieveRequest object containing the query and documents.

    Returns:
        Response object containing the retrieved documents and status code.
    """
    try:
        # if documents are provided, create a new collection
        if request.documents:
            documents = [json_to_document(doc) for doc in request.documents]
            retriever = Retriever(model_name=request.embedding_model)
            retriever.create_vector_store(
                documents, collection_name="temp_collection")

        # if existing collection and qdrant path are provided, use them
        elif request.existing_collection and request.existing_qdrant_path:
            retriever = Retriever(model_name=request.embedding_model)
            retriever.get_vector_store(
                qdrant_path=request.existing_qdrant_path, collection_name=request.existing_collection)
        else:
            raise ValueError(
                "No documents or existing collection provided for retrieval.")

        relevant_docs = retriever.retrieve_docs(request.query)

        # Format response properly
        response_data = [
            {
                "metadata": doc.metadata,
                "page_content": doc.page_content
            }
            for doc in relevant_docs
        ]

        return {"docs": response_data, "status_code": 200}

    except Exception as e:
        print("Error in retrieval:", str(e))  # Print error to logs
        print(traceback.format_exc())  # Print full traceback
        return {"docs": [], "status_code": 500, "error": str(e)}


def get_model(generation_model):
    """
    Retrieve or create a cached instance of the language model.
    """
    if generation_model not in MODEL_INSTANCES:
        MODEL_INSTANCES[generation_model] = LanguageModel(
            model_name=generation_model, quantization="8bit")
        MODEL_INSTANCES[generation_model].load_language_model()
        MODEL_INSTANCES[generation_model].load_hg_pipeline()
    return MODEL_INSTANCES[generation_model]


@app.post("/generate/")
async def generate(request: GenerationRequest):
    """
    Generate text based on the prompt.

    Args:
        request: GenerationRequest object containing the prompt and model name.
    Returns:
        Response object containing the generated text and status code.
    """
    try:
        model = get_model(request.generation_model)
        response = model.inference(request.prompt)
        return {"answer": response, "status_code": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
