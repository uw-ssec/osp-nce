from transformers import AutoModelForCausalLM, AutoTokenizer,  BitsAndBytesConfig
import os
from urllib.request import urlretrieve
import logging
from typing import Literal
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain_huggingface import HuggingFaceEmbeddings


class LanguageModel():
    def __init__(self, 
                 model_name, 
                 model_path_prefix = None, 
                 model_source = None, 
                 generation_config = {}):
        
        self.model_name = model_name
        self.generation_config = generation_config or {}
        self.cache_path = os.path.join(os.path.dirname(__file__), "model_cache")
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
            os.makedirs(os.path.join(self.cache_path, "llm"))
        self.model_source = model_source 
        self.llm = None
    def load_language_model(self, 
                            model_name : str,
                            quantization: Literal["8bit", "4bit"]
                            ):
         # Define the quantization config
        if quantization == "8bit":
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        if quantization == "4bit":
            quantization_config = BitsAndBytesConfig(load_in_4bit=True)
       
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=os.path.join(self.cache_path, "llm"))

        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=os.path.join(self.cache_path, "llm"),
            device_map="auto",
            quantization_config=quantization_config
        )
        self.llm = model
        self.tokenizer = tokenizer
    
    def load_hg_pipeline(self):
        if self.llm and self.tokenizer:
            pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=self.generation_config.get("max_new_tokens", 512),
                temperature=self.generation_config.get("temperature", 0.8),
                do_sample=self.generation_config.get("do_sample", True),
                return_full_text=self.generation_config.get("return_full_text", False)
            )
            self.hg_pipeline = HuggingFacePipeline(pipeline=pipe)
        else:
            logging.info("Model and tokenizer not loaded. Cannot create pipeline.")
            return None
    async def inference(self, prompt):
        if self.hg_pipeline:
            response = self.hg_pipeline.ainvoke(prompt)
            return response
        else:
            logging.info("Model and tokenizer not loaded. Cannot create pipeline.")
            return None
            
         
    


