import os
from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model(model_name: str) -> HuggingFaceEmbeddings:
    """
    Returns an instance of a cached embedding model.

    Parameters:
        model_name (str): The name/identifier of the embedding model to use.

    Returns:
        HuggingFaceEmbeddings: An instance of the embedding model.
    """
    cache_path = os.path.join(os.path.dirname(__file__), "model_cache", "embeddings")
    os.makedirs(cache_path, exist_ok=True)
    
    model_path = os.path.join(cache_path, model_name.replace("/", "_"))
    
    return HuggingFaceEmbeddings(model_name=model_name, cache_folder=model_path)