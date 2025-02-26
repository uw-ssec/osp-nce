from transformers import AutoModelForCausalLM, AutoTokenizer,  BitsAndBytesConfig
import os
from langchain_huggingface import HuggingFaceEmbeddings
from urllib.request import urlretrieve


class ModelLoader():
    def __init__(self):
        self.model_cache = {}
        self.cache_path = os.path.join(os.path.dirname(__file__), "model_cache")
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        pass

    def get_embedding_model(self, model_name, model_path=None, download_model = True):
        if not download_model and model_path:
            embeddings = HuggingFaceEmbeddings(model_name=model_path, cache_folder = self.cache_path, model_kwargs={"local_files_only": True})
        else: 
            embeddings = HuggingFaceEmbeddings(model_name=model_name, cache_folder = self.cache_path)
        return embeddings
    
    def get_language_model(self, model_name, model_path=None, download_model = True):
    if model_path.exists() and not force:
        print(f"{model_name} model already exists at {model_path}")
        return model_path

    print(f"Downloading {model_name} model...")

    if source.startswith("http"):
        # Download from URL
        urlretrieve(source, model_path)
    else:
        raise ValueError("Source must be a valid URL.")

    print(f"{model_name} model cached at {model_path}")
    return model_path
    
