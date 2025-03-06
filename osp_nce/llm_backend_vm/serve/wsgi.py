from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from libs.retriever.retriever import Retriever
from langchain.schema import Document
import traceback
from libs.models.language_model import LanguageModel


app = FastAPI(title = "RAG Application") 

# Global model instance (lazy-loaded)
MODEL_INSTANCES = {}

class RetrieveRequest(BaseModel):
    documents: Optional[List[Dict[str,Any]]] = []
    query: str
    existing_collection: Optional[str] = None
    existing_qdrant_path: Optional[str] = None
    embedding_model: str

class GenerationRequest(BaseModel):
    prompt: str
    generation_model: str

def json_to_document(json_data):
    """Convert JSON dict to LangChain Document object."""
    return Document(
        page_content=json_data["page_content"],
        metadata=json_data["metadata"]
    )

@app.post("/retrieve/")
async def retrieve(request: RetrieveRequest):
    try:
        if request.documents:
            documents = [json_to_document(doc) for doc in request.documents]
            retriever = Retriever(model_name = request.embedding_model)
            retriever.create_vector_store(documents, collection_name="temp_collection")
        elif request.existing_collection and request.existing_qdrant_path:
            retriever = Retriever(model_name = request.embedding_model)
            retriever.get_vector_store(qdrant_path=request.existing_qdrant_path, collection_name=request.existing_collection)
        else:
            raise ValueError("No documents or existing collection provided for retrieval.")
        
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
        return {"docs" : [], "status_code" : 500, "error": str(e)}


def get_model(generation_model):
    """
    Retrieve or create a cached instance of the language model.
    """
    if generation_model not in MODEL_INSTANCES:
        MODEL_INSTANCES[generation_model] = LanguageModel(model_name=generation_model, quantization="8bit")
        MODEL_INSTANCES[generation_model].load_language_model()
        MODEL_INSTANCES[generation_model].load_hg_pipeline()
    return MODEL_INSTANCES[generation_model]

@app.post("/generate/")
async def generate(request: GenerationRequest):
    try:
        model = get_model(request.generation_model)
        response = model.inference(request.prompt)
        return {"answer": response, "status_code": 200} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500, reload=True)